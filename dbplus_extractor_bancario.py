#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS PLUS - MÓDULO ESPECIALIZADO DE LECTURA Y CONCILIACIÓN DE EXTRACTOS BANCARIOS
========================================================================================
Lee extractos bancarios de cualquier banco de Colombia (Bancolombia, Davivienda, Bogotá,
Occidente, BBVA, AV Villas, etc.) en formato Excel (.xlsx, .xls) o CSV (.csv).

Funciones principales:
1. Normalización y detección inteligente de abonos/créditos bancarios.
2. Cruce con el censo de propietarios y cartera de DBPlus (MMxxxx.DBF, SSxxxx.DBF).
3. Motor de Matching Multinivel (Referencia, Apto en descripción, Cédula/NIT, Nombre, Valor).
4. Semáforo de confianza:
   - 🟢 Alta (>= 90%): Apto identificado con certeza.
   - 🟡 Media (50% - 89%): Sugerencia con coincidencia parcial.
   - 🔴 Baja (< 50%): Pago no identificado (para asignación manual o suspenso).
5. Imputación contable conforme a la Ley 675 / DBPlus (Intereses, Multas, Otros, Admon).
6. Escritor binario puro dBASE III (.DBF) sin dependencias externas para generar:
   - BASEPAG.DBF  (Todos los pagos)
   - BASEPAG1.DBF (Pagos identificados)
   - BASEPAG2.DBF (Pagos no identificados / en suspenso)
   - BASERC.DBF   (Recibos de caja oficiales)
   - BASELRC.DBF  (Listado oficial de recibos para entrega)
