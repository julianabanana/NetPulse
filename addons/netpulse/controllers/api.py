"""API HTTP versionada para el cliente OWL de NetPulse."""
import json
import logging

from odoo import _, http
from odoo.exceptions import AccessDenied, AccessError, MissingError, UserError, ValidationError
from odoo.http import request
from werkzeug.wrappers import Response

from netpulse_core.application.incident_service import (
    IncidentApplicationService,
    IncidentNotFound,
)
from netpulse_core.jwt_service import InvalidToken, NetpulseJwtService
from ..services.odoo_incident_repository import OdooIncidentRepository

_logger = logging.getLogger(__name__)

ADMIN_GROUP = "netpulse.group_netpulse_admin"
TECHNICIAN_GROUP = "netpulse.group_netpulse_technician"


class NetpulseApiController(http.Controller):
    """Adaptador HTTP: valida entrada, delega al modelo y serializa respuestas."""

    @staticmethod
    def _response(payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, default=str)
        return Response(
            body,
            status=status,
            content_type="application/json; charset=utf-8",
        )

    @staticmethod
    def _json_body():
        payload = request.httprequest.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ValidationError(_("El cuerpo debe ser un objeto JSON."))
        return payload

    @staticmethod
    def _bearer_token():
        header = request.httprequest.headers.get("Authorization", "")
        scheme, separator, token = header.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip():
            raise AccessDenied(_("Se requiere Authorization: Bearer <token>."))
        return token.strip()

    def _authenticated_user(self):
        token = self._bearer_token()
        return NetpulseJwtService.authenticate_token(
            token,
            request.env["res.users"],
        )

    @staticmethod
    def _handle_error(error):
        if isinstance(error, (AccessDenied, InvalidToken)):
            return NetpulseApiController._response(
                {"error": "unauthorized", "message": str(error)}, 401
            )
        if isinstance(error, AccessError):
            return NetpulseApiController._response(
                {"error": "forbidden", "message": str(error)}, 403
            )
        if isinstance(error, (IncidentNotFound, MissingError)):
            return NetpulseApiController._response(
                {"error": "not_found", "message": str(error)}, 404
            )
        if isinstance(error, (ValidationError, UserError, ValueError, TypeError)):
            return NetpulseApiController._response(
                {"error": "bad_request", "message": str(error)}, 400
            )
        _logger.exception("Error inesperado en la API NetPulse", exc_info=error)
        return NetpulseApiController._response(
            {"error": "internal_server_error", "message": _("Error interno.")},
            500,
        )

    @http.route(
        "/api/v1/auth/login",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def login(self, **kwargs):
        """Autentica credenciales Odoo y entrega un JWT de corta duración."""
        try:
            payload = self._json_body()
            login = str(payload.get("login", "")).strip()
            password = payload.get("password", "")
            if not login or not isinstance(password, str) or not password:
                raise ValidationError(_("Usuario y contraseña son obligatorios."))

            user = request.env["res.users"].sudo().search(
                [("login", "=", login), ("active", "=", True)],
                limit=1,
            )
            if not user:
                raise AccessDenied(_("Credenciales inválidas."))

            user.with_user(user)._check_credentials(
                password,
                {"interactive": True},
            )
            if not (
                user.has_group(ADMIN_GROUP)
                or user.has_group(TECHNICIAN_GROUP)
            ):
                raise AccessError(_("La cuenta no tiene un rol de NetPulse."))

            token = NetpulseJwtService.issue_token(user)
            role = "admin" if user.has_group(ADMIN_GROUP) else "technician"
            return self._response({
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": NetpulseJwtService.TOKEN_TTL_SECONDS,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "login": user.login,
                    "role": role,
                },
            })
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/devices",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def list_devices(self, **kwargs):
        try:
            user = self._authenticated_user()
            devices = request.env["netpulse.device"].with_user(user)
            records = devices.search_read(
                [("active", "=", True)],
                ["name", "device_type", "criticality", "status", "open_incident_count"],
                order="name",
                limit=500,
            )
            return self._response({"items": records})
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def list_incidents(self, **kwargs):
        try:
            user = self._authenticated_user()
            incidents = request.env["netpulse.incident"].with_user(user)
            records = incidents.search_read(
                [],
                [
                    "name",
                    "device_id",
                    "root_cause",
                    "description",
                    "priority",
                    "state",
                    "technician_id",
                    "origin",
                    "date_detected",
                ],
                order="date_detected desc, id desc",
                limit=100,
            )
            return self._response({"items": records})
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents/<int:incident_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def get_incident(self, incident_id, **kwargs):
        try:
            user = self._authenticated_user()
            incident = request.env["netpulse.incident"].with_user(user).browse(
                incident_id
            ).exists()
            if not incident:
                return self._response(
                    {"error": "not_found", "message": _("Incidencia inexistente.")},
                    404,
                )
            incident.check_access_rights("read")
            incident.check_access_rule("read")
            return self._response({
                "id": incident.id,
                "name": incident.name,
                "device_id": [incident.device_id.id, incident.device_id.name],
                "root_cause": incident.root_cause,
                "description": incident.description,
                "priority": incident.priority,
                "state": incident.state,
                "technician_id": (
                    [incident.technician_id.id, incident.technician_id.name]
                    if incident.technician_id else False
                ),
                "origin": incident.origin,
                "date_detected": incident.date_detected,
                "date_resolved": incident.date_resolved,
            })
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def create_incident(self, **kwargs):
        try:
            user = self._authenticated_user()
            payload = self._json_body()
            allowed_fields = {"device_id", "description", "root_cause"}
            if user.has_group(ADMIN_GROUP):
                allowed_fields |= {"priority", "technician_id"}
            unexpected = set(payload) - allowed_fields
            if unexpected:
                raise ValidationError(
                    _("Campos no permitidos: %s") % ", ".join(sorted(unexpected))
                )
            values = {
                key: value
                for key, value in payload.items()
                if key in allowed_fields
            }
            role = "admin" if user.has_group(ADMIN_GROUP) else "technician"
            service = IncidentApplicationService(
                OdooIncidentRepository(request.env, user)
            )
            incident = service.create_incident(role, values, user.id)
            return self._response(
                {"id": incident.id, "name": incident.name},
                201,
            )
        except Exception as error:
            return self._handle_error(error)


    @http.route(
        "/api/v1/technicians",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def list_technicians(self, **kwargs):
        try:
            user = self._authenticated_user()
            if not user.has_group(ADMIN_GROUP):
                raise AccessError(_("Solo un administrador puede consultar los técnicos."))
            technicians = request.env["res.users"].sudo().search(
                [
                    ("groups_id", "in", [request.env.ref(TECHNICIAN_GROUP).id]),
                    ("groups_id", "not in", [request.env.ref(ADMIN_GROUP).id]),
                    ("active", "=", True),
                ],
                order="name",
            )
            return self._response({
                "items": [{"id": technician.id, "name": technician.name}
                          for technician in technicians]
            })
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents/<int:incident_id>/priority",
        type="http",
        auth="public",
        methods=["PATCH"],
        csrf=False,
        save_session=False,
    )
    def update_incident_priority(self, incident_id, **kwargs):
        try:
            user = self._authenticated_user()
            if not user.has_group(ADMIN_GROUP):
                raise AccessError(_("Solo un administrador puede cambiar la prioridad."))
            payload = self._json_body()
            if set(payload) != {"priority"}:
                raise ValidationError(_("Debe indicar únicamente la prioridad."))
            priority = str(payload["priority"])
            if priority not in {"0", "1", "2"}:
                raise ValidationError(_("La prioridad debe ser Baja, Media o Alta."))
            incident = request.env["netpulse.incident"].with_user(user).browse(
                incident_id
            ).exists()
            if not incident:
                raise IncidentNotFound(_("La incidencia solicitada no existe."))
            incident.write({"priority": priority})
            return self._response({
                "id": incident.id,
                "priority": incident.priority,
            })
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents/<int:incident_id>/assignment",
        type="http",
        auth="public",
        methods=["PATCH"],
        csrf=False,
        save_session=False,
    )
    def assign_incident(self, incident_id, **kwargs):
        try:
            user = self._authenticated_user()
            if not user.has_group(ADMIN_GROUP):
                raise AccessError(_("Solo un administrador puede asignar técnicos."))
            payload = self._json_body()
            if set(payload) != {"technician_id"}:
                raise ValidationError(_("Debe indicar únicamente el técnico."))
            technician_id = payload["technician_id"]
            technician = request.env["res.users"].sudo().browse(technician_id).exists()
            if (
                not technician
                or not technician.has_group(TECHNICIAN_GROUP)
                or technician.has_group(ADMIN_GROUP)
            ):
                raise ValidationError(_("Seleccione un usuario con rol de técnico."))
            incident = request.env["netpulse.incident"].sudo().browse(incident_id).exists()
            if not incident:
                raise IncidentNotFound(_("La incidencia solicitada no existe."))
            incident.write({"technician_id": technician.id})
            return self._response({
                "id": incident.id,
                "technician_id": [technician.id, technician.name],
            })
        except Exception as error:
            return self._handle_error(error)

    @http.route(
        "/api/v1/incidents/<int:incident_id>/state",
        type="http",
        auth="public",
        methods=["PATCH"],
        csrf=False,
        save_session=False,
    )
    def update_incident_state(self, incident_id, **kwargs):
        try:
            user = self._authenticated_user()
            payload = self._json_body()
            state = payload.get("state")
            if state not in {"in_progress", "resolved"}:
                raise ValidationError(_("El estado solicitado no es válido."))

            service = IncidentApplicationService(
                OdooIncidentRepository(request.env, user)
            )
            incident = service.advance_state(incident_id, state)
            return self._response({
                "id": incident.id,
                "state": incident.state,
                "date_resolved": incident.date_resolved,
            })
        except Exception as error:
            return self._handle_error(error)
