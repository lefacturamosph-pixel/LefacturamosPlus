# -*- coding: utf-8 -*-
"""
build_mm_ss_and_excel.py
Generador oficial de tablas DBF (MMxxxx.DBF y SSxxxx.DBF) y libros Excel (.xlsx)
para EDIFICIO ALCALÁ (0955) y EDIFICIO LA FORTALEZA (0950)
a partir de los documentos PDF de cuentas de cobro de Noviembre 2026.
"""

import os
import struct
import datetime
import shutil
import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# ESQUEMAS BINARIOS OFICIALES FOXPRO / CLIPPER PARA DBF
# ==============================================================================

# Esquema para Maestro de Inmuebles MMxxxx.DBF (47 campos)
SCHEMA_MM = [
    ('CODIGO', 'C', 4, 0), ('COD', 'C', 2, 0), ('BLOQ', 'C', 2, 0), ('APTO', 'C', 4, 0),
    ('CLAVE', 'C', 8, 0), ('CODIGO1', 'C', 4, 0), ('UBICA', 'C', 50, 0), ('NOMURB', 'C', 45, 0),
    ('BEP_CEL', 'C', 17, 0), ('TEL', 'N', 12, 0), ('CODPROP', 'C', 8, 0), ('NOM', 'C', 30, 0),
    ('NOMINQ', 'C', 30, 0), ('DIREC', 'C', 70, 0), ('ACTUAL', 'N', 11, 0), ('MORA', 'N', 8, 4),
    ('ADM_APTO', 'N', 11, 0), ('ADM_PQ_UT', 'N', 11, 0), ('COEF_URB', 'N', 9, 6),
    ('COEF_MOD_A', 'N', 9, 6), ('COEF_MOD_B', 'N', 9, 6), ('COEF_APA', 'N', 9, 6),
    ('COEF_LIBRE', 'N', 9, 6), ('COEF_GAR', 'N', 9, 6), ('COEF_GAR1', 'N', 9, 6),
    ('COEF_UTIL', 'N', 9, 6), ('COEF_PQUT', 'N', 9, 6), ('ARAPA', 'N', 6, 2),
    ('ARTERR', 'N', 6, 2), ('ARGAR', 'N', 6, 2), ('ARUTIL', 'N', 6, 2), ('ARLIBRE', 'N', 6, 2),
    ('ARTOTAL', 'N', 6, 2), ('OTROSA', 'N', 11, 0), ('OTROSVAL', 'N', 11, 0),
    ('CC_NIT', 'C', 12, 0), ('TEL_OFIC', 'N', 9, 0), ('FAC', 'N', 6, 0), ('VALOR', 'N', 11, 0),
    ('IDENT', 'C', 1, 0), ('EMAIL', 'C', 60, 0), ('EMAIL1', 'C', 60, 0), ('EMAIL2', 'C', 60, 0),
    ('EMAIL3', 'C', 60, 0), ('INTERES', 'C', 8, 0), ('REFER', 'C', 8, 0), ('TIPO', 'C', 4, 0)
]

