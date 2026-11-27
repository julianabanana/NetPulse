import json

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestNetpulseHttpApi(HttpCase):
    """Pruebas HTTP reales de los endpoints JWT y de incidencias."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        technician_group = cls.env.ref("netpulse.group_netpulse_technician")
        admin_group = cls.env.ref("netpulse.group_netpulse_admin")
        cls.admin = cls.env["res.users"].create({
            "name": "API Administrator",
            "login": "api_admin",
            "password": "ApiPassword123!",
            "groups_id": [(6, 0, [admin_group.id])],
        })
        cls.technician = cls.env["res.users"].create({
            "name": "API Technician",
            "login": "api_technician",
            "password": "ApiPassword123!",
            "groups_id": [(6, 0, [technician_group.id])],
        })
        cls.other_technician = cls.env["res.users"].create({
            "name": "API Other Technician",
            "login": "api_other_technician",
            "password": "ApiPassword123!",
            "groups_id": [(6, 0, [technician_group.id])],
        })
        cls.device = cls.env["netpulse.device"].create({
            "name": "API-SW-01",
            "criticality": "normal",
        })

    def _database_path(self, path):
        separator = "&" if "?" in path else "?"
        return "%s%sdb=%s" % (path, separator, self.env.cr.dbname)

    def _login(self, login="api_technician", password="ApiPassword123!"):
        response = self.url_open(
            self._database_path("/api/v1/auth/login"),
            data=json.dumps({
                "login": login,
                "password": password,
            }),
            headers={"Content-Type": "application/json"},
        )
        return response

    def _token(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def _request(self, path, token=None, payload=None, method="GET"):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer %s" % token

        database_path = self._database_path(path)
        if method == "PATCH":
            return self.opener.request(
                "PATCH",
                self.base_url() + database_path,
                data=json.dumps(payload),
                headers=headers,
                timeout=10,
            )

        data = json.dumps(payload) if payload is not None else None
        return self.url_open(database_path, data=data, headers=headers)

    def test_login_returns_signed_bearer_token(self):
        response = self._login()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["access_token"])
        self.assertEqual(body["token_type"], "Bearer")
        self.assertEqual(body["user"]["role"], "technician")

    def test_list_incidents_without_token_returns_401(self):
        response = self._request("/api/v1/incidents")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_list_incidents_with_token_returns_200(self):
        response = self._request(
            "/api/v1/incidents",
            token=self._token(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_list_devices_without_token_returns_401(self):
        response = self._request("/api/v1/devices")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_list_devices_with_token_returns_available_devices(self):
        response = self._request(
            "/api/v1/devices",
            token=self._token(),
        )

        self.assertEqual(response.status_code, 200)
        devices = response.json()["items"]
        self.assertTrue(any(
            device["id"] == self.device.id and device["name"] == self.device.name
            for device in devices
        ))

    def test_create_incident_returns_201(self):
        response = self._request(
            "/api/v1/incidents",
            token=self._token(),
            payload={
                "device_id": self.device.id,
                "root_cause": "Prueba de integración",
                "description": "Incidencia creada por HTTP",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["id"])
        incident = self.env["netpulse.incident"].browse(response.json()["id"])
        self.assertEqual(incident.device_id, self.device)

    def test_invalid_incident_payload_returns_400(self):
        response = self._request(
            "/api/v1/incidents",
            token=self._token(),
            payload={"device_id": "no-es-un-entero"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "bad_request")

    def test_forbidden_incident_detail_returns_403(self):
        incident = self.env["netpulse.incident"].create({
            "device_id": self.device.id,
            "technician_id": self.other_technician.id,
        })

        response = self._request(
            "/api/v1/incidents/%s" % incident.id,
            token=self._token(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "forbidden")

    def test_missing_incident_returns_404(self):
        response = self._request(
            "/api/v1/incidents/987654321",
            token=self._token(),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "not_found")

    def test_admin_can_update_incident_priority(self):
        incident = self.env["netpulse.incident"].create({
            "device_id": self.device.id,
            "priority": "0",
        })
        login = self._login(login="api_admin")
        self.assertEqual(login.status_code, 200)
        token = login.json()["access_token"]

        response = self._request(
            "/api/v1/incidents/%s/priority" % incident.id,
            token=token,
            payload={"priority": "2"},
            method="PATCH",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["priority"], "2")
        self.assertEqual(incident.priority, "2")

    def test_technician_cannot_update_incident_priority(self):
        incident = self.env["netpulse.incident"].create({
            "device_id": self.device.id,
            "technician_id": self.technician.id,
        })

        response = self._request(
            "/api/v1/incidents/%s/priority" % incident.id,
            token=self._token(),
            payload={"priority": "2"},
            method="PATCH",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(incident.priority, "1")

    def test_technician_can_advance_own_incident(self):
        incident = self.env["netpulse.incident"].create({
            "device_id": self.device.id,
            "technician_id": self.technician.id,
        })
        token = self._token()

        started = self._request(
            "/api/v1/incidents/%s/state" % incident.id,
            token=token,
            payload={"state": "in_progress"},
            method="PATCH",
        )
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.json()["state"], "in_progress")

        resolved = self._request(
            "/api/v1/incidents/%s/state" % incident.id,
            token=token,
            payload={"state": "resolved"},
            method="PATCH",
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()["state"], "resolved")

    def test_login_with_invalid_password_returns_401(self):
        response = self._login(password="WrongPassword123!")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_technician_creation_assigns_incident_to_creator(self):
        response = self._request(
            "/api/v1/incidents",
            token=self._token(),
            payload={
                "device_id": self.device.id,
                "description": "Incidencia de prueba",
                "root_cause": "Fallo de conexión",
            },
            method="POST",
        )

        self.assertEqual(response.status_code, 201)

        incident = self.env["netpulse.incident"].browse(
            response.json()["id"]
        )
        self.assertEqual(incident.technician_id, self.technician)
        self.assertEqual(incident.priority, "1")
        self.assertEqual(incident.state, "pending")
        self.assertEqual(incident.origin, "manual")
        self.assertFalse(incident.date_resolved)

    def test_technician_cannot_override_incident_priority(self):
        response = self._request(
            "/api/v1/incidents",
            token=self._token(),
            payload={
                "device_id": self.device.id,
                "description": "Prueba de seguridad",
                "priority": "2",
            },
            method="POST",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "bad_request")

    def test_technician_cannot_list_technicians(self):
        response = self._request(
            "/api/v1/technicians",
            token=self._token(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "forbidden")

    def test_technician_cannot_assign_incident(self):
        incident = self.env["netpulse.incident"].create({
            "device_id": self.device.id,
            "technician_id": self.technician.id,
        })

        response = self._request(
            "/api/v1/incidents/%s/assignment" % incident.id,
            token=self._token(),
            payload={"technician_id": self.other_technician.id},
            method="PATCH",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(incident.technician_id, self.technician)