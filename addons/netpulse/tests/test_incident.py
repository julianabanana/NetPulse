from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNetpulse(TransactionCase):
    def setUp(self):
        super().setUp()
        group_tech = self.env.ref("netpulse.group_netpulse_technician")
        self.tech = self.env["res.users"].create({
            "name": "Tec Test", "login": "tec_test", "groups_id": [(6, 0, [group_tech.id])],
        })
        self.sw2 = self.env["netpulse.device"].create({"name": "SW2-T", "criticality": "critical"})

    def test_critical_down_creates_one_incident(self):
        self.sw2.update_status(False)
        self.sw2.update_status(False)  # el segundo ciclo no duplica
        incidents = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents.priority, "2")
        self.assertEqual(incidents.origin, "auto")

    def test_normal_device_does_not_create_incident(self):
        dev = self.env["netpulse.device"].create({"name": "R-normal"})
        dev.update_status(False)
        self.assertFalse(self.env["netpulse.incident"].search([("device_id", "=", dev.id)]))

    def test_invalid_transition(self):
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        inc.technician_id = self.tech
        with self.assertRaises(ValidationError):
            inc.write({"state": "resolved"})  # no puede saltar En proceso
        inc.action_start()
        inc.action_resolve()
        self.assertTrue(inc.date_resolved)

    def test_technician_cannot_delete_device_or_reassign(self):
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        inc.technician_id = self.tech
        with self.assertRaises(AccessError):
            self.sw2.with_user(self.tech).unlink()
        with self.assertRaises(AccessError):
            inc.with_user(self.tech).write({"priority": "0"})

    def test_assignment_requires_a_netpulse_technician(self):
        ordinary_user = self.env["res.users"].create({
            "name": "Usuario sin rol técnico",
            "login": "ordinary_netpulse_test",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        incident = self.env["netpulse.incident"].create({"device_id": self.sw2.id})
        with self.assertRaises(ValidationError):
            incident.write({"technician_id": ordinary_user.id})

    def test_technician_creation_forces_safe_defaults_and_self_assignment(self):
        other_tech = self.env["res.users"].create({
            "name": "Otro técnico",
            "login": "other_tech_test",
            "groups_id": [(6, 0, [self.env.ref("netpulse.group_netpulse_technician").id])],
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

    def test_device_recovery_posts_message_on_incident(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search(
            [("device_id", "=", self.sw2.id)], limit=1
        )
        messages_before = len(incident.message_ids)

        self.sw2.update_status(True)

        self.assertGreater(len(incident.message_ids), messages_before)

    def test_incident_name_assigned_from_sequence(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search(
            [("device_id", "=", self.sw2.id)], limit=1
        )

        self.assertTrue(incident.name.startswith("INC-"))

    def test_resolved_incident_cannot_reopen(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search(
            [("device_id", "=", self.sw2.id)], limit=1
        )
        incident.write({"technician_id": self.tech.id})
        incident.action_start()
        incident.action_resolve()

        with self.assertRaises(ValidationError):
            incident.write({"state": "in_progress"})

    def test_duplicate_open_incident_raises_validation_error(self):
        self.sw2.update_status(False)

        with self.assertRaises(ValidationError):
            self.env["netpulse.incident"].create({
                "device_id": self.sw2.id,
                "origin": "manual",
                "priority": "1",
            })

    def test_priority_values_are_all_valid(self):
        dev = self.env["netpulse.device"].create({
            "name": "SW-priority-test",
        })

        for priority_value in ("0", "1", "2"):
            incident = self.env["netpulse.incident"].create({
                "device_id": dev.id,
                "origin": "manual",
                "priority": priority_value,
            })

            self.assertEqual(incident.priority, priority_value)

            incident.write({"technician_id": self.tech.id})
            incident.action_start()
            incident.action_resolve()

    def test_technician_cannot_modify_origin_on_incident(self):
        self.sw2.update_status(False)
        incident = self.env["netpulse.incident"].search(
            [("device_id", "=", self.sw2.id)], limit=1
        )
        incident.write({"technician_id": self.tech.id})

        with self.assertRaises(AccessError):
            incident.with_user(self.tech).write({"origin": "manual"})
