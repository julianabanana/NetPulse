#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
    echo "Falta .env. Copie .env.example y configure NETPULSE_JWT_SECRET."
    exit 1
fi

echo "==> Iniciando PostgreSQL"
docker compose up -d db

echo "==> Pruebas unitarias e integración del cliente"
docker run --rm \
    -v "$ROOT_DIR:/app" \
    -w /app \
    node:20-alpine \
    npm run test:client

echo "==> Pruebas unitarias del dominio y aplicación + cobertura"
docker run --rm --user root \
    -v "$ROOT_DIR/addons:/app" \
    -w /app \
    python:3.12-slim \
    bash -lc "pip install coverage==7.6.1 && PYTHONPATH=/app python -m coverage run --source=netpulse_core.domain,netpulse_core.application -m unittest discover -s netpulse/tests/unit -p 'test_*.py' && python -m coverage report --include='netpulse_core/domain/*,netpulse_core/application/*' --fail-under=70 && python -m coverage html --include='netpulse_core/domain/*,netpulse_core/application/*' -d /app/netpulse/coverage_html"

echo "==> Pruebas ORM e integración HTTP de Odoo"
docker compose run --rm odoo \
    odoo --database=netpulse_test --init=netpulse --update=netpulse \
    --test-enable --stop-after-init --log-level=test

echo "==> Todas las suites terminaron correctamente."
