from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

ADMIN_GROUP = "netpulse.group_netpulse_admin"


class NetpulseIncident(models.Model):
    """Raíz del agregado Incidencia.

    Invariantes: (1) una sola incidencia abierta por dispositivo; (2) transiciones
    Pendiente -> En proceso -> Resuelta; (3) En proceso/Resuelta exigen técnico;
    (4) Resuelta guarda fecha de cierre y no se reabre.
    """

    _name = "netpulse.incident"
    _description = "Incidencia de red"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, date_detected desc, id desc"

    # Patrón State: tabla de transiciones permitidas
    _TRANSITIONS = {
        "pending": {"in_progress"},
        "in_progress": {"resolved"},
        "resolved": set(),
    }

    name = fields.Char("Referencia", readonly=True, copy=False, default=lambda self: _("Nuevo"))
    device_id = fields.Many2one("netpulse.device", string="Dispositivo", required=True,
                                ondelete="restrict", tracking=True, index=True)
    device_status = fields.Selection(related="device_id.status", string="Estado del dispositivo")
    root_cause = fields.Char("Causa raíz", tracking=True)
    description = fields.Text("Descripción")
    priority = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta")],
        string="Prioridad", default="1", required=True, tracking=True,
    )
    state = fields.Selection(
        [("pending", "Pendiente"), ("in_progress", "En proceso"), ("resolved", "Resuelta")],
        string="Estado", default="pending", required=True, tracking=True, index=True,
    )
    technician_id = fields.Many2one("res.users", string="Técnico", tracking=True, index=True)
    origin = fields.Selection(
        [("auto", "Automático (monitor)"), ("manual", "Manual")],
        string="Origen", default="manual", required=True,
    )
    date_detected = fields.Datetime("Detectada", default=fields.Datetime.now, readonly=True)
    date_resolved = fields.Datetime("Cerrada", readonly=True, copy=False)
    is_open = fields.Boolean(compute="_compute_is_open", store=True)
    is_admin = fields.Boolean(compute="_compute_is_admin")

    # ------------------------------------------------------------------
    @api.depends("state")
    def _compute_is_open(self):
        for rec in self:
            rec.is_open = rec.state != "resolved"

    @api.depends_context("uid")
    def _compute_is_admin(self):
        is_admin = self.env.user.has_group(ADMIN_GROUP)
        for rec in self:
            rec.is_admin = is_admin

    # ------------------------------------------------------------------
    # Invariantes
    # ------------------------------------------------------------------
    @api.constrains("device_id", "state")
    def _check_single_open_incident(self):
        for rec in self:
            if rec.state != "resolved":
                duplicates = self.sudo().search_count([
                    ("device_id", "=", rec.device_id.id),
                    ("state", "!=", "resolved"),
                    ("id", "!=", rec.id),
                ])
                if duplicates:
                    raise ValidationError(_(
                        "El dispositivo %s ya tiene una incidencia abierta.") % rec.device_id.name)

    @api.constrains("state", "technician_id")
    def _check_technician_required(self):
        for rec in self:
            if rec.state in ("in_progress", "resolved") and not rec.technician_id:
                raise ValidationError(_("Asigne un técnico antes de atender o resolver la incidencia."))

    # ------------------------------------------------------------------
    # CRUD con reglas de negocio
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        is_admin = self.env.su or self.env.user.has_group(ADMIN_GROUP)
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].sudo().next_by_code("netpulse.incident") or _("Nuevo")
            # Un técnico que registra una incidencia manual queda como responsable.
            if not is_admin and not vals.get("technician_id"):
                vals["technician_id"] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and not self.env.user.has_group(ADMIN_GROUP):
            restricted = {"technician_id", "priority", "device_id", "origin"} & set(vals)
            if restricted:
                raise AccessError(_(
                    "Solo un administrador puede modificar: %s") % ", ".join(sorted(restricted)))
        if "state" in vals:
            labels = dict(self._fields["state"].selection)
            for rec in self:
                new = vals["state"]
                if new != rec.state and new not in self._TRANSITIONS[rec.state]:
                    raise ValidationError(_("Transición no permitida: %s -> %s.") % (
                        labels[rec.state], labels[new]))
            if vals["state"] == "resolved":
                vals = dict(vals, date_resolved=fields.Datetime.now())
        previous = {rec.id: rec.technician_id for rec in self}
        result = super().write(vals)
        if "technician_id" in vals:
            for rec in self:
                if rec.technician_id and rec.technician_id != previous[rec.id]:
                    rec.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=rec.technician_id.id,
                        summary=_("Atender incidencia %s") % rec.name,
                        note=_("Dispositivo: %s. Causa raíz: %s") % (
                            rec.device_id.name, rec.root_cause or "-"),
                    )
        return result

    # ------------------------------------------------------------------
    # Acciones (botones)
    # ------------------------------------------------------------------
    def action_start(self):
        for rec in self:
            if not rec.technician_id:
                raise UserError(_("Asigne un técnico antes de iniciar la atención."))
        self.write({"state": "in_progress"})
        return True

    def action_resolve(self):
        self.write({"state": "resolved"})
        return True

    # ------------------------------------------------------------------
    # Llamadas del monitor (sistema)
    # ------------------------------------------------------------------
    @api.model
    def create_from_monitor(self, device, notify_existing=False):
        device = device.sudo()
        existing = self.sudo().search([("device_id", "=", device.id), ("state", "!=", "resolved")], limit=1)
        if existing:
            if notify_existing:
                existing.message_post(body=_("El monitor volvió a detectar %s caído.") % device.name)
            return existing
        return self.sudo().create({
            "device_id": device.id,
            "origin": "auto",
            "priority": "2",
            "root_cause": _("%s offline") % device.name,
            "description": _("Falla crítica detectada automáticamente por el monitor."),
        })

    @api.model
    def note_recovery(self, device):
        for inc in self.sudo().search([("device_id", "=", device.id), ("state", "!=", "resolved")]):
            inc.message_post(body=_("El dispositivo %s volvió a estar activo.") % device.name)
