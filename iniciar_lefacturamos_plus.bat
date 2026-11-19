@echo off
title LEFACTURAMOS PLUS - Centro de Control (Puerto 8100)
color 0B
cd /d "%~dp0"
echo =====================================================================
echo                LEFACTURAMOS PLUS - LEY 675 DE 2001
echo           Facturacion y Administracion de Propiedad Horizontal
echo =====================================================================
echo.
echo  [1/2] Liberando puerto 8100 si habia una sesion previa...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8100') do taskkill /f /pid %%a >nul 2>&1
timeout /t 1 /nobreak >nul

echo  [2/2] Iniciando Servidor Web LefacturamosPlus en puerto 8100...
echo        - Administrador: http://127.0.0.1:8100/superadmin
echo        - Portal Web:    http://127.0.0.1:8100/
echo.
start http://127.0.0.1:8100/superadmin
python -m uvicorn lefacturamos_backend:app --host 127.0.0.1 --port 8100 --reload
pause