7. Generación de informe de conciliación bancaria en Excel (.xlsx).
"""

import os
import io
import re
import csv
import json
import struct
import datetime
from typing import Dict, List, Any, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# CONVERSOR DE NÚMEROS A LETRAS EN PESOS (VALETRAS)
# ==============================================================================
UNIDADES_LETRAS = [
    "", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE",
    "DIECIOCHO", "DIECINUEVE", "VEINTE"
]
DECENAS_LETRAS = [
    "", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"
]
CENTENAS_LETRAS = [
    "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
    "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"
]

def numero_a_letras(n: int) -> str:
    """Convierte un entero a palabras en español para VALETRAS en los recibos de caja."""
    if n == 0:
        return "CERO PESOS M/CTE"
    if n < 0:
        return "MENOS " + numero_a_letras(abs(n))
    
    def _bloque(num: int) -> str:
        if num == 100:
            return "CIEN"
        res = []
        c = num // 100
        d = (num % 100) // 10
        u = num % 10
        
        if c > 0:
            res.append(CENTENAS_LETRAS[c])
        if d == 1:
            res.append(UNIDADES_LETRAS[10 + u])
        elif d == 2:
            if u == 0:
                res.append("VEINTE")
            else:
                res.append(f"VEINTI{UNIDADES_LETRAS[u]}")
        else:
            if d > 0:
                res.append(DECENAS_LETRAS[d])
            if u > 0:
                if d > 0:
                    res.append("Y")
                res.append(UNIDADES_LETRAS[u])
        return " ".join([r for r in res if r])

    partes = []
    millones = n // 1000000
    resto_millones = n % 1000000
    miles = resto_millones // 1000
    unidades = resto_millones % 1000

    if millones > 0:
        if millones == 1:
            partes.append("UN MILLON")
        else:
            partes.append(f"{_bloque(millones)} MILLONES")

    if miles > 0:
        if miles == 1:
            partes.append("UN MIL")
        else:
            partes.append(f"{_bloque(miles)} MIL")

    if unidades > 0:
        partes.append(_bloque(unidades))

    texto = " ".join(partes).strip() + " PESOS M/CTE"
    return texto[:75]  # Límite campo VALETRAS DBF


# ==============================================================================
# ESCRITOR BINARIO PURO DBASE III / FOXPRO (.DBF)
# ==============================================================================
def escribir_dbf_puro(ruta_archivo: str, campos: List[Tuple[str, str, int, int]], registros: List[Dict[str, Any]]):
    """
    Escribe un archivo DBF binario estándar dBASE III sin librerías externas.
    campos: lista de tuplas (nombre, tipo, longitud, decimales)
    """
    os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
    
    now = datetime.datetime.now()
    num_records = len(registros)
    header_len = 32 + (len(campos) * 32) + 1
    record_len = 1 + sum(flen for _, _, flen, _ in campos)

    with open(ruta_archivo, "wb") as f:
        # 1. Cabecera principal (32 bytes)
        # Byte 0: 0x03 (dBASE III sin memo)
        # Bytes 1-3: AA MM DD
        # Bytes 4-7: Número de registros (uint32)
        # Bytes 8-9: Header length (uint16)
        # Bytes 10-11: Record length (uint16)
        # Bytes 12-31: Reservados (ceros)
        f.write(struct.pack(
            "<BBBBIHH20s",
            0x03,
            now.year - 2000 if now.year >= 2000 else now.year - 1900,
            now.month,
            now.day,
            num_records,
            header_len,
            record_len,
            b"\x00" * 20
        ))

        # 2. Descriptores de campos (32 bytes c/u)
        for fname, ftype, flen, fdec in campos:
            fname_bytes = fname.encode("latin1", errors="ignore")[:10].ljust(11, b"\x00")
            ftype_byte = ftype.encode("ascii")[:1]
            f.write(struct.pack(
                "<11scIBB14s",
                fname_bytes,
                ftype_byte,
                0,      # Dirección en memoria
                flen,   # Longitud
                fdec,   # Decimales
                b"\x00" * 14
            ))

        # 3. Terminador de cabecera
        f.write(b"\x0D")

        # 4. Registros
        for r in registros:
            # Byte de borrado: 0x20 = no borrado
            f.write(b"\x20")
            for fname, ftype, flen, fdec in campos:
                val = r.get(fname, "")
                if ftype == "N":
                    if val is None or val == "":
                        val_str = "0".rjust(flen)
                    else:
                        try:
                            if fdec > 0:
                                val_str = f"{float(val):.{fdec}f}".rjust(flen)
                            else:
                                val_str = str(int(round(float(val)))).rjust(flen)
                        except Exception:
                            val_str = "0".rjust(flen)
                    if len(val_str) > flen:
                        val_str = val_str[-flen:]
                    f.write(val_str.encode("latin1", errors="ignore"))
                elif ftype == "C":
                    val_str = str(val if val is not None else "").strip()
                    val_bytes = val_str.encode("latin1", errors="replace")[:flen].ljust(flen, b" ")
                    f.write(val_bytes)
                elif ftype == "D":
                    # Formato YYYYMMDD
                    val_str = str(val if val is not None else "").replace("-", "").replace("/", "").strip()[:8].ljust(8, b" ")
                    f.write(val_str.encode("ascii", errors="ignore"))
                else:
                    val_str = str(val if val is not None else "")[:flen].ljust(flen, b" ")
                    f.write(val_str.encode("latin1", errors="ignore"))

        # 5. EOF marker
        f.write(b"\x1A")


# Definición exacta de los esquemas de campos DBPlus
CAMPOS_BASEPAG = [
    ("CODIGO", "C", 4, 0),
    ("COD", "C", 2, 0),
    ("BLOQ", "C", 2, 0),
    ("APTO", "C", 4, 0),
    ("CLAVE", "C", 8, 0),
    ("FAC", "N", 6, 0),
    ("AA", "C", 4, 0),
    ("MESPAG", "C", 2, 0),
    ("DIAPAG", "C", 2, 0),
    ("VALOR", "N", 10, 0),
    ("TOTAL", "N", 10, 0),
    ("IDENT", "C", 1, 0),
    ("ADMONPAG", "N", 10, 0),
    ("INTERPAG", "N", 10, 0),
    ("OTROSPAG", "N", 10, 0),
    ("EXTRAPAG", "N", 10, 0),
    ("MULTAPAG", "N", 10, 0),
    ("SERPUPAG", "N", 10, 0),
    ("SERVIPAG", "N", 10, 0),
    ("NDNCPAG", "N", 10, 0),
    ("INT", "N", 8, 0),
    ("DIAS", "N", 3, 0),
    ("NOMURBAN", "C", 45, 0),
    ("MESTITULO", "C", 20, 0)
]

CAMPOS_BASERC = [
    ("CODIGO", "C", 4, 0),
    ("COD", "C", 2, 0),
    ("BLOQ", "C", 2, 0),
    ("APTO", "C", 4, 0),
    ("CLAVE", "C", 8, 0),
    ("FAC", "N", 6, 0),
    ("AA", "N", 5, 0),
    ("MESPAG", "N", 3, 0),
    ("DIAPAG", "N", 3, 0),
    ("PAGO", "N", 10, 0),
    ("CONCEPTO", "C", 60, 0),
    ("IDENT", "C", 1, 0),
    ("NUMRECI", "N", 6, 0),
    ("NOM", "C", 30, 0),
    ("DIREC", "C", 50, 0),
    ("EMAIL", "C", 60, 0),
    ("EMAIL1", "C", 60, 0),
    ("EMAIL2", "C", 60, 0),
    ("VALETRAS", "C", 75, 0),
    ("DIRAPTO", "C", 30, 0),
    ("NOMURBAN", "C", 55, 0),
    ("NITURBAN", "C", 11, 0),
    ("BANCO", "C", 23, 0),
    ("EMAILURBAN", "C", 60, 0),
    ("TEL", "N", 12, 0),
    ("TIPO", "C", 10, 0)
]

CAMPOS_BASELRC = [
    ("CODIGO", "C", 4, 0),
    ("COD", "C", 2, 0),
    ("BLOQ", "C", 2, 0),
    ("APTO", "C", 4, 0),
    ("CLAVE", "C", 8, 0),
    ("FAC", "N", 6, 0),
    ("AA", "N", 5, 0),
    ("MESPAG", "N", 3, 0),
    ("DIAPAG", "N", 3, 0),
    ("PAGO", "N", 10, 0),
    ("CONCEPTO", "C", 30, 0),
    ("IDENT", "C", 1, 0),
    ("NUMRECI", "N", 6, 0),
    ("NOMURBAN", "C", 55, 0),
    ("NOM", "C", 30, 0),
    ("DIRAPTO", "C", 30, 0),
    ("EMAIL", "C", 60, 0),
    ("EMAIL1", "C", 60, 0),
    ("EMAIL2", "C", 60, 0),
    ("MESTITULO", "C", 20, 0),
    ("TIPO", "C", 10, 0)
]


# ==============================================================================
# LECTOR Y PARSER DE EXTRACTOS BANCARIOS (EXCEL, CSV, TXT)
# ==============================================================================
def limpiar_valor_moneda(val: Any) -> float:
    """Convierte cadenas monetarias colombianas ($ 450.000, 450000.00, etc.) a float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(" ", "")
    if not s:
        return 0.0
    # Manejar formatos 1.250.000,00 vs 1,250,000.00
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            # 1.250.000,00 -> español
            s = s.replace(".", "").replace(",", ".")
        else:
            # 1,250,000.00 -> inglés
            s = s.replace(",", "")
    elif "," in s:
        # Puede ser 1250,50 o 1,250,000
        parts = s.split(",")
        if len(parts[-1]) == 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        # Extraer dígitos
        digits = re.findall(r"[-+]?\d*\.\d+|\d+", s)
        return float(digits[0]) if digits else 0.0


