#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal
LANZADOR Y CENTRO DE CONTROL MAESTRO (Windows, Android, iOS y Web)
========================================================================================
Uso:
  python run_lefacturamos.py              -> Muestra menú interactivo
  python run_lefacturamos.py --desktop    -> Inicia la App de Escritorio Flet en Windows
  python run_lefacturamos.py --server     -> Inicia el Servidor Backend API (puerto 8000)
  python run_lefacturamos.py --web        -> Inicia el Servidor Web (puerto 8080)
  python run_lefacturamos.py --test       -> Ejecuta la suite de pruebas completa
  python run_lefacturamos.py --build-apk  -> Compila el APK nativo de Android con Gradle
  python run_lefacturamos.py --sync-drive -> Ejecuta sincronización con Google Drive
========================================================================================
"""

import os
import sys
import subprocess
import argparse
import webbrowser
import time

BANNER = r"""
========================================================================================
  _      ______ ______      _____ _______ _    _ _____          __  __  ____   _____ 
 | |    |  ____|  ____/\   / ____|__   __| |  | |  __ \   /\   |  \/  |/ __ \ / ____|
 | |    | |__  | |__ /  \ | |       | |  | |  | | |__) | /  \  | \  / | |  | | (___  
 | |    |  __| |  __/ /\ \| |       | |  | |  | |  _  / / /\ \ | |\/| | |  | |\___ \ 
 | |____| |____| | / ____ \ |____   | |  | |__| | | \ \/ ____ \| |  | | |__| |____) |
 |______|______|_|/_/    \_\_____|  |_|   \____/|_|  \_\/    \_\_|  |_|\____/|_____/ 
                                                                                       
           Plataforma de Administración de Propiedad Horizontal (Ley 675)
          Windows • Android • iOS • Backend Python • Pagos Bre-B / PSE / DIAN
========================================================================================
"""

def iniciar_servidor_api():
    print("[*] Iniciando Servidor Backend API en http://127.0.0.1:8000...")
    subprocess.run([sys.executable, "-m", "uvicorn", "lefacturamos_backend:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def iniciar_desktop_flet():
    print("[*] Iniciando Aplicación Flet (Windows Desktop / Multiplataforma)...")
    subprocess.run([sys.executable, "app_flet.py"])

def iniciar_servidor_web():
    print("[*] Iniciando Servidor Web en http://127.0.0.1:8080...")
    webbrowser.open("http://127.0.0.1:8080")
    subprocess.run([sys.executable, "-m", "http.server", "8080", "--directory", "www"])

def ejecutar_pruebas():
    print("[*] Ejecutando suite de pruebas automatizadas...")
    subprocess.run([sys.executable, "test_lefacturamos.py"])

def compilar_apk_android():
    print("[*] Sincronizando Capacitor y compilando APK de Android...")
    os.environ["JAVA_HOME"] = r"C:\Program Files\Android\Android Studio\jbr"
    os.environ["PATH"] = os.environ["JAVA_HOME"] + r"\bin;" + os.environ["PATH"]
    
    subprocess.run(["npx", "cap", "sync", "android"], shell=True)
    
    android_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "android")
    print(f"[*] Ejecutando Gradle en {android_dir}...")
    res = subprocess.run([os.path.join(android_dir, "gradlew.bat"), "assembleDebug"], cwd=android_dir, shell=True)
    if res.returncode == 0:
        apk_src = os.path.join(android_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
        apk_dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LEFACTURAMOS_Android_v4.apk")
        if os.path.exists(apk_src):
            import shutil
            shutil.copy2(apk_src, apk_dst)
            print(f"[OK] APK generado y listo en: {apk_dst}")

def sincronizar_drive():
    print("[*] Iniciando sincronizador oficial de Google Drive (LefacturamosPH@lefacturamos.com)...")
    subprocess.run([sys.executable, "lefacturamos_google_drive_sync.py"])

def menu_interactivo():
    while True:
        print(BANNER)
        print(" Seleccione una opción:")
        print("  1. Iniciar Aplicación de Escritorio Flet (Windows nativo)")
        print("  2. Iniciar Servidor Backend API (FastAPI - Puerto 8000)")
        print("  3. Iniciar Servidor Web / Móvil (Puerto 8080)")
        print("  4. Ejecutar Suite de Pruebas Automatizadas (12 Módulos)")
        print("  5. Compilar APK de Android (Gradle debug)")
        print("  6. Sincronizar Documentos con Google Drive")
        print("  7. Abrir Google Drive Oficial en el Navegador")
        print("  8. Salir")
        print("-" * 88)
        
        opc = input(" Ingrese el número de opción (1-8): ").strip()
        
        if opc == "1":
            iniciar_desktop_flet()
        elif opc == "2":
            iniciar_servidor_api()
        elif opc == "3":
            iniciar_servidor_web()
        elif opc == "4":
            ejecutar_pruebas()
        elif opc == "5":
            compilar_apk_android()
        elif opc == "6":
            sincronizar_drive()
        elif opc == "7":
            webbrowser.open("https://drive.google.com/drive/folders/1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E?usp=drive_link")
        elif opc == "8":
            print("\n¡Gracias por utilizar LEFACTURAMOS!\n")
            break
        else:
            print("\n[!] Opción no válida. Intente nuevamente.\n")
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="LEFACTURAMOS - Lanzador y Centro de Control")
    parser.add_argument("--desktop", action="store_true", help="Inicia la app Flet")
    parser.add_argument("--server", action="store_true", help="Inicia el backend API")
    parser.add_argument("--web", action="store_true", help="Inicia el servidor web")
    parser.add_argument("--test", action="store_true", help="Ejecuta pruebas automatizadas")
    parser.add_argument("--build-apk", action="store_true", help="Compila el APK de Android")
    parser.add_argument("--sync-drive", action="store_true", help="Sincroniza con Google Drive")

    args = parser.parse_args()

    if args.desktop:
        iniciar_desktop_flet()
    elif args.server:
        iniciar_servidor_api()
    elif args.web:
        iniciar_servidor_web()
    elif args.test:
        ejecutar_pruebas()
    elif args.build_apk:
        compilar_apk_android()
    elif args.sync_drive:
        sincronizar_drive()
    else:
        menu_interactivo()

if __name__ == "__main__":
    main()
