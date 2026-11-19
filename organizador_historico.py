import os
import re
import shutil
import tempfile
import pandas as pd
import patoolib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
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
                print(f"❌ Error: No se encuentra '{CREDENTIALS_PATH}' en C:\\Users\\CARLOS\\LefacturamosApp")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def obtener_o_crear_carpeta(service, nombre_carpeta, id_padre=None):
    query = f"name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if id_padre:
        query += f" and '{id_padre}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    else:
        file_metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if id_padre:
            file_metadata['parents'] = [id_padre]
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def cargar_maestro_edificios(ruta_excel_edificios):
    if not os.path.exists(ruta_excel_edificios):
        print(f"⚠️ No se encontró el archivo maestro en: {ruta_excel_edificios}")
        return {}
    
    df = pd.read_excel(ruta_excel_edificios)
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    if 'nomurban' not in df.columns or 'codigo' not in df.columns:
        print("❌ Error: El archivo Excel debe tener las columnas 'nomurban' y 'codigo'.")
        return {}

    maestro = {}
    for _, row in df.iterrows():
        nombre_edificio = str(row['nomurban']).strip().upper()
        codigo_edificio = str(row['codigo']).strip()
        if nombre_edificio and nombre_edificio != "NAN":
            maestro[nombre_edificio] = codigo_edificio
            
    print(f"📋 Se cargaron {len(maestro)} edificios desde el archivo maestro.")
    return maestro

def obtener_mes_y_anio_preciso(nombre_archivo_upper):
    """
    Busca de manera exacta el patrón de mes seguido de su año 
    (Ej: 'DICIEMBRE DE 2025' o 'ENERO 2026'), evitando confusiones con nombres propios.
    """
    patron_fecha = r'\b(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\b(?:\s+DE\s+|\s+)(20\d{2})'
    
    match = re.search(patron_fecha, nombre_archivo_upper)
    if match:
        mes = match.group(1)
        anio = match.group(2)
        return mes, anio
        
    return None, None

def calcular_ciclo_facturacion(mes_texto, anio_base_str, tipo_documento):
    """
    Agrupa todo el paquete en el mes principal de facturación:
    - Planilla (ej. Enero 2026) ➔ Pertenece al ciclo de Diciembre (-1 mes).
    - Pagos / Recibos / Descuentos (ej. Noviembre 2025) ➔ Pertenecen al ciclo de Diciembre (+1 mes).
    - Facturas / Facturación / Pendientes (ej. Diciembre 2025) ➔ Se quedan en Diciembre (0).
    """
    meses_orden = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", 
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    
    if mes_texto not in meses_orden:
        return mes_texto, anio_base_str
    
    idx = meses_orden.index(mes_texto)
    anio_base = int(anio_base_str)
    tipo_doc_up = tipo_documento.upper()
    
    # Asignar el desplazamiento para agruparlo en el mes base de facturación
    if "PLANILLA" in tipo_doc_up:
        desplazamiento = -1  # Si dice Enero 2026, lo anclamos a Diciembre 2025
    elif any(x in tipo_doc_up for x in ["RECIBO", "RECIBOS", "CAJA", "PAGOS", "DESCUENTOS"]):
        desplazamiento = 1   # Si dice Noviembre 2025, lo anclamos a Diciembre 2025
    else:
        desplazamiento = 0   # Si dice Diciembre 2025, se queda en Diciembre 2025
        
    nuevo_idx = idx + desplazamiento
    nuevo_anio = anio_base
    
    if nuevo_idx >= 12:
        nuevo_idx = 0
        nuevo_anio += 1
    elif nuevo_idx < 0:
        nuevo_idx = 11
        nuevo_anio -= 1
        
    return meses_orden[nuevo_idx], str(nuevo_anio)