def normalizar_fecha(val: Any) -> Tuple[str, str, str]:
    """Retorna (año, mes, dia) en formato string ('2026', '8', '19')."""
    now = datetime.datetime.now()
    if isinstance(val, (datetime.datetime, datetime.date)):
        return (str(val.year), str(val.month), str(val.day))
    
    s = str(val or "").strip()
    # Buscar patrones YYYY-MM-DD o DD/MM/YYYY o DD-MM-YYYY
    m1 = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m1:
        return (m1.group(1), str(int(m1.group(2))), str(int(m1.group(3))))
    m2 = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", s)
    if m2:
        y = m2.group(3)
        if len(y) == 2:
            y = f"20{y}"
        return (y, str(int(m2.group(2))), str(int(m2.group(1))))
    
    return (str(now.year), str(now.month), str(now.day))


def parsear_archivo_extracto(archivo_bytes: bytes, nombre_archivo: str) -> List[Dict[str, Any]]:
    """
    Parsea el contenido de un archivo de extracto bancario en Excel, CSV o texto.
    Extrae filas con: {fecha_str, aa, mes, dia, descripcion, referencia, valor, documento}
    """
    fn_lower = nombre_archivo.lower()
    filas_raw = []

    if fn_lower.endswith((".xlsx", ".xlsm", ".xltx")):
        wb = openpyxl.load_workbook(io.BytesIO(archivo_bytes), data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            if any(cell is not None and str(cell).strip() != "" for cell in row):
                filas_raw.append([c for c in row])
    elif fn_lower.endswith((".csv", ".txt")):
        try:
            texto = archivo_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                texto = archivo_bytes.decode("latin1")
            except:
                texto = archivo_bytes.decode("cp850", errors="replace")
        
        # Detectar delimitador
        sample = texto[:2048]
        delim = ";" if sample.count(";") > sample.count(",") else ("," if sample.count(",") > sample.count("\t") else "\t")
        reader = csv.reader(io.StringIO(texto), delimiter=delim)
        for r in reader:
            if any(cell.strip() for cell in r):
                filas_raw.append(r)
    else:
        # Intentar como Excel o CSV por defecto
        try:
            wb = openpyxl.load_workbook(io.BytesIO(archivo_bytes), data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                filas_raw.append([c for c in row])
        except Exception:
            try:
                texto = archivo_bytes.decode("utf-8", errors="ignore")
                reader = csv.reader(io.StringIO(texto), delimiter=";")
                for r in reader:
                    filas_raw.append(r)
            except Exception as ex:
                raise ValueError(f"Formato no compatible para extracto bancario: {ex}")

    if not filas_raw:
        return []

    # Detectar fila de encabezados
    idx_header = -1
    col_fecha = -1
    col_desc = -1
    col_valor = -1
    col_ref = -1
    col_credito = -1

    keywords_fecha = ["fecha", "date", "fec", "dia", "transaccion", "fechatransaccion"]
    keywords_desc = ["descripcion", "concepto", "detalle", "movimiento", "transaccion", "tercero", "beneficiario", "descrip"]
    keywords_valor = ["credito", "abono", "deposito", "valor", "monto", "importe", "entrada"]
    keywords_ref = ["referencia", "ref", "documento", "doc", "comprobante", "aprobacion", "autorizacion", "nro"]

    for i, row in enumerate(filas_raw[:25]):
        row_str = [str(c or "").lower().strip() for c in row]
        matches = 0
        for col_idx, text in enumerate(row_str):
            clean_t = re.sub(r"[^a-z0-9]", "", text)
            if any(k in clean_t for k in keywords_fecha) and col_fecha == -1:
                col_fecha = col_idx
                matches += 1
            elif any(k in clean_t for k in ["credito", "abono", "deposito"]) and col_credito == -1:
                col_credito = col_idx
                col_valor = col_idx
                matches += 1
            elif any(k in clean_t for k in keywords_valor) and col_valor == -1:
                col_valor = col_idx
                matches += 1
            elif any(k in clean_t for k in keywords_desc) and col_desc == -1:
                col_desc = col_idx
                matches += 1
            elif any(k in clean_t for k in keywords_ref) and col_ref == -1:
                col_ref = col_idx
                matches += 1

        if matches >= 2:
            idx_header = i
            break

    # Si no se detectó encabezado explícito, usar primeras 4 columnas
    if idx_header == -1:
        idx_header = 0
        col_fecha = 0
        col_desc = 1 if len(filas_raw[0]) > 1 else 0
        col_valor = 2 if len(filas_raw[0]) > 2 else 1
        col_ref = 3 if len(filas_raw[0]) > 3 else -1

    transacciones = []
    for row in filas_raw[idx_header + 1:]:
        if not row:
            continue
        c_val = col_credito if col_credito != -1 else col_valor
        raw_val = row[c_val] if c_val < len(row) else 0
        valor = limpiar_valor_moneda(raw_val)

        # Solo nos interesan abonos / depósitos a la cuenta del edificio (> 0)
        if valor <= 0:
            continue

        raw_fecha = row[col_fecha] if col_fecha != -1 and col_fecha < len(row) else ""
        aa, mes, dia = normalizar_fecha(raw_fecha)
        fecha_str = f"{aa}-{int(mes):02d}-{int(dia):02d}"

        raw_desc = str(row[col_desc] if col_desc != -1 and col_desc < len(row) else "").strip()
        raw_ref = str(row[col_ref] if col_ref != -1 and col_ref < len(row) else "").strip()

        # Si no hay descripción pero hay referencia o viceversa
        desc_completa = f"{raw_desc} {raw_ref}".strip()

        transacciones.append({
            "fecha": fecha_str,
            "aa": aa,
            "mes": mes,
            "dia": dia,
            "descripcion": raw_desc or desc_completa,
            "referencia": raw_ref,
            "texto_completo": desc_completa.upper(),
            "valor": valor,
            "valorFmt": f"${valor:,.0f}".replace(",", ".")
        })

    return transacciones


# ==============================================================================
# MOTOR INTELIGENTE DE MATCHING (CRUCE EXTRACTO VS EDIFICIO DBPLUS)
# ==============================================================================
def extraer_posibles_aptos(texto: str) -> List[str]:
    """Extrae números de apartamento potenciales de una cadena de texto bancario."""
    candidatos = []
    # Patrones comunes en extractos bancarios colombianos:
    # "APTO 302", "APT 0302", "APTO-302", "#302", "TORRE 1 302", "CASA 12"
    pats = [
        r"(?:APTO|APT|AP|APARTAMENTO|OFICINA|OFI|LOCAL|LOC|CASA)[\s\-_.:#]*([0-9]{2,5})",
        r"#\s*([0-9]{3,5})",
        r"\b([0-9]{3,4})\b"
    ]
    for p in pats:
        encontrados = re.findall(p, texto, flags=re.IGNORECASE)
        for e in encontrados:
            if isinstance(e, tuple):
                e = e[0]
            e_str = str(e).strip()
            if len(e_str) >= 2 and e_str not in candidatos:
                candidatos.append(e_str)
    return candidatos


def conciliar_extracto_con_edificio(
    transacciones: List[Dict[str, Any]], 
    datos_edificio: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Cruza la lista de transacciones bancarias contra las unidades y propietarios
    del edificio DBPlus, clasificando en semáforo:
    - 🟢 Alta confianza (identificado automático)
    - 🟡 Media confianza (sugerencia de coincidencia)
    - 🔴 Baja confianza (no identificado / suspenso)
    """
    unidades = datos_edificio.get("unidades", [])
    info_ed = datos_edificio.get("edificio", {})
    cod_edificio = str(datos_edificio.get("codigo", "")).strip()

    # Índices para búsqueda ultrarrápida
    map_apto_directo = {}
    map_clave = {}
    map_cc = {}
    map_nombres = []

    for u in unidades:
        apto_norm = str(u.get("apto", "")).strip().zfill(4)
        apto_raw = str(u.get("apto", "")).strip()
        bloq = str(u.get("bloq", "00")).strip()
        clave = f"{cod_edificio[-2:]}{bloq.zfill(2)}{apto_norm}"
        
        map_apto_directo[apto_norm] = u
        map_apto_directo[apto_raw] = u
        map_clave[clave] = u
        
        cc = str(u.get("cc", "")).strip()
        if cc and len(cc) >= 6:
            map_cc[cc] = u
            
        nombre = str(u.get("propietario", "")).strip().upper()
        if nombre:
            palabras = [w for w in re.split(r"[^A-Z0-9]", nombre) if len(w) > 3 and w not in ["EDIFICIO", "APTO", "SENOR", "SENORA"]]
            map_nombres.append({"unidad": u, "nombre_completo": nombre, "palabras": palabras})

    pagos_clasificados = []
    total_recaudado = 0.0
    count_verde = 0
    count_amarillo = 0
    count_rojo = 0

    for idx, tx in enumerate(transacciones):
        texto = tx["texto_completo"]
        ref = str(tx.get("referencia", "")).strip().upper()
        valor = tx["valor"]
        total_recaudado += valor

        unidad_match = None
        confianza = 0
        criterio = "No Identificado"
        sugerencias = []

        # 1. Búsqueda por CLAVE DBPlus en referencia o texto (ej: 80000302)
        for clave, u in map_clave.items():
            if clave in ref or clave in texto:
                unidad_match = u
                confianza = 100
                criterio = f"Clave DBPlus ({clave})"
                break

        # 2. Búsqueda por Cédula / NIT en referencia o texto
        if not unidad_match:
            for cc, u in map_cc.items():
                if cc in texto or cc in ref:
                    unidad_match = u
                    confianza = 98
                    criterio = f"Cédula Propietario ({cc})"
                    break

        # 3. Búsqueda de Apto explícito en texto (ej: "APTO 302", "APT-0302")
        if not unidad_match:
            posibles = extraer_posibles_aptos(texto)
            for p in posibles:
                p_norm = p.zfill(4)
                if p_norm in map_apto_directo:
                    unidad_match = map_apto_directo[p_norm]
                    confianza = 95
                    criterio = f"Número de Apto detectado ({unidad_match['apto']})"
                    break
                elif p in map_apto_directo:
                    unidad_match = map_apto_directo[p]
                    confianza = 95
                    criterio = f"Número de Apto detectado ({p})"
                    break

        # 4. Búsqueda por Nombre de Propietario (coincidencia de palabras clave)
        if not unidad_match:
            mejores_candidatos = []
            for item in map_nombres:
                coincidencias = sum(1 for w in item["palabras"] if w in texto)
                if coincidencias >= 2:
                    mejores_candidatos.append((coincidencias, item["unidad"], item["nombre_completo"]))
                elif coincidencias == 1 and len(item["palabras"]) <= 2:
                    mejores_candidatos.append((1, item["unidad"], item["nombre_completo"]))

            if mejores_candidatos:
                mejores_candidatos.sort(key=lambda x: x[0], reverse=True)
                top = mejores_candidatos[0]
                if top[0] >= 2:
                    unidad_match = top[1]
                    confianza = 90
                    criterio = f"Nombre Propietario ({top[2]})"
                else:
                    confianza = 70
                    criterio = f"Coincidencia Parcial de Nombre ({top[2]})"
                    sugerencias = [cand[1]["apto"] for cand in mejores_candidatos[:3]]

        # 5. Coincidencia por Valor Exacto si aún no hay match
        if not unidad_match:
            unidades_con_valor = [
                u for u in unidades 
                if abs(float(u.get("totalFinal", 0.0)) - valor) < 1.0 or abs(float(u.get("admon", 0.0)) - valor) < 1.0
            ]
            if len(unidades_con_valor) == 1:
                confianza = 65
                criterio = f"Valor exacto coincide con deuda/cuota de Apto {unidades_con_valor[0]['apto']}"
                sugerencias = [unidades_con_valor[0]["apto"]]
            elif len(unidades_con_valor) > 1:
                confianza = 50
                criterio = f"Valor coincide con {len(unidades_con_valor)} unidades del edificio"
                sugerencias = [u["apto"] for u in unidades_con_valor[:4]]

        # Semáforo
        if confianza >= 85 and unidad_match:
            color = "verde"
            count_verde += 1
            ident_flag = "1"
        elif confianza >= 50 or sugerencias:
            color = "amarillo"
            count_amarillo += 1
            ident_flag = "1" if unidad_match else "N"
        else:
            color = "rojo"
            count_rojo += 1
            ident_flag = "N"

        apto_asignado = unidad_match["apto"] if unidad_match else (sugerencias[0] if sugerencias else "")
        propietario_asignado = unidad_match.get("propietario", "") if unidad_match else ""

        # Imputación contable estimada
        imputacion = imputar_pago_ley675(valor, unidad_match) if unidad_match else {
            "admon": valor, "interes": 0, "otros": 0, "extra": 0, "multa": 0, "ser_pub": 0, "ser_serv": 0, "notas_dc": 0
        }

        pagos_clasificados.append({
            "id": f"pago_{idx+1}",
            "indice": idx + 1,
            "fecha": tx["fecha"],
            "aa": tx["aa"],
            "mes": tx["mes"],
            "dia": tx["dia"],
            "descripcion": tx["descripcion"],
            "referencia": tx["referencia"],
            "valor": valor,
            "valorFmt": tx["valorFmt"],
            "apto": apto_asignado,
            "bloq": unidad_match.get("bloq", "00") if unidad_match else "00",
            "propietario": propietario_asignado,
            "confianza": confianza,
            "color": color,
            "criterio": criterio,
            "sugerencias": sugerencias,
            "ident": ident_flag,
            "imputacion": imputacion
        })

    return {
        "status": "success",
        "codigo_edificio": cod_edificio,
        "edificio": info_ed,
        "total_transacciones": len(transacciones),
        "total_recaudado": total_recaudado,
        "total_recaudado_fmt": f"${total_recaudado:,.0f}".replace(",", "."),
        "metricas": {
            "verdes": count_verde,
            "amarillos": count_amarillo,
            "rojos": count_rojo,
            "porcentaje_identificado": round((count_verde / len(transacciones) * 100), 1) if transacciones else 0
        },
        "pagos": pagos_clasificados
    }


# ==============================================================================
# IMPUTACIÓN DE PAGOS SEGÚN LEY 675 / DBPLUS
# ==============================================================================
def imputar_pago_ley675(valor_pago: float, unidad_info: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """
    Distribuye el dinero en el orden normativo de la Ley 675:
    1. Intereses de mora
    2. Multas
    3. Otros conceptos / Cuotas extraordinarias
    4. Servicios y notas
    5. Administración ordinaria
    """
    if not unidad_info:
        return {
            "admon": valor_pago, "interes": 0.0, "otros": 0.0, "extra": 0.0, 
            "multa": 0.0, "ser_pub": 0.0, "ser_serv": 0.0, "notas_dc": 0.0
        }

    remanente = float(valor_pago)
    
    # Saldos pendientes de la unidad
    deuda_int = float(unidad_info.get("interes", 0.0) or (float(unidad_info.get("inta", 0)) + float(unidad_info.get("intp", 0))))
    deuda_mul = float(unidad_info.get("multa", 0.0) or (float(unidad_info.get("multaa", 0)) + float(unidad_info.get("multap", 0))))
    deuda_ext = float(unidad_info.get("extra", 0.0) or (float(unidad_info.get("extraa", 0)) + float(unidad_info.get("extrap", 0))))
    deuda_otr = float(unidad_info.get("otros", 0.0) or (float(unidad_info.get("otrosa", 0)) + float(unidad_info.get("otrosp", 0))))
    deuda_sp = float(unidad_info.get("ser_pub", 0.0) or (float(unidad_info.get("serpua", 0)) + float(unidad_info.get("serpup", 0))))
    deuda_ss = float(unidad_info.get("ser_serv", 0.0) or (float(unidad_info.get("servia", 0)) + float(unidad_info.get("servip", 0))))
    deuda_nd = float(unidad_info.get("notas_dc", 0.0) or (float(unidad_info.get("ndnca", 0)) + float(unidad_info.get("ndncp", 0))))
    deuda_adm = float(unidad_info.get("actual", 0.0) or unidad_info.get("admon", 0.0)) + float(unidad_info.get("pend", 0.0))

    def cobrar(deuda: float) -> Tuple[float, float]:
        nonlocal remanente
        if remanente <= 0 or deuda <= 0:
            return 0.0, remanente
        pago = min(remanente, deuda)
        remanente -= pago
        return pago, remanente

    p_int, _ = cobrar(deuda_int)
    p_mul, _ = cobrar(deuda_mul)
    p_ext, _ = cobrar(deuda_ext)
    p_otr, _ = cobrar(deuda_otr)
    p_sp, _ = cobrar(deuda_sp)
    p_ss, _ = cobrar(deuda_ss)
    p_nd, _ = cobrar(deuda_nd)
    
    # El resto va a administración ordinaria (incluso si es anticipo)
    p_adm = remanente
    remanente = 0.0

    return {
        "interes": round(p_int, 2),
        "multa": round(p_mul, 2),
        "extra": round(p_ext, 2),
        "otros": round(p_otr, 2),
        "ser_pub": round(p_sp, 2),
        "ser_serv": round(p_ss, 2),
        "notas_dc": round(p_nd, 2),
        "admon": round(p_adm, 2)
    }


# ==============================================================================
# GENERADOR OFICIAL DE ARCHIVOS DBPLUS (BASEPAG, BASERC, BASELRC, EXCEL)
# ==============================================================================
def generar_archivos_dbplus_pagos(
    pagos_confirmados: List[Dict[str, Any]], 
    codigo_edificio: str, 
    directorio_salida: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera los archivos oficiales de pagos en formato DBPlus (.DBF):
    1. BASEPAG.DBF
    2. BASEPAG1.DBF (Identificados)
    3. BASEPAG2.DBF (No identificados / en suspenso)
    4. BASERC.DBF   (Recibos de caja)
    5. BASELRC.DBF  (Listado oficial)
    6. CONCILIACION_BANCARIA_{codigo}.xlsx
    """
    from dbplus_service import obtener_datos_dbplus_edificio
    db_data = obtener_datos_dbplus_edificio(codigo_edificio) or {}
    edificio = db_data.get("edificio", {})
    unidades = db_data.get("unidades", [])
    map_u = {str(u.get("apto", "")).strip(): u for u in unidades}

    clean_cod = str(codigo_edificio).replace("cj_", "").strip()
    cod_2d = clean_cod[-2:].zfill(2)
    nom_edif = edificio.get("nombre", f"EDIFICIO {clean_cod}").upper()
    nit_edif = edificio.get("nit", "").strip()
    banco_edif = edificio.get("banco", "").strip()
    email_edif = edificio.get("email", "").strip()
    tel_edif = int(re.sub(r"[^0-9]", "", str(edificio.get("telefono", "0")))) if re.sub(r"[^0-9]", "", str(edificio.get("telefono", "0"))) else 0

    if not directorio_salida:
        # Prioridad: C:\dbplus\{codigo} si existe localmente, o data/extractos/{codigo}
        c_cand = f"C:/dbplus/{clean_cod}"
        if os.path.exists(c_cand) and os.path.isdir(c_cand):
            directorio_salida = c_cand
        else:
            directorio_salida = os.path.join(os.path.abspath("data"), "extractos", clean_cod)

    os.makedirs(directorio_salida, exist_ok=True)

    # Consecutivo inicial de recibo de caja
    consecutivo_recibo = 3500

    regs_basepag = []
    regs_basepag1 = []
    regs_basepag2 = []
    regs_baserc = []
    regs_baselrc = []

    now = datetime.datetime.now()
    meses_nombres = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

    for p in pagos_confirmados:
        apto = str(p.get("apto", "")).strip().zfill(4) if p.get("apto") else "0000"
        bloq = str(p.get("bloq", "00")).strip().zfill(2)
        clave = f"{cod_2d}{bloq}{apto}"
        valor = float(p.get("valor", 0.0))
        aa = str(p.get("aa") or now.year)
        mes_pag = str(p.get("mes") or now.month)
        dia_pag = str(p.get("dia") or now.day)
        ident = "1" if (p.get("ident") == "1" or (p.get("apto") and apto != "0000")) else "N"
        
        # Info de la unidad
        u_info = map_u.get(str(p.get("apto", "")).strip(), {})
        fac = int(u_info.get("fac") or 0)
        nom_prop = (p.get("propietario") or u_info.get("propietario") or (f"PROPIETARIO APTO {apto}" if ident == "1" else "PAGO NO IDENTIFICADO")).upper()[:30]
        email_prop = (u_info.get("email") or "")[:60]
        dir_apto = f"APTO-{apto} Bloque {bloq}"[:30]

        # Desglose de conceptos
        imp = p.get("imputacion") or imputar_pago_ley675(valor, u_info)
        admon_pag = float(imp.get("admon", valor if ident == "1" else 0.0))
        inter_pag = float(imp.get("interes", 0.0))
        otros_pag = float(imp.get("otros", 0.0))
        extra_pag = float(imp.get("extra", 0.0))
        multa_pag = float(imp.get("multa", 0.0))
        serpu_pag = float(imp.get("ser_pub", 0.0))
        servi_pag = float(imp.get("ser_serv", 0.0))
        ndnc_pag = float(imp.get("notas_dc", 0.0))
        total_imp = admon_pag + inter_pag + otros_pag + extra_pag + multa_pag + serpu_pag + servi_pag + ndnc_pag

        mes_nombre = meses_nombres[int(mes_pag) - 1] if 1 <= int(mes_pag) <= 12 else "DEL MES"
        mes_titulo = f"{mes_nombre} DE {aa}"

        # 1. Registro BASEPAG
        rec_pag = {
            "CODIGO": clean_cod,
            "COD": cod_2d,
            "BLOQ": bloq,
            "APTO": apto,
            "CLAVE": clave,
            "FAC": fac,
            "AA": aa,
            "MESPAG": mes_pag,
            "DIAPAG": dia_pag,
            "VALOR": valor,
            "TOTAL": total_imp if ident == "1" else 0,
            "IDENT": ident,
            "ADMONPAG": admon_pag,
            "INTERPAG": inter_pag,
            "OTROSPAG": otros_pag,
            "EXTRAPAG": extra_pag,
            "MULTAPAG": multa_pag,
            "SERPUPAG": serpu_pag,
            "SERVIPAG": servi_pag,
            "NDNCPAG": ndnc_pag,
            "INT": 0,
            "DIAS": 0,
            "NOMURBAN": nom_edif[:45],
            "MESTITULO": mes_titulo[:20]
        }
        regs_basepag.append(rec_pag)

        if ident == "1":
            regs_basepag1.append(rec_pag)
        else:
            regs_basepag2.append(rec_pag)

        # 2. Registro BASERC (Recibo de caja)
        consecutivo_recibo += 1
        rec_rc = {
            "CODIGO": clean_cod,
            "COD": cod_2d,
            "BLOQ": bloq,
            "APTO": apto,
            "CLAVE": clave,
            "FAC": fac,
            "AA": int(aa),
            "MESPAG": int(mes_pag),
            "DIAPAG": int(dia_pag),
            "PAGO": valor,
            "CONCEPTO": f"Pago/Abono del mes de {mes_nombre.capitalize()}"[:60],
            "IDENT": ident,
            "NUMRECI": consecutivo_recibo,
            "NOM": nom_prop,
            "DIREC": edificio.get("direccion", "")[:50],
            "EMAIL": email_prop,
            "EMAIL1": "",
            "EMAIL2": "",
            "VALETRAS": numero_a_letras(int(valor)),
            "DIRAPTO": dir_apto,
            "NOMURBAN": nom_edif[:55],
            "NITURBAN": nit_edif[:11],
            "BANCO": banco_edif[:23],
            "EMAILURBAN": email_edif[:60],
            "TEL": tel_edif,
            "TIPO": "APTO"
        }
        regs_baserc.append(rec_rc)

        # 3. Registro BASELRC (Listado para entrega / envío)
        regs_baselrc.append({
            "CODIGO": clean_cod,
            "COD": cod_2d,
            "BLOQ": bloq,
            "APTO": apto,
            "CLAVE": clave,
            "FAC": fac,
            "AA": int(aa),
            "MESPAG": int(mes_pag),
            "DIAPAG": int(dia_pag),
            "PAGO": valor,
            "CONCEPTO": f"Pago/Abono del mes de"[:30],
            "IDENT": ident,
            "NUMRECI": consecutivo_recibo,
            "NOMURBAN": nom_edif[:55],
            "NOM": nom_prop,
            "DIRAPTO": dir_apto,
            "EMAIL": email_prop,
            "EMAIL1": "",
            "EMAIL2": "",
            "MESTITULO": mes_titulo[:20],
            "TIPO": "APTO"
        })

    # Guardar los archivos DBF
    p_basepag = os.path.join(directorio_salida, "BASEPAG.DBF")
    p_basepag1 = os.path.join(directorio_salida, "BASEPAG1.DBF")
    p_basepag2 = os.path.join(directorio_salida, "BASEPAG2.DBF")
    p_baserc = os.path.join(directorio_salida, "BASERC.DBF")
    p_baselrc = os.path.join(directorio_salida, "BASELRC.DBF")

    escribir_dbf_puro(p_basepag, CAMPOS_BASEPAG, regs_basepag)
    escribir_dbf_puro(p_basepag1, CAMPOS_BASEPAG, regs_basepag1)
    escribir_dbf_puro(p_basepag2, CAMPOS_BASEPAG, regs_basepag2)
    escribir_dbf_puro(p_baserc, CAMPOS_BASERC, regs_baserc)
    escribir_dbf_puro(p_baselrc, CAMPOS_BASELRC, regs_baselrc)

    # Generar Informe Oficial en Excel (.xlsx)
    p_excel = os.path.join(directorio_salida, f"CONCILIACION_BANCARIA_{clean_cod}_{now.strftime('%Y%m%d_%H%M')}.xlsx")
    generar_excel_conciliacion(regs_basepag, regs_baserc, edificio, p_excel)

    return {
        "status": "success",
        "codigo": clean_cod,
        "directorio": directorio_salida,
        "total_pagos": len(regs_basepag),
        "identificados": len(regs_basepag1),
        "no_identificados": len(regs_basepag2),
        "total_valor": sum(r["VALOR"] for r in regs_basepag),
        "archivos": {
            "basepag": p_basepag,
            "basepag1": p_basepag1,
            "basepag2": p_basepag2,
            "baserc": p_baserc,
            "baselrc": p_baselrc,
            "excel": p_excel
        }
    }


def generar_excel_conciliacion(regs_basepag, regs_baserc, edificio, ruta_salida):
    """Genera un archivo Excel elegante con el resumen de la conciliación bancaria."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Conciliación Bancaria"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    f_title = Font(name="Segoe UI", size=14, bold=True, color="1E293B")
    f_sub = Font(name="Segoe UI", size=10, bold=False, color="64748B")
    f_head = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    f_data = Font(name="Segoe UI", size=10, color="0F172A")
    f_bold = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
    
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_total = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_verde = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    fill_rojo = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    border_thin = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    ws["A1"] = f"LEFACTURAMOS PLUS • CONCILIACIÓN DE EXTRACTO BANCARIO"
    ws["A1"].font = f_title
    ws["A2"] = f"Edificio: {edificio.get('nombre', '')} | NIT: {edificio.get('nit', '')} | Banco: {edificio.get('banco', '')} {edificio.get('cuenta', '')}"
    ws["A2"].font = f_sub

    headers = [
        "Recibo #", "Fecha", "Apto", "Propietario", "Valor Banco", 
        "Admón", "Interés", "Otros", "Extra", "Multa", "Estado"
    ]
    for c_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=c_idx, value=h)
        cell.font = f_head
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    map_rc = {r["APTO"]: r for r in regs_baserc}
    row_num = 5
    tot_val = 0.0
    tot_adm = 0.0
    tot_int = 0.0

    for p in regs_basepag:
        rc = map_rc.get(p["APTO"], {})
        ws.cell(row=row_num, column=1, value=rc.get("NUMRECI", "-")).alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=2, value=f"{p['AA']}-{int(p['MESPAG']):02d}-{int(p['DIAPAG']):02d}").alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=3, value=p["APTO"]).alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=4, value=rc.get("NOM", "PAGO NO IDENTIFICADO"))
        
        c_val = ws.cell(row=row_num, column=5, value=p["VALOR"])
        c_val.number_format = "$#,##0"
        
        c_adm = ws.cell(row=row_num, column=6, value=p["ADMONPAG"])
        c_adm.number_format = "$#,##0"
        
        c_int = ws.cell(row=row_num, column=7, value=p["INTERPAG"])
        c_int.number_format = "$#,##0"
        
        c_otr = ws.cell(row=row_num, column=8, value=p["OTROSPAG"])
        c_otr.number_format = "$#,##0"
        
        c_ext = ws.cell(row=row_num, column=9, value=p["EXTRAPAG"])
        c_ext.number_format = "$#,##0"
        
        c_mul = ws.cell(row=row_num, column=10, value=p["MULTAPAG"])
        c_mul.number_format = "$#,##0"
        
        c_est = ws.cell(row=row_num, column=11, value="Identificado" if p["IDENT"] == "1" else "En Suspenso")
        c_est.alignment = Alignment(horizontal="center")
        c_est.fill = fill_verde if p["IDENT"] == "1" else fill_rojo

        for c_idx in range(1, 12):
            cell = ws.cell(row=row_num, column=c_idx)
            cell.font = f_data
            cell.border = border_thin

        tot_val += p["VALOR"]
        tot_adm += p["ADMONPAG"]
        tot_int += p["INTERPAG"]
        row_num += 1

    # Fila de Totales
    ws.cell(row=row_num, column=1, value="")
    ws.cell(row=row_num, column=2, value="")
    ws.cell(row=row_num, column=3, value="")
    cell_tot_lbl = ws.cell(row=row_num, column=4, value="TOTAL CONCILIADO:")
    cell_tot_lbl.font = f_bold
    cell_tot_lbl.alignment = Alignment(horizontal="right")
    
    cell_tot_val = ws.cell(row=row_num, column=5, value=tot_val)
    cell_tot_val.font = f_bold
    cell_tot_val.number_format = "$#,##0"
    
    cell_tot_adm = ws.cell(row=row_num, column=6, value=tot_adm)
    cell_tot_adm.font = f_bold
    cell_tot_adm.number_format = "$#,##0"
    
    cell_tot_int = ws.cell(row=row_num, column=7, value=tot_int)
    cell_tot_int.font = f_bold
    cell_tot_int.number_format = "$#,##0"

    for c_idx in range(1, 12):
        ws.cell(row=row_num, column=c_idx).fill = fill_total
        ws.cell(row=row_num, column=c_idx).border = border_thin

    # Ajustar ancho de columnas
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    wb.save(ruta_salida)


def generar_plantilla_extracto_excel(ruta_destino: str):
    """Crea una plantilla modelo de extracto bancario con transacciones de ejemplo."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Extracto Bancario Modelo"
    ws.views.sheetView[0].showGridLines = True

    header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    
    headers = ["Fecha", "Descripcion / Concepto", "Referencia / Documento", "Credito / Abono", "Saldo"]
    for c_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    ejemplos = [
        ("2026-08-19", "TRANSFERENCIA DE: CLAUDIA RODRIGUEZ", "80000302", 453900, 15450000),
        ("2026-08-16", "CONSIGNACION CORRESPONSAL BANCARIO", "0503", 3100, 15453100),
        ("2026-08-03", "PAGO PSE REF: ALVARO ANTONIO GONZALEZ", "80000403", 142100, 15595200),
        ("2026-08-10", "ABONO APTO 301 TRANSFERENCIA BANCOLOMBIA", "10203040", 449000, 16044200),
        ("2026-08-12", "CONSIGNACION EFECTIVO SUCURSAL BELLO", "009944", 250000, 16294200)
    ]
    for r_idx, ej in enumerate(ejemplos, 2):
        ws.cell(row=r_idx, column=1, value=ej[0]).alignment = Alignment(horizontal="center")
        ws.cell(row=r_idx, column=2, value=ej[1])
        ws.cell(row=r_idx, column=3, value=ej[2]).alignment = Alignment(horizontal="center")
        c_val = ws.cell(row=r_idx, column=4, value=ej[3])
        c_val.number_format = "$#,##0"
        c_sal = ws.cell(row=r_idx, column=5, value=ej[4])
        c_sal.number_format = "$#,##0"

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    wb.save(ruta_destino)
