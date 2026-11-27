# NetPulse — Prototipo 2 (en desarrollo)

Ingeniería de Software II (2016702) · Universidad Nacional de Colombia · Sede Bogotá · 2026-II

**Integrantes:** Juliana Parra Caro · Manuel Federico Castro Suarez · Fabian David Mora Martinez · Andres Felipe Arias Gonzalez

NetPulse conecta el monitoreo de red (GNS3) con la gestión de incidencias (Odoo): cuando un dispositivo
**crítico** cae, se crea automáticamente una incidencia con prioridad alta y causa raíz; el administrador la
asigna a un técnico y el técnico la lleva de *Pendiente → En proceso → Resuelta*.

## Enlaces
- Wireframes (Figma, solo lectura): [Wireframes](https://www.figma.com/design/Z7XpwDRNMefjx80Mwmpafs/Wireframe-NetPulse?node-id=0-1&t=L85pH1zrQ5Nr9IPm-1)
- Documentación de la API: [`docs/openapi.yaml`](docs/openapi.yaml) (pegar en https://editor.swagger.io)
- Tablero (GitHub Projects): [`Git-project`](https://github.com/users/Fmoram/projects/2)
- Documento PDF del Prototipo 1: Raíz del repositorio
- [Trazabilidad de historias y pruebas](docs/traceability.md)
- [Plantilla de evidencia de depuración](docs/debugging-evidence.md)

## Tecnologías
Odoo 17 Community (Python, ORM, OWL/XML) · API HTTP con JWT · PostgreSQL 15 · Docker Compose · GNS3 (API REST).

## Ejecutar en local
Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env            # edite las claves (nunca suba .env)
# Genere un secreto JWT propio; no use el valor de ejemplo:
sed -i 's|^NETPULSE_JWT_SECRET=.*|NETPULSE_JWT_SECRET='"$(openssl rand -hex 32)"'|' .env
docker compose up -d db
# Primera vez: crea la base "netpulse" e instala el módulo con datos de demostración
docker compose run --rm odoo odoo -d netpulse -i netpulse --stop-after-init
docker compose up -d
```

Abra http://localhost:8069 e ingrese con `admin` (la base creada por línea de comandos usa la contraseña
`admin`: **cámbiela de inmediato** en Preferencias → Seguridad de la cuenta).

La lista de bases de datos está deshabilitada en `config/odoo.conf`; la inicialización y actualización
del módulo se realizan mediante los comandos Docker documentados abajo.

Para actualizar el módulo tras cambios de código:
`docker compose run --rm odoo odoo -d netpulse -u netpulse --stop-after-init`

Ejecutar todas las pruebas (cliente, dominio, aplicación, ORM e integración HTTP) desde un clon limpio:

```bash
bash scripts/test_all.sh
```

El script usa Node 20 y la imagen Odoo 17, inicia PostgreSQL y crea/actualiza la base
`netpulse_test`. Genera el reporte HTML de cobertura en `addons/netpulse/coverage_html/`.

Inventario implementado: 21 pruebas unitarias puras de backend (incluye 5 casos de uso
con dobles), 12 pruebas HTTP de integración de backend, 2 pruebas unitarias de presentación
y 3 pruebas de integración del cliente HTTP. Además, hay 11 pruebas ORM de Odoo para
permisos, incidencias y creación de usuarios. Los resultados definitivos se consultan en CI.
Para ejecutar solo las pruebas del cliente: `npm run test:client`.

## Variables de entorno (valores de ejemplo en `.env.example`)
| Variable | Uso |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD` | Credenciales de PostgreSQL |
| `NETPULSE_JWT_SECRET` | Secreto aleatorio de al menos 32 bytes para firmar JWT |
| `GNS3_URL`, `GNS3_PROJECT_ID` | Servidor y proyecto GNS3 a monitorear |
| `GNS3_USER`, `GNS3_PASSWORD` | Opcionales, si su GNS3 exige autenticación |

## Roles y administración de usuarios
| Rol | Puede |
|---|---|
| **Administrador** | Dashboard, topología, CRUD de dispositivos e incidencias, asignar técnicos, cambiar prioridad, sincronizar con GNS3 y crear usuarios Administrador/Técnico |
| **Técnico** | Consultar dispositivos; consultar, crear y atender sus propias incidencias. No puede asignar, cambiar prioridad, cambiar el origen ni eliminar dispositivos/incidencias |

La asignación de una incidencia valida en el servidor que el usuario seleccionado tenga rol Técnico y no sea administrador. Al crear incidencias, el sistema fuerza los valores seguros según el rol; un técnico queda como responsable de su propia incidencia, que comienza Pendiente, con prioridad Media y origen Manual.

Los administradores pueden crear cuentas desde **NetPulse → Configuración → Crear usuario**. El formulario permite elegir el rol Administrador o Técnico y establecer una contraseña inicial de al menos 10 caracteres. El identificador de acceso debe ser único. El asistente solo está disponible para administradores de NetPulse.

El usuario técnico de demostración `tecnico@netpulse.local` viene **sin contraseña**: asígnela desde Ajustes → Usuarios → Acción → Cambiar contraseña, o cree una cuenta nueva desde NetPulse.

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

## Cliente OWL y API JWT

El menú **NetPulse → Incidencias → Cliente NetPulse** abre el cliente web OWL integrado
en Odoo. La vista no accede directamente al ORM: utiliza un cliente HTTP dedicado que
consume los endpoints versionados de la API.

- `POST /api/v1/auth/login`: valida usuario y contraseña de Odoo y devuelve un JWT HS256.
- `GET /api/v1/incidents`: lista las incidencias visibles para el usuario.
- `GET /api/v1/devices`: lista los dispositivos activos que pueden vincularse al crear una incidencia.
- `GET /api/v1/incidents/{id}`: consulta el detalle de una incidencia.
- `POST /api/v1/incidents`: crea una incidencia y devuelve HTTP 201.
- `PATCH /api/v1/incidents/{id}/state`: avanza el estado según las reglas del dominio.

Las rutas protegidas requieren `Authorization: Bearer <token>`. El JWT expira en 30 minutos
y el cliente lo conserva únicamente en memoria; al recibir 401 se elimina y se solicita
iniciar sesión otra vez. Un 403 muestra un mensaje de permiso insuficiente. El secreto de
firma se lee de `NETPULSE_JWT_SECRET`; nunca se guarda en Git ni en la base de datos.

Ejemplo de inicio de sesión:

```bash
curl -i http://localhost:8069/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"TU_CLAVE"}'
```

Copie el campo `access_token` de la respuesta para probar una ruta protegida:

```bash
curl -i http://localhost:8069/api/v1/incidents \
  -H "Authorization: Bearer TU_TOKEN"
```

La especificación OpenAPI está en [docs/openapi.yaml](docs/openapi.yaml). La colección
Postman del Prototipo 1 conserva las llamadas JSON-RPC para administración e inspección
directa de Odoo; esas llamadas no son el mecanismo JWT utilizado por el nuevo cliente.

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
addons/netpulse/   módulo Odoo (models, services, controllers, static OWL, views, security, tests)
addons/netpulse_core/   dominio, casos de uso y servicio JWT puros
config/odoo.conf   list_db=False, dbfilter, proxy_mode
docs/openapi.yaml  especificación OpenAPI 3
postman/           colección y environment (sin llaves)
scripts/           monitor alterno vía API externa
docker-compose.yml · .env.example · .gitignore
```