# Esquema para Saldos y Facturación SSxxxx.DBF (57 campos)
SCHEMA_SS = [
    ('CODIGO', 'C', 4, 0), ('COD', 'C', 2, 0), ('BLOQ', 'C', 2, 0), ('APTO', 'C', 4, 0),
    ('CLAVE', 'C', 8, 0), ('CODIGO1', 'C', 4, 0), ('CODPROP', 'C', 8, 0), ('FAC', 'N', 6, 0),
    ('C_V', 'N', 4, 0), ('PEND', 'N', 11, 0), ('INTP', 'N', 11, 0), ('OTROSP', 'N', 11, 0),
    ('EXTRAP', 'N', 11, 0), ('MULTAP', 'N', 11, 0), ('SERPUP', 'N', 11, 0), ('SERVIP', 'N', 11, 0),
    ('NDNCP', 'N', 11, 0), ('ACTUAL', 'N', 11, 0), ('INTA', 'N', 11, 0), ('OTROSA', 'N', 11, 0),
    ('EXTRAA', 'N', 11, 0), ('MULTAA', 'N', 11, 0), ('SERPUA', 'N', 11, 0), ('SERVIA', 'N', 11, 0),
    ('NDNCA', 'N', 11, 0), ('TADMI', 'N', 11, 0), ('TINTE', 'N', 11, 0), ('TOTRO', 'N', 11, 0),
    ('TEXTR', 'N', 11, 0), ('TMULT', 'N', 11, 0), ('TSERP', 'N', 11, 0), ('TSERVI', 'N', 11, 0),
    ('TNDNC', 'N', 11, 0), ('COEF_URB', 'N', 11, 6), ('COEF_APA', 'N', 11, 6), ('COEF_GAR', 'N', 11, 6),
    ('COEF_GAR1', 'N', 11, 6), ('COEF_UTIL', 'N', 11, 6), ('COEF_MOD_A', 'N', 11, 6),
    ('COEF_PQUT', 'N', 11, 6), ('COEF_MOD_B', 'N', 11, 6), ('LECTANT', 'N', 10, 3),
    ('LECTACT', 'N', 10, 3), ('CONSUMO', 'N', 12, 0), ('COSTO', 'N', 11, 0), ('TOTAL', 'N', 11, 0),
    ('VALDESC', 'N', 11, 0), ('VALPAG', 'N', 11, 0), ('VALOR', 'N', 11, 0), ('EXTR', 'N', 11, 0),
    ('MULT', 'N', 11, 0), ('SPP', 'N', 11, 0), ('OTR', 'N', 11, 0), ('SER', 'N', 11, 0),
    ('NDNC', 'N', 11, 0), ('INT', 'N', 11, 0), ('IDENT', 'C', 1, 0)
]

