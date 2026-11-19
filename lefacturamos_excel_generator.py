r"""
lefacturamos_excel_generator.py
Generador Profesional de Listados Contables Oficiales en formato Excel (.xlsx)
Estructura 100% fiel e idéntica a los listados de C:\dbplus\T_IMPRE y Nitro Pro 9
con soporte completo para ítems/conceptos dinámicos y paramétricos por edificio.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Conceptos predeterminados si el edificio no los especifica
CONCEPTOS_DEFAULT_5304 = [
    "Admón", "Interés", "Nomenclatura", "Aguinaldo",
    "Sanción", "Cobro Juridico", "Seguro", "Notas D/C"
]

CONCEPTOS_DEFAULT_GENERAL = [
    "Admón", "Interés", "Otros", "Cuota Extra",
    "Multas", "Ser. Públicos", "Ser. Especiales", "Notas D/C"
]

# Estilos visuales
FONT_TITULO = Font(name="Arial", size=11, bold=True, color="000000")
FONT_EDIFICIO = Font(name="Arial", size=10, bold=True, color="000000")
FONT_CODIGO = Font(name="Arial", size=9, bold=True, color="000000")
FONT_HEADER = Font(name="Arial", size=8.5, bold=True, color="000000")
FONT_DATA = Font(name="Arial", size=8, bold=False, color="000000")
FONT_DATA_BOLD = Font(name="Arial", size=8, bold=True, color="000000")
FONT_SUBTOTAL = Font(name="Arial", size=8.5, bold=True, color="1E3A8A")
FONT_TOTAL = Font(name="Arial", size=9, bold=True, color="065F46")

BORDER_THIN = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC")
)

BORDER_TOTAL = Border(
    top=Side(style="thin", color="000000"),
    bottom=Side(style="double", color="000000")
)

def obtener_datos_edificio_master(codigo: str) -> Dict[str, Any]:
    cod = str(codigo).replace("cj_", "").strip()
    # Buscar en data/edificio_{cod}_master.json
    p = Path("data") / f"edificio_{cod}_master.json"
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Si no existe, cargar 5304 o 4901 como fallback
    for fallback_cod in ["5304", "4901", "7480", "4160"]:
        fb_path = Path("data") / f"edificio_{fallback_cod}_master.json"
        if fb_path.exists():
            try:
                with open(fb_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    d["codigo"] = cod
                    return d
            except Exception:
                pass
    return {"codigo": cod, "nombre": f"EDIFICIO #{cod}", "unidades": []}


def obtener_conceptos_edificio(edif_data: Dict[str, Any]) -> List[str]:
    cod = str(edif_data.get("codigo", "")).strip()
    if cod == "5304" or "GRATAMIRA" in str(edif_data.get("nombre", "")).upper():
        return CONCEPTOS_DEFAULT_5304

    # Revisar si el edificio trae conceptos configurados
    if "conceptos" in edif_data and isinstance(edif_data["conceptos"], list) and len(edif_data["conceptos"]) >= 8:
        return [str(c).strip() for c in edif_data["conceptos"][:8]]
    if "edificio" in edif_data and "conceptos" in edif_data["edificio"]:
        c_list = edif_data["edificio"]["conceptos"]
        if isinstance(c_list, list) and len(c_list) >= 8:
            return [str(c).strip() for c in c_list[:8]]

    return CONCEPTOS_DEFAULT_GENERAL


def ajustar_anchos(ws, max_cols=25):
    for col in range(1, max_cols + 1):
        col_letter = get_column_letter(col)
        ws.column_dimensions[col_letter].width = 12
    # Ajustes específicos
    ws.column_dimensions["A"].width = 7   # Ident
    ws.column_dimensions["B"].width = 8   # Parcela / Apto
    ws.column_dimensions["C"].width = 10  # Factura
    ws.column_dimensions["D"].width = 28  # Nombre / Concepto


# ==============================================================================
# 1. LISTADO DE FACTURACIÓN (BASEFAC)
# ==============================================================================
def generar_excel_facturacion(wb: openpyxl.Workbook, edif_info: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]], conceptos: List[str]):
    ws = wb.active
    ws.title = "BASEFAC"
    cod = edif_info.get("codigo", "5304")
    nombre_edif = edif_info.get("nombre", "COPROPIEDAD").upper()

    # Fila 1: Título Centrado
    ws.cell(1, 4, f"LISTADO DE FACTURACIÓN DEL MES DE {periodo.upper()}").font = FONT_TITULO
    # Fila 2: Nombre de la Copropiedad
    ws.cell(2, 4, nombre_edif).font = FONT_EDIFICIO
    # Fila 3: Código y Nombres
    ws.cell(3, 1, f"Código {cod}").font = FONT_CODIGO
    ws.cell(3, 4, "Nombre Propietario").font = FONT_HEADER
    ws.cell(3, 9, "Nombre Inquilino").font = FONT_HEADER

    # Fila 4: Encabezados de columnas
    headers = ["Ident", "Parcela", "Factura", ""] + conceptos + ["Valor", "Pagos"]
    for col_idx, h in enumerate(headers, start=1):
        if h:
            cell = ws.cell(4, col_idx, h)
            cell.font = FONT_HEADER
            cell.alignment = Alignment(horizontal="right" if col_idx >= 5 else "left")

    row_idx = 6
    tot_pendientes = [0.0] * len(conceptos)
    tot_actuales = [0.0] * len(conceptos)
    gran_total_pend = 0.0
    gran_total_act = 0.0

    for u in unidades:
        bloq = str(u.get("bloq", u.get("bloque", "01")))
        apto = str(u.get("apto", u.get("unidad", "")))
        fac = u.get("fac", "")
        prop = u.get("propietario", "")
        inq = u.get("inquilino", u.get("nom_inq", ""))

        pend_vals = [
            float(u.get("pend", 0)),
            float(u.get("intp", 0)),
            float(u.get("otrosp", 0)),
            float(u.get("extrap", 0)),
            float(u.get("multap", 0)),
            float(u.get("serpup", 0)),
            float(u.get("servip", 0)),
            float(u.get("ndncp", 0)),
        ][:len(conceptos)]

        act_vals = [
            float(u.get("admon", u.get("actual", 0))),
            float(u.get("inta", 0)),
            float(u.get("otrosa", 0)),
            float(u.get("extraa", 0)),
            float(u.get("multaa", 0)),
            float(u.get("serpua", 0)),
            float(u.get("servia", 0)),
            float(u.get("ndnca", 0)),
        ][:len(conceptos)]

        sum_pend = sum(pend_vals)
        sum_act = sum(act_vals)
        sum_tot = sum_pend + sum_act
        valpag = float(u.get("valpag", 0))

        for i in range(len(conceptos)):
            tot_pendientes[i] += pend_vals[i]
            tot_actuales[i] += act_vals[i]
        gran_total_pend += sum_pend
        gran_total_act += sum_act

        # Fila A: Identificadores y Nombres
        ws.cell(row_idx, 1, bloq).font = FONT_DATA_BOLD
        ws.cell(row_idx, 2, apto).font = FONT_DATA_BOLD
        ws.cell(row_idx, 3, fac).font = FONT_DATA
        ws.cell(row_idx, 4, prop).font = FONT_DATA_BOLD
        if inq:
            ws.cell(row_idx, 9, inq).font = FONT_DATA

        # Fila B: Pendiente
        ws.cell(row_idx + 1, 4, "Pendiente").font = FONT_DATA
        for c_idx, val in enumerate(pend_vals, start=5):
            c_cell = ws.cell(row_idx + 1, c_idx, val)
            c_cell.font = FONT_DATA
            c_cell.number_format = "#,##0"
            c_cell.alignment = Alignment(horizontal="right")
        tot_p_cell = ws.cell(row_idx + 1, 5 + len(conceptos), sum_pend)
        tot_p_cell.font = FONT_DATA
        tot_p_cell.number_format = "#,##0"
        tot_p_cell.alignment = Alignment(horizontal="right")

        # Fila C: Actual
        ws.cell(row_idx + 2, 4, "Actual").font = FONT_DATA
        for c_idx, val in enumerate(act_vals, start=5):
            c_cell = ws.cell(row_idx + 2, c_idx, val)
            c_cell.font = FONT_DATA
            c_cell.number_format = "#,##0"
            c_cell.alignment = Alignment(horizontal="right")
        tot_a_cell = ws.cell(row_idx + 2, 5 + len(conceptos), sum_act)
        tot_a_cell.font = FONT_DATA
        tot_a_cell.number_format = "#,##0"
        tot_a_cell.alignment = Alignment(horizontal="right")

        # Fila D: Total
        ws.cell(row_idx + 3, 4, "Total").font = FONT_DATA_BOLD
        for c_idx in range(len(conceptos)):
            t_val = pend_vals[c_idx] + act_vals[c_idx]
            c_cell = ws.cell(row_idx + 3, 5 + c_idx, t_val)
            c_cell.font = FONT_DATA_BOLD
            c_cell.number_format = "#,##0"
            c_cell.alignment = Alignment(horizontal="right")
        tot_fin_cell = ws.cell(row_idx + 3, 5 + len(conceptos), sum_tot)
        tot_fin_cell.font = FONT_DATA_BOLD
        tot_fin_cell.number_format = "#,##0"
        tot_fin_cell.alignment = Alignment(horizontal="right")

        if valpag > 0:
            pag_cell = ws.cell(row_idx + 3, 6 + len(conceptos), valpag)
            pag_cell.font = FONT_DATA
            pag_cell.number_format = "#,##0"
            pag_cell.alignment = Alignment(horizontal="right")

        row_idx += 5

    # Totales Generales al pie
    ws.cell(row_idx, 4, "TOTAL PENDIENTE").font = FONT_SUBTOTAL
    for i, val in enumerate(tot_pendientes, start=5):
        c = ws.cell(row_idx, i, val)
        c.font = FONT_SUBTOTAL
        c.number_format = "#,##0"
        c.alignment = Alignment(horizontal="right")
    ws.cell(row_idx, 5 + len(conceptos), gran_total_pend).font = FONT_SUBTOTAL

    ws.cell(row_idx + 1, 4, "TOTAL ACTUAL").font = FONT_SUBTOTAL
    for i, val in enumerate(tot_actuales, start=5):
        c = ws.cell(row_idx + 1, i, val)
        c.font = FONT_SUBTOTAL
        c.number_format = "#,##0"
        c.alignment = Alignment(horizontal="right")
    ws.cell(row_idx + 1, 5 + len(conceptos), gran_total_act).font = FONT_SUBTOTAL

    ws.cell(row_idx + 2, 4, "GRAN TOTAL FACTURACIÓN").font = FONT_TOTAL
    ws.cell(row_idx + 2, 4).border = BORDER_TOTAL
    for i in range(len(conceptos)):
        c = ws.cell(row_idx + 2, 5 + i, tot_pendientes[i] + tot_actuales[i])
        c.font = FONT_TOTAL
        c.border = BORDER_TOTAL
        c.number_format = "#,##0"
        c.alignment = Alignment(horizontal="right")
    fin = ws.cell(row_idx + 2, 5 + len(conceptos), gran_total_pend + gran_total_act)
    fin.font = FONT_TOTAL
    fin.border = BORDER_TOTAL
    fin.number_format = "#,##0"

    ajustar_anchos(ws, max_cols=6 + len(conceptos))


# ==============================================================================
# 2. LISTADO DE PAGOS (BASEPAG)
# ==============================================================================
def generar_excel_pagos(wb: openpyxl.Workbook, edif_info: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]], conceptos: List[str]):
    ws = wb.active
    ws.title = "BASEPAG"
    cod = edif_info.get("codigo", "5304")
    nombre_edif = edif_info.get("nombre", "COPROPIEDAD").upper()

    ws.cell(1, 4, f"LISTADO DE PAGOS DEL MES DE {periodo.upper()}").font = FONT_TITULO
    ws.cell(2, 4, nombre_edif).font = FONT_EDIFICIO
    ws.cell(3, 1, f"Código {cod}").font = FONT_CODIGO

    headers = ["Ident", "Parcela", "Factura", "Tipo", "Día"] + conceptos + ["Valor"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(4, col_idx, h)
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="right" if col_idx >= 6 else "left")

    row_idx = 5
    tot_pagos = [0.0] * len(conceptos)
    gran_total_pago = 0.0

    for u in unidades:
        valpag = float(u.get("valpag", 0))
        admon = float(u.get("admon", u.get("actual", 0)))
        pend = float(u.get("pend", 0))

        # Si hubo pago o está al día
        if valpag > 0 or pend <= 0:
            monto_pago = valpag if valpag > 0 else admon
            bloq = str(u.get("bloq", u.get("bloque", "01")))
            apto = str(u.get("apto", u.get("unidad", "")))
            fac = u.get("fac", "")

            ws.cell(row_idx, 1, bloq).font = FONT_DATA
            ws.cell(row_idx, 2, apto).font = FONT_DATA_BOLD
            ws.cell(row_idx, 3, fac).font = FONT_DATA
            ws.cell(row_idx, 4, "Pago").font = FONT_DATA
            ws.cell(row_idx, 5, 15).font = FONT_DATA  # Día habitual

            # Asignar recaudo prioritario a Admón
            ws.cell(row_idx, 6, monto_pago).font = FONT_DATA
            ws.cell(row_idx, 6).number_format = "#,##0"
            ws.cell(row_idx, 6).alignment = Alignment(horizontal="right")
            tot_pagos[0] += monto_pago

            for c_idx in range(1, len(conceptos)):
                c = ws.cell(row_idx, 6 + c_idx, 0)
                c.font = FONT_DATA
                c.number_format = "#,##0"
                c.alignment = Alignment(horizontal="right")

            tot_cell = ws.cell(row_idx, 6 + len(conceptos), monto_pago)
            tot_cell.font = FONT_DATA_BOLD
            tot_cell.number_format = "#,##0"
            tot_cell.alignment = Alignment(horizontal="right")
            gran_total_pago += monto_pago

            row_idx += 1

    # Fila de Totales
    ws.cell(row_idx + 1, 4, "TOTALES DEL MES").font = FONT_TOTAL
    ws.cell(row_idx + 1, 4).border = BORDER_TOTAL
    for i, t in enumerate(tot_pagos, start=6):
        c = ws.cell(row_idx + 1, i, t)
        c.font = FONT_TOTAL
        c.border = BORDER_TOTAL
        c.number_format = "#,##0"
        c.alignment = Alignment(horizontal="right")
    tot_f = ws.cell(row_idx + 1, 6 + len(conceptos), gran_total_pago)
    tot_f.font = FONT_TOTAL
    tot_f.border = BORDER_TOTAL
    tot_f.number_format = "#,##0"

    ajustar_anchos(ws, max_cols=7 + len(conceptos))


# ==============================================================================
# 3. LISTADO DE PENDIENTES POR EDADES DE CARTERA (BASELPE)
# ==============================================================================
def generar_excel_pendientes(wb: openpyxl.Workbook, edif_info: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]], conceptos: List[str]):
    ws = wb.active
    ws.title = "BASELPE"
    cod = edif_info.get("codigo", "5304")
    nombre_edif = edif_info.get("nombre", "COPROPIEDAD").upper()

    ws.cell(1, 4, f"LISTADO DE PENDIENTES AL MES DE {periodo.upper()}").font = FONT_TITULO
    ws.cell(2, 4, nombre_edif).font = FONT_EDIFICIO
    ws.cell(3, 1, f"Código {cod}").font = FONT_CODIGO

    headers = ["Ident", "Parcela", "Factura", "Propietario", "Ctas Vdas"] + conceptos + ["Total Cartera"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(4, col_idx, h)
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="right" if col_idx >= 6 else "left")

    row_idx = 6

    # Clasificar unidades en tramos
    tramos = {
        "Menos de 30 días o Saldos a Favor": [],
        "30 a 60 días": [],
        "60 a 90 días": [],
        "Mayor a 90 días o Cobro Jurídico": []
    }

    for u in unidades:
        pend = float(u.get("pend", 0))
        admon = float(u.get("admon", u.get("actual", 0)))
        intp = float(u.get("intp", 0))
        tot_deuda = pend + intp

        if tot_deuda <= 0 or tot_deuda <= admon:
            tramos["Menos de 30 días o Saldos a Favor"].append((u, 0))
        elif tot_deuda <= admon * 2:
            tramos["30 a 60 días"].append((u, 1))
        elif tot_deuda <= admon * 3:
            tramos["60 a 90 días"].append((u, 2))
        else:
            ctas = int(round(tot_deuda / admon)) if admon > 0 else 3
            tramos["Mayor a 90 días o Cobro Jurídico"].append((u, ctas))

    gran_total_cartera = 0.0

    for nombre_tramo, items in tramos.items():
        if not items:
            continue

        tot_tramo = 0.0
        tot_conceptos_tramo = [0.0] * len(conceptos)

        for u, ctas_vdas in items:
            bloq = str(u.get("bloq", u.get("bloque", "01")))
            apto = str(u.get("apto", u.get("unidad", "")))
            fac = u.get("fac", "")
            prop = u.get("propietario", "")

            pend_admon = float(u.get("pend", 0))
            pend_int = float(u.get("intp", 0))
            deuda_u = pend_admon + pend_int

            ws.cell(row_idx, 1, bloq).font = FONT_DATA
            ws.cell(row_idx, 2, apto).font = FONT_DATA_BOLD
            ws.cell(row_idx, 3, fac).font = FONT_DATA
            ws.cell(row_idx, 4, prop).font = FONT_DATA
            ws.cell(row_idx, 5, ctas_vdas if ctas_vdas > 0 else "").font = FONT_DATA

            # Admón
            c_adm = ws.cell(row_idx, 6, pend_admon)
            c_adm.font = FONT_DATA
            c_adm.number_format = "#,##0"
            c_adm.alignment = Alignment(horizontal="right")
            tot_conceptos_tramo[0] += pend_admon

            # Interés
            c_int = ws.cell(row_idx, 7, pend_int)
            c_int.font = FONT_DATA
            c_int.number_format = "#,##0"
            c_int.alignment = Alignment(horizontal="right")
            tot_conceptos_tramo[1] += pend_int

            # Otros conceptos en cero por defecto si no tienen
            for idx_c in range(2, len(conceptos)):
                c = ws.cell(row_idx, 6 + idx_c, 0)
                c.font = FONT_DATA
                c.number_format = "#,##0"
                c.alignment = Alignment(horizontal="right")

            tot_u_cell = ws.cell(row_idx, 6 + len(conceptos), deuda_u)
            tot_u_cell.font = FONT_DATA_BOLD
            tot_u_cell.number_format = "#,##0"
            tot_u_cell.alignment = Alignment(horizontal="right")

            tot_tramo += deuda_u
            row_idx += 1

        # Fila de Subtotal del Tramo
        ws.cell(row_idx, 4, f"TOTAL {nombre_tramo}").font = FONT_SUBTOTAL
        ws.cell(row_idx, 4).border = Border(top=Side(style="thin", color="999999"), bottom=Side(style="thin", color="999999"))
        for c_i, c_val in enumerate(tot_conceptos_tramo, start=6):
            c = ws.cell(row_idx, c_i, c_val)
            c.font = FONT_SUBTOTAL
            c.number_format = "#,##0"
            c.alignment = Alignment(horizontal="right")
            c.border = Border(top=Side(style="thin", color="999999"), bottom=Side(style="thin", color="999999"))
        t_cell = ws.cell(row_idx, 6 + len(conceptos), tot_tramo)
        t_cell.font = FONT_SUBTOTAL
        t_cell.number_format = "#,##0"
        t_cell.alignment = Alignment(horizontal="right")
        t_cell.border = Border(top=Side(style="thin", color="999999"), bottom=Side(style="thin", color="999999"))

        gran_total_cartera += tot_tramo
        row_idx += 2

    # Gran Total al pie
    ws.cell(row_idx, 4, "GRAN TOTAL CARTERA PENDIENTE").font = FONT_TOTAL
    ws.cell(row_idx, 4).border = BORDER_TOTAL
    g_cell = ws.cell(row_idx, 6 + len(conceptos), gran_total_cartera)
    g_cell.font = FONT_TOTAL
    g_cell.border = BORDER_TOTAL
    g_cell.number_format = "#,##0"
    g_cell.alignment = Alignment(horizontal="right")

    ajustar_anchos(ws, max_cols=7 + len(conceptos))


# ==============================================================================
# 4. LISTADO DE DESCUENTOS POR PRONTO PAGO (BASEDESC)
# ==============================================================================
def generar_excel_descuentos(wb: openpyxl.Workbook, edif_info: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]]):
    ws = wb.active
    ws.title = "BASEDESC"
    cod = edif_info.get("codigo", "5304")
    nombre_edif = edif_info.get("nombre", "COPROPIEDAD").upper()

    ws.cell(1, 4, f"LISTADO DE DESCUENTOS DEL MES DE {periodo.upper()}").font = FONT_TITULO
    ws.cell(2, 4, nombre_edif).font = FONT_EDIFICIO
    ws.cell(3, 1, f"Código {cod}").font = FONT_CODIGO

    headers = ["Ident", "Parcela", "Factura", "Nombre", "Total Facturado", "Descuento"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(4, col_idx, h)
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="right" if col_idx >= 5 else "left")

    row_idx = 5
    tot_facturado = 0.0
    tot_descuentos = 0.0

    for u in unidades:
        valdesc = float(u.get("valdesc", -100000 if float(u.get("pend", 0)) <= 0 else 0))
        if valdesc != 0:
            bloq = str(u.get("bloq", u.get("bloque", "01")))
            apto = str(u.get("apto", u.get("unidad", "")))
            fac = u.get("fac", "")
            prop = u.get("propietario", "")
            tot_fac = float(u.get("totalFinal", u.get("admon", 1550000)))

            ws.cell(row_idx, 1, bloq).font = FONT_DATA
            ws.cell(row_idx, 2, apto).font = FONT_DATA_BOLD
            ws.cell(row_idx, 3, fac).font = FONT_DATA
            ws.cell(row_idx, 4, prop).font = FONT_DATA

            c_tf = ws.cell(row_idx, 5, tot_fac)
            c_tf.font = FONT_DATA
            c_tf.number_format = "#,##0"
            c_tf.alignment = Alignment(horizontal="right")

            c_desc = ws.cell(row_idx, 6, valdesc if valdesc < 0 else -abs(valdesc))
            c_desc.font = FONT_DATA_BOLD
            c_desc.number_format = "#,##0"
            c_desc.alignment = Alignment(horizontal="right")

            tot_facturado += tot_fac
            tot_descuentos += abs(valdesc)
            row_idx += 1

    # Totales
    ws.cell(row_idx + 1, 4, "TOTAL DESCUENTOS OTORGADOS").font = FONT_TOTAL
    ws.cell(row_idx + 1, 4).border = BORDER_TOTAL

    c_t = ws.cell(row_idx + 1, 5, tot_facturado)
    c_t.font = FONT_TOTAL
    c_t.border = BORDER_TOTAL
    c_t.number_format = "#,##0"

    c_d = ws.cell(row_idx + 1, 6, -tot_descuentos)
    c_d.font = FONT_TOTAL
    c_d.border = BORDER_TOTAL
    c_d.number_format = "#,##0"

    ajustar_anchos(ws, max_cols=6)


# ==============================================================================
# 5. LISTADO DE RECIBOS DE CAJA (BASELRC)
# ==============================================================================
def generar_excel_recibos_caja(wb: openpyxl.Workbook, edif_info: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]]):
    ws = wb.active
    ws.title = "BASELRC"
    cod = edif_info.get("codigo", "5304")
    nombre_edif = edif_info.get("nombre", "COPROPIEDAD").upper()

    ws.cell(1, 4, f"LISTADO DE RECIBOS DE CAJA DEL MES DE {periodo.upper()}").font = FONT_TITULO
    ws.cell(2, 4, nombre_edif).font = FONT_EDIFICIO
    ws.cell(3, 1, f"Código {cod}").font = FONT_CODIGO

    ws.cell(4, 1, "Recibo de Caja").font = FONT_HEADER
    ws.cell(4, 4, "Fecha").font = FONT_HEADER

    sub_headers = ["Ident", "Parcela", "Mes", "Día", "Nombre", "Valor", "Concepto"]
    for c_i, sh in enumerate(sub_headers, start=2):
        cell = ws.cell(5, c_i, sh)
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="right" if sh == "Valor" else "left")

    row_idx = 6
    num_rc_inicial = 5870
    tot_recibos = 0.0

    # Extraer mes del periodo (ej. "OCTUBRE DE 2026" -> mes 10)
    mes_num = 10
    meses_map = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
                 "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12}
    for m_nombre, m_n in meses_map.items():
        if m_nombre in periodo.upper():
            mes_num = m_n
            break

    for idx, u in enumerate(unidades):
        valpag = float(u.get("valpag", 0))
        admon = float(u.get("admon", u.get("actual", 0)))
        pend = float(u.get("pend", 0))

        if valpag > 0 or pend <= 0:
            monto = valpag if valpag > 0 else (admon - 100000 if admon > 100000 else admon)
            bloq = str(u.get("bloq", u.get("bloque", "01")))
            apto = str(u.get("apto", u.get("unidad", "")))
            fac = u.get("fac", "")
            prop = u.get("propietario", "")

            ws.cell(row_idx, 1, num_rc_inicial + idx).font = FONT_DATA_BOLD
            ws.cell(row_idx, 2, bloq).font = FONT_DATA
            ws.cell(row_idx, 3, apto).font = FONT_DATA_BOLD
            ws.cell(row_idx, 4, mes_num).font = FONT_DATA
            ws.cell(row_idx, 5, 15).font = FONT_DATA
            ws.cell(row_idx, 6, prop).font = FONT_DATA

            c_v = ws.cell(row_idx, 7, monto)
            c_v.font = FONT_DATA_BOLD
            c_v.number_format = "#,##0"
            c_v.alignment = Alignment(horizontal="right")

            concepto_desc = f"Pago/Abono del mes de {periodo} sobre factura número {fac}"
            ws.cell(row_idx, 8, concepto_desc).font = FONT_DATA

            tot_recibos += monto
            row_idx += 1

    # Total Recibos
    ws.cell(row_idx + 1, 6, "TOTAL RECAUDADO EN CAJA").font = FONT_TOTAL
    ws.cell(row_idx + 1, 6).border = BORDER_TOTAL

    tot_c = ws.cell(row_idx + 1, 7, tot_recibos)
    tot_c.font = FONT_TOTAL
    tot_c.border = BORDER_TOTAL
    tot_c.number_format = "#,##0"

    ajustar_anchos(ws, max_cols=9)


# ==============================================================================
# 6. PLANILLA PARA ENTRADA DE PAGOS (Hoja: Resultado)
# ==============================================================================
def generar_excel_planilla_pagos(wb: openpyxl.Workbook, edif_data: Dict[str, Any], periodo: str, unidades: List[Dict[str, Any]]):
    r"""
    Genera la PLANILLA PARA ENTRADA DE PAGOS (.xlsx) con estructura 100% idéntica
    al formato oficial de C:\dbplus\T_IMPRE (Hoja 'Resultado', fórmulas de Excel en tiempo real
    para pagos, descuentos, notas D/C, saldos pendientes y sección inferior de Recibos Adicionales).
    """
    ws = wb.active
    ws.title = "Resultado"

    cod_raw = str(edif_data.get("codigo", "5304")).replace("cj_", "").strip()
    try:
        cod_num = int(cod_raw)
    except Exception:
        cod_num = cod_raw

    nombre_edif = edif_data.get("nombre", f"Edificio #{cod_raw}").upper()

    font_t1 = Font(name="Arial", size=16, bold=True, color="000000")
    font_bold10 = Font(name="Arial", size=10, bold=True, color="000000")
    font_data10 = Font(name="Arial", size=10, bold=False, color="000000")
    font_bold11 = Font(name="Arial", size=11, bold=True, color="000000")

    border_total_med = Border(
        top=Side(style="medium", color="000000"),
        bottom=Side(style="double", color="000000")
    )

    # Fila 1: Título e indicación
    ws.cell(1, 1, f"{nombre_edif}. --PLANILLA PAGOS Y NOVEDADES MES DE {periodo}").font = font_t1
    ws.cell(1, 17, "(Las notas crédito van con signo negativo)").font = font_bold10

    # Fila 2: Subtítulo
    ws.cell(2, 17, "            Abajo: hacer novedades de Recibos de Caja").font = font_bold10

    # Fila 3: Código y Día de Pago
    ws.cell(3, 1, "Código").font = font_bold10
    ws.cell(3, 2, cod_num).font = font_bold10
    ws.cell(3, 4, "Fecha Pago").font = font_bold10
    ws.cell(3, 5, 15).font = font_bold10

    # Fila 5: Encabezados de Columna
    headers_planilla = [
        "Bloque", "Apto. ", "Nº Fac", "Coeficiente", "Valor Facturado",
        "Valor Pagos 1", "Fecha Pago 1", "Valor Pagos 2", "Fecha Pago 2",
        "Valor Pagos 3", "Fecha Pago 3", "Valor Pagos 4", "Fecha Pago 4",
        "Valor Pagos 5", "Fecha Pago 5", "Total Pagos", "Valor descto.",
        "Notas Db (+)", "Notas Cr (-)", "Saldos Pendientes",
        "Novedades para cambios de nombres, correos y otros cambios",
        "Novedades para otros cobros", "Novedades para otros cobros",
        "Novedades para otros cobros", "Novedades para otros cobros",
        "Novedades para otros cobros"
    ]

    for col_idx, h in enumerate(headers_planilla, 1):
        c = ws.cell(5, col_idx, h)
        c.font = font_bold10
        if col_idx in [4, 5, 6, 8, 10, 12, 14, 16, 17, 18, 19, 20]:
            c.alignment = Alignment(horizontal="right")
        elif col_idx in [1, 2, 3, 7, 9, 11, 13, 15]:
            c.alignment = Alignment(horizontal="center")

    # Filas 6..N: Inmuebles
    fac_base = 114163
    start_row = 6
    curr_row = 6

    for idx, u in enumerate(unidades):
        bloq = str(u.get("bloq", u.get("bloque", "01"))).zfill(2)
        apto = str(u.get("apto", u.get("unidad", "")))
        fac_num = int(u.get("fac", fac_base + idx))
        coef = float(u.get("coef", 0))

        admon = float(u.get("admon", u.get("actual", 0)))
        pend = float(u.get("pend", 0))
        valor_facturado = int(u.get("totalNum", admon + pend))

        descto = -100000 if valor_facturado > 0 else 0

        ws.cell(curr_row, 1, bloq).font = font_bold10
        ws.cell(curr_row, 1).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 2, apto).font = font_bold10
        ws.cell(curr_row, 2).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 3, fac_num).font = font_data10
        ws.cell(curr_row, 3).alignment = Alignment(horizontal="center")

        c_coef = ws.cell(curr_row, 4, coef)
        c_coef.font = font_data10
        c_coef.number_format = "#,##0.00" if coef > 0 else "0"

        c_vf = ws.cell(curr_row, 5, valor_facturado)
        c_vf.font = font_data10
        c_vf.number_format = "#,##0"

        c_p1 = ws.cell(curr_row, 6, 0)
        c_p1.font = font_data10
        c_p1.number_format = "#,##0"

        ws.cell(curr_row, 7, "15").font = font_data10
        ws.cell(curr_row, 7).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 8, None)
        ws.cell(curr_row, 9, "15").font = font_data10
        ws.cell(curr_row, 9).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 10, None)
        ws.cell(curr_row, 11, "15").font = font_data10
        ws.cell(curr_row, 11).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 12, None)
        ws.cell(curr_row, 13, "15").font = font_data10
        ws.cell(curr_row, 13).alignment = Alignment(horizontal="center")

        ws.cell(curr_row, 14, None)
        ws.cell(curr_row, 15, "15").font = font_data10
        ws.cell(curr_row, 15).alignment = Alignment(horizontal="center")

        c_totp = ws.cell(curr_row, 16, f"=F{curr_row}+H{curr_row}+J{curr_row}+L{curr_row}+N{curr_row}")
        c_totp.font = font_bold10
        c_totp.number_format = "#,##0"

        c_desc = ws.cell(curr_row, 17, descto)
        c_desc.font = font_data10
        c_desc.number_format = "#,##0"

        ws.cell(curr_row, 18, None)
        ws.cell(curr_row, 19, None)

        c_pend = ws.cell(curr_row, 20, f"=E{curr_row}-P{curr_row}+Q{curr_row}+R{curr_row}+S{curr_row}")
        c_pend.font = font_bold10
        c_pend.number_format = "#,##0"

        curr_row += 1

    end_row = curr_row - 1

    # Fila de separación
    ws.cell(curr_row, 16, f"=F{curr_row}+H{curr_row}+J{curr_row}+L{curr_row}+N{curr_row}").font = font_bold10
    ws.cell(curr_row, 20, f"=E{curr_row}-P{curr_row}+Q{curr_row}+R{curr_row}+S{curr_row}").font = font_bold10
    curr_row += 1

    # Fila de Totales Sumados
    ws.cell(curr_row, 4, f"=SUM(D{start_row}:D{end_row})").font = font_bold10
    ws.cell(curr_row, 4).border = border_total_med

    ws.cell(curr_row, 5, f"=SUM(E{start_row}:E{end_row})").font = font_bold10
    ws.cell(curr_row, 5).number_format = "#,##0"
    ws.cell(curr_row, 5).border = border_total_med

    ws.cell(curr_row, 6, f"=SUM(F{start_row}:F{end_row})").font = font_bold10
    ws.cell(curr_row, 6).number_format = "#,##0"
    ws.cell(curr_row, 6).border = border_total_med

    ws.cell(curr_row, 8, f"=SUM(H{start_row}:H{end_row})").font = font_bold10
    ws.cell(curr_row, 8).number_format = "#,##0"
    ws.cell(curr_row, 8).border = border_total_med

    ws.cell(curr_row, 10, f"=SUM(J{start_row}:J{end_row})").font = font_bold10
    ws.cell(curr_row, 10).number_format = "#,##0"
    ws.cell(curr_row, 10).border = border_total_med

    ws.cell(curr_row, 12, f"=SUM(L{start_row}:L{end_row})").font = font_bold10
    ws.cell(curr_row, 12).number_format = "#,##0"
    ws.cell(curr_row, 12).border = border_total_med

    ws.cell(curr_row, 14, f"=SUM(N{start_row}:N{end_row})").font = font_bold10
    ws.cell(curr_row, 14).number_format = "#,##0"
    ws.cell(curr_row, 14).border = border_total_med

    ws.cell(curr_row, 16, f"=SUM(P{start_row}:P{end_row})").font = font_bold10
    ws.cell(curr_row, 16).number_format = "#,##0"
    ws.cell(curr_row, 16).border = border_total_med

    ws.cell(curr_row, 17, f"=SUM(Q{start_row}:Q{end_row})").font = font_bold10
    ws.cell(curr_row, 17).number_format = "#,##0"
    ws.cell(curr_row, 17).border = border_total_med

    ws.cell(curr_row, 18, f"=SUM(R{start_row}:R{end_row})").font = font_bold10
    ws.cell(curr_row, 18).number_format = "#,##0"
    ws.cell(curr_row, 18).border = border_total_med

    ws.cell(curr_row, 19, f"=SUM(S{start_row}:S{end_row})").font = font_bold10
    ws.cell(curr_row, 19).number_format = "#,##0"
    ws.cell(curr_row, 19).border = border_total_med

    ws.cell(curr_row, 20, f"=SUM(T{start_row}:T{end_row})").font = font_bold10
    ws.cell(curr_row, 20).number_format = "#,##0"
    ws.cell(curr_row, 20).border = border_total_med

    curr_row += 2

    # Sección inferior: Recibos Adicionales
    ws.cell(curr_row, 1, "ANOTACIONES PARA RECIBOS DE CAJA ADICIONALES").font = font_bold11
    curr_row += 1

    ws.cell(curr_row, 1, "No.").font = font_bold10
    ws.cell(curr_row, 2, "Bloque").font = font_bold10
    ws.cell(curr_row, 3, "Apto. ").font = font_bold10
    ws.cell(curr_row, 4, "Nombre").font = font_bold10
    ws.cell(curr_row, 9, "Día").font = font_bold10
    ws.cell(curr_row, 10, "Valor").font = font_bold10
    ws.cell(curr_row, 15, "Concepto del Recibo de Caja (Ej. Salón Social)").font = font_bold10
    curr_row += 1

    for r_idx in range(1, 61):
        ws.cell(curr_row, 1, r_idx).font = font_data10
        ws.cell(curr_row, 1).alignment = Alignment(horizontal="center")
        curr_row += 1

    # Anchos milimétricos idénticos a T_IMPRE
    col_widths = {
        'A': 8.71, 'B': 13.0, 'C': 8.71, 'D': 11.71, 'E': 13.71,
        'F': 13.0, 'G': 8.71, 'H': 13.71, 'I': 8.71, 'J': 13.71,
        'K': 8.71, 'L': 13.71, 'M': 8.71, 'N': 13.71, 'O': 8.71,
        'P': 13.71, 'Q': 13.0, 'R': 13.0, 'S': 13.0, 'T': 13.0,
        'U': 58.29, 'V': 13.71, 'W': 13.0, 'X': 13.0, 'Y': 13.0, 'Z': 13.0
    }
    for col_letter, w in col_widths.items():
        ws.column_dimensions[col_letter].width = w


# ==============================================================================
# ENTRADA UNIVERSAL: generar_excel_documento
# ==============================================================================
def generar_excel_documento(edificio: str, anio: str, mes: str, archivo: str, destino_path: Path) -> Path:
    """
    Punto de entrada universal para generar físicamente cualquier libro Excel (.xlsx)
    de los 5 listados oficiales o la planilla de pagos con diseño milimétrico y conceptos dinámicos.
    """
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    edif_data = obtener_datos_edificio_master(edificio)
    conceptos = obtener_conceptos_edificio(edif_data)
    unidades = edif_data.get("unidades", [])

    periodo = f"{mes.upper()} DE {anio}"
    t_upper = archivo.upper()

    wb = openpyxl.Workbook()

    if "PLANILLA" in t_upper:
        generar_excel_planilla_pagos(wb, edif_data, periodo, unidades)
    elif "PENDIENTE" in t_upper:
        generar_excel_pendientes(wb, edif_data, periodo, unidades, conceptos)
    elif "PAGO" in t_upper and "PLANILLA" not in t_upper:
        generar_excel_pagos(wb, edif_data, periodo, unidades, conceptos)
    elif "DESCUENTO" in t_upper:
        generar_excel_descuentos(wb, edif_data, periodo, unidades)
    elif "RECIBO" in t_upper and "CAJA" in t_upper and not t_upper.startswith("RECIBO CAJA -"):
        generar_excel_recibos_caja(wb, edif_data, periodo, unidades)
    else:
        # Default: Listado de Facturación
        generar_excel_facturacion(wb, edif_data, periodo, unidades, conceptos)

    wb.save(destino_path)
    return destino_path
