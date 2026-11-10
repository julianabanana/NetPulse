import logging
import os

import requests

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Gns3Adapter(models.AbstractModel):
    """Patrón Adapter: traduce la API REST de GNS3 al vocabulario del dominio.

    El dominio solo conoce "dispositivo activo / caído"; los términos de GNS3
    (node, started, stopped, suspended) no salen de esta clase.
    """

    _name = "netpulse.gns3.adapter"
    _description = "Adaptador GNS3"

    @api.model
    def _get_config(self):
        params = self.env["ir.config_parameter"].sudo()
        base = os.environ.get("GNS3_URL") or params.get_param("netpulse.gns3_url")
        project = os.environ.get("GNS3_PROJECT_ID") or params.get_param("netpulse.gns3_project_id")
        user = os.environ.get("GNS3_USER")
        password = os.environ.get("GNS3_PASSWORD")
        return base, project, ((user, password) if user else None)

    @api.model
    def fetch_nodes(self):
        """Devuelve {node_id: True si está activo}. Lanza UserError si GNS3 no responde."""
        base, project, auth = self._get_config()
        if not base or not project:
            raise UserError(_("GNS3 no está configurado: defina GNS3_URL y GNS3_PROJECT_ID."))
        url = "%s/v2/projects/%s/nodes" % (base.rstrip("/"), project)
        try:
            response = requests.get(url, auth=auth, timeout=10)
            response.raise_for_status()
            nodes = response.json()
        except (requests.RequestException, ValueError) as exc:
            _logger.warning("NetPulse: no fue posible consultar GNS3 (%s)", exc)
            raise UserError(_("No fue posible consultar GNS3.")) from exc
        return {n["node_id"]: n.get("status") == "started" for n in nodes if n.get("node_id")}
