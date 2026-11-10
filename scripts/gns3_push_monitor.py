#!/usr/bin/env python3
"""Monitor alterno: úselo cuando Odoo corre en la nube y GNS3 en su computador.

Consulta GNS3 localmente y actualiza Odoo por la API externa (XML-RPC) con una API key.
Variables de entorno: GNS3_URL, GNS3_PROJECT_ID, ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY
"""
import os
import time
import xmlrpc.client

import requests

GNS3 = os.environ["GNS3_URL"].rstrip("/")
PROJECT = os.environ["GNS3_PROJECT_ID"]
URL, DB = os.environ["ODOO_URL"].rstrip("/"), os.environ["ODOO_DB"]
USER, KEY = os.environ["ODOO_USER"], os.environ["ODOO_API_KEY"]
INTERVAL = int(os.environ.get("INTERVAL_SECONDS", "30"))

uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, USER, KEY, {})
if not uid:
    raise SystemExit("Credenciales de Odoo inválidas")
odoo = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def call(model, method, *args, **kwargs):
    return odoo.execute_kw(DB, uid, KEY, model, method, list(args), kwargs)


while True:
    try:
        nodes = requests.get(f"{GNS3}/v2/projects/{PROJECT}/nodes", timeout=10).json()
        for node in nodes:
            ids = call("netpulse.device", "search", [["gns3_node_id", "=", node["node_id"]]], limit=1)
            if ids:
                call("netpulse.device", "update_status", ids, node["status"] == "started")
    except requests.RequestException as exc:
        print("GNS3 no responde:", exc)
    time.sleep(INTERVAL)
