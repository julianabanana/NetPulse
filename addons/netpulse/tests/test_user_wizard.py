from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNetpulseUserWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.admin_group = self.env.ref("netpulse.group_netpulse_admin")
        self.tech_group = self.env.ref("netpulse.group_netpulse_technician")
        self.admin = self.env["res.users"].create({
            "name": "NetPulse Admin Test",
            "login": "np_admin_test",
            "groups_id": [(6, 0, [self.admin_group.id])],
        })
        self.tech = self.env["res.users"].create({
            "name": "NetPulse Tech Test",
            "login": "np_tech_test",
            "groups_id": [(6, 0, [self.tech_group.id])],
        })

    def _wizard(self, role="technician", login="new_tech"):
        return self.env["netpulse.user.wizard"].with_user(self.admin).create({
            "name": "Usuario de prueba",
            "login": login,
            "email": login + "@example.test",
            "password": "ClaveSegura123",
            "role": role,
        })

    def test_admin_can_create_technician(self):
        wizard = self._wizard()
        wizard.action_create_user()
        user = self.env["res.users"].sudo().search([("login", "=", "new_tech")])
        self.assertTrue(user)
        self.assertTrue(user.has_group("netpulse.group_netpulse_technician"))
        self.assertFalse(user.has_group("netpulse.group_netpulse_admin"))
        self.assertIsNone(user.with_user(user)._check_credentials(
            "ClaveSegura123",
            {"interactive": True},
        ))

    def test_admin_can_create_another_admin(self):
        wizard = self._wizard(role="admin", login="new_admin")
        wizard.action_create_user()
        user = self.env["res.users"].sudo().search([("login", "=", "new_admin")])
        self.assertTrue(user.has_group("netpulse.group_netpulse_admin"))
        self.assertTrue(user.has_group("netpulse.group_netpulse_technician"))

    def test_duplicate_login_is_rejected(self):
        wizard = self._wizard(login="np_tech_test")
        with self.assertRaises(UserError):
            wizard.action_create_user()

    def test_weak_password_is_rejected(self):
        wizard = self._wizard(login="weak_password_user")
        wizard.password = "123"
        with self.assertRaises(UserError):
            wizard.action_create_user()

    def test_technician_cannot_open_user_wizard(self):
        with self.assertRaises(AccessError):
            self.env["netpulse.user.wizard"].with_user(self.tech).create({
                "name": "Intento",
                "login": "forbidden_user",
                "password": "ClaveSegura123",
                "role": "admin",
            })
