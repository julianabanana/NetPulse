# NetPulse — Prototipo 1 (Odoo 17 Community, low-code)

Ingeniería de Software II (2016702) · Universidad Nacional de Colombia · Sede Bogotá · 2026-II

**Integrantes:** Juliana Parra Caro · Manuel Federico Castro Suarez · Fabian David Mora Martinez · Andres Felipe Arias Gonzalez

NetPulse conecta el monitoreo de red (GNS3) con la gestión de incidencias (Odoo): cuando un dispositivo
**crítico** cae, se crea automáticamente una incidencia con prioridad alta y causa raíz; el administrador la
asigna a un técnico y el técnico la lleva de *Pendiente → En proceso → Resuelta*.

## Enlaces
- Wireframes (Figma, solo lectura): https://www.figma.com/design/Z7XpwDRNMefjx80Mwmpafs/Wireframe-NetPulse?node-id=1-8401&t=YOqq5XuvQFGRLyLy-1
- Documentación de la API: [`docs/openapi.yaml`](docs/openapi.yaml) (pegar en https://editor.swagger.io)
- Tablero (GitHub Projects): _pegar enlace_
- Documento PDF del Prototipo 1: _pegar enlace / ver entrega_

## Tecnologías
Odoo 17 Community (Python, ORM, vistas XML) · PostgreSQL 15 · Docker Compose · GNS3 (API REST) · Postman.

## Ejecutar en local
Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env            # edite las claves (nunca suba .env)
docker compose up -d db
# Primera vez: crea la base "netpulse" e instala el módulo con datos de demostración
docker compose run --rm odoo odoo -d netpulse -i netpulse --stop-after-init
docker compose up -d
```
Abra http://localhost:8069 e ingrese con `admin` (la base creada por línea de comandos usa la contraseña
`admin`: **cámbiela de inmediato** en Preferencias → Seguridad de la cuenta).

Para actualizar el módulo tras cambios de código:
`docker compose run --rm odoo odoo -d netpulse -u netpulse --stop-after-init`

Pruebas automáticas del módulo (en una base aparte):
`docker compose run --rm odoo odoo -d netpulse_test -i netpulse --test-enable --stop-after-init`

## Variables de entorno (valores de ejemplo en `.env.example`)
| Variable | Uso |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD` | Credenciales de PostgreSQL |
| `ODOO_MASTER_PASSWORD` | Contraseña maestra de Odoo |
| `GNS3_URL`, `GNS3_PROJECT_ID` | Servidor y proyecto GNS3 a monitorear |
| `GNS3_USER`, `GNS3_PASSWORD` | Opcionales, si su GNS3 exige autenticación |

## Roles
| Rol | Puede |
|---|---|
| **Administrador** | Todo: dashboard, topología, CRUD de dispositivos e incidencias, asignar técnico y prioridad, sincronizar con GNS3 |
| **Técnico** | Ver dispositivos; ver, crear y atender **solo sus** incidencias; no elimina ni reasigna ni cambia prioridad |

Cree el usuario técnico en Ajustes → Usuarios (el de demostración `tecnico@netpulse.local` viene **sin contraseña**:
asígnela con Acción → Cambiar contraseña).

## Guion de demostración (5 minutos)
1. **Dashboard / Topología:** dispositivos verdes (activos) y rojos (caídos).
2. En **Dispositivos → SW2 → "Simular caída (demo)"** (o apague el nodo en GNS3 y espere ≤ 2 min).
3. **Incidencias → Bandeja:** aparece `INC-0001`, Alta, causa raíz "SW2 offline". Repetir la caída **no** duplica el ticket.
4. Como administrador, asigne el técnico → el técnico recibe una actividad pendiente.
5. Inicie sesión como técnico: solo ve su incidencia; intenta cambiar prioridad o eliminar un dispositivo → **AccessError (≈403)**.
6. Técnico: *Iniciar atención* → *Marcar resuelta* (no puede saltar de Pendiente a Resuelta).
7. Muestre `docs/openapi.yaml` en Swagger Editor y la colección de Postman en verde.

## Integración con GNS3
- **Por defecto:** una acción programada de Odoo (cada minuto) consulta `GET /v2/projects/{id}/nodes` de GNS3
  mediante el adaptador `netpulse.gns3.adapter`. Cada dispositivo se asocia a su nodo con el campo *ID de nodo GNS3*.
- Si GNS3 no responde, los estados pasan a *Desconocido* y **no** se crean tickets falsos.
- Si Odoo está en la nube y GNS3 en su computador, use [`scripts/gns3_push_monitor.py`](scripts/gns3_push_monitor.py).
- Sin GNS3 disponible, use los botones *Simular caída / recuperación* (solo administrador).

## API y pruebas (Postman)
Importe `postman/NetPulse.postman_collection.json` y `postman/NetPulse.postman_environment.json`.
Cree una **API key** para el administrador y otra para el técnico (Preferencias → Seguridad de la cuenta → Nueva clave de API)
y péguelas en el environment (variables `admin_api_key`, `tech_api_key`; **no las suba al repositorio**).
Ejecute la colección completa con el Collection Runner (17 peticiones: login, CRUD, credencial inválida,
rol insuficiente, datos inválidos).

Equivalencias frente a la guía: Odoo responde con HTTP 200 y el error en el cuerpo —
`AccessDenied` ≈ 401, `AccessError` ≈ 403, `ValidationError` ≈ 400. No hay JWT nativo: la autenticación es por
sesión/API key (almacenadas con hash); opcionalmente puede añadirse el módulo OCA `auth_jwt`.

## HTTPS
Para producción ponga Odoo detrás de Caddy o Nginx con certificado Let's Encrypt, active `proxy_mode = True`
en `config/odoo.conf` y redirija HTTP a HTTPS. Ejemplo mínimo con Caddy (`Caddyfile`):
```
netpulse.example.com {
    reverse_proxy odoo:8069
}
```

## Estructura
```
addons/netpulse/   módulo Odoo (models, views, security, data, demo, tests)
config/odoo.conf   list_db=False, dbfilter, proxy_mode
docs/openapi.yaml  especificación OpenAPI 3
postman/           colección y environment (sin llaves)
scripts/           monitor alterno vía API externa
docker-compose.yml · .env.example · .gitignore
```

## Trabajo en equipo
Ramas por historia de usuario (`feature/hu-03-ticket-automatico`), *pull requests* revisados por otro integrante
y commits descriptivos de todos. Acceso otorgado al profesor.
