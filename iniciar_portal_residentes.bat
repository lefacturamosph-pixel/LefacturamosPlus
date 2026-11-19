@echo off
title LEFACTURAMOS PLUS - Portal Copropietarios (Puerto 8100)
color 0A
cd /d "%~dp0"
echo =====================================================================
echo                LEFACTURAMOS PLUS - PORTAL RESIDENTES
echo           Consulta de Facturas y Recibos (Mes Actual y Backups)
echo =====================================================================
echo.
echo  [1/2] Verificando puerto 8100...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8100') do taskkill /f /pid %%a >nul 2>&1
timeout /t 1 /nobreak >nul

echo  [2/2] Abriendo Portal de Residentes en http://127.0.0.1:8100/ ...
start http://127.0.0.1:8100/
python -m uvicorn lefacturamos_backend:app --host 127.0.0.1 --port 8100 --reload
pause
