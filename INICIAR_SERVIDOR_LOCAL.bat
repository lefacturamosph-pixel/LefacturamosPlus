@echo off
title INICIAR SERVIDOR LOCAL LEFACTURAMOS (PUERTO 8000)
cd /d "%~dp0"
echo =====================================================================
echo  INICIANDO SERVIDOR LOCAL LEFACTURAMOS EN PUERTO 8000...
echo =====================================================================
echo  Abriendo http://localhost:8000/superadmin en el navegador...
echo.
timeout /t 2 /nobreak >nul
start http://localhost:8000/superadmin
python -m uvicorn lefacturamos_backend:app --host 127.0.0.1 --port 8000 --reload
pause
