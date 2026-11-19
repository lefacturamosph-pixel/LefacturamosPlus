@echo off
title LEFACTURAMOS - Subiendo archivos a GitHub y Render...
color 0A
cd /d "C:\Users\CARLOS\LefacturamosApp"
set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"

echo =====================================================================
echo    SUBIENDO ARCHIVOS DE LEFACTURAMOS A GITHUB PARA RENDER.COM
echo =====================================================================
echo.
echo 1. Preparando archivos y cambios...
git add .
git commit -m "Deploy a Render: listados y saldos actualizados" >nul 2>&1

echo 2. Enviando a GitHub (https://github.com/lefacturamosph-pixel/lefacturamos)...
git push -u origin main

echo.
echo =====================================================================
if %errorlevel% equ 0 (
    echo   [OK] EXITO: Todos los archivos quedaron en GitHub y Render!
    echo   La plataforma en la nube (Render) se actualizara en 1 a 2 minutos.
) else (
    echo   [AVISO] Si le aparecio una ventana pidiendo autorizar GitHub,
    echo   haga clic en autorizar y presione cualquier tecla.
)
echo =====================================================================
echo.
pause
