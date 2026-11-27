"""Adaptador de persistencia para el caso de uso de incidencias."""
class OdooIncidentRepository:
    """Implementa el puerto de repositorio usando el ORM de Odoo."""

    def __init__(self, environment, user):
        self._environment = environment
        self._user = user

    def create(self, values):
        return self._environment["netpulse.incident"].with_user(
            self._user
        ).create(values)

    def get(self, incident_id):
        incident = self._environment["netpulse.incident"].with_user(
            self._user
        ).browse(incident_id).exists()
        if not incident:
            return None
        incident.check_access_rights("read")
        incident.check_access_rule("read")
        return incident

    def update_state(self, incident_id, state):
        incident = self._environment["netpulse.incident"].with_user(
            self._user
        ).browse(incident_id).exists()
        if not incident:
            return None
        incident.write({"state": state})
        return incident
