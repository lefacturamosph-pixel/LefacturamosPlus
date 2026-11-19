@echo off
title LEFACTURAMOS PLUS - Subiendo a GitHub para Render.com...
color 0B
cd /d "C:\Users\CARLOS\LefacturamosPlus"
set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"

echo =====================================================================
echo    SUBIENDO ARCHIVOS DE LEFACTURAMOS PLUS A GITHUB PARA RENDER
echo =====================================================================
echo.
echo 1. Preparando archivos y cambios de LefacturamosPlus...
git add .
git commit -m "Deploy LefacturamosPlus a Render: Facturacion Individual, Planilla D/C y Drive" >nul 2>&1

echo 2. Enviando a GitHub (https://github.com/lefacturamosph-pixel/lefacturamosplus)...
git push -u origin main

echo.
echo =====================================================================
if %errorlevel% equ 0 (
    echo   [OK] EXITO: Todos los archivos quedaron en GitHub y Render!
    echo   Render iniciara el despliegue automatico en:
    echo   https://lefacturamosplus.onrender.com/
) else (
    echo   [AVISO] Si aun no has creado el repositorio "lefacturamosplus" en GitHub,
    echo   entra a: https://github.com/new y crealo con el nombre "lefacturamosplus".
    echo   Luego vuelve a dar doble clic a este archivo.
)
echo =====================================================================
echo.
pause
