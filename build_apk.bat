@echo off
set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
cd /d "%~dp0"
echo Sincronizando archivos web a Android...
if not exist "android\app\src\main\assets\public" mkdir "android\app\src\main\assets\public"
xcopy /s /e /y "www\*" "android\app\src\main\assets\public\" >nul
cd android
call gradlew.bat --stop
call gradlew.bat assembleDebug --no-daemon
cd ..
if exist "android\app\build\outputs\apk\debug\app-debug.apk" (
    copy /y android\app\build\outputs\apk\debug\app-debug.apk Lefacturamos.apk
    copy /y android\app\build\outputs\apk\debug\app-debug.apk LEFACTURAMOS_Android_v4.apk
    echo APK COMPILED SUCCESSFULLY COMO Lefacturamos.apk
) else (
    echo APK BUILD FAILED
)
