import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from netpulse_core.application.incident_service import (
    IncidentApplicationService,
    IncidentNotFound,
)
from netpulse_core.domain.incident_rules import InvalidTransition


class TestIncidentApplicationService(unittest.TestCase):
    """Casos de uso probados con dobles del repositorio."""

    def setUp(self):
        self.repository = Mock()
        self.service = IncidentApplicationService(self.repository)

    def test_invalid_device_does_not_persist_incident(self):
        with self.assertRaises(ValueError):
            self.service.create_incident(
                "technician",
                {"device_id": 0},
                user_id=12,
            )

        self.repository.create.assert_not_called()

    def test_technician_creation_persists_safe_values(self):
        self.repository.create.return_value = SimpleNamespace(id=41)

        result = self.service.create_incident(
            "technician",
            {
                "device_id": 9,
                "technician_id": 99,
                "priority": "2",
                "state": "resolved",
                "origin": "auto",
            },
            user_id=12,
        )

        self.assertEqual(result.id, 41)
        saved_values = self.repository.create.call_args.args[0]
        self.assertEqual(saved_values["technician_id"], 12)
        self.assertEqual(saved_values["priority"], "1")
        self.assertEqual(saved_values["state"], "pending")
        self.assertEqual(saved_values["origin"], "manual")

    def test_invalid_transition_does_not_update_repository(self):
        self.repository.get.return_value = SimpleNamespace(state="pending")

        with self.assertRaises(InvalidTransition):
            self.service.advance_state(incident_id=5, next_state="resolved")

        self.repository.update_state.assert_not_called()

    def test_missing_incident_does_not_update_repository(self):
        self.repository.get.return_value = None

        with self.assertRaises(IncidentNotFound):
            self.service.advance_state(incident_id=404, next_state="in_progress")

        self.repository.update_state.assert_not_called()

    def test_valid_transition_updates_repository_once(self):
        self.repository.get.return_value = SimpleNamespace(state="pending")
        self.repository.update_state.return_value = "updated"

        result = self.service.advance_state(incident_id=5, next_state="in_progress")

        self.assertEqual(result, "updated")
        self.repository.update_state.assert_called_once_with(5, "in_progress")


if __name__ == "__main__":
    unittest.main()
