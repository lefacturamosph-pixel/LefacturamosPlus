@echo off
title LEFACTURAMOS - Subir cambios a GitHub para Render.com
color 0B
echo =====================================================================
echo         LEFACTURAMOS PH - ACTUALIZAR SERVIDOR EN LA NUBE
echo =====================================================================
echo.

set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo [CONFIGURACION INICIAL]
    echo Por favor pega la URL de tu repositorio de GitHub:
    echo (Ejemplo: https://github.com/tu-usuario/lefacturamos.git)
    echo.
    set /p REPO_URL="URL del repositorio: "
    git remote add origin %REPO_URL%
    echo Repositorio vinculado correctamente.
    echo.
)

echo Preparando archivos...
git add .
set /p MENSAJE="Mensaje de actualizacion (presiona Enter para dejar 'Actualizacion'): "
if "%MENSAJE%"=="" set MENSAJE=Actualizacion

git commit -m "%MENSAJE%"
echo.
echo Subiendo cambios a GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo =====================================================================
    echo   EXITO: Los cambios se subieron a GitHub.
    echo   Render.com actualizara tu enlace en la nube automaticamente.
    echo =====================================================================
) else (
    echo.
    echo [AVISO] Si te solicita iniciar sesion en GitHub, ingresa tus datos.
)

echo.
pause