def write_dbf(filepath, fields, records):
    """
    Escribe físicamente un archivo binario dBase III (.DBF) 100% compatible
    con FoxPro, Clipper y el sistema DBPlus.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    now = datetime.datetime.now()
    yy = now.year - 2000 if now.year >= 2000 else now.year - 1900
    mm, dd = now.month, now.day
    num_records = len(records)
    header_len = 32 + len(fields) * 32 + 1
    record_len = 1 + sum(f[2] for f in fields)

    with open(filepath, 'wb') as f:
        # Cabecera principal (32 bytes)
        f.write(struct.pack('<BBBBIHH20s', 0x03, yy, mm, dd, num_records, header_len, record_len, b'\x00' * 20))
        # Descriptores de campos (32 bytes cada uno)
        for name, ftype, flen, fdec in fields:
            name_bytes = name.encode('ascii')[:10].ljust(11, b'\x00')
            type_byte = ftype.encode('ascii')
            f.write(struct.pack('<11sc4sBB14s', name_bytes, type_byte, b'\x00' * 4, flen, fdec, b'\x00' * 14))
        # Terminador de cabecera
        f.write(b'\x0D')
        # Registros de datos
        for r in records:
            f.write(b' ')  # 0x20: Registro activo (no eliminado)
            for name, ftype, flen, fdec in fields:
                val = r.get(name, '')
                if ftype == 'N':
                    if val is None or val == '':
                        s = '0'
                    elif isinstance(val, (int, float)):
                        if fdec > 0:
                            s = f"{val:.{fdec}f}"
                        else:
                            s = str(int(round(val)))
                    else:
                        s = str(val).strip()
                    val_bytes = s.rjust(flen)[:flen].encode('latin1')
                else:
                    s = str(val) if val is not None else ''
                    val_bytes = s.encode('latin1', errors='replace').ljust(flen)[:flen]
                f.write(val_bytes)
        # Terminador de fin de archivo EOF
        f.write(b'\x1A')


# ==============================================================================
# INMUEBLES EXTRAÍDOS DE EDIFICIO ALCALÁ (0955) - 15 Unidades
# ==============================================================================
UNIDADES_ALCALA = [
    { 'bloq': '01', 'apto': '0101', 'nom': 'Bayron Antonio Jimenez', 'cc': '71114686', 'pago_ant': 208000, 'pend': -23, 'actual': 208000, 'total': 207977, 'fac': 19, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0201', 'nom': 'Yessica Arbelaez Jimenez', 'cc': '', 'pago_ant': 0, 'pend': 216000, 'actual': 216000, 'total': 432000, 'fac': 20, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0202', 'nom': 'Yessica Arbelaez Jimenez', 'cc': '1036393647', 'pago_ant': 0, 'pend': 172000, 'actual': 172000, 'total': 344000, 'fac': 21, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0203', 'nom': 'Jhon Dario Ochoa', 'cc': '70753981', 'pago_ant': 163000, 'pend': -500, 'actual': 163000, 'total': 162500, 'fac': 22, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0301', 'nom': 'Sandro de Jesus Idarraga', 'cc': '21627790', 'pago_ant': 218000, 'pend': 1000, 'actual': 219000, 'total': 220000, 'fac': 23, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0302', 'nom': 'Adriana Maria Soto Osorio', 'cc': '43712847', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 24, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0303', 'nom': 'Luis Fernado Arias Zuluaga', 'cc': '71110737', 'pago_ant': 0, 'pend': 156659, 'actual': 157000, 'total': 313659, 'fac': 25, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0401', 'nom': 'Paula Andrea Trujillo Pineda', 'cc': '21628443', 'pago_ant': 176000, 'pend': 0, 'actual': 176000, 'total': 176000, 'fac': 26, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0402', 'nom': 'Deisy Yuliana Giraldo Lopez', 'cc': '1036394808', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 27, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0403', 'nom': 'Conrrado Antonio Castañeda C.', 'cc': '70879169', 'pago_ant': 273000, 'pend': -159, 'actual': 273000, 'total': 272841, 'fac': 28, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0501', 'nom': 'Paola Andrea Orozco', 'cc': '43160064', 'pago_ant': 392000, 'pend': -359, 'actual': 221000, 'total': 220641, 'fac': 29, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0502', 'nom': 'Patricia del Carmen Ochoa Z.', 'cc': '43423107', 'pago_ant': 139000, 'pend': 0, 'actual': 139000, 'total': 139000, 'fac': 30, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': 'LC01', 'nom': 'Inmobiliaria Nivel 5 S.A.S', 'cc': '900325481', 'pago_ant': 0, 'pend': -294001, 'actual': 147000, 'total': -147001, 'fac': 31, 'tipo': 'LOCA' },
    { 'bloq': '01', 'apto': 'PQM1', 'nom': 'Daniela (Arrendatario)', 'cc': '', 'pago_ant': 99652, 'pend': 0, 'actual': 48326, 'total': 48326, 'fac': 32, 'tipo': 'PARQ' },
    { 'bloq': '01', 'apto': 'PQ01', 'nom': 'Javier Garcia (Arrendatario)', 'cc': '', 'pago_ant': 133000, 'pend': -1375, 'actual': 132828, 'total': 131453, 'fac': 33, 'tipo': 'PARQ' }
]

# ==============================================================================
# INMUEBLES EXTRAÍDOS DE EDIFICIO LA FORTALEZA (0950) - 16 Unidades
# ==============================================================================
UNIDADES_FORTALEZA = [
    { 'bloq': '01', 'apto': '0101', 'nom': 'Maria Eugenia Suarez Isaza', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 290, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0102', 'nom': 'Margarita Maria Builes Gil', 'cc': '', 'pago_ant': 0, 'pend': 0, 'actual': 183000, 'total': 183000, 'fac': 291, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0103', 'nom': 'Natalia Marcela Rojas', 'cc': '', 'pago_ant': 301000, 'pend': 0, 'actual': 301000, 'total': 301000, 'fac': 292, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0104', 'nom': 'Flor Cifuentes R.', 'cc': '', 'pago_ant': 137000, 'pend': -137000, 'actual': 137000, 'total': 0, 'fac': 293, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0201', 'nom': 'Martha Estella Lopez', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 294, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0202', 'nom': 'German Antonio Giraldo M', 'cc': '', 'pago_ant': 0, 'pend': -264000, 'actual': 132000, 'total': -132000, 'fac': 295, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0203', 'nom': 'David Tobon Orozco', 'cc': '', 'pago_ant': 256000, 'pend': 0, 'actual': 256000, 'total': 256000, 'fac': 296, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0204', 'nom': 'Maria Nelly Gonzalez', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 297, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0301', 'nom': 'Piedad Zuleta', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 298, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0302', 'nom': 'Manuel Jimenez Mejia', 'cc': '', 'pago_ant': 264000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 299, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0303', 'nom': 'Maria Cristina Henao', 'cc': '', 'pago_ant': 256000, 'pend': 256000, 'actual': 256000, 'total': 512000, 'fac': 300, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0304', 'nom': 'Teresita Gomez', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 301, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0401', 'nom': 'Karolina Gomez', 'cc': '', 'pago_ant': 132000, 'pend': 0, 'actual': 132000, 'total': 132000, 'fac': 302, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0402', 'nom': 'Jorge A. Lopez', 'cc': '', 'pago_ant': 0, 'pend': 264000, 'actual': 132000, 'total': 396000, 'fac': 303, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0403', 'nom': 'Luz Marina Romero M.', 'cc': '', 'pago_ant': 512000, 'pend': 0, 'actual': 256000, 'total': 256000, 'fac': 304, 'tipo': 'APTO' },
    { 'bloq': '01', 'apto': '0404', 'nom': 'Luz Amparo Botero', 'cc': '', 'pago_ant': 396000, 'pend': -396800, 'actual': 132000, 'total': -264800, 'fac': 305, 'tipo': 'APTO' }
]

def generar_dbf_edificio(codigo, cod_dos, nombre_urb, unidades, out_dir):
    records_mm = []
    records_ss = []

    for u in unidades:
        bloq = u['bloq']
        apto = u['apto']
        clave = f"{cod_dos}{bloq}{apto}"
        nom = u['nom'][:30]
        fac = u['fac']
        actual = u['actual']
        pend = u['pend']
        pago_ant = u['pago_ant']
        tot = u['total']
        cc = u.get('cc', '')[:12]
        tipo = u.get('tipo', 'APTO')

        # Registro MMxxxx.DBF
        r_mm = {
            'CODIGO': codigo, 'COD': cod_dos, 'BLOQ': bloq, 'APTO': apto,
            'CLAVE': clave, 'CODIGO1': '', 'UBICA': '', 'NOMURB': nombre_urb[:45],
            'BEP_CEL': '', 'TEL': 0, 'CODPROP': '', 'NOM': nom, 'NOMINQ': '',
            'DIREC': '', 'ACTUAL': actual, 'MORA': 2.1010, 'ADM_APTO': 0, 'ADM_PQ_UT': 0,
            'COEF_URB': 0.0, 'COEF_MOD_A': 0.0, 'COEF_MOD_B': 0.0, 'COEF_APA': 0.0,
            'COEF_LIBRE': 0.0, 'COEF_GAR': 0.0, 'COEF_GAR1': 0.0, 'COEF_UTIL': 0.0,
            'COEF_PQUT': 0.0, 'ARAPA': 0.0, 'ARTERR': 0.0, 'ARGAR': 0.0, 'ARUTIL': 0.0,
            'ARLIBRE': 0.0, 'ARTOTAL': 0.0, 'OTROSA': 0, 'OTROSVAL': 0,
            'CC_NIT': cc, 'TEL_OFIC': 0, 'FAC': fac, 'VALOR': 1, 'IDENT': '',
            'EMAIL': '', 'EMAIL1': '', 'EMAIL2': '', 'EMAIL3': '',
            'INTERES': '2.101', 'REFER': '', 'TIPO': tipo
        }
        records_mm.append(r_mm)

        # Registro SSxxxx.DBF
        r_ss = {
            'CODIGO': codigo, 'COD': cod_dos, 'BLOQ': bloq, 'APTO': apto,
            'CLAVE': clave, 'CODIGO1': '', 'CODPROP': '', 'FAC': fac, 'C_V': 0,
            'PEND': pend, 'INTP': 0, 'OTROSP': 0, 'EXTRAP': 0, 'MULTAP': 0,
            'SERPUP': 0, 'SERVIP': 0, 'NDNCP': 0, 'ACTUAL': actual, 'INTA': 0,
            'OTROSA': 0, 'EXTRAA': 0, 'MULTAA': 0, 'SERPUA': 0, 'SERVIA': 0,
            'NDNCA': 0, 'TADMI': actual + pend, 'TINTE': 0, 'TOTRO': 0,
            'TEXTR': 0, 'TMULT': 0, 'TSERP': 0, 'TSERVI': 0, 'TNDNC': 0,
            'COEF_URB': 0.0, 'COEF_APA': 0.0, 'COEF_GAR': 0.0, 'COEF_GAR1': 0.0,
            'COEF_UTIL': 0.0, 'COEF_MOD_A': 0.0, 'COEF_PQUT': 0.0, 'COEF_MOD_B': 0.0,
            'LECTANT': 0.0, 'LECTACT': 0.0, 'CONSUMO': 0, 'COSTO': 0,
            'TOTAL': tot, 'VALDESC': 0, 'VALPAG': pago_ant, 'VALOR': tot,
            'EXTR': 0, 'MULT': 0, 'SPP': 0, 'OTR': 0, 'SER': 0, 'NDNC': 0,
            'INT': 0, 'IDENT': ''
        }
        records_ss.append(r_ss)

    mm_path = os.path.join(out_dir, f"MM{codigo}.DBF")
    ss_path = os.path.join(out_dir, f"SS{codigo}.DBF")
    write_dbf(mm_path, SCHEMA_MM, records_mm)
    write_dbf(ss_path, SCHEMA_SS, records_ss)
    print(f"Creados exitosamente: {mm_path} y {ss_path}")


# ==============================================================================
# GENERADOR DE LIBROS EXCEL (.XLSX) PROFESIONALES
# ==============================================================================
def generar_excel_edificio(codigo, nombre_edif, nit, direccion, cuenta, periodo, vencimiento, unidades, destino_xlsx):
    wb = openpyxl.Workbook()

    # -------------------------------------------------------------
    # Hoja 1: BASE DE FACTURACION
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Base_Facturacion"

    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_tot = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")

    font_title = Font(name="Arial", size=13, bold=True, color="1E3A8A")
    font_sub = Font(name="Arial", size=9.5, bold=False, color="475569")
    font_h = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    font_data = Font(name="Arial", size=8.5, bold=False, color="000000")
    font_data_bold = Font(name="Arial", size=8.5, bold=True, color="000000")
    font_tot = Font(name="Arial", size=9.5, bold=True, color="065F46")

    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    border_total = Border(
        top=Side(style='thin', color='000000'),
        bottom=Side(style='double', color='000000')
    )

    # Encabezado Copropiedad
    ws1.cell(1, 1, f"{nombre_edif.upper()} -- FACTURACIÓN MENSUAL").font = font_title
    ws1.cell(2, 1, f"NIT: {nit} • Dirección: {direccion} • Código DBPlus: {codigo}").font = font_sub
    ws1.cell(3, 1, f"Periodo de Facturación: {periodo} • Fecha Límite de Pago: {vencimiento} • Cuenta: {cuenta}").font = font_sub

    headers = [
        "Bloque", "Apto / Unidad", "Nº Factura", "Tipo", "Nombre Copropietario / Residente",
        "Cédula / NIT", "Pago Anterior", "Admin. Pendiente", "Admin. Mes Actual",
        "Interés Mora", "Otros Cobros", "Cuota Extra", "Reingreso Gasto",
        "Valor Bruto", "Descuento", "TOTAL A PAGAR"
    ]

    row_idx = 5
    for c_idx, h in enumerate(headers, 1):
        cell = ws1.cell(row_idx, c_idx, h)
        cell.font = font_h
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center" if c_idx <= 4 else ("right" if c_idx >= 7 else "left"), vertical="center", wrap_text=True)

    ws1.row_dimensions[5].height = 25

    start_row = 6
    curr_row = 6

    for u in unidades:
        ws1.row_dimensions[curr_row].height = 19
        ws1.cell(curr_row, 1, u['bloq']).font = font_data
        ws1.cell(curr_row, 1).alignment = Alignment(horizontal="center")
        ws1.cell(curr_row, 1).border = border_thin

        ws1.cell(curr_row, 2, u['apto']).font = font_data_bold
        ws1.cell(curr_row, 2).alignment = Alignment(horizontal="center")
        ws1.cell(curr_row, 2).border = border_thin

        ws1.cell(curr_row, 3, u['fac']).font = font_data
        ws1.cell(curr_row, 3).alignment = Alignment(horizontal="center")
        ws1.cell(curr_row, 3).border = border_thin

        ws1.cell(curr_row, 4, u.get('tipo', 'APTO')).font = font_data
        ws1.cell(curr_row, 4).alignment = Alignment(horizontal="center")
        ws1.cell(curr_row, 4).border = border_thin

        ws1.cell(curr_row, 5, u['nom']).font = font_data_bold
        ws1.cell(curr_row, 5).border = border_thin

        ws1.cell(curr_row, 6, u.get('cc', '')).font = font_data
        ws1.cell(curr_row, 6).alignment = Alignment(horizontal="center")
        ws1.cell(curr_row, 6).border = border_thin

        # Valores numéricos con formato de moneda
        cols_val = [
            (7, u['pago_ant']),
            (8, u['pend']),
            (9, u['actual']),
            (10, 0),
            (11, 0),
            (12, 0),
            (13, 0),
            (14, f"=H{curr_row}+I{curr_row}+J{curr_row}+K{curr_row}+L{curr_row}+M{curr_row}"),
            (15, 0),
            (16, f"=N{curr_row}-O{curr_row}")
        ]

        for c_idx, val in cols_val:
            cell = ws1.cell(curr_row, c_idx, val)
            cell.font = font_data_bold if c_idx in [8, 9, 14, 16] else font_data
            cell.alignment = Alignment(horizontal="right")
            cell.border = border_thin
            cell.number_format = "$ #,##0;($ #,##0);$ 0"

        curr_row += 1

    end_row = curr_row - 1

    # Fila de Totales Sumados
    ws1.row_dimensions[curr_row].height = 22
    ws1.cell(curr_row, 5, "TOTALES DE FACTURACIÓN:").font = font_tot
    ws1.cell(curr_row, 5).alignment = Alignment(horizontal="right")
    ws1.cell(curr_row, 5).border = border_total

    for c_idx in range(7, 17):
        col_let = get_column_letter(c_idx)
        cell = ws1.cell(curr_row, c_idx, f"=SUM({col_let}{start_row}:{col_let}{end_row})")
        cell.font = font_tot
        cell.fill = fill_tot
        cell.alignment = Alignment(horizontal="right")
        cell.border = border_total
        cell.number_format = "$ #,##0;($ #,##0);$ 0"

    # Auto-ajustar anchos
    for col in ws1.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            v_str = str(cell.value or '')
            if len(v_str) > max_len: max_len = len(v_str)
        ws1.column_dimensions[col_letter].width = max(max_len + 3, 12)

    ws1.column_dimensions['E'].width = 32
    ws1.column_dimensions['A'].width = 8
    ws1.column_dimensions['B'].width = 14
    ws1.column_dimensions['C'].width = 12
    ws1.column_dimensions['D'].width = 8

    # -------------------------------------------------------------
    # Hoja 2: METADATOS Y CONTROL COPROPIEDAD
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Datos_Copropiedad")
    ws2.cell(1, 1, "FICHA TÉCNICA Y RESUMEN CONTABLE").font = font_title

    meta_rows = [
        ("Código Copropiedad (DBPlus)", codigo),
        ("Nombre de la Copropiedad", nombre_edif),
        ("Número de Identificación Tributaria (NIT)", nit),
        ("Dirección Oficial", direccion),
        ("Entidad Bancaria y Cuenta", cuenta),
        ("Periodo Facturado", periodo),
        ("Fecha Límite / Vencimiento", vencimiento),
        ("Total Unidades / Inmuebles", len(unidades)),
        ("Total Cuota Actual del Mes", f"=SUM(Base_Facturacion!I{start_row}:I{end_row})"),
        ("Total Cartera Pendiente del Mes", f"=SUM(Base_Facturacion!H{start_row}:H{end_row})"),
        ("Total General a Pagar / Recaudar", f"=SUM(Base_Facturacion!P{start_row}:P{end_row})")
    ]

    for r_i, (k, v) in enumerate(meta_rows, 3):
        c_k = ws2.cell(r_i, 1, k)
        c_k.font = font_data_bold
        c_k.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        c_k.border = border_thin

        c_v = ws2.cell(r_i, 2, v)
        c_v.font = font_data_bold if r_i >= 11 else font_data
        c_v.border = border_thin
        if r_i >= 11:
            c_v.number_format = "$ #,##0;($ #,##0);$ 0"
            c_v.fill = fill_tot

    ws2.column_dimensions['A'].width = 38
    ws2.column_dimensions['B'].width = 45

    wb.save(destino_xlsx)
    print(f"Excel generado exitosamente: {destino_xlsx}")


# ==============================================================================
# EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("==================================================================")
    print("1. PROCESANDO EDIFICIO ALCALÁ (CÓDIGO 0955)")
    print("==================================================================")
    dir_0955 = r"C:\dbplus\0955"
    generar_dbf_edificio('0955', '55', 'EDIFICIO ALCALÁ', UNIDADES_ALCALA, dir_0955)

    xlsx_0955 = os.path.join(dir_0955, "EDIFICIO_ALCALA_0955_NOVIEMBRE_2026.xlsx")
    generar_excel_edificio(
        '0955', 'EDIFICIO ALCALÁ', '901575286-5', 'Cra 30 23-68 70-72',
        'Bancolombia Ahorros N° 556-000016-31', 'Noviembre 2026', '28/11/2026',
        UNIDADES_ALCALA, xlsx_0955
    )

    print("\n==================================================================")
    print("2. PROCESANDO EDIFICIO LA FORTALEZA (CÓDIGO 0950)")
    print("==================================================================")
    dir_0950 = r"C:\dbplus\0950"
    # Backup previas de 0950 si existen
    if os.path.exists(os.path.join(dir_0950, "MM0950.DBF")):
        shutil.copy2(os.path.join(dir_0950, "MM0950.DBF"), os.path.join(dir_0950, "MM0950_OLD_2022.DBF"))
    if os.path.exists(os.path.join(dir_0950, "SS0950.DBF")):
        shutil.copy2(os.path.join(dir_0950, "SS0950.DBF"), os.path.join(dir_0950, "SS0950_OLD_2022.DBF"))

    generar_dbf_edificio('0950', '50', 'Edificio La Fortaleza P.H.', UNIDADES_FORTALEZA, dir_0950)

    xlsx_0950 = os.path.join(dir_0950, "EDIFICIO_LA_FORTALEZA_0950_NOVIEMBRE_2026.xlsx")
    generar_excel_edificio(
        '0950', 'ED. LA FORTALEZA', '900428879', 'Calle 47 Nro 82-26',
        'Bancolombia Ahorros N° 61300060942', 'Noviembre 2026', '28/11/2026',
        UNIDADES_FORTALEZA, xlsx_0950
    )

    # 3. Copiar réplicas a C:\dbplus\T_IMPRE para visualización directa
    print("\n==================================================================")
    print("3. COPIANDO A C:\\dbplus\\T_IMPRE Y A LEFACTURAMOSPLUS")
    print("==================================================================")
    dir_timpre = r"C:\dbplus\T_IMPRE"
    archivos_copiar = [
        (os.path.join(dir_0955, "MM0955.DBF"), "MM0955.DBF"),
        (os.path.join(dir_0955, "SS0955.DBF"), "SS0955.DBF"),
        (xlsx_0955, "EDIFICIO_ALCALA_0955_NOVIEMBRE_2026.xlsx"),
        (os.path.join(dir_0950, "MM0950.DBF"), "MM0950.DBF"),
        (os.path.join(dir_0950, "SS0950.DBF"), "SS0950.DBF"),
        (xlsx_0950, "EDIFICIO_LA_FORTALEZA_0950_NOVIEMBRE_2026.xlsx")
    ]
    for src, dst_name in archivos_copiar:
        shutil.copy2(src, os.path.join(dir_timpre, dst_name))
        print(f"Copiado a T_IMPRE: {dst_name}")

    # 4. Crear archivos JSON master para LefacturamosPlus en data/
    dir_data = r"C:\Users\CARLOS\LefacturamosPlus\data"
    os.makedirs(dir_data, exist_ok=True)

    master_0955 = {
        "codigo": "0955",
        "nombre": "EDIFICIO ALCALÁ",
        "nit": "901575286-5",
        "direccion": "Cra 30 23-68 70-72",
        "ciudad": "Medellín • Antioquia",
        "cuenta": "Bancolombia Ahorros N° 556-000016-31",
        "periodo": "NOVIEMBRE DE 2026",
        "vencimiento": "28/11/2026",
        "conceptos": ["ADMINISTRACIÓN", "INTERÉS DE MORA", "OTROS", "CUOTA EXTRA", "REINGRESO DEL GASTO", "Concepto 6", "Concepto 7", "Notas D/C"],
        "unidades": UNIDADES_ALCALA
    }
    with open(os.path.join(dir_data, "edificio_0955_master.json"), "w", encoding="utf-8") as f:
        json.dump(master_0955, f, ensure_ascii=False, indent=2)

    master_0950 = {
        "codigo": "0950",
        "nombre": "EDIFICIO LA FORTALEZA",
        "nit": "900428879",
        "direccion": "Calle 47 Nro 82-26",
        "ciudad": "Medellín • Antioquia",
        "cuenta": "Bancolombia Ahorros N° 61300060942",
        "periodo": "NOVIEMBRE DE 2026",
        "vencimiento": "28/11/2026",
        "conceptos": ["ADMINISTRACIÓN", "INTERÉS DE MORA", "OTROS (RETROACTIVO)", "CUOTA EXTRA", "REINGRESO DEL GASTO", "Concepto 6", "Concepto 7", "Notas D/C"],
        "unidades": UNIDADES_FORTALEZA
    }
    with open(os.path.join(dir_data, "edificio_0950_master.json"), "w", encoding="utf-8") as f:
        json.dump(master_0950, f, ensure_ascii=False, indent=2)

    print("Archivos JSON master para LefacturamosPlus creados exitosamente en data/")
    print("=== TODO COMPLETADO CON ÉXITO ===")
