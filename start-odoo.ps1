# Script para iniciar Odoo correctamente

Write-Host "Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker compose down

Write-Host "`nIniciando servicios..." -ForegroundColor Yellow
docker compose up -d

Write-Host "`nEsperando 20 segundos para que Odoo inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "`nEstado de los servicios:" -ForegroundColor Green
docker compose ps

Write-Host "`n`nÚltimas líneas del log de Odoo:" -ForegroundColor Green
docker compose logs odoo --tail 30

Write-Host "`n`n✅ Si ves 'HTTP service (werkzeug) running' arriba, Odoo está listo." -ForegroundColor Green
Write-Host "   Accede a: http://localhost:8069" -ForegroundColor Cyan
Write-Host "`n   Usuario: admin" -ForegroundColor Cyan
Write-Host "   Contraseña: admin" -ForegroundColor Cyan
