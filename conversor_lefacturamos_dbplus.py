#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal
CONVERSOR MAESTRO DE BASES DE DATOS (DBPlus / FoxPro / DBF / Excel a Estándar Ley 675)
========================================================================================

DESCRIPCIÓN:
Convierte automáticamente los archivos contables de copropiedades (ssxxxx.DBF o ssxxxx.xlsx)
aplicando las reglas de cálculo de saldos y la homologación de nombres definida en CAMPO_FAC:
  1. Extrae: APTO, BLOQ, FAC
  2. Saldos Pendientes: PEND, INTP, OTROSP, EXTRAP, MULTAP, SERPUP, SERVIP, NDNCP
  3. Cobro del Mes: ACTUAL, INTA, OTROSA, EXTRAA, MULTAA, SERPUA, SERVIA, NDNCA
  4. Suma cada campo en su orden:
     PEND+ACTUAL    -> Admón
     INTP+INTA      -> Interés
     OTROSP+OTROSA  -> Otros
     EXTRAP+EXTRAA  -> Extra
     MULTAP+MULTAA  -> Multa
     SERPUP+SERPUA  -> Ser_Pub
     SERVIP+SERVIA  -> Ser_Serv
     NDNCP+NDNCA    -> Notas_d_c
     TOTAL FINAL    -> Suma horizontal de cada concepto
  5. Totaliza verticalmente cada columna al pie de la tabla.
  6. Cruza con EDIFICIO.xlsx/EDIFICIO.DBF (Nombre, NIT, Banco, Cuenta, Período).
  7. Cruza con BASEFAC.DBF / BASENVIP.DBF (Propietarios, Cédulas, Correos).
  8. Emite el archivo Excel oficial y archivo JSON listo para la Web y Apps Móviles.

COMPATIBILIDAD:
  - Windows (PowerShell / CMD), Android, iOS (Backend Python API)
  - 100% Python nativo con OpenPyXL y Pandas (lector DBF binario puro, sin librerías C).
