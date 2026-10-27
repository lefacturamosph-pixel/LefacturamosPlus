@echo off
title LEFACTURAMOS - Acceso Remoto desde Casa
color 0A
echo =====================================================================
echo           LEFACTURAMOS PH - ACCESO REMOTO POR INTERNET
echo =====================================================================
echo.
echo 1. Asegurando que el servidor local este activo en el puerto 8000...
netstat -ano | findstr :8000 >nul
if %errorlevel% neq 0 (
    echo Iniciando backend en segundo plano...
    start /B python -m uvicorn lefacturamos_backend:app --host 0.0.0.0 --port 8000
    timeout /t 3 /nobreak >nul
)

echo 2. Generando enlace seguro HTTPS para ver desde la casa o celular...
echo.
echo Presione CTRL+C si desea cerrar el acceso cuando ya no lo use.
echo =====================================================================
echo.
cloudflared.exe tunnel --url http://127.0.0.1:8000
pause
