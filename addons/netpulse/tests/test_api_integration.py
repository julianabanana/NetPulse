"""Pruebas de integracion HTTP para los endpoints JSON-RPC de NetPulse.

Usan odoo.tests.common.HttpCase, que levanta un servidor HTTP real durante
la ejecucion de las pruebas y expone self.base_url() como URL base.

Dependencia opcional de 'requests': si el paquete no esta disponible en el
entorno Odoo se omite el modulo completo con un aviso (SkipTest).
"""
try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

import unittest
from odoo.tests.common import HttpCase, tagged


@unittest.skipUnless(_REQUESTS_AVAILABLE, "El paquete 'requests' no esta disponible en este entorno.")
@tagged("post_install", "-at_install")
class TestApiIntegration(HttpCase):
    """Pruebas de integracion que ejercen el endpoint JSON-RPC de Odoo sobre HTTP."""

    # ------------------------------------------------------------------
    # Configuracion de clase: se ejecuta UNA sola vez antes de todas las
    # pruebas y hace commit real para que el servidor HTTP vea los datos.
    # ------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Resetear la contrasena del admin a un valor conocido y hacer commit.
        admin = cls.env.ref("base.user_admin")
        admin.sudo().write({"password": "admin_test_pass"})
        cls.admin_pass = "admin_test_pass"

        # Crear o recuperar usuario tecnico.
        group_tech = cls.env.ref("netpulse.group_netpulse_technician")
        tech = cls.env["res.users"].search([("login", "=", "tech_integration")], limit=1)
        if not tech:
            tech = cls.env["res.users"].create({
                "name": "Tech Integration",
                "login": "tech_integration",
                "password": "tech_pass_123",
                "groups_id": [(6, 0, [group_tech.id])],
            })
        else:
            tech.sudo().write({
                "password": "tech_pass_123",
                "groups_id": [(6, 0, [group_tech.id])],
            })
        cls.tech_user = tech

        # Crear dispositivo de prueba para test_crear_incidencia_tecnico_exito.
        dev = cls.env["netpulse.device"].search([("name", "=", "SW-inc-api-fixture")], limit=1)
        if not dev:
            dev = cls.env["netpulse.device"].create({"name": "SW-inc-api-fixture"})
        cls.fixture_device_id = dev.id

        # Commit unico: todo lo anterior queda visible para el servidor HTTP.
        cls.env.cr.commit()

    # ------------------------------------------------------------------
    # test_login_exitoso_devuelve_uid (200 / result = numero)
    # ------------------------------------------------------------------

    def test_login_exitoso_devuelve_uid(self):
        """authenticate con credenciales validas devuelve un uid numerico > 0."""
        # Arrange
        payload = {
            "jsonrpc": "2.0", "method": "call", "id": 1,
            "params": {
                "db": self.env.cr.dbname,
                "login": "admin",
                "password": self.__class__.admin_pass,
            },
        }
        # Act
        resp = _requests.post(self.base_url() + "/web/session/authenticate",
                              json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        uid = data.get("result", {}).get("uid")
        self.assertIsInstance(uid, int, "El uid debe ser un entero.")
        self.assertGreater(uid, 0, "El uid debe ser positivo al autenticarse correctamente.")

    # ------------------------------------------------------------------
    # test_login_credenciales_invalidas_devuelve_false (resultado false)
    # ------------------------------------------------------------------

    def test_login_credenciales_invalidas_devuelve_false(self):
        """authenticate con contrasena incorrecta devuelve uid False."""
        # Arrange
        payload = {
            "jsonrpc": "2.0", "method": "call", "id": 1,
            "params": {
                "db": self.env.cr.dbname,
                "login": "admin",
                "password": "contrasena_incorrecta",
            },
        }
        # Act
        resp = _requests.post(self.base_url() + "/web/session/authenticate",
                              json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        uid = data.get("result", {}).get("uid")
        self.assertFalse(uid, "Las credenciales invalidas deben producir uid=False.")

    # ------------------------------------------------------------------
    # test_crear_dispositivo_admin_exito (create -> result es entero > 0)
    # ------------------------------------------------------------------

    def test_crear_dispositivo_admin_exito(self):
        """Un administrador puede crear un dispositivo via JSON-RPC y recibe su ID."""
        # Arrange
        session = _requests.Session()
        self._authenticate_session(session, "admin", self.admin_pass)
        payload = self._kw_payload("netpulse.device", "create", args=[{
            "name": "SW-API-Test-%d" % id(self),
            "criticality": "normal",
            "device_type": "switch",
        }])
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        device_id = data.get("result")
        self.assertIsInstance(device_id, int,
                              "create() debe devolver un entero (el ID del registro).")
        self.assertGreater(device_id, 0)

    # ------------------------------------------------------------------
    # test_leer_dispositivos_devuelve_lista (search_read -> lista)
    # ------------------------------------------------------------------

    def test_leer_dispositivos_devuelve_lista(self):
        """search_read sobre netpulse.device devuelve una lista."""
        # Arrange
        session = _requests.Session()
        self._authenticate_session(session, "admin", self.admin_pass)
        payload = self._kw_payload("netpulse.device", "search_read",
                                   kwargs={"domain": [], "fields": ["name", "status"], "limit": 10})
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(data.get("result"), list,
                              "search_read debe devolver una lista.")

    # ------------------------------------------------------------------
    # test_crear_dispositivo_datos_invalidos_error (400 equivalente)
    # ------------------------------------------------------------------

    def test_crear_dispositivo_datos_invalidos_error(self):
        """Crear un dispositivo sin nombre devuelve un error JSON-RPC."""
        # Arrange
        session = _requests.Session()
        self._authenticate_session(session, "admin", self.admin_pass)
        payload = self._kw_payload("netpulse.device", "create", args=[{
            # 'name' intencionalmente omitido
            "criticality": "normal",
        }])
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", data,
                      "Crear sin nombre obligatorio debe producir un error JSON-RPC.")

    # ------------------------------------------------------------------
    # test_acceso_sin_credencial_es_access_denied (401 equivalente)
    # ------------------------------------------------------------------

    def test_acceso_sin_credencial_es_access_denied(self):
        """Llamar a call_kw sin sesion autenticada es rechazado."""
        # Arrange - sesion nueva sin autenticar
        session = _requests.Session()
        payload = self._kw_payload("netpulse.device", "search_read",
                                   kwargs={"domain": [], "fields": ["name"]})
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert - sin sesion Odoo no devuelve una lista de registros
        has_error = ("error" in data) or (not isinstance(data.get("result"), list))
        self.assertTrue(has_error,
                        "Una sesion sin autenticar no debe poder leer datos de negocio.")

    # ------------------------------------------------------------------
    # test_tecnico_no_puede_crear_dispositivo (403 equivalente)
    # ------------------------------------------------------------------

    def test_tecnico_no_puede_crear_dispositivo(self):
        """Un tecnico no tiene permiso de create en netpulse.device."""
        # Arrange
        session = _requests.Session()
        self._authenticate_session(session, "tech_integration", "tech_pass_123")
        payload = self._kw_payload("netpulse.device", "create", args=[{
            "name": "SW-Tech-Forbidden-%d" % id(self),
            "criticality": "normal",
        }])
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", data,
                      "El tecnico no debe poder crear dispositivos (AccessError esperado).")

    # ------------------------------------------------------------------
    # test_recurso_inexistente_en_search_read (404 equivalente)
    # ------------------------------------------------------------------

    def test_recurso_inexistente_en_search_read(self):
        """search_read con un ID inexistente devuelve lista vacia, no un error."""
        # Arrange
        session = _requests.Session()
        self._authenticate_session(session, "admin", self.admin_pass)
        payload = self._kw_payload(
            "netpulse.device", "search_read",
            kwargs={
                "domain": [("id", "=", 999999999)],
                "fields": ["name"],
            },
        )
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("error", data, "Una busqueda sin resultados no debe ser un error.")
        self.assertEqual(data.get("result"), [],
                         "Buscar un ID inexistente debe devolver lista vacia.")

    # ------------------------------------------------------------------
    # test_crear_incidencia_tecnico_exito (201 equivalente)
    # ------------------------------------------------------------------

    def test_crear_incidencia_tecnico_exito(self):
        """Un tecnico puede crear una incidencia manual y queda como tecnico asignado."""
        # Arrange - el dispositivo fixture fue creado en setUpClass con commit real
        session = _requests.Session()
        self._authenticate_session(session, "tech_integration", "tech_pass_123")
        payload = self._kw_payload("netpulse.incident", "create", args=[{
            "device_id": self.fixture_device_id,
            "origin": "manual",
            "priority": "1",
        }])
        # Act
        resp = session.post(self.base_url() + "/web/dataset/call_kw",
                            json=payload, timeout=10)
        data = resp.json()
        # Assert
        self.assertEqual(resp.status_code, 200)
        incident_id = data.get("result")
        self.assertIsInstance(incident_id, int,
                              "create() de incidencia debe devolver un entero.")
        # Verificar que el tecnico quedo asignado
        inc = self.env["netpulse.incident"].sudo().browse(incident_id)
        self.assertEqual(inc.technician_id.id, self.tech_user.id,
                         "El tecnico que crea la incidencia debe quedar como responsable.")

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _authenticate_session(self, session, login, password):
        """Autentica una requests.Session contra Odoo y devuelve el uid."""
        payload = {
            "jsonrpc": "2.0", "method": "call", "id": 0,
            "params": {
                "db": self.env.cr.dbname,
                "login": login,
                "password": password,
            },
        }
        resp = session.post(self.base_url() + "/web/session/authenticate",
                            json=payload, timeout=10)
        return resp.json().get("result", {}).get("uid")

    @staticmethod
    def _kw_payload(model, method, args=None, kwargs=None):
        """Construye el payload JSON-RPC 2.0 para /web/dataset/call_kw."""
        return {
            "jsonrpc": "2.0", "method": "call", "id": 1,
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {},
            },
        }
