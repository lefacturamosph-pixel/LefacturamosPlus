import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CARPETA_RAIZ_DRIVE_ID = '1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E'
TOKEN_PATH = os.path.expanduser('~\\Documents\\token_lefacturamos.json')
CREDENTIALS_PATH = 'credentials.json'

def autenticar_google_drive():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"❌ Error: No se encuentra el archivo '{CREDENTIALS_PATH}' en la carpeta C:\Users\CARLOS\LefacturamosApp")
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
    
    ruta_envio = f"C:\\dbplus\\{codigo_edificio}\\Envio"
    
    if not os.path.exists(ruta_envio):
        print(f"❌ No se encontró la ruta local: {ruta_envio}")
        return

    print(f"\n🔍 Buscando estructura en Google Drive para: Lefacturamos ➔ {codigo_edificio} ➔ {anio} ➔ {mes}...")
    
    # Navegar o crear la estructura en Google Drive dentro de la carpeta oficial compartida
    id_edificio = obtener_o_crear_carpeta(service, codigo_edificio, CARPETA_RAIZ_DRIVE_ID)
    id_anio = obtener_o_crear_carpeta(service, str(anio), id_edificio)
    id_mes = obtener_o_crear_carpeta(service, mes.upper(), id_anio)

    print(f"🚀 Iniciando traslado de archivos a la carpeta del mes...\n")
    
    # Subir cada archivo de la carpeta Envio directo al mes correspondiente
    for archivo in os.listdir(ruta_envio):
        ruta_archivo_local = os.path.join(ruta_envio, archivo)
        
        if os.path.isfile(ruta_archivo_local):
            file_metadata = {
                'name': archivo,
                'parents': [id_mes] # Se asigna como padre la carpeta del mes exacta
            }
            media = MediaFileUpload(ruta_archivo_local, resumable=True)
            
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"✅ Subido con éxito: {archivo}")

    print("\n✨ ¡Proceso de sincronización y subida finalizado con éxito!")

if __name__ == "__main__":
    codigo = input("Ingrese el código del edificio (ej: 0127): ")
    anio_ingresado = input("Ingrese el año (ej: 2026): ")
    mes_ingresado = input("Ingrese el mes (ej: SEPTIEMBRE): ")
    
    subir_archivos_dbplus(codigo, anio_ingresado, mes_ingresado)