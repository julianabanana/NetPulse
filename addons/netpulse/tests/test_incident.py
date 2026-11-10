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
