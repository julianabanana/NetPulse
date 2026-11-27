import unittest

from netpulse_core.domain.incident_rules import (
    InvalidAssignment,
    InvalidTransition,
    is_open,
    normalize_technician_payload,
    validate_assignment,
    validate_device_identifier,
    validate_priority,
    validate_transition,
)


class TestIncidentDomainRules(unittest.TestCase):
    """Pruebas unitarias puras de reglas del dominio (sin Odoo ni base de datos)."""

    def test_pending_incident_is_open(self):
        self.assertTrue(is_open("pending"))

    def test_in_progress_incident_is_open(self):
        self.assertTrue(is_open("in_progress"))

    def test_resolved_incident_is_not_open(self):
        self.assertFalse(is_open("resolved"))

    def test_pending_can_transition_to_in_progress(self):
        self.assertTrue(validate_transition("pending", "in_progress"))

    def test_in_progress_can_transition_to_resolved(self):
        self.assertTrue(validate_transition("in_progress", "resolved"))

    def test_pending_cannot_skip_to_resolved(self):
        with self.assertRaises(InvalidTransition):
            validate_transition("pending", "resolved")

    def test_resolved_incident_cannot_be_reopened(self):
        with self.assertRaises(InvalidTransition):
            validate_transition("resolved", "pending")

    def test_technician_payload_forces_safe_values(self):
        payload = normalize_technician_payload(
            {
                "technician_id": 99,
                "priority": "2",
                "state": "resolved",
                "origin": "auto",
            },
            technician_id=7,
        )

        self.assertEqual(payload["technician_id"], 7)
        self.assertEqual(payload["priority"], "1")
        self.assertEqual(payload["state"], "pending")
        self.assertEqual(payload["origin"], "manual")
        self.assertFalse(payload["date_resolved"])

    def test_assignment_rejects_administrator(self):
        with self.assertRaises(InvalidAssignment):
            validate_assignment(is_technician=True, is_admin=True)

    def test_assignment_accepts_technician(self):
        self.assertTrue(
            validate_assignment(is_technician=True, is_admin=False)
        )

    def test_invalid_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_priority("urgent")

    def test_device_identifier_must_be_positive_integer(self):
        self.assertTrue(validate_device_identifier(12))
        with self.assertRaises(ValueError):
            validate_device_identifier(0)
        with self.assertRaises(ValueError):
            validate_device_identifier(True)


if __name__ == "__main__":
    unittest.main()