"""

import os
import sys
import glob
import json
import struct
import argparse
from typing import Dict, List, Any, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

VERSION = "3.1.0-2026"

# ==============================================================================
# LECTOR PURO DE ARCHIVOS DBASE / FOXPRO (.DBF)
# ==============================================================================
def leer_dbf_puro(ruta_dbf: str) -> List[Dict[str, Any]]:
    """Lee archivos .DBF dBase III / FoxPro sin necesidad de paquetes externos."""
    if not os.path.exists(ruta_dbf):
        raise FileNotFoundError(f"No existe el archivo DBF: {ruta_dbf}")

    with open(ruta_dbf, "rb") as f:
        header = f.read(32)
        if len(header) < 32:
            return []
        
        num_records, header_len, record_len = struct.unpack("<IHH", header[4:12])
        num_fields = (header_len - 33) // 32
        
        fields = []
        for _ in range(num_fields):
            fdata = f.read(32)
            fname = fdata[:11].replace(b"\x00", b"").decode("latin1", errors="ignore").strip().upper()
            ftype = chr(fdata[11])
            flen = fdata[16]
            fdec = fdata[17]
            fields.append((fname, ftype, flen, fdec))
            
        f.seek(header_len)
        records = []
        for _ in range(num_records):
            buf = f.read(record_len)
            if not buf or len(buf) < record_len:
                break
            if buf[0] == 0x2A: # Registro marcado como eliminado
                continue
            
            rec = {}
            offset = 1
            for fname, ftype, flen, fdec in fields:
                val_str = buf[offset:offset + flen].decode("latin1", errors="ignore").strip()
                if ftype == "N":
                    try:
                        if "." in val_str:
                            rec[fname] = float(val_str)
                        else:
                            rec[fname] = int(val_str) if val_str else 0
                    except:
                        rec[fname] = 0
                else:
                    rec[fname] = val_str
                offset += flen
            records.append(rec)
            
        return records

# ==============================================================================
# CARGADOR DE HOMOLOGACIÓN DESDE CAMPO_FAC.XLSX
# ==============================================================================
def cargar_mapeo_campo_fac(ruta_campo_fac: str = "CAMPO_FAC.xlsx") -> Dict[str, str]:
    """
    Carga el archivo CAMPO_FAC.xlsx para obtener los nombres que deben figurar
    en el segundo renglón según lo establecido por el usuario:
      - pend y actual -> Admón
      - intp y inta -> Interés
      - otrosp y otrosa -> Otros
      - extrap y extraa -> Extra
      - multap y multaa -> Multa
      - serpup y serpua -> Ser_Pub
      - servip y servia -> Ser_Serv
      - ndncp y ndnca -> Notas_d_c
    """
    mapeo_por_defecto = {
        "admon": "Admón",
        "interes": "Interés",
        "otros": "Otros",
        "extra": "Extra",
        "multa": "Multa",
        "ser_pub": "Ser_Pub",
        "ser_serv": "Ser_Serv",
        "notas_d_c": "Notas_d_c"
    }

    if not os.path.exists(ruta_campo_fac):
        print(f"[*] Usando nombres estandar de CAMPO_FAC (archivo no encontrado en {ruta_campo_fac}).")
        return mapeo_por_defecto

    try:
        wb = openpyxl.load_workbook(ruta_campo_fac, data_only=True)
        ws = wb.active
        
        row1 = [str(ws.cell(row=1, column=c).value or "").strip().upper() for c in range(1, 15)]
        row2 = [str(ws.cell(row=2, column=c).value or "").strip() for c in range(1, 15)]
        
        resultado = dict(mapeo_por_defecto)
        for idx, col_code in enumerate(row1):
            if idx < len(row2) and row2[idx]:
                raw = row2[idx]
                # Limpiar caracteres invalidos
                if "ADMON" in col_code:
                    resultado["admon"] = "Admón"
                elif "INTERES" in col_code:
                    resultado["interes"] = "Interés"
                elif "OTROS" in col_code:
                    resultado["otros"] = "Otros" if ("otro" in raw.lower() or not raw) else raw.replace("", "")
                elif "EXTRA" in col_code:
                    resultado["extra"] = "Extra"
                elif "MULTA" in col_code:
                    resultado["multa"] = "Multa"
                elif "SER_PUB" in col_code:
                    resultado["ser_pub"] = "Ser_Pub" if "pub" in raw.lower() else raw.replace("", "")
                elif "SER_SERV" in col_code:
                    resultado["ser_serv"] = "Ser_Serv" if "seg" in raw.lower() else raw.replace("", "")
                elif "NOTAS" in col_code:
                    resultado["notas_d_c"] = "Notas_d_c"

        print(f"[OK] Homologacion CAMPO_FAC cargada correctamente: {resultado}")
        return resultado
    except Exception as e:
        print(f"[!] Aviso al leer CAMPO_FAC ({e}). Aplicando nombres canonicos.")
        return mapeo_por_defecto

# ==============================================================================
# CARGADOR DE DATOS DE EDIFICIO (EDIFICIO.XLSX / EDIFICIO.DBF)
# ==============================================================================
def cargar_datos_edificio(codigo_edificio: str, ruta_base: str = ".") -> Dict[str, Any]:
    """Busca los datos maestros del edificio por su código alfanumérico (ej: 7480)."""
    cod_clean = str(codigo_edificio).strip().upper()
    info = {
        "codigo": cod_clean,
        "nombre": f"EDIFICIO {cod_clean}",
        "nit": "",
        "banco": "",
        "cuenta": "",
        "mes_actual": "",
        "anio": "",
        "direccion": "",
        "telefono": "",
        "email": ""
    }

    # Intentar primero con EDIFICIO.xlsx
    ruta_xlsx = os.path.join(ruta_base, "EDIFICIO.xlsx")
    if os.path.exists(ruta_xlsx):
        try:
            wb = openpyxl.load_workbook(ruta_xlsx, data_only=True)
            ws = wb.active
            headers = [str(ws.cell(row=1, column=c).value or "").strip().upper() for c in range(1, ws.max_column + 1)]
            
            c_cod = headers.index("CODIGO") + 1 if "CODIGO" in headers else -1
            c_nom = headers.index("NOMURBAN") + 1 if "NOMURBAN" in headers else -1
            c_nit = headers.index("NITURBAN") + 1 if "NITURBAN" in headers else -1
            c_ban = headers.index("BANCO") + 1 if "BANCO" in headers else -1
            c_cue = headers.index("CUENTA") + 1 if "CUENTA" in headers else -1
            c_mes = headers.index("MESACT") + 1 if "MESACT" in headers else -1
            c_ano = headers.index("ANO") + 1 if "ANO" in headers else -1
            c_dir = headers.index("DIREC") + 1 if "DIREC" in headers else -1
            c_tel = headers.index("TEL") + 1 if "TEL" in headers else -1
            c_ema = headers.index("EMAILURBAN") + 1 if "EMAILURBAN" in headers else -1

            if c_cod != -1:
                for r in range(2, ws.max_row + 1):
                    val = str(ws.cell(row=r, column=c_cod).value or "").strip().upper()
                    if val == cod_clean:
                        if c_nom != -1: info["nombre"] = str(ws.cell(row=r, column=c_nom).value or info["nombre"]).strip()
                        if c_nit != -1: info["nit"] = str(ws.cell(row=r, column=c_nit).value or "").strip()
                        if c_ban != -1: info["banco"] = str(ws.cell(row=r, column=c_ban).value or "").strip()
                        if c_cue != -1: info["cuenta"] = str(ws.cell(row=r, column=c_cue).value or "").strip()
                        if c_mes != -1: info["mes_actual"] = str(ws.cell(row=r, column=c_mes).value or "").strip()
                        if c_ano != -1: info["anio"] = str(ws.cell(row=r, column=c_ano).value or "").strip()
                        if c_dir != -1: info["direccion"] = str(ws.cell(row=r, column=c_dir).value or "").strip()
                        if c_tel != -1: info["telefono"] = str(ws.cell(row=r, column=c_tel).value or "").strip()
                        if c_ema != -1: info["email"] = str(ws.cell(row=r, column=c_ema).value or "").strip()
                        break
        except Exception as e:
            print(f"[!] Error leyendo EDIFICIO.xlsx: {e}")

    # Si falta información, intentar con EDIFICIO.DBF
    ruta_dbf = os.path.join(ruta_base, "EDIFICIO.DBF")
    if os.path.exists(ruta_dbf) and not info["nit"]:
        try:
            recs = leer_dbf_puro(ruta_dbf)
            for r in recs:
                if str(r.get("CODIGO", "")).strip().upper() == cod_clean:
                    info["nombre"] = r.get("NOMURBAN", info["nombre"])
                    info["nit"] = r.get("NITURBAN", info["nit"])
                    info["banco"] = r.get("BANCO", info["banco"])
                    info["cuenta"] = r.get("CUENTA", info["cuenta"])
                    info["mes_actual"] = r.get("MESACT", info["mes_actual"])
                    info["anio"] = str(r.get("ANO", info["anio"]))
                    info["direccion"] = r.get("DIREC", info["direccion"])
                    info["telefono"] = str(r.get("TEL", info["telefono"]))
                    info["email"] = r.get("EMAILURBAN", info["email"])
                    break
        except Exception as e:
            print(f"[!] Error leyendo EDIFICIO.DBF: {e}")

    return info

# ==============================================================================
# CARGADOR DE DATOS DE PROPIETARIOS Y CORREOS (BASEFAC.DBF / BASENVIP.DBF)
# ==============================================================================
def cargar_directorio_propietarios(codigo_edificio: str, ruta_base: str = ".") -> Dict[str, Dict[str, str]]:
    """Carga los nombres de propietarios, cédulas y correos para cruzar por BLOQ y APTO."""
    directorio = {}
    
    # 1. Leer BASEFAC.DBF
    ruta_basefac = os.path.join(ruta_base, "BASEFAC.DBF")
    if os.path.exists(ruta_basefac):
        try:
            for r in leer_dbf_puro(ruta_basefac):
                apto = str(r.get("APTO", "")).strip()
                bloq = str(r.get("BLOQ", "")).strip()
                key = f"{bloq}_{apto}" if bloq else apto
                directorio[key] = {
                    "propietario": r.get("NOM", "").strip(),
                    "inquilino": r.get("NOMINQ", "").strip(),
                    "documento": r.get("CC_NIT", "").strip(),
                    "coef_urb": float(r.get("COEF_URB", 0) or 0),
                    "email": ""
                }
        except Exception as e:
            print(f"[!] Error leyendo BASEFAC.DBF: {e}")

    # 2. Leer BASENVIP.DBF para correos electrónicos
    ruta_envip = os.path.join(ruta_base, "BASENVIP.DBF")
    if os.path.exists(ruta_envip):
        try:
            for r in leer_dbf_puro(ruta_envip):
                apto = str(r.get("APTO", "")).strip()
                bloq = str(r.get("BLOQ", "")).strip()
                key = f"{bloq}_{apto}" if bloq else apto
                email = r.get("EMAIL", "").strip() or r.get("CORREOS", "").strip()
                if key in directorio:
                    directorio[key]["email"] = email
                else:
                    directorio[key] = {
                        "propietario": r.get("NOM", "").strip(),
                        "inquilino": "",
                        "documento": "",
                        "coef_urb": 0.0,
                        "email": email
                    }
        except Exception as e:
            print(f"[!] Error leyendo BASENVIP.DBF: {e}")

    return directorio

# ==============================================================================
# MOTOR PRINCIPAL DE CONVERSIÓN Y LIQUIDACIÓN SSxxxx
# ==============================================================================
class ConversorLefacturamosDBPlus:
    def __init__(self, ruta_archivo_ss: str, ruta_base: str = "."):
        self.ruta_archivo = ruta_archivo_ss
        self.ruta_base = ruta_base
        
        # Deducir código del edificio del nombre de archivo (ej: SS7480.DBF -> 7480)
        basename = os.path.basename(ruta_archivo_ss)
        name_no_ext = os.path.splitext(basename)[0].upper()
        self.codigo_edificio = name_no_ext.replace("SS", "").strip()
        
        self.mapeo_campos = cargar_mapeo_campo_fac(os.path.join(ruta_base, "CAMPO_FAC.xlsx"))
        self.info_edificio = cargar_datos_edificio(self.codigo_edificio, ruta_base)
        self.directorio = cargar_directorio_propietarios(self.codigo_edificio, ruta_base)
        self.registros_procesados = []

    def cargar_datos_origen(self) -> List[Dict[str, Any]]:
        """Lee el archivo SSxxxx ya sea en formato DBF o Excel (.xlsx/.xls)"""
        ext = os.path.splitext(self.ruta_archivo)[1].lower()
        if ext == ".dbf":
            return leer_dbf_puro(self.ruta_archivo)
        elif ext in [".xlsx", ".xls"]:
            wb = openpyxl.load_workbook(self.ruta_archivo, data_only=True)
            ws = wb.active
            headers = [str(ws.cell(row=1, column=c).value or "").strip().upper() for c in range(1, ws.max_column + 1)]
            recs = []
            for r in range(2, ws.max_row + 1):
                rec = {}
                for c, h in enumerate(headers, start=1):
                    rec[h] = ws.cell(row=r, column=c).value
                recs.append(rec)
            return recs
        else:
            raise ValueError(f"Extensión no soportada: {ext}")

    def procesar(self) -> Dict[str, Any]:
        """Aplica las fórmulas exactas y estructura solicitadas por el usuario."""
        raw_recs = self.cargar_datos_origen()
        print(f"[*] Procesando {len(raw_recs)} unidades para el Edificio [{self.codigo_edificio}] - {self.info_edificio['nombre']}...")

        totales_edificio = {
            "PEND": 0.0, "INTP": 0.0, "OTROSP": 0.0, "EXTRAP": 0.0,
            "MULTAP": 0.0, "SERPUP": 0.0, "SERVIP": 0.0, "NDNCP": 0.0,
            "ACTUAL": 0.0, "INTA": 0.0, "OTROSA": 0.0, "EXTRAA": 0.0,
            "MULTAA": 0.0, "SERPUA": 0.0, "SERVIA": 0.0, "NDNCA": 0.0,
            "T_ADMON": 0.0, "T_INTERES": 0.0, "T_OTROS": 0.0, "T_EXTRA": 0.0,
            "T_MULTA": 0.0, "T_SER_PUB": 0.0, "T_SER_SERV": 0.0, "T_NOTAS_DC": 0.0,
            "TOTAL_PAGAR": 0.0, "COEF_TOTAL": 0.0
        }

        self.registros_procesados = []

        for r in raw_recs:
            apto = str(r.get("APTO", "")).strip()
            bloq = str(r.get("BLOQ", "")).strip()
            fac = r.get("FAC", 0)

            # 1. Saldos Pendientes
            pend = float(r.get("PEND", 0) or 0)
            intp = float(r.get("INTP", 0) or 0)
            otrosp = float(r.get("OTROSP", 0) or 0)
            extrap = float(r.get("EXTRAP", 0) or 0)
            multap = float(r.get("MULTAP", 0) or 0)
            serpup = float(r.get("SERPUP", 0) or 0)
            servip = float(r.get("SERVIP", 0) or 0)
            ndncp = float(r.get("NDNCP", 0) or 0)

            # 2. Cobro del Mes
            actual = float(r.get("ACTUAL", 0) or 0)
            inta = float(r.get("INTA", 0) or 0)
            otrosa = float(r.get("OTROSA", 0) or 0)
            extraa = float(r.get("EXTRAA", 0) or 0)
            multaa = float(r.get("MULTAA", 0) or 0)
            serpua = float(r.get("SERPUA", 0) or 0)
            servia = float(r.get("SERVIA", 0) or 0)
            ndnca = float(r.get("NDNCA", 0) or 0)

            # 3. Sumas concepto por concepto según CAMPO_FAC:
            t_admon = pend + actual
            t_interes = intp + inta
            t_otros = otrosp + otrosa
            t_extra = extrap + extraa
            t_multa = multap + multaa
            t_ser_pub = serpup + serpua
            t_ser_serv = servip + servia
            t_notas_dc = ndncp + ndnca

            total_fila = (
                t_admon + t_interes + t_otros + t_extra +
                t_multa + t_ser_pub + t_ser_serv + t_notas_dc
            )

            # Campos de sumaria SSxxxx: VALDESC y VALPAG
            valdesc = float(r.get("VALDESC", 0) or r.get("DESCUENTO", 0) or r.get("DESC", 0) or 0)
            valpag = float(r.get("VALPAG", 0) or (total_fila - valdesc))

            # Coeficientes
            coef_apa = float(r.get("COEF_APA", 0) or 0)
            coef_gar = float(r.get("COEF_GAR", 0) or 0)
            coef_util = float(r.get("COEF_UTIL", 0) or 0)
            coef_total = coef_apa + coef_gar + coef_util
            if coef_total == 0.0 and "COEF_URB" in r:
                coef_total = float(r.get("COEF_URB", 0) or 0)

            # Buscar propietario
            key_dir = f"{bloq}_{apto}" if bloq else apto
            dir_info = self.directorio.get(key_dir, {})
            propietario = dir_info.get("propietario", str(r.get("NOM", "")).strip())
            documento = dir_info.get("documento", str(r.get("CC_NIT", "")).strip())
            email = dir_info.get("email", "")

            # Acumular totales
            totales_edificio["PEND"] += pend
            totales_edificio["INTP"] += intp
            totales_edificio["OTROSP"] += otrosp
            totales_edificio["EXTRAP"] += extrap
            totales_edificio["MULTAP"] += multap
            totales_edificio["SERPUP"] += serpup
            totales_edificio["SERVIP"] += servip
            totales_edificio["NDNCP"] += ndncp

            totales_edificio["ACTUAL"] += actual
            totales_edificio["INTA"] += inta
            totales_edificio["OTROSA"] += otrosa
            totales_edificio["EXTRAA"] += extraa
            totales_edificio["MULTAA"] += multaa
            totales_edificio["SERPUA"] += serpua
            totales_edificio["SERVIA"] += servia
            totales_edificio["NDNCA"] += ndnca

            totales_edificio["T_ADMON"] += t_admon
            totales_edificio["T_INTERES"] += t_interes
            totales_edificio["T_OTROS"] += t_otros
            totales_edificio["T_EXTRA"] += t_extra
            totales_edificio["T_MULTA"] += t_multa
            totales_edificio["T_SER_PUB"] += t_ser_pub
            totales_edificio["T_SER_SERV"] += t_ser_serv
            totales_edificio["T_NOTAS_DC"] += t_notas_dc
            totales_edificio["TOTAL_PAGAR"] += total_fila
            totales_edificio["COEF_TOTAL"] += coef_total

            item = {
                "bloq": bloq,
                "apto": apto,
                "fac": fac,
                "propietario": propietario,
                "documento": documento,
                "email": email,
                "coeficiente": coef_total,
                "pendientes": {
                    "pend": pend, "intp": intp, "otrosp": otrosp, "extrap": extrap,
                    "multap": multap, "serpup": serpup, "servip": servip, "ndncp": ndncp
                },
                "cobro_mes": {
                    "actual": actual, "inta": inta, "otrosa": otrosa, "extraa": extraa,
                    "multaa": multaa, "serpua": serpua, "servia": servia, "ndnca": ndnca
                },
                "totales_concepto": {
                    "admon": t_admon,
                    "interes": t_interes,
                    "otros": t_otros,
                    "extra": t_extra,
                    "multa": t_multa,
                    "ser_pub": t_ser_pub,
                    "ser_serv": t_ser_serv,
                    "notas_d_c": t_notas_dc,
                    "valdesc": valdesc,
                    "valpag": valpag
                },
                "valdesc": valdesc,
                "valpag": valpag,
                "total_a_pagar": total_fila,
                "estado": "Al Día" if total_fila <= 0 or (pend == 0 and intp == 0) else "Pendiente"
            }
            self.registros_procesados.append(item)

        return {
            "edificio": self.info_edificio,
            "mapeo_columnas": self.mapeo_campos,
            "total_unidades": len(self.registros_procesados),
            "totales_generales": totales_edificio,
            "unidades": self.registros_procesados
        }

    def exportar_excel_oficial(self, ruta_salida: str):
        """Genera el libro Excel profesional con formato visual LEFACTURAMOS."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Facturacion_y_Cartera"

        # Encabezado Edificio
        ws.merge_cells("A1:W1")
        ws["A1"] = f"LEFACTURAMOS - {self.info_edificio['nombre'].upper()} (CÓDIGO: {self.codigo_edificio})"
        ws["A1"].font = Font(name="Segoe UI", size=13, bold=True, color="065F46")

        ws.merge_cells("A2:W2")
        periodo = self.info_edificio.get("mes_actual", "") or "PERÍODO ACTUAL"
        nit = self.info_edificio.get("nit", "")
        ws["A2"] = f"NIT: {nit} • Período: {periodo} • Cuenta: {self.info_edificio.get('banco', '')} {self.info_edificio.get('cuenta', '')}"
        ws["A2"].font = Font(name="Segoe UI", size=9, italic=True, color="475569")

        # Fila 4: Bloques de columnas
        ws.merge_cells("A4:E4")
        ws["A4"] = "DATOS INMUEBLE & PROPIETARIO"
        ws["A4"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        ws["A4"].font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        ws["A4"].alignment = Alignment(horizontal="center")

        ws.merge_cells("F4:M4")
        ws["F4"] = "SALDOS PENDIENTES (ANTERIORES)"
        ws["F4"].fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
        ws["F4"].font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        ws["F4"].alignment = Alignment(horizontal="center")

        ws.merge_cells("N4:U4")
        ws["N4"] = "COBRO DEL MES (ACTUAL)"
        ws["N4"].fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        ws["N4"].font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        ws["N4"].alignment = Alignment(horizontal="center")

        ws.merge_cells("V4:AC4")
        ws["V4"] = "TOTALES LIQUIDADOS (HOMOLOGADOS CON CAMPO_FAC)"
        ws["V4"].fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid")
        ws["V4"].font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        ws["V4"].alignment = Alignment(horizontal="center")

        ws.merge_cells("AD4:AE4")
        ws["AD4"] = "LIQUIDACIÓN FINAL"
        ws["AD4"].fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
        ws["AD4"].font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        ws["AD4"].alignment = Alignment(horizontal="center")

        # Fila 5: Nombres de columnas
        cols_def = [
            ("BLOQ", "Bloque"),
            ("APTO", "Apto"),
            ("PROPIETARIO", "Propietario"),
            ("CC_NIT", "Cédula / NIT"),
            ("FAC", "No. Fac"),
            # Pendientes
            ("PEND", "PEND"),
            ("INTP", "INTP"),
            ("OTROSP", "OTROSP"),
            ("EXTRAP", "EXTRAP"),
            ("MULTAP", "MULTAP"),
            ("SERPUP", "SERPUP"),
            ("SERVIP", "SERVIP"),
            ("NDNCP", "NDNCP"),
            # Actual
            ("ACTUAL", "ACTUAL"),
            ("INTA", "INTA"),
            ("OTROSA", "OTROSA"),
            ("EXTRAA", "EXTRAA"),
            ("MULTAA", "MULTAA"),
            ("SERPUA", "SERPUA"),
            ("SERVIA", "SERVIA"),
            ("NDNCA", "NDNCA"),
            # Totales homologados CAMPO_FAC
            ("T_ADMON", self.mapeo_campos["admon"]),
            ("T_INTERES", self.mapeo_campos["interes"]),
            ("T_OTROS", self.mapeo_campos["otros"]),
            ("T_EXTRA", self.mapeo_campos["extra"]),
            ("T_MULTA", self.mapeo_campos["multa"]),
            ("T_SER_PUB", self.mapeo_campos["ser_pub"]),
            ("T_SER_SERV", self.mapeo_campos["ser_serv"]),
            ("T_NOTAS_DC", self.mapeo_campos["notas_d_c"]),
            # Finales
            ("TOTAL_PAGAR", "TOTAL A PAGAR"),
            ("ESTADO", "Estado")
        ]

        for c_idx, (c_id, c_title) in enumerate(cols_def, start=1):
            cell = ws.cell(row=5, column=c_idx, value=c_title)
            cell.font = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if c_idx <= 5:
                cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
            elif c_idx <= 13:
                cell.fill = PatternFill(start_color="B91C1C", end_color="B91C1C", fill_type="solid")
            elif c_idx <= 21:
                cell.fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
            elif c_idx <= 29:
                cell.fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
            else:
                cell.fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")

        # Filas de Datos
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        row_start = 6
        for idx, u in enumerate(self.registros_procesados):
            r_idx = row_start + idx
            p = u["pendientes"]
            m = u["cobro_mes"]
            t = u["totales_concepto"]

            fila_valores = [
                u["bloq"], u["apto"], u["propietario"], u["documento"], u["fac"],
                p["pend"], p["intp"], p["otrosp"], p["extrap"], p["multap"], p["serpup"], p["servip"], p["ndncp"],
                m["actual"], m["inta"], m["otrosa"], m["extraa"], m["multaa"], m["serpua"], m["servia"], m["ndnca"],
                t["admon"], t["interes"], t["otros"], t["extra"], t["multa"], t["ser_pub"], t["ser_serv"], t["notas_d_c"],
                u["total_a_pagar"], u["estado"]
            ]

            for c_idx, val in enumerate(fila_valores, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = Font(name="Segoe UI", size=9)
                cell.border = thin_border
                if c_idx in [1, 2, 4, 5, 31]:
                    cell.alignment = Alignment(horizontal="center")
                elif c_idx == 3:
                    cell.alignment = Alignment(horizontal="left")
                else:
                    cell.number_format = '"$"#,##0'
                    cell.alignment = Alignment(horizontal="right")

        # Fila de Totales Generales
        total_row = row_start + len(self.registros_procesados)
        ws.cell(row=total_row, column=1, value="TOTAL GENERAL DEL EDIFICIO").font = Font(name="Segoe UI", size=10, bold=True, color="065F46")
        ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=5)

        total_border = Border(
            top=Side(style='thin', color='065F46'),
            bottom=Side(style='double', color='065F46')
        )

        for c_idx in range(6, 31):
            col_let = get_column_letter(c_idx)
            cell = ws.cell(row=total_row, column=c_idx, value=f"=SUM({col_let}{row_start}:{col_let}{total_row - 1})")
            cell.font = Font(name="Segoe UI", size=10, bold=True, color="065F46")
            cell.border = total_border
            cell.number_format = '"$"#,##0'
            cell.alignment = Alignment(horizontal="right")

        # Hoja 2: Directorio de Propietarios y Residentes
        ws_prop = wb.create_sheet(title="Directorio_Copropietarios")
        ws_prop.append(["Bloque", "Apto", "Propietario", "Cédula / NIT", "Correo Electrónico", "Coeficiente (%)", "Estado Cartera"])
        for c in range(1, 8):
            cell = ws_prop.cell(row=1, column=c)
            cell.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        for u in self.registros_procesados:
            ws_prop.append([
                u["bloq"], u["apto"], u["propietario"], u["documento"],
                u["email"] or "Pendiente de registro", u["coeficiente"], u["estado"]
            ])

        # Ajuste de anchos en ambas hojas (iniciando en fila 5 para evitar que títulos combinados A1:W1 ensanchen la Columna A)
        for sheet in [ws, ws_prop]:
            for col in range(1, sheet.max_column + 1):
                col_letter = get_column_letter(col)
                max_len = 0
                for row in range(5, min(sheet.max_row + 1, 150)):
                    val = sheet.cell(row=row, column=col).value
                    if val is not None:
                        max_len = max(max_len, len(str(val)))
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 11)

        # Ajustes de ancho estéticos y proporcionados para las columnas principales
        ws.column_dimensions["A"].width = 8   # Bloque (no se ensancha por el título)
        ws.column_dimensions["B"].width = 9   # Apto
        ws.column_dimensions["C"].width = 28  # Propietario
        ws.column_dimensions["D"].width = 14  # Cédula / NIT
        ws.column_dimensions["E"].width = 10  # No. Factura

        ws_prop.column_dimensions["A"].width = 8
        ws_prop.column_dimensions["B"].width = 9
        ws_prop.column_dimensions["C"].width = 28

        try:
            wb.save(ruta_salida)
        except PermissionError:
            import time
            from pathlib import Path
            ts = int(time.time()) % 100000
            p = Path(ruta_salida)
            ruta_salida = str(p.parent / f"{p.stem}_{ts}{p.suffix}")
            wb.save(ruta_salida)

        print(f"[ÉXITO] Archivo Excel oficial guardado en: {ruta_salida}")

    def exportar_json(self, ruta_salida: str):
        """Exporta los datos estructurados en JSON para la Web App y Apps Móviles."""
        data = {
            "version": VERSION,
            "edificio": self.info_edificio,
            "columnas_homologadas": self.mapeo_campos,
            "total_unidades": len(self.registros_procesados),
            "unidades": self.registros_procesados
        }
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[ÉXITO] Archivo JSON de integración guardado en: {ruta_salida}")

