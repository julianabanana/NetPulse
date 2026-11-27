from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError


class NetpulseUserWizard(models.TransientModel):
    """Wizard exclusivo de administradores para crear usuarios de NetPulse."""

    _name = "netpulse.user.wizard"
    _description = "Crear usuario de NetPulse"

    name = fields.Char(string="Nombre completo", required=True)
    login = fields.Char(string="Usuario / correo de acceso", required=True)
    email = fields.Char(string="Correo electrónico")
    password = fields.Char(string="Contraseña inicial", required=True)
    role = fields.Selection(
        [("technician", "Técnico"), ("admin", "Administrador")],
        string="Rol de NetPulse",
        required=True,
        default="technician",
    )

    def action_create_user(self):
        self.ensure_one()
        if not self.env.user.has_group("netpulse.group_netpulse_admin"):
            raise AccessError(_("Solo un administrador de NetPulse puede crear usuarios."))

        login = (self.login or "").strip()
        if not login:
            raise UserError(_("El usuario de acceso es obligatorio."))
        if len(self.password or "") < 10:
            raise UserError(_("La contraseña inicial debe tener al menos 10 caracteres."))

        User = self.env["res.users"].sudo()
        if User.search_count([("login", "=", login)]):
            raise UserError(_("Ya existe un usuario con ese identificador de acceso."))

        group_xmlid = (
            "netpulse.group_netpulse_admin"
            if self.role == "admin"
            else "netpulse.group_netpulse_technician"
        )
        internal_group = self.env.ref("base.group_user")
        role_group = self.env.ref(group_xmlid)

        User.create({
            "name": self.name.strip(),
            "login": login,
            "email": (self.email or "").strip() or False,
            "password": self.password,
            "share": False,
            "groups_id": [(6, 0, [internal_group.id, role_group.id])],
        })

        return {"type": "ir.actions.act_window_close"}
