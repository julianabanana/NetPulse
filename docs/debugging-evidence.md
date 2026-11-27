# Evidencia de depuración — Prototipo 2

Este documento contiene las ubicaciones verificadas en el commit de CI aprobado `920c02c37183931a9bcb096d20607e970ee4133e`. Las columnas de valores observados y capturas deben completarse durante la ejecución real en Odoo; no se deben inventar resultados.

## Flujos obligatorios

1. **Login exitoso:** formulario OWL → cliente HTTP → controlador de login → validación de contraseña → emisión del JWT → siguiente petición con `Authorization: Bearer`.
2. **Crear incidencia:** formulario OWL → cliente HTTP → controlador → caso de uso `IncidentApplicationService` → repositorio Odoo → ORM.
3. **Acceso rechazado:** petición con token de un técnico a una incidencia ajena → validación de acceso/record rule → respuesta 403 → mensaje de permiso insuficiente en OWL.

## Inventario de breakpoints

Los números corresponden al commit indicado arriba. Si se cambia el código, hay que volver a comprobar las líneas antes de tomar las capturas.

| N.º | Flujo | Capa | Archivo y línea verificada | Tipo y configuración | Valor esperado | Valor observado |
|---:|---|---|---|---|---|---|
| 1 | Login | OWL | `addons/netpulse/static/src/js/netpulse_client.js:30` | Normal, entrada a `login()` | Usuario y contraseña ingresados; ejecución una vez | Por completar |
| 2 | Login | Cliente HTTP | `addons/netpulse/static/src/js/api_client.js:59` | Normal, entrada a `api.login()` | POST a `/auth/login` con el cuerpo esperado | Por completar |
| 3 | Login | Cliente HTTP | `addons/netpulse/static/src/js/api_client.js:33` | **Condicional:** `response.status === 401 || response.status === 200` | Detenerse solo ante login aceptado o rechazado | Por completar |
| 4 | Login | Backend | `addons/netpulse/controllers/api.py:89` | Normal, entrada al controlador | Login recibido y usuario activo localizado | Por completar |
| 5 | Login | JWT | `addons/netpulse_core/jwt_service.py:47` | Normal, emisión del token | `sub`, `iat` y `exp` coherentes; TTL de 1800 s | Por completar |
| 6 | Crear | OWL | `addons/netpulse/static/src/js/netpulse_client.js:85` | **Logpoint:** `[NetPulse] crear incidencia`, `{ deviceId: this.state.deviceId, user: this.state.user?.login }` | Identificador de dispositivo y usuario antes del POST | Por completar |
| 7 | Crear | Backend | `addons/netpulse/controllers/api.py:211` | Normal, entrada a `create_incident()` | Petición autenticada y payload JSON recibido | Por completar |
| 8 | Crear | Aplicación | `addons/netpulse_core/application/incident_service.py:21` | Normal, entrada a `create_incident()` | Rol, identificador y valores validados | Por completar |
| 9 | Crear | Persistencia | `addons/netpulse/services/odoo_incident_repository.py:9` | Normal, entrada a `create()` | Valores seguros enviados al ORM | Por completar |
| 10 | 403 | Persistencia/seguridad | `addons/netpulse/services/odoo_incident_repository.py:21` | Normal, en `check_access_rule("read")` tras entrar a `get()` | La regla de registro rechaza la lectura de la incidencia ajena | Por completar |

> En el logpoint de la fila 6, configurar el mensaje indicado en las herramientas de desarrollo del navegador/depurador, sin modificar el código fuente. La fila 10 debe ejecutarse con el token de un técnico distinto al propietario de la incidencia.

## Registro de cada parada

Para cada breakpoint, guardar:
- Captura con el editor y el breakpoint visible.
- Variables inspeccionadas y valor observado.
- Pila de llamadas (call stack).
- Uso de Step Over y Step Into cuando aplique.
- En el breakpoint condicional, condición exacta configurada.
- En el logpoint, expresión exacta y mensaje registrado.

## Depuración de una prueba automatizada

Ejecutar en modo debug una prueba HTTP real, por ejemplo:

```bash
docker compose run --rm odoo odoo \
    --database=netpulse_test \
    --update=netpulse \
    --test-enable \
    --stop-after-init \
    --log-level=test
```

Configurar el depurador para detenerse dentro del controlador o del caso de uso invocado por la prueba. Guardar la captura y documentar la prueba ejecutada.

## Hallazgo, corrección y regresión

| Defecto o suposición detectada | Evidencia del depurador | Corrección aplicada | Prueba de regresión | Commit |
|---|---|---|---|---|
| Por completar con un hallazgo real | Por completar | Por completar | Por completar | Por completar |
