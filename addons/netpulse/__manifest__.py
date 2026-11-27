{
    "name": "NetPulse",
    "summary": "Monitoreo de red (GNS3) y gestión automática de incidencias",
    "description": "Convierte las fallas críticas detectadas en GNS3 en incidencias "
                   "con prioridad, asignación de técnico y trazabilidad.",
    "version": "17.0.1.0.0",
    "category": "Services",
    "author": "Equipo NetPulse - Ingeniería de Software II, UNAL",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web"],
    "assets": {
        "web.assets_backend": [
            "netpulse/static/src/js/api_client.js",
            "netpulse/static/src/js/presentation_state.js",
            "netpulse/static/src/js/netpulse_client.js",
            "netpulse/static/src/xml/netpulse_client.xml",
            "netpulse/static/src/scss/netpulse_client.scss",
        ],
    },
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/cron.xml",
        "views/device_views.xml",
        "views/incident_views.xml",
        "views/user_wizard_views.xml",
        "views/client_action.xml",
        "views/menus.xml",
    ],
    "demo": ["demo/demo.xml"],
    "application": True,
    "installable": True,
}
