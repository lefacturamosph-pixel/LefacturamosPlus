import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CARPETA_RAIZ_DRIVE_ID = '1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E'

# Rutas seguras independientes de la carpeta de ejecución
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.expanduser(os.path.join('~', 'Documents', 'token_lefacturamos.json'))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

def autenticar_google_drive():
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"⚠️ Aviso al leer token guardado: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Error al refrescar token: {e}. Se solicitará inicio de sesión nuevo.")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"❌ Error: No se encuentra el archivo 'credentials.json' en:")
                print(f"   {BASE_DIR}")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def obtener_o_crear_carpeta(service, nombre_carpeta, id_padre=None):
    # Buscar si la carpeta ya existe dentro del padre
    query = f"name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if id_padre:
        query += f" and '{id_padre}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    else:
        # Si no existe, se crea automáticamente
        file_metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if id_padre:
            file_metadata['parents'] = [id_padre]
            
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"📁 Carpeta creada en Drive: {nombre_carpeta}")
        return folder.get('id')

def subir_archivos_dbplus(codigo_edificio, anio, mes):
    service = autenticar_google_drive()
    if not service:
        return
    
    codigo_limpio = str(codigo_edificio).strip()
    codigo_4digitos = codigo_limpio.zfill(4) if codigo_limpio.isdigit() else codigo_limpio
    
    # Buscar posibles rutas de Envio en C:\dbplus
    rutas_candidatas = [
        os.path.join("C:\\dbplus", codigo_limpio, "Envio"),
        os.path.join("C:\\dbplus", codigo_4digitos, "Envio"),
        os.path.join("C:\\dbplus", codigo_limpio, "envio"),
        os.path.join("C:\\dbplus", codigo_4digitos, "envio"),
        os.path.join("C:\\dbplus", codigo_limpio, "ENVIO"),
        os.path.join("C:\\dbplus", codigo_4digitos, "ENVIO")
    ]
    
    ruta_envio = None
    for r in rutas_candidatas:
        if os.path.exists(r):
            ruta_envio = r
            break
            
    if not ruta_envio:
        print(f"❌ No se encontró la ruta local: C:\\dbplus\\{codigo_limpio}\\Envio")
        print(f"   Verifique que la carpeta exista en C:\\dbplus\\{codigo_4digitos}\\Envio")
        return

    archivos_locales = [a for a in os.listdir(ruta_envio) if os.path.isfile(os.path.join(ruta_envio, a))]
    if not archivos_locales:
        print(f"⚠️ La carpeta '{ruta_envio}' no contiene archivos para subir.")
        return

    codigo_final = codigo_4digitos if os.path.exists(os.path.join("C:\\dbplus", codigo_4digitos)) else codigo_limpio

    print(f"\n🔍 Buscando estructura en Google Drive para: Lefacturamos ➔ {codigo_final} ➔ {anio} ➔ {str(mes).upper()}...")
    
    # Navegar o crear la estructura en Google Drive dentro de la carpeta oficial compartida
    id_edificio = obtener_o_crear_carpeta(service, codigo_final, CARPETA_RAIZ_DRIVE_ID)
    id_anio = obtener_o_crear_carpeta(service, str(anio).strip(), id_edificio)
    id_mes = obtener_o_crear_carpeta(service, str(mes).strip().upper(), id_anio)

    # Consultar archivos que ya existen en esa carpeta para evitar duplicar
    archivos_existentes = {}
    try:
        query_existentes = f"'{id_mes}' in parents and trashed = false"
        page_token = None
        while True:
            resp = service.files().list(
                q=query_existentes,
                spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token
            ).execute()
            for f in resp.get('files', []):
                archivos_existentes[f['name']] = f['id']
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"⚠️ Nota: No se pudo consultar archivos existentes ({e}), se procederá normalmente.")

    print(f"🚀 Iniciando traslado de {len(archivos_locales)} archivos desde {ruta_envio} a Google Drive...\n")
    
    subidos = 0
    actualizados = 0
    errores = 0

    for idx, archivo in enumerate(archivos_locales, 1):
        ruta_archivo_local = os.path.join(ruta_envio, archivo)
        try:
            media = MediaFileUpload(ruta_archivo_local, resumable=True)
            
            if archivo in archivos_existentes:
                file_id = archivos_existentes[archivo]
                service.files().update(fileId=file_id, media_body=media).execute()
                print(f"[{idx}/{len(archivos_locales)}] 🔄 Actualizado en Drive (reemplazo): {archivo}")
                actualizados += 1
            else:
                file_metadata = {
                    'name': archivo,
                    'parents': [id_mes]
                }
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"[{idx}/{len(archivos_locales)}] ✅ Subido con éxito: {archivo}")
                subidos += 1
        except Exception as err:
            print(f"[{idx}/{len(archivos_locales)}] ❌ Error al subir {archivo}: {err}")
            errores += 1

    print(f"\n✨ ¡Proceso de sincronización y subida a Google Drive finalizado con éxito!")
    print(f"   • Nuevos subidos: {subidos}")
    print(f"   • Actualizados:   {actualizados}")
    if errores > 0:
        print(f"   • Con error:      {errores}")

    # Sincronización automática inmediata hacia Render Cloud (data/drive_docs, Master contable y GitHub)
    try:
        from sincronizador_completo import sincronizar_todo_el_edificio
        print("\n🌐 Sincronizando y desplegando automáticamente a Render Cloud...")
        sincronizar_todo_el_edificio(codigo_final, str(anio), str(mes), subir_google_drive=False)
    except Exception as e_sync:
        print(f"⚠️ Nota al sincronizar con Render: {e_sync}")

if __name__ == "__main__":
    codigo = input("Ingrese el código del edificio (ej: 0127): ")
    anio_ingresado = input("Ingrese el año (ej: 2026): ")
    mes_ingresado = input("Ingrese el mes (ej: SEPTIEMBRE): ")
    
    subir_archivos_dbplus(codigo, anio_ingresado, mes_ingresado)
