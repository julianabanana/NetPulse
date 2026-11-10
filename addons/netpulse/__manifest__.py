{
    "name": "NetPulse",
    "summary": "Monitoreo de red (GNS3) y gestión automática de incidencias",
    "description": "Convierte las fallas críticas detectadas en GNS3 en incidencias "
                   "con prioridad, asignación de técnico y trazabilidad.",
    "version": "17.0.1.0.0",
    "category": "Services",
    "author": "Equipo NetPulse - Ingeniería de Software II, UNAL",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron.xml",
        "views/device_views.xml",
        "views/incident_views.xml",
        "views/menus.xml",
    ],
    "demo": ["demo/demo.xml"],
    "application": True,
    "installable": True,
}