# ==============================================================================
# FUNCIÓN PRINCIPAL CLI / INTERACTIVA
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="LEFACTURAMOS - Conversor Maestro DBPlus / SSxxxx")
    parser.add_argument("--archivo", "-a", type=str, help="Ruta del archivo SSxxxx.DBF o SSxxxx.xlsx")
    parser.add_argument("--edificio", "-e", type=str, help="Código del edificio (ej: 7480)")
    parser.add_argument("--auto", action="store_true", help="Convierte automáticamente todos los archivos SS*.DBF encontrados")

    args = parser.parse_args()

    print("=" * 75)
    print(f" LEFACTURAMOS - Conversor Maestro de Bases de Datos (Python v{VERSION})")
    print(" Formato oficial: SSxxxx + CAMPO_FAC -> Plataforma Web y Apps Android/iOS")
    print("=" * 75)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    archivos_a_procesar = []

    if args.auto:
        archivos_a_procesar = sorted(list(set(glob.glob(os.path.join(base_dir, "SS*.DBF")) + glob.glob(os.path.join(base_dir, "SS*.dbf")))))
        print(f"[*] Modo Automatico: Detectados {len(archivos_a_procesar)} archivos contables SSxxxx.")
    elif args.archivo:
        archivos_a_procesar = [args.archivo]
    else:
        # Buscar archivos por defecto
        candidatos = sorted(list(set(glob.glob(os.path.join(base_dir, "SS*.DBF")) + glob.glob(os.path.join(base_dir, "SS*.dbf")))))
        if candidatos:
            print("\nArchivos contables encontrados en el directorio:")
            for idx, c in enumerate(candidatos, start=1):
                print(f"  {idx}. {os.path.basename(c)}")
            print(f"  {len(candidatos) + 1}. Ingresar otra ruta de archivo manualmente")
            
            sel = input(f"\nSeleccione una opcion (1-{len(candidatos) + 1}) [Enter = Todos]: ").strip()
            if not sel:
                archivos_a_procesar = candidatos
            else:
                try:
                    num = int(sel)
                    if 1 <= num <= len(candidatos):
                        archivos_a_procesar = [candidatos[num - 1]]
                    else:
                        manual = input("Ingrese la ruta del archivo (.DBF o .xlsx): ").strip().strip('"')
                        archivos_a_procesar = [manual]
                except:
                    archivos_a_procesar = candidatos
        else:
            manual = input("Ingrese la ruta del archivo SSxxxx (.DBF o .xlsx): ").strip().strip('"')
            archivos_a_procesar = [manual]

    if not archivos_a_procesar:
        print("[-] No se encontraron archivos para procesar.")
        return

    for archivo in archivos_a_procesar:
        if not os.path.exists(archivo):
            print(f"[-] Archivo no existe: {archivo}")
            continue

        print("\n" + "-" * 75)
        print(f"[*] Iniciando conversion de: {os.path.basename(archivo)}")
        conversor = ConversorLefacturamosDBPlus(archivo, base_dir)
        datos = conversor.procesar()

        cod = conversor.codigo_edificio
        mes_slug = (conversor.info_edificio.get("mes_actual") or "ACTUAL").replace(" ", "_").replace(".", "")
        
        salida_excel = os.path.join(base_dir, f"LEFACTURAMOS_CONVERTIDO_{cod}_{mes_slug}.xlsx")
        salida_json = os.path.join(base_dir, f"LEFACTURAMOS_CONVERTIDO_{cod}_{mes_slug}.json")

        conversor.exportar_excel_oficial(salida_excel)
        conversor.exportar_json(salida_json)

        print(f"[OK] Edificio {conversor.info_edificio['nombre']} liquidado con exito:")
        print(f"     Total Unidades: {datos['total_unidades']}")
        print(f"     Total Cartera Pendiente: ${datos['totales_generales']['PEND']:,.0f}")
        print(f"     Total Cobro del Mes:     ${datos['totales_generales']['ACTUAL']:,.0f}")
        print(f"     Total a Pagar Conjunto:  ${datos['totales_generales']['TOTAL_PAGAR']:,.0f}")

    print("\n" + "=" * 75)
    print("[EXITO] Proceso completado. Archivos listos para alimentar LEFACTURAMOS.")
    print("=" * 75)

if __name__ == "__main__":
    main()