def procesar_archivo_individual(service, ruta_archivo, nombre_referencia, maestro_edificios, id_lefacturamos):
    nombre_archivo_upper = nombre_referencia.upper()

    # 1. Extraer Mes y Año impreso exactos
    mes_impreso, anio_impreso = obtener_mes_y_anio_preciso(nombre_archivo_upper)
    
    if not mes_impreso or not anio_impreso:
        print(f"   ⚠️ Omitido (No se detectó un periodo válido de mes/año): {nombre_referencia}")
        return False

    # 2. Cruzar edificio con 'nomurban' del Excel
    codigo_encontrado = None
    for nomurban, codigo in maestro_edificios.items():
        if nomurban in nombre_archivo_upper:
            codigo_encontrado = codigo
            break
    
    if not codigo_encontrado:
        print(f"   ⚠️ Omitido (Edificio no encontrado en edificio.xlsx): {nombre_referencia}")
        return False

    # 3. Calcular la carpeta de destino unificada según el ciclo de facturación
    mes_final, anio_final = calcular_ciclo_facturacion(mes_impreso, anio_impreso, nombre_archivo_upper)

    print(f"   📁 [Ciclo Unificado] {nombre_referencia[:45]}... ➔ Carpeta Nube: {mes_final} {anio_final}")

    # 4. Crear estructura en Google Drive: Lefacturamos ➔ Código ➔ Año ➔ Mes
    id_edificio = obtener_o_crear_carpeta(service, codigo_encontrado, id_lefacturamos)
    id_anio = obtener_o_crear_carpeta(service, anio_final, id_edificio)
    id_mes = obtener_o_crear_carpeta(service, mes_final, id_anio)

    # 5. Subir archivo a Google Drive
    file_metadata = {
        'name': os.path.basename(ruta_archivo),
        'parents': [id_mes]
    }
    media = MediaFileUpload(ruta_archivo, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"   ✅ Subido con éxito a [{codigo_encontrado} / {anio_final} / {mes_final}]")
    return True

def procesar_backup_impresas(ruta_backup, ruta_maestro):
    service = autenticar_google_drive()
    if not service:
        return

    maestro_edificios = cargar_maestro_edificios(ruta_maestro)
    if not maestro_edificios:
        return

    if not os.path.exists(ruta_backup):
        print(f"❌ No se encontró la ruta local: {ruta_backup}")
        return

    print(f"🚀 Analizando archivos en {ruta_backup}...\n")
    id_lefacturamos = obtener_o_crear_carpeta(service, "Lefacturamos")
    contador = 0

    for archivo in os.listdir(ruta_backup):
        ruta_completa = os.path.join(ruta_backup, archivo)
        if not os.path.isfile(ruta_completa):
            continue

        if archivo.lower().endswith('.rar'):
            print(f"\n📦 Descomprimiendo archivo RAR: {archivo}")
            dir_temporal = tempfile.mkdtemp()
            try:
                patoolib.extract_archive(ruta_completa, outdir=dir_temporal, verbosity=-1)
                for raiz, _, archivos_internos in os.walk(dir_temporal):
                    for archivo_interno in archivos_internos:
                        ruta_interno = os.path.join(raiz, archivo_interno)
                        nombre_mixto = f"{archivo} {archivo_interno}"
                        if procesar_archivo_individual(service, ruta_interno, nombre_mixto, maestro_edificios, id_lefacturamos):
                            contador += 1
            except Exception as e:
                print(f"⚠️ Error al descomprimir {archivo}: {e}")
            finally:
                shutil.rmtree(dir_temporal, ignore_errors=True)
        else:
            if procesar_archivo_individual(service, ruta_completa, archivo, maestro_edificios, id_lefacturamos):
                contador += 1

    print(f"\n✨ ¡Proceso finalizado! Total de archivos subidos correctamente: {contador}")

if __name__ == "__main__":
    ruta_backup_local = r"D:\Impresas"  # Cambiar a r"D:\Impresas" cuando estés listo para todo el disco
    ruta_archivo_maestro = r"C:\Users\CARLOS\LefacturamosApp\edificio.xlsx"
    
    procesar_backup_impresas(ruta_backup_local, ruta_archivo_maestro)