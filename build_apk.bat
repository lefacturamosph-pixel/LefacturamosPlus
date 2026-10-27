@echo off
set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
cd android
call gradlew.bat --stop
call gradlew.bat assembleDebug --no-daemon
cd ..
if exist "android\app\build\outputs\apk\debug\app-debug.apk" (
    copy /y android\app\build\outputs\apk\debug\app-debug.apk LEFACTURAMOS_Android_v4.apk
    echo APK COMPILED SUCCESSFULLY
) else (
    echo APK BUILD FAILED
)
