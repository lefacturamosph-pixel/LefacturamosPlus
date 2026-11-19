@echo off
title INICIAR SERVIDOR LOCAL LEFACTURAMOS PLUS (PUERTO 8100)
cd /d "%~dp0"
echo =====================================================================
echo  INICIANDO SERVIDOR LOCAL LEFACTURAMOS PLUS EN PUERTO 8100...
echo =====================================================================
echo.
echo  [1/2] Liberando puerto 8100 por si habia una sesion anterior abierta...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8100') do taskkill /f /pid %%a >nul 2>&1
timeout /t 1 /nobreak >nul

echo  [2/2] Abriendo menu principal en el navegador...
echo        - Administrador: http://127.0.0.1:8100/superadmin
echo        - Portal Web:    http://127.0.0.1:8100/
echo.
start http://127.0.0.1:8100/superadmin
python -m uvicorn lefacturamos_backend:app --host 127.0.0.1 --port 8100 --reload
pause
