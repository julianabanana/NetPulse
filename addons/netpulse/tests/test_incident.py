from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNetpulse(TransactionCase):
    def setUp(self):
        super().setUp()
        group_tech = self.env.ref("netpulse.group_netpulse_technician")
        self.tech = self.env["res.users"].create({
            "name": "Tec Test", "login": "tec_test", "groups_id": [(6, 0, [group_tech.id])],
        })
        self.sw2 = self.env["netpulse.device"].create({"name": "SW2-T", "criticality": "critical"})

    # ------------------------------------------------------------------
    # Pruebas originales (no modificar)
    # ------------------------------------------------------------------

    def test_critical_down_creates_one_incident(self):
        self.sw2.update_status(False)
        self.sw2.update_status(False)  # el segundo ciclo no duplica
        incidents = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents.priority, "2")
        self.assertEqual(incidents.origin, "auto")

    def test_normal_device_does_not_create_incident(self):
        dev = self.env["netpulse.device"].create({"name": "R-normal"})
        dev.update_status(False)
        self.assertFalse(self.env["netpulse.incident"].search([("device_id", "=", dev.id)]))

    def test_invalid_transition(self):
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        inc.technician_id = self.tech
        with self.assertRaises(ValidationError):
            inc.write({"state": "resolved"})  # no puede saltar En proceso
        inc.action_start()
        inc.action_resolve()
        self.assertTrue(inc.date_resolved)

    def test_technician_cannot_delete_device_or_reassign(self):
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)])
        inc.technician_id = self.tech
        with self.assertRaises(AccessError):
            self.sw2.with_user(self.tech).unlink()
        with self.assertRaises(AccessError):
            inc.with_user(self.tech).write({"priority": "0"})

    # ------------------------------------------------------------------
    # Nuevas pruebas — Dominio: Device
    # ------------------------------------------------------------------

    def test_device_name_must_be_unique(self):
        """Crear dos dispositivos con el mismo nombre debe lanzar un error SQL."""
        # Arrange
        self.env["netpulse.device"].create({"name": "UNIQUE-SW"})
        # Act & Assert
        with self.assertRaises(Exception):
            # La restricción SQL unique(name) provoca IntegrityError que Odoo
            # envuelve en ValidationError o psycopg2.IntegrityError según el contexto.
            self.env["netpulse.device"].create({"name": "UNIQUE-SW"})

    def test_device_status_unknown_to_up_sets_up(self):
        """update_status(True) en un dispositivo con estado desconocido lo pone en 'up'."""
        # Arrange
        dev = self.env["netpulse.device"].create({"name": "R-unknown"})
        self.assertEqual(dev.status, "unknown")

        # Act
        dev.update_status(True)

        # Assert
        self.assertEqual(dev.status, "up")

    def test_device_recovery_posts_message_on_incident(self):
        """Cuando un dispositivo crítico cae y luego se recupera, la incidencia recibe un mensaje."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        messages_before = len(inc.message_ids)

        # Act
        self.sw2.update_status(True)

        # Assert
        # note_recovery() llama message_post() en la incidencia abierta,
        # por lo que message_ids debe haber crecido al menos en 1.
        self.assertGreater(len(inc.message_ids), messages_before)

    def test_non_critical_device_up_after_down_does_not_create_incident(self):
        """Un dispositivo normal que pasa de down a up no genera incidencia en ningún momento."""
        # Arrange
        dev = self.env["netpulse.device"].create({"name": "R-normal-recovery", "criticality": "normal"})

        # Act
        dev.update_status(False)
        dev.update_status(True)

        # Assert
        self.assertFalse(
            self.env["netpulse.incident"].search([("device_id", "=", dev.id)])
        )

    # ------------------------------------------------------------------
    # Nuevas pruebas — Dominio: Incident
    # ------------------------------------------------------------------

    def test_incident_name_assigned_from_sequence(self):
        """Al crear una incidencia, el campo name toma el formato INC-XXXX de la secuencia."""
        # Arrange & Act
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)

        # Assert
        self.assertTrue(inc.name.startswith("INC-"), f"Nombre inesperado: {inc.name!r}")

    def test_incident_requires_technician_to_start(self):
        """action_start() sin técnico asignado lanza UserError."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        self.assertFalse(inc.technician_id)

        # Act & Assert
        with self.assertRaises(UserError):
            inc.action_start()

    def test_resolved_incident_sets_date_resolved(self):
        """Después de resolver una incidencia, date_resolved tiene un valor."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        inc.write({"technician_id": self.tech.id})
        inc.action_start()

        # Act
        inc.action_resolve()

        # Assert
        self.assertTrue(inc.date_resolved, "date_resolved debería haberse fijado al resolver.")

    def test_resolved_incident_cannot_reopen(self):
        """Intentar volver a 'in_progress' desde 'resolved' lanza ValidationError."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        inc.write({"technician_id": self.tech.id})
        inc.action_start()
        inc.action_resolve()
        self.assertEqual(inc.state, "resolved")

        # Act & Assert
        with self.assertRaises(ValidationError):
            inc.write({"state": "in_progress"})

    def test_duplicate_open_incident_raises_validation_error(self):
        """Crear manualmente una segunda incidencia abierta para el mismo dispositivo lanza ValidationError."""
        # Arrange
        self.sw2.update_status(False)  # crea la primera incidencia automática
        self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)

        # Act & Assert
        with self.assertRaises(ValidationError):
            self.env["netpulse.incident"].create({
                "device_id": self.sw2.id,
                "origin": "manual",
                "priority": "1",
            })

    def test_technician_assigned_as_self_on_manual_create(self):
        """Un técnico que crea una incidencia manual queda como technician_id automáticamente."""
        # Arrange
        dev = self.env["netpulse.device"].create({"name": "SW-manual"})

        # Act
        # El técnico crea la incidencia en su propio contexto de usuario.
        inc = self.env["netpulse.incident"].with_user(self.tech).create({
            "device_id": dev.id,
            "origin": "manual",
            "priority": "1",
        })

        # Assert
        self.assertEqual(
            inc.technician_id.id, self.tech.id,
            "El técnico que crea la incidencia debería quedar como responsable.",
        )

    def test_priority_values_are_all_valid(self):
        """Las tres prioridades (0, 1, 2) se pueden asignar sin error."""
        # Arrange
        dev = self.env["netpulse.device"].create({"name": "SW-priority-test"})

        for priority_value in ("0", "1", "2"):
            # Act
            inc = self.env["netpulse.incident"].create({
                "device_id": dev.id,
                "origin": "manual",
                "priority": priority_value,
            })
            # Assert
            self.assertEqual(inc.priority, priority_value)
            # Resolver para liberar el dispositivo para la siguiente iteración.
            inc.write({"technician_id": self.tech.id})
            inc.action_start()
            inc.action_resolve()

    def test_incident_is_open_computed_true_when_not_resolved(self):
        """is_open es True cuando state es 'pending' o 'in_progress'."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)

        # Assert — estado inicial pending
        self.assertEqual(inc.state, "pending")
        self.assertTrue(inc.is_open)

        # Act — avanzar a in_progress
        inc.write({"technician_id": self.tech.id})
        inc.action_start()

        # Assert — sigue abierta
        self.assertTrue(inc.is_open)

    def test_incident_is_open_computed_false_when_resolved(self):
        """is_open es False cuando state es 'resolved'."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        inc.write({"technician_id": self.tech.id})
        inc.action_start()

        # Act
        inc.action_resolve()

        # Assert
        self.assertFalse(inc.is_open)

    def test_technician_cannot_modify_device_id_on_incident(self):
        """Un técnico no puede cambiar el device_id de una incidencia que tiene asignada."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        inc.write({"technician_id": self.tech.id})
        other_dev = self.env["netpulse.device"].create({"name": "SW-other"})

        # Act & Assert
        with self.assertRaises(AccessError):
            inc.with_user(self.tech).write({"device_id": other_dev.id})

    def test_technician_cannot_modify_origin_on_incident(self):
        """Un técnico no puede cambiar el campo origin de una incidencia que tiene asignada."""
        # Arrange
        self.sw2.update_status(False)
        inc = self.env["netpulse.incident"].search([("device_id", "=", self.sw2.id)], limit=1)
        inc.write({"technician_id": self.tech.id})

        # Act & Assert
        with self.assertRaises(AccessError):
            inc.with_user(self.tech).write({"origin": "manual"})
