import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NetpulseDevice(models.Model):
    _name = "netpulse.device"
    _description = "Dispositivo de red"
    _inherit = ["mail.thread"]
    _order = "criticality, name"

    name = fields.Char("Nombre", required=True, tracking=True)
    gns3_node_id = fields.Char("ID de nodo GNS3", copy=False, index=True)
    device_type = fields.Selection(
        [("router", "Router"), ("switch", "Switch"), ("other", "Otro")],
        string="Tipo", default="router", required=True,
    )
    criticality = fields.Selection(
        [("critical", "Crítico"), ("normal", "Normal")],
        string="Criticidad", default="normal", required=True, tracking=True,
    )
    status = fields.Selection(
        [("down", "Caído"), ("up", "Activo"), ("unknown", "Desconocido")],
        string="Estado", default="unknown", required=True, tracking=True,
    )
    last_seen = fields.Datetime("Última actualización", readonly=True)
    active = fields.Boolean(default=True)
    incident_ids = fields.One2many("netpulse.incident", "device_id", string="Incidencias")
    open_incident_count = fields.Integer("Incidencias abiertas", compute="_compute_open_incident_count")
    color = fields.Integer(compute="_compute_color")

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Ya existe un dispositivo con ese nombre."),
        ("gns3_node_uniq", "unique(gns3_node_id)", "Ese nodo de GNS3 ya está asociado a otro dispositivo."),
    ]

    @api.depends("status")
    def _compute_color(self):
        mapping = {"up": 10, "down": 1, "unknown": 0}
        for dev in self:
            dev.color = mapping.get(dev.status, 0)

    def _compute_open_incident_count(self):
        Incident = self.env["netpulse.incident"].sudo()
        for dev in self:
            dev.open_incident_count = Incident.search_count(
                [("device_id", "=", dev.id), ("state", "!=", "resolved")]
            )

    # ------------------------------------------------------------------
    # Dominio
    # ------------------------------------------------------------------
    def update_status(self, is_up):
        """Actualiza el estado y, si es una falla crítica, dispara la incidencia."""
        Incident = self.env["netpulse.incident"]
        now = fields.Datetime.now()
        for dev in self:
            previous = dev.status
            new = "up" if is_up else "down"
            dev.write({"status": new, "last_seen": now})
            if new == "down" and dev.criticality == "critical":
                Incident.create_from_monitor(dev, notify_existing=(previous != "down"))
            elif new == "up" and previous == "down":
                Incident.note_recovery(dev)
        return True

    def action_simulate_down(self):
        """Botón de demostración: simula la caída sin depender de GNS3."""
        return self.update_status(False)

    def action_simulate_up(self):
        return self.update_status(True)

    # ------------------------------------------------------------------
    # Monitoreo (cron cada minuto)
    # ------------------------------------------------------------------
    @api.model
    def cron_sync_gns3(self):
        adapter = self.env["netpulse.gns3.adapter"]
        try:
            states = adapter.fetch_nodes()
        except UserError as exc:
            _logger.info("NetPulse: ciclo de monitoreo omitido (%s)", exc)
            # GNS3 no responde: estado desconocido, sin crear tickets falsos.
            self.search([("gns3_node_id", "!=", False), ("status", "!=", "unknown")]).write(
                {"status": "unknown"}
            )
            return False
        for dev in self.search([("gns3_node_id", "in", list(states))]):
            dev.update_status(states[dev.gns3_node_id])
        return True
