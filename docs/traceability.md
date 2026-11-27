# Trazabilidad de historias de usuario

> Los resultados se deben actualizar únicamente después de ejecutar las pruebas en CI. No marcar como aprobada una prueba que todavía no se haya ejecutado.

| Historia | Criterio de aceptación (Given–When–Then) | Pruebas automatizadas | Resultado |
|---|---|---|---|
| HU-01 — Autenticación segura | Dado un usuario activo con rol NetPulse, cuando envía sus credenciales válidas a `POST /api/v1/auth/login`, entonces recibe un JWT Bearer con expiración. Si no presenta token en una ruta protegida, recibe HTTP 401. | `test_login_returns_signed_bearer_token`, `test_list_incidents_without_token_returns_401`, `test_issued_token_contains_valid_user_identity`, `test_tampered_signature_is_rejected` | Pendiente de CI |
| HU-02 — Registro y consulta de incidencias | Dado un usuario autenticado y un dispositivo existente, cuando crea una incidencia, entonces recibe HTTP 201 y puede consultarla en el listado (HTTP 200). Si los datos son inválidos recibe 400 y si el recurso no existe recibe 404. | `test_create_incident_returns_201`, `test_list_incidents_with_token_returns_200`, `test_invalid_incident_payload_returns_400`, `test_missing_incident_returns_404` | Pendiente de CI |
| HU-03 — Atención de incidencias según permisos | Dada una incidencia asignada al técnico autenticado y en estado Pendiente, cuando avanza a En proceso y luego a Resuelta, entonces ambas transiciones se guardan. Si intenta consultar la incidencia de otro técnico, recibe HTTP 403. | `test_technician_can_advance_own_incident`, `test_forbidden_incident_detail_returns_403`, `test_invalid_transition`, `test_technician_creation_forces_safe_defaults_and_self_assignment` | Pendiente de CI |

## Ubicación de las pruebas

- API HTTP: `addons/netpulse/tests/test_api.py`
- Reglas de dominio: `addons/netpulse/tests/unit/test_incident_rules.py` (ejecutan `netpulse_core.domain`)
- Casos de uso con dobles: `addons/netpulse/tests/unit/test_incident_service.py` (ejecutan `netpulse_core.application`)
- JWT: `addons/netpulse/tests/unit/test_jwt_service.py` (ejecuta `netpulse_core.jwt_service`)
- Cliente HTTP: `addons/netpulse/tests/client/api_client.test.js`
- Estado de presentación: `addons/netpulse/tests/client/presentation_state.test.js`

Los nombres de las pruebas se mantienen descriptivos para que esta tabla pueda verificarse directamente en el repositorio.
