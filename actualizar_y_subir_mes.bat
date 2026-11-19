@echo off
title LEFACTURAMOS - Sincronizacion y Despliegue Automatico (Drive + Render)
color 0B
cd /d "C:\Users\CARLOS\LefacturamosApp"
set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"

echo =====================================================================
echo    LEFACTURAMOS: SINCRONIZADOR UNIVERSAL (DRIVE + DBPLUS + RENDER)
echo =====================================================================
echo.
echo Este script realiza automaticamente:
echo   1. Subida oficial a Google Drive (Lefacturamos / Edificio / Anio / Mes)
echo   2. Empaquetado de listados PDF/XLSX y facturas de Envio
echo   3. Actualizacion contable DBPlus (Saldos, unidades y coeficientes)
echo   4. Despliegue automatico a Render Cloud para verlo de inmediato en web
echo =====================================================================
echo.

python sincronizador_completo.py

echo.
echo =====================================================================
echo Proceso finalizado. Puede cerrar esta ventana.
echo =====================================================================
pause
