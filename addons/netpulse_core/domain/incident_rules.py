"""Reglas puras del dominio de incidencias.

Este módulo no depende de Odoo ni de infraestructura. Los modelos ORM y los
casos de uso pueden reutilizar estas reglas sin duplicar decisiones de negocio.
"""
from copy import deepcopy


TRANSITIONS = {
    "pending": frozenset({"in_progress"}),
    "in_progress": frozenset({"resolved"}),
    "resolved": frozenset(),
}

PRIORITIES = frozenset({"0", "1", "2"})
STATES = frozenset(TRANSITIONS)


class IncidentRuleError(ValueError):
    """Error de una regla del dominio."""


class InvalidTransition(IncidentRuleError):
    """La incidencia intenta saltar una transición no permitida."""


class InvalidAssignment(IncidentRuleError):
    """El usuario asignado no tiene un rol técnico válido."""


def is_open(state):
    """Una incidencia está abierta mientras no esté resuelta."""
    if state not in STATES:
        raise IncidentRuleError("Estado de incidencia desconocido.")
    return state != "resolved"


def validate_transition(current_state, next_state):
    """Valida una transición sin modificar el agregado."""
    if current_state not in STATES or next_state not in STATES:
        raise IncidentRuleError("Estado de incidencia desconocido.")
    if current_state != next_state and next_state not in TRANSITIONS[current_state]:
        raise InvalidTransition(
            "Transición no permitida: %s -> %s."
            % (current_state, next_state)
        )
    return True


def normalize_technician_payload(values, technician_id):
    """Impide que un técnico suplante roles, estados u origen al crear."""
    normalized = deepcopy(values)
    normalized.update({
        "technician_id": technician_id,
        "priority": "1",
        "state": "pending",
        "origin": "manual",
        "date_resolved": False,
    })
    return normalized


def validate_assignment(is_technician, is_admin):
    """Solo una cuenta de técnico no administradora puede recibir asignaciones."""
    if not is_technician or is_admin:
        raise InvalidAssignment(
            "La incidencia solo puede asignarse a un usuario con rol Técnico."
        )
    return True


def validate_priority(priority):
    """Comprueba que la prioridad pertenezca al vocabulario del dominio."""
    if priority not in PRIORITIES:
        raise IncidentRuleError("Prioridad de incidencia desconocida.")
    return True


def validate_device_identifier(device_id):
    """Comprueba el identificador de dispositivo recibido desde un caso de uso."""
    if isinstance(device_id, bool) or not isinstance(device_id, int) or device_id <= 0:
        raise IncidentRuleError("El identificador del dispositivo debe ser positivo.")
    return True
