"""Casos de uso de incidencias, independientes del ORM de Odoo."""
from netpulse_core.domain.incident_rules import (
    IncidentRuleError,
    normalize_technician_payload,
    validate_device_identifier,
    validate_priority,
    validate_transition,
)


class IncidentNotFound(LookupError):
    """El repositorio no encontró la incidencia solicitada."""


class IncidentApplicationService:
    """Orquesta reglas de dominio y persistencia mediante un repositorio."""

    def __init__(self, repository):
        self._repository = repository

    def create_incident(self, role, values, user_id):
        payload = dict(values)
        validate_device_identifier(payload.get("device_id"))

        if role == "technician":
            payload = normalize_technician_payload(payload, user_id)
        elif role != "admin":
            raise IncidentRuleError("Rol de NetPulse no autorizado.")

        if "priority" in payload:
            validate_priority(payload["priority"])

        return self._repository.create(payload)

    def advance_state(self, incident_id, next_state):
        incident = self._repository.get(incident_id)
        if incident is None:
            raise IncidentNotFound("La incidencia solicitada no existe.")

        validate_transition(incident.state, next_state)
        return self._repository.update_state(incident_id, next_state)
