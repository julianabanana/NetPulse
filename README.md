# NetPulse — Prototipo 1 (Odoo 17 Community)

Ingeniería de Software II (2016702) · Universidad Nacional de Colombia · Sede Bogotá · 2026-II

## Entrega 1

**Integrantes:** Juliana Parra Caro · Manuel Federico Castro Suarez · Fabian David Mora Martinez · Andres Felipe Arias Gonzalez

NetPulse conecta el monitoreo de red (GNS3) con la gestión de incidencias (Odoo): cuando un dispositivo
**crítico** cae, se crea automáticamente una incidencia con prioridad alta y causa raíz; el administrador la
asigna a un técnico y el técnico la lleva de *Pendiente → En proceso → Resuelta*.

## Enlaces
- Wireframes (Figma, solo lectura): [Wireframes](https://www.figma.com/design/Z7XpwDRNMefjx80Mwmpafs/Wireframe-NetPulse?node-id=0-1&t=L85pH1zrQ5Nr9IPm-1)
- Documentación de la API: [`docs/openapi.yaml`](docs/openapi.yaml) (pegar en https://editor.swagger.io)
- Tablero (GitHub Projects): [`Git-project`](https://github.com/users/Fmoram/projects/2)
- Documento PDF del Prototipo 1: Raíz del repositorio


## Tecnologías
Odoo 17 Community (Python, ORM, vistas XML) · PostgreSQL 15 · Docker Compose · GNS3 (API REST) · Postman.


## Roles
| Rol | Puede |
|---|---|
| **Administrador** | Todo: dashboard, topología, CRUD de dispositivos e incidencias, asignar técnico y prioridad, sincronizar con GNS3 |
| **Técnico** | Ver dispositivos; ver, crear y atender **solo sus** incidencias; no elimina ni reasigna ni cambia prioridad |


## Estructura
```
addons/netpulse/   módulo Odoo (models, views, security, data, demo, tests)
config/odoo.conf   list_db=False, dbfilter, proxy_mode
docs/openapi.yaml  especificación OpenAPI 3
postman/           colección y environment (sin llaves)
scripts/           monitor alterno vía API externa
docker-compose.yml · .env.example · .gitignore
```
