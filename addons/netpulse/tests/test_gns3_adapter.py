"""Pruebas del adaptador GNS3 usando dobles de prueba (mocks).

Se mockea `requests.get` para aislar completamente la capa HTTP de GNS3 y
probar únicamente la lógica del adaptador y el cron de sincronización.
"""
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGns3Adapter(TransactionCase):
    """Pruebas unitarias del modelo netpulse.gns3.adapter."""

    def setUp(self):
        super().setUp()
        # Configurar parámetros mínimos para que _get_config() devuelva valores.
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("netpulse.gns3_url", "http://gns3-mock:3080")
        params.set_param("netpulse.gns3_project_id", "test-project-uuid")

    # ------------------------------------------------------------------
    # test_fetch_nodes_returns_status_dict
    # ------------------------------------------------------------------

    def test_fetch_nodes_returns_status_dict(self):
        """fetch_nodes() mapea nodos GNS3 a {node_id: bool} según su status."""
        # Arrange
        fake_nodes = [
            {"node_id": "node-aaa", "status": "started"},
            {"node_id": "node-bbb", "status": "stopped"},
            {"node_id": "node-ccc", "status": "suspended"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = fake_nodes
        mock_response.raise_for_status.return_value = None

        # Act
        with patch("odoo.addons.netpulse.models.gns3_adapter.requests.get",
                   return_value=mock_response) as mock_get:
            result = self.env["netpulse.gns3.adapter"].fetch_nodes()

        # Assert
        mock_get.assert_called_once()
        self.assertEqual(result["node-aaa"], True,  "Un nodo 'started' debe ser True.")
        self.assertEqual(result["node-bbb"], False, "Un nodo 'stopped' debe ser False.")
        self.assertEqual(result["node-ccc"], False, "Un nodo 'suspended' debe ser False.")

    # ------------------------------------------------------------------
    # test_fetch_nodes_raises_on_connection_error
    # ------------------------------------------------------------------

    def test_fetch_nodes_raises_on_connection_error(self):
        """fetch_nodes() lanza UserError cuando requests.get falla por conectividad."""
        import requests as _requests

        # Arrange — simular fallo de red
        with patch("odoo.addons.netpulse.models.gns3_adapter.requests.get",
                   side_effect=_requests.exceptions.ConnectionError("unreachable")):
            # Act & Assert
            with self.assertRaises(UserError):
                self.env["netpulse.gns3.adapter"].fetch_nodes()

    # ------------------------------------------------------------------
    # test_fetch_nodes_raises_on_timeout
    # ------------------------------------------------------------------

    def test_fetch_nodes_raises_on_timeout(self):
        """fetch_nodes() lanza UserError cuando la petición a GNS3 agota el tiempo."""
        import requests as _requests

        # Arrange
        with patch("odoo.addons.netpulse.models.gns3_adapter.requests.get",
                   side_effect=_requests.exceptions.Timeout("timeout")):
            # Act & Assert
            with self.assertRaises(UserError):
                self.env["netpulse.gns3.adapter"].fetch_nodes()

    # ------------------------------------------------------------------
    # test_cron_sets_unknown_when_gns3_unavailable
    # ------------------------------------------------------------------

    def test_cron_sets_unknown_when_gns3_unavailable(self):
        """Cuando GNS3 no está disponible, el cron pone status='unknown' y NO crea incidencias."""
        # Arrange — dispositivo con node_id conocido y estado actual 'up'
        dev = self.env["netpulse.device"].create({
            "name": "SW-cron-test",
            "gns3_node_id": "node-cron-aaa",
            "status": "up",
            "criticality": "normal",
        })
        incidents_before = self.env["netpulse.incident"].search_count([
            ("device_id", "=", dev.id)
        ])

        # Act — simular que fetch_nodes() lanza UserError
        with patch.object(
            type(self.env["netpulse.gns3.adapter"]),
            "fetch_nodes",
            side_effect=UserError("GNS3 no disponible"),
        ):
            self.env["netpulse.device"].cron_sync_gns3()

        # Assert
        self.assertEqual(dev.status, "unknown",
                         "El dispositivo debería pasar a 'unknown' si GNS3 no responde.")
        incidents_after = self.env["netpulse.incident"].search_count([
            ("device_id", "=", dev.id)
        ])
        self.assertEqual(incidents_before, incidents_after,
                         "El cron NO debe crear incidencias cuando GNS3 no está disponible.")

    # ------------------------------------------------------------------
    # test_cron_updates_device_status_from_gns3_response
    # ------------------------------------------------------------------

    def test_cron_updates_device_status_from_gns3_response(self):
        """El cron actualiza el estado del dispositivo con los datos reales de GNS3."""
        # Arrange
        dev_up = self.env["netpulse.device"].create({
            "name": "SW-cron-up",
            "gns3_node_id": "node-up-111",
            "status": "unknown",
            "criticality": "normal",
        })
        dev_down = self.env["netpulse.device"].create({
            "name": "SW-cron-down",
            "gns3_node_id": "node-down-222",
            "status": "unknown",
            "criticality": "normal",
        })

        fake_states = {
            "node-up-111": True,
            "node-down-222": False,
        }

        # Act
        with patch.object(
            type(self.env["netpulse.gns3.adapter"]),
            "fetch_nodes",
            return_value=fake_states,
        ):
            self.env["netpulse.device"].cron_sync_gns3()

        # Assert
        self.assertEqual(dev_up.status, "up",
                         "Un nodo 'started' en GNS3 debe quedar como 'up'.")
        self.assertEqual(dev_down.status, "down",
                         "Un nodo 'stopped' en GNS3 debe quedar como 'down'.")

    # ------------------------------------------------------------------
    # test_fetch_nodes_ignores_nodes_without_node_id
    # ------------------------------------------------------------------

    def test_fetch_nodes_ignores_nodes_without_node_id(self):
        """fetch_nodes() omite entradas del JSON que no tengan node_id."""
        # Arrange
        fake_nodes = [
            {"node_id": "node-valid", "status": "started"},
            {"status": "started"},          # sin node_id — debe ignorarse
            {"node_id": "", "status": "started"},  # node_id vacío — falsy, se ignora
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = fake_nodes
        mock_response.raise_for_status.return_value = None

        # Act
        with patch("odoo.addons.netpulse.models.gns3_adapter.requests.get",
                   return_value=mock_response):
            result = self.env["netpulse.gns3.adapter"].fetch_nodes()

        # Assert
        self.assertIn("node-valid", result)
        self.assertEqual(len(result), 1,
                         "Solo deben aparecer los nodos con node_id no vacío.")
