from odoo.exceptions import AccessError, UserError, ValidationError
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNetpulse(TransactionCase):
    def setUp(self):
        super().setUp()
        group_tech = self.env.ref("netpulse.group_netpulse_technician")
        self.tech = self.env["res.users"].create({
            "name": "Tec Test",
            "login": "tec_test",
            "groups_id": [(6, 0, [group_tech.id])],
        })
        self.sw2 = self.env["netpulse.device"].create({
            "name": "SW2-T",
            "criticality": "critical",
        })

    # Device behavior

    def test_critical_down_creates_one_incident(self):
        self.sw2.update_status(False)
        self.sw2.update_status(False)

        incidents = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents.priority, "2")
        self.assertEqual(incidents.origin, "auto")

    def test_normal_device_does_not_create_incident(self):
        device = self.env["netpulse.device"].create({"name": "R-normal"})

        device.update_status(False)

        self.assertFalse(self.env["netpulse.incident"].search([
            ("device_id", "=", device.id),
        ]))

    def test_device_name_must_be_unique(self):
        self.env["netpulse.device"].create({"name": "UNIQUE-SW"})

        # The SQL UNIQUE constraint raises an IntegrityError. Use a savepoint
        # so the expected database error does not leave the test transaction
        # in an aborted state.
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["netpulse.device"].create({"name": "UNIQUE-SW"})

    def test_device_status_unknown_to_up_sets_up(self):
        device = self.env["netpulse.device"].create({"name": "R-unknown"})
        self.assertEqual(device.status, "unknown")

        device.update_status(True)

        self.assertEqual(device.status, "up")

    def test_device_recovery_posts_message_on_incident(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        messages_before = len(incident.message_ids)

        self.sw2.update_status(True)

        self.assertGreater(len(incident.message_ids), messages_before)

    def test_non_critical_device_recovery_does_not_create_incident(self):
        device = self.env["netpulse.device"].create({
            "name": "R-normal-recovery",
            "criticality": "normal",
        })

        device.update_status(False)
        device.update_status(True)

        self.assertFalse(self.env["netpulse.incident"].search([
            ("device_id", "=", device.id),
        ]))

    def test_technician_cannot_delete_device(self):
        with self.assertRaises(AccessError):
            self.sw2.with_user(self.tech).unlink()

    # Incident behavior

    def test_incident_name_is_assigned_from_sequence(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)

        self.assertTrue(incident.name.startswith("INC-"))

    def test_incident_requires_technician_to_start(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        self.assertFalse(incident.technician_id)

        with self.assertRaises(UserError):
            incident.action_start()

    def test_invalid_transition_cannot_skip_in_progress(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech

        with self.assertRaises(ValidationError):
            incident.write({"state": "resolved"})

        incident.action_start()
        incident.action_resolve()
        self.assertTrue(incident.date_resolved)

    def test_resolved_incident_cannot_be_reopened(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech
        incident.action_start()
        incident.action_resolve()

        with self.assertRaises(ValidationError):
            incident.write({"state": "in_progress"})

    def test_duplicate_open_incident_is_rejected(self):
        self.sw2.update_status(False)

        with self.assertRaises(ValidationError):
            self.env["netpulse.incident"].create({
                "device_id": self.sw2.id,
                "origin": "manual",
                "priority": "1",
            })

    def test_assignment_requires_a_netpulse_technician(self):
        ordinary_user = self.env["res.users"].create({
            "name": "Usuario sin rol técnico",
            "login": "ordinary_netpulse_test",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        incident = self.env["netpulse.incident"].create({
            "device_id": self.sw2.id,
        })

        with self.assertRaises(ValidationError):
            incident.write({"technician_id": ordinary_user.id})

    def test_technician_creation_forces_safe_defaults_and_self_assignment(self):
        other_tech = self.env["res.users"].create({
            "name": "Otro técnico",
            "login": "other_tech_test",
            "groups_id": [(6, 0, [
                self.env.ref("netpulse.group_netpulse_technician").id,
            ])],
        })

        incident = self.env["netpulse.incident"].with_user(self.tech).create({
            "device_id": self.sw2.id,
            "technician_id": other_tech.id,
            "priority": "2",
            "state": "resolved",
            "origin": "auto",
        })

        self.assertEqual(incident.technician_id, self.tech)
        self.assertEqual(incident.priority, "1")
        self.assertEqual(incident.state, "pending")
        self.assertEqual(incident.origin, "manual")
        self.assertFalse(incident.date_resolved)

    def test_all_priority_values_are_valid(self):
        device = self.env["netpulse.device"].create({
            "name": "SW-priority-test",
        })

        for priority in ("0", "1", "2"):
            incident = self.env["netpulse.incident"].create({
                "device_id": device.id,
                "origin": "manual",
                "priority": priority,
            })
            self.assertEqual(incident.priority, priority)

            # Resolve each incident before creating the next one for this device.
            incident.write({"technician_id": self.tech.id})
            incident.action_start()
            incident.action_resolve()

    def test_is_open_is_true_before_resolution(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)

        self.assertEqual(incident.state, "pending")
        self.assertTrue(incident.is_open)

        incident.technician_id = self.tech
        incident.action_start()
        self.assertTrue(incident.is_open)

    def test_is_open_is_false_after_resolution(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech
        incident.action_start()
        incident.action_resolve()

        self.assertFalse(incident.is_open)

    def test_technician_cannot_reassign_incident(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech

        with self.assertRaises(AccessError):
            incident.with_user(self.tech).write({"priority": "0"})

    def test_technician_cannot_modify_incident_device(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech
        other_device = self.env["netpulse.device"].create({
            "name": "SW-other",
        })

        with self.assertRaises(AccessError):
            incident.with_user(self.tech).write({
                "device_id": other_device.id,
            })

    def test_technician_cannot_modify_incident_origin(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search([
            ("device_id", "=", self.sw2.id),
        ], limit=1)
        incident.technician_id = self.tech

        with self.assertRaises(AccessError):
            incident.with_user(self.tech).write({"origin": "manual"})

