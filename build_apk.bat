@echo off
title COMPILADOR APK ANDROID - LEFACTURAMOS PLUS
color 0E
echo =====================================================================
echo           COMPILANDO APK NATIVO DE ANDROID: LEFACTURAMUS PLUS
echo =====================================================================
echo.

set "JAVA_HOME=C:\Users\CARLOS\.jdks\jbr-21.0.11"
cd /d "%~dp0"

echo [1/3] Sincronizando archivos web a la aplicacion Android...
if not exist "android\app\src\main\assets\public" mkdir "android\app\src\main\assets\public"
xcopy /s /e /y "www\*" "android\app\src\main\assets\public\" >nul

echo [2/3] Compilando con Gradle assembleDebug...
cd android
call gradlew.bat --stop
call gradlew.bat assembleDebug --no-daemon
cd ..

echo.
echo [3/3] Verificando instalador APK generado...
if exist "android\app\build\outputs\apk\debug\app-debug.apk" (
    copy /y "android\app\build\outputs\apk\debug\app-debug.apk" "LefacturamosPlus.apk" >nul
    copy /y "android\app\build\outputs\apk\debug\app-debug.apk" "LefacturamosPlus_Android_v4.apk" >nul
    echo.
    echo =====================================================================
    echo   [OK] APK COMPILADO CON EXITO CON EL NOMBRE: LefacturamosPlus.apk
    echo        Ubicacion: C:\Users\CARLOS\LefacturamosPlus\LefacturamosPlus.apk
    echo =====================================================================
) else (
    echo.
    echo [ERROR] No se pudo generar el archivo app-debug.apk.
)
pause
