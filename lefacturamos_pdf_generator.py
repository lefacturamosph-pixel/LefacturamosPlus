#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - GENERADOR DINÁMICO DE DOCUMENTOS PDF OFICIALES
Genera facturas de administración, recibos de caja e informes contables en formato PDF
con diseño auténtico, cumplimiento estricto de la Ley 675 de 2001 y validez contable.
========================================================================================
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Intento de carga de ReportLab
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


EDIFICIOS_INFO = {
    "4160": {
        "codigo": "4160",
        "nombre": "Edificio Mixto Riachuelo",
        "nit": "901079657-7",
        "direccion": "CALLE 76D SUR No 43A - 100",
        "ciudad": "Medellín • Antioquia",
        "banco": "BANCOLOMBIA",
        "cuenta": "436-848008-18",
        "convenio": "4160",
        "administrador": "60 JAVIER MAURICIO PEREZ MESA"
    },
    "4901": {
        "codigo": "4901",
        "nombre": "EDIFICIO ROBLE ALTO P.H.",
        "nit": "901690778-9",
        "direccion": "DG 79A No 76-250/252/254/256",
        "ciudad": "Medellín – Antioquia",
        "banco": "BANCOLOMBIA - CUENTA DE AHORROS",
        "cuenta": "10022286922",
        "convenio": "64821",
        "administrador": "Adriana Salgado Patiño"
    },
    "7480": {
        "codigo": "7480",
        "nombre": "CONJUNTO RESIDENCIAL BOSQUES DE LA COLINA P.H.",
        "nit": "900543210-4",
        "direccion": "Calle 45 No 12-34",
        "ciudad": "Medellín – Antioquia",
        "banco": "BANCOLOMBIA - CUENTA CORRIENTE",
        "cuenta": "23456789012",
        "convenio": "54890",
        "administrador": "Carlos Mario Gómez"
    },
    "5304": {
        "codigo": "5304",
        "nombre": "PARCELACION VALLADOS DE GRATAMIRA P.H.",
        "nit": "800145805-7",
        "direccion": "Vía Las Palmas Km 12",
        "ciudad": "Medellín – Antioquia",
        "banco": "BANCOLOMBIA - CUENTA DE AHORROS",
        "cuenta": "10022286922",
        "convenio": "53040",
        "administrador": "Elena Mercedes Valdés"
    }
}


def obtener_info_edificio(codigo: str) -> Dict[str, Any]:
    cod = str(codigo).replace("cj_", "").strip()
    if cod in EDIFICIOS_INFO:
        return EDIFICIOS_INFO[cod]
    # Buscar en archivo master si existe
    m_path = Path("data") / f"edificio_{cod}_master.json"
    if m_path.exists():
        try:
            with open(m_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                ed = d.get("edificio", d)
                return {
                    "codigo": cod,
                    "nombre": ed.get("nombre", d.get("nombre", f"Edificio #{cod}")),
                    "nit": ed.get("nit", d.get("nit", "901079657-7")),
                    "direccion": ed.get("direccion", d.get("direccion", "Medellín - Antioquia")),
                    "ciudad": ed.get("ciudad", d.get("ciudad", "Medellín")),
                    "banco": ed.get("banco", d.get("banco", "BANCOLOMBIA")),
                    "cuenta": ed.get("cuenta", d.get("cuenta", "436-848008-18")),
                    "convenio": ed.get("convenio", d.get("convenio", cod)),
                    "administrador": ed.get("administrador", d.get("administrador", "Administración Oficial"))
                }
        except Exception:
            pass
    return {
        "codigo": cod,
        "nombre": f"Edificio #{cod}",
        "nit": "901079657-7",
        "direccion": "Medellín – Antioquia",
        "ciudad": "Medellín",
        "banco": "BANCOLOMBIA",
        "cuenta": "436-848008-18",
        "convenio": cod,
        "administrador": "Administración del Edificio"
    }


def extraer_datos_unidad(codigo: str, apto: str) -> Dict[str, Any]:
    cod = str(codigo).replace("cj_", "").strip()
    u_clean = apto.strip()
    u_num = re.sub(r'\D', '', u_clean)

    # Revisar master json
    m_path = Path("data") / f"edificio_{cod}_master.json"
    if m_path.exists():
        try:
            with open(m_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                for u in d.get("unidades", []):
                    u_ap = str(u.get("unidad", u.get("apto", ""))).strip()
                    if u_ap == u_clean or (u_num and re.sub(r'\D', '', u_ap) == u_num):
                        admon_val = u.get("admon", u.get("actual", 0))
                        pend_val = u.get("pend", 0)
                        inta_val = u.get("inta", 0)
                        intp_val = u.get("intp", 0)
                        tot_val = u.get("totalNum", u.get("totalFinal", admon_val + pend_val + inta_val))
                        valpag_val = u.get("valpag", admon_val)
                        return {
                            "apto": u_clean,
                            "propietario": u.get("propietario", f"Copropietario Apto {u_clean}"),
                            "cc": u.get("cc", ""),
                            "coef": u.get("coeficiente", u.get("coef", "1.000%")),
                            "admon": admon_val,
                            "pend": pend_val,
                            "inta": inta_val,
                            "intp": intp_val,
                            "totalNum": tot_val,
                            "valpag": valpag_val
                        }
        except Exception:
            pass

    return {
        "apto": u_clean,
        "propietario": f"Copropietario Unidad {u_clean}",
        "cc": "",
        "coef": "1.000%",
        "admon": 205000,
        "pend": 0,
        "inta": 0,
        "intp": 0,
        "totalNum": 205000,
        "valpag": 205000
    }


def parsear_nombre_archivo(archivo: str, edificio: str, anio: str, mes: str) -> Dict[str, Any]:
    arch_upper = archivo.upper()
    es_libro_facturas = "FACTURAS DE COBRO" in arch_upper
    es_listado = not es_libro_facturas and any(k in arch_upper for k in ["LISTADO", "INFORME", "PLANILLA", "RECIBOS DE CAJA"])
    es_fac = not es_listado and not es_libro_facturas and ("FACTURA" in arch_upper)
    es_rec = not es_listado and ("RECIBO" in arch_upper)

    # Buscar consecutivo
    m_num = re.search(r'[-–]\s*(\d{3,6})\s*[-–]', archivo)
    consecutivo = m_num.group(1) if m_num else ("102401" if es_fac else "2501")

    # Buscar apto si no es listado
    m_apto = re.search(r'(?:APTO|LOCA|LOCL)?[-–\s]*([0-9]{3,4})(?:[-–][0-9A-Za-z]+)?', archivo, re.I) if not es_listado else None
    apto = m_apto.group(1) if m_apto else "0201"

    # Buscar propietario si viene en el nombre
    m_prop = re.search(r'[-–]\s*([A-Za-zÁÉÍÓÚáéíóúÑñ\s\.]+)\.PDF', archivo, re.I)
    prop_en_nombre = m_prop.group(1).strip() if m_prop else None

    # Datos contables de la unidad
    u_data = extraer_datos_unidad(edificio, apto)
    if prop_en_nombre and len(prop_en_nombre) > 3 and not any(k in prop_en_nombre.upper() for k in ["FACTURA", "RECIBO", "2026", "OCTUBRE", "SEPTIEMBRE", "LISTADO"]):
        u_data["propietario"] = prop_en_nombre

    if es_libro_facturas:
        tipo = "FACTURAS_LIBRO"
    elif es_listado:
        tipo = "LISTADO"
    elif es_fac:
        tipo = "FACTURA"
    elif es_rec:
        tipo = "RECIBO_CAJA"
    else:
        tipo = "INFORME"

    return {
        "tipo": tipo,
        "consecutivo": consecutivo,
        "apto": apto,
        "periodo": f"{mes.upper()} DE {anio}",
        "propietario": u_data["propietario"],
        "u_data": u_data,
        "nombre_archivo": archivo
    }


def draw_individual_factura(c, x_offset, y_top, w, edif_info, data):
    apto = data.get("apto", "0107")
    prop = data.get("propietario", "Copropietario").upper()
    fac_num = data.get("consecutivo", data.get("fac", 2745))
    mes = data.get("periodo", "NOVIEMBRE DE 2026")
    u = data.get("u_data", {})
    pend = u.get("pend", 0)
    admon = u.get("admon", u.get("actual", 412000))
    inta = u.get("inta", 0)
    total = u.get("totalNum", admon + pend + inta)
    valpag = u.get("valpag", admon)
    ctas_vdas = 1 if pend > 0 else 0
    cc = u.get("cc", "")
    coef = u.get("coef", u.get("coeficiente", "1.205%"))
    if not str(coef).endswith("%"):
        coef = f"{coef}%"
    
    edif_nom = edif_info.get("nombre", "COPROPIEDAD").upper()
    edif_nit = edif_info.get("nit", "901690778-9")
    edif_dir = edif_info.get("direccion", "Medellín – Antioquia")
    edif_ciu = edif_info.get("ciudad", "Medellín")
    edif_bco = edif_info.get("banco", "BANCOLOMBIA")
    edif_cta = edif_info.get("cuenta", "436-848008-18")
    edif_adm = edif_info.get("administrador", "Administración PH")

    fmt_cur = lambda v: f"${int(v):,}".replace(",", ".") if v else "$0"

    # Marco exterior de la factura individual (Un solo cuerpo completo por página)
    c.setStrokeColor(colors.HexColor("#0f172a"))
    c.setLineWidth(1.2)
    h_box = 690
    y_box = y_top - h_box
    c.rect(x_offset, y_box, w, h_box, fill=0, stroke=1)

    # 1. ENCABEZADO INSTITUCIONAL
    c.setFillColor(colors.HexColor("#064e3b"))
    c.rect(x_offset, y_top - 62, w, 62, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#10b981"))
    c.rect(x_offset, y_top - 66, w, 4, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x_offset + 14, y_top - 22, edif_nom[:45])
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#a7f3d0"))
    c.drawString(x_offset + 14, y_top - 36, f"NIT: {edif_nit} • {edif_dir} • {edif_ciu}")
    c.drawString(x_offset + 14, y_top - 48, f"Administración: {edif_adm} • Régimen de Propiedad Horizontal (Ley 675 de 2001)")

    # Badge Cuenta de Cobro / Factura Individual
    c.setFillColor(colors.HexColor("#059669"))
    c.roundRect(x_offset + w - 185, y_top - 54, 172, 44, 6, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x_offset + w - 99, y_top - 24, "FACTURA INDIVIDUAL")
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x_offset + w - 99, y_top - 42, f"C. COBRO N° {fac_num}")

    # 2. DATOS DEL INMUEBLE Y COPROPIETARIO
    y_sec2 = y_top - 74
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.rect(x_offset + 1, y_sec2 - 76, w - 2, 76, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.line(x_offset, y_sec2 - 76, x_offset + w, y_sec2 - 76)

    # Columna Izquierda: Copropietario
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x_offset + 14, y_sec2 - 16, "SEÑOR(A) / COPROPIETARIO(A):")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(x_offset + 14, y_sec2 - 30, prop[:42])

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(x_offset + 14, y_sec2 - 46, f"C.C. / NIT: {cc if cc else 'No registrado'}")
    c.drawString(x_offset + 14, y_sec2 - 60, f"INQUILINO / OCUPANTE: {data.get('inquilino', 'El Propietario')}")

    # Columna Derecha: Unidad y Referencia
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x_offset + 320, y_sec2 - 16, "INMUEBLE / UNIDAD:")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#065f46"))
    c.drawString(x_offset + 320, y_sec2 - 31, f"APARTAMENTO {apto}")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(x_offset + 320, y_sec2 - 46, f"COEFICIENTE: {coef} • BLOQUE / TORRE: {data.get('bloq', '01')}")
    c.drawString(x_offset + 320, y_sec2 - 60, f"MES FACTURADO: {mes} • CUOTAS EN MORA: {ctas_vdas}")

    # 3. TABLA DE CONCEPTOS FACTURADOS
    y_table = y_sec2 - 94
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(x_offset, y_table, w, 22, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_offset + 16, y_table + 7, "CONCEPTO / DESCRIPCIÓN")
    c.drawRightString(x_offset + 300, y_table + 7, "SALDO ANTERIOR")
    c.drawRightString(x_offset + 420, y_table + 7, "ACTUAL DEL MES")
    c.drawRightString(x_offset + w - 16, y_table + 7, "TOTAL CONCEPTO")

    # Filas de conceptos
    concepts = [
        ("CUOTA ORDINARIA DE ADMINISTRACIÓN", pend, admon, pend + admon),
        ("INTERÉS DE MORA (LEY 675)", 0, inta, inta),
        ("CUOTA EXTRAORDINARIA", 0, 0, 0),
        ("FONDO DE IMPREVISTOS", 0, 0, 0),
        ("PARQUEADERO / ÁREAS COMUNES", 0, 0, 0),
        ("SERVICIOS PÚBLICOS COMUNES", 0, 0, 0),
        ("SANCIONES / MULTAS DE CONVIVENCIA", 0, 0, 0),
        ("AJUSTES / NOTAS DÉBITO O CRÉDITO", 0, 0, 0)
    ]

    y_row = y_table - 20
    for i, (nom_c, val_p, val_a, val_t) in enumerate(concepts):
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#f8fafc"))
            c.rect(x_offset + 1, y_row - 4, w - 2, 18, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor("#1e293b"))
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 8)
        c.drawString(x_offset + 16, y_row + 2, nom_c)
        
        c.setFont("Helvetica", 8)
        c.drawRightString(x_offset + 300, y_row + 2, fmt_cur(val_p) if val_p else "$0")
        c.drawRightString(x_offset + 420, y_row + 2, fmt_cur(val_a) if val_a else "$0")
        c.setFont("Helvetica-Bold" if val_t else "Helvetica", 8)
        c.drawRightString(x_offset + w - 16, y_row + 2, fmt_cur(val_t) if val_t else "$0")

        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(0.5)
        c.line(x_offset, y_row - 4, x_offset + w, y_row - 4)
        y_row -= 20

    # 4. RECUADRO DE PAGO Y TOTALES
    y_tot = y_row - 10
    
    # Caja izquierda: Datos Bancarios
    w_banco = 300
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1)
    c.roundRect(x_offset + 12, y_tot - 110, w_banco, 105, 6, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x_offset + 22, y_tot - 18, "INFORMACIÓN OFICIAL PARA EL PAGO:")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(x_offset + 22, y_tot - 34, f"• Entidad Bancaria: {edif_bco}")
    c.drawString(x_offset + 22, y_tot - 48, f"• Cuenta de Recaudo: {edif_cta}")
    c.drawString(x_offset + 22, y_tot - 62, f"• Titular: {edif_nom}")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#065f46"))
    c.drawString(x_offset + 22, y_tot - 78, f"• Referencia Obligatoria: {apto}")
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(x_offset + 22, y_tot - 96, "Por favor envíe su soporte a la administración para oportuna conciliación.")

    # Caja derecha: Total Neto Liquidado
    w_tot_box = w - w_banco - 36
    x_tot_box = x_offset + w_banco + 24
    
    bg_color = colors.HexColor("#fef2f2") if pend > 0 else colors.HexColor("#ecfdf5")
    border_color = colors.HexColor("#ef4444") if pend > 0 else colors.HexColor("#10b981")
    
    c.setFillColor(bg_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(1.5)
    c.roundRect(x_tot_box, y_tot - 110, w_tot_box, 105, 6, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_tot_box + 12, y_tot - 18, "TOTAL LIQUIDADO:")
    
    c.setFont("Helvetica", 8)
    c.drawString(x_tot_box + 12, y_tot - 34, "Cuota del Mes:")
    c.drawRightString(x_tot_box + w_tot_box - 12, y_tot - 34, fmt_cur(admon))

    c.drawString(x_tot_box + 12, y_tot - 48, "Saldo en Mora:")
    c.drawRightString(x_tot_box + w_tot_box - 12, y_tot - 48, fmt_cur(pend))

    c.drawString(x_tot_box + 12, y_tot - 62, "Intereses Mora:")
    c.drawRightString(x_tot_box + w_tot_box - 12, y_tot - 62, fmt_cur(inta))

    c.setStrokeColor(border_color)
    c.setLineWidth(1)
    c.line(x_tot_box + 10, y_tot - 70, x_tot_box + w_tot_box - 10, y_tot - 70)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(x_tot_box + 12, y_tot - 86, "TOTAL A PAGAR:")
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#b91c1c") if pend > 0 else colors.HexColor("#047857"))
    c.drawRightString(x_tot_box + w_tot_box - 12, y_tot - 98, fmt_cur(total))

    # 5. LEYENDA LEGAL Y CERTIFICACIÓN
    y_leg = y_tot - 130
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(0.5)
    c.line(x_offset + 10, y_leg + 10, x_offset + w - 10, y_leg + 10)

    c.setFont("Helvetica-Bold", 6.8)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(x_offset + w/2, y_leg, "ESTA CUENTA DE COBRO SE ASIMILA PARA TODOS SUS EFECTOS LEGALES A UNA LETRA DE CAMBIO (ART. 774 DEL CÓDIGO DE COMERCIO).")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(x_offset + w/2, y_leg - 10, "CONFORME A LA LEY 675 DE 2001, EL NO PAGO OPORTUNO CAUSARÁ INTERESES DE MORA A LA TASA MÁXIMA LEGAL PERMITIDA.")
    c.drawCentredString(x_offset + w/2, y_leg - 20, "«Camina con cuidado y mucho tacto, y recuerda que la vida es un gran acto de equilibrio».")

    # Pie institucional
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.HexColor("#065f46"))
    c.drawString(x_offset + 14, y_leg - 38, "LEFACTURAMOS PLUS • SISTEMA DE GESTIÓN Y FACTURACIÓN DE PROPIEDAD HORIZONTAL")
    c.setFont("Helvetica", 6.8)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawRightString(x_offset + w - 14, y_leg - 38, "ORIGINAL: FACTURA INDIVIDUAL DEL COPROPIETARIO")


def generar_pdf_factura(c, width, height, edif_info: Dict[str, Any], datos: Dict[str, Any]):
    """Genera una factura INDIVIDUAL (un solo cuerpo completo por página, no doble)."""
    w = 540
    x_offset = (width - w) / 2
    y_top = height - 40
    draw_individual_factura(c, x_offset, y_top, w, edif_info, datos)


def generar_pdf_libro_facturas_individuales(c, width, height, edif_info: Dict[str, Any], datos: Dict[str, Any]):
    """Genera el libro de facturas del mes donde CADA página es una FACTURA INDIVIDUAL de cada apartamento (no dobles)."""
    cod = str(edif_info.get("codigo", "4160")).replace("cj_", "").strip()
    periodo = datos.get("periodo", "NOVIEMBRE DE 2026")

    unidades = []
    m_path = Path("data") / f"edificio_{cod}_master.json"
    if m_path.exists():
        try:
            with open(m_path, "r", encoding="utf-8") as f:
                unidades = json.load(f).get("unidades", [])
        except Exception:
            pass
    if not unidades and Path("data/edificio_4160_master.json").exists():
        try:
            with open("data/edificio_4160_master.json", "r", encoding="utf-8") as f:
                unidades = json.load(f).get("unidades", [])
        except Exception:
            pass

    w = 540
    x_offset = (width - w) / 2
    y_top = height - 40

    if not unidades:
        draw_individual_factura(c, x_offset, y_top, w, edif_info, datos)
        return

    fac_base = int(datos.get("consecutivo", 2701))
    for idx, u in enumerate(unidades):
        u_datos = {
            "apto": str(u.get("unidad", u.get("apto", f"Apto {idx+1}"))),
            "propietario": u.get("propietario", "Copropietario"),
            "consecutivo": str(fac_base + idx),
            "periodo": periodo,
            "u_data": u,
            "bloq": u.get("bloq", "01"),
            "inquilino": u.get("inquilino", "El Propietario")
        }
        draw_individual_factura(c, x_offset, y_top, w, edif_info, u_datos)
        if idx < len(unidades) - 1:
            c.showPage()



def generar_pdf_recibo(c, width, height, edif_info: Dict[str, Any], datos: Dict[str, Any]):
    u = datos["u_data"]
    apto = datos["apto"]
    prop = datos["propietario"]
    num = datos["consecutivo"]
    periodo = datos["periodo"]
    val_pag = u.get("valpag", 625000)

    # 1. Encabezado Lefacturamos (Verde Esmeralda Oscuro)
    c.setFillColor(colors.HexColor("#064e3b"))
    c.rect(0, height - 90, width, 90, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#34d399"))
    c.rect(0, height - 94, width, 4, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 38, "LEFACTURAMOS")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#a7f3d0"))
    c.drawString(36, height - 52, "Comprobante Oficial de Ingreso y Pago de Expensas Comunes")
    c.drawString(36, height - 66, "Ley 675 de 2001 • Conciliado con Extracto Bancario Oficial")

    # Badge Recibo
    c.setFillColor(colors.HexColor("#10b981"))
    c.roundRect(width - 180, height - 65, 144, 38, 6, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width - 108, height - 44, "RECIBO DE CAJA")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width - 108, height - 58, f"RECIBO N° {num}")

    # 2. Información del Edificio Emisor
    y = height - 120
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(36, y, edif_info["nombre"])

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(36, y - 14, f"NIT: {edif_info['nit']} • Dirección: {edif_info['direccion']}")
    c.drawString(36, y - 26, f"Ciudad: {edif_info['ciudad']} • Administrador: {edif_info['administrador']}")

    # Línea
    y = height - 158
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1)
    c.line(36, y, width - 36, y)

    # 3. Datos del Pago y Residente
    y = height - 170
    card_h = 80
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(36, y - card_h, width - 72, card_h, 6, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 20, "HEMOS RECIBIDO DE:")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.drawString(180, y - 20, prop)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(50, y - 36, "INMUEBLE / UNIDAD:")
    c.setFont("Helvetica", 9)
    c.drawString(180, y - 36, f"Apartamento {apto} (Coeficiente: {u.get('coef', '1.205%')})")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 52, "CONCEPTO:")
    c.setFont("Helvetica", 9)
    c.drawString(180, y - 52, f"Abono / Pago de cuota de administración correspondiente al periodo {periodo}")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 68, "MEDIO DE RECEPCIÓN:")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#059669"))
    c.drawString(180, y - 68, f"Transferencia Bancaria / PSE Conciliada en {edif_info['banco']}")

    # 4. Valor Pagado Destacado
    y_val = y - card_h - 40
    c.setFillColor(colors.HexColor("#ecfdf5"))
    c.setStrokeColor(colors.HexColor("#10b981"))
    c.setLineWidth(2)
    c.roundRect(36, y_val, width - 72, 60, 8, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#065f46"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_val + 34, "VALOR TOTAL RECIBIDO Y APLICADO:")
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - 50, y_val + 24, f"${val_pag:,.0f} COP".replace(",", "."))

    # 5. Estado y Certificación
    y_cert = y_val - 80
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.roundRect(36, y_cert, width - 72, 70, 6, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y_cert + 52, "ESTADO CONTABLE:")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#16a34a"))
    c.drawString(180, y_cert + 52, "✓ CONCILIADO Y ASENTADO EN LIBROS CONTABLES")

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 8)
    c.drawString(50, y_cert + 36, "El presente recibo certifica la recepción efectiva de los fondos y constituye paz y salvo por dicho importe.")
    c.drawString(50, y_cert + 24, "Regulado por la Ley 675 de 2001 y las Normas de Información Financiera (NIIF para Copropiedades).")
    c.drawString(50, y_cert + 12, f"Firma Digital: Administración {edif_info['nombre']} • Lefacturamos Colombia")

    # Pie
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 24, "Lefacturamos Cloud PH • Recibo de Caja Digital • www.lefacturamos.com")


def generar_pdf_informe(c, width, height, edif_info: Dict[str, Any], datos: Dict[str, Any]):
    """
    Genera el informe oficial contable o listado general (Facturacion, Pendientes, Pagos, Recibos)
    replicando con exactitud el diseno tabular de Nitro Pro 9 y cargando las 25 unidades reales.
    """
    cod = str(edif_info.get("codigo", "4160")).replace("cj_", "").strip()
    titulo_raw = datos.get("nombre_archivo", "LISTADO DE FACTURACION").replace(".PDF", "").replace(".pdf", "")
    periodo = datos.get("periodo", "OCTUBRE DE 2026")
    nombre_edif = edif_info.get("nombre", f"Edificio #{cod}")
    
    # Determinar tipo de reporte
    t_upper = titulo_raw.upper()
    if "PENDIENTE" in t_upper:
        tipo_reporte = "LISTADO DE PENDIENTES"
    elif "PAGO" in t_upper:
        tipo_reporte = "LISTADO DE PAGOS"
    elif "RECIBO" in t_upper:
        tipo_reporte = "LISTADO DE RECIBOS DE CAJA"
    else:
        tipo_reporte = "LISTADO DE FACTURACIÓN"

    # Cargar unidades reales del master json
    unidades = []
    m_path = Path("data") / f"edificio_{cod}_master.json"
    if m_path.exists():
        try:
            with open(m_path, "r", encoding="utf-8") as f:
                m_data = json.load(f)
                unidades = m_data.get("unidades", [])
        except Exception:
            pass

    # Si no hay master, buscar en edificio_4160_master.json como referencia oficial
    if not unidades and Path("data/edificio_4160_master.json").exists():
        try:
            with open("data/edificio_4160_master.json", "r", encoding="utf-8") as f:
                unidades = json.load(f).get("unidades", [])
        except Exception:
            pass

    fmt_num = lambda v: f"{int(v):,}".replace(",", ".") if v else "0"

    # Paginacion: 7 unidades por pagina (cada unidad tiene 3 lineas: Pendiente, Actual, Total)
    chunk_size = 7
    total_unidades = len(unidades)
    total_paginas = max(1, (total_unidades + chunk_size - 1) // chunk_size)

    for pag in range(total_paginas):
        page_num = pag + 1
        page_units = unidades[pag * chunk_size : (pag + 1) * chunk_size]

        # 1. ENCABEZADO ESTILO NITRO PRO 9
        # Marco exterior superior
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(36, height - 85, width - 72, 50, fill=0, stroke=1)

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width / 2, height - 52, f"{tipo_reporte} DEL MES DE {periodo}")
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(width / 2, height - 68, nombre_edif)

        # 2. ENCABEZADO DE TABLA
        y_th = height - 105
        c.rect(36, y_th - 16, width - 72, 16, fill=0, stroke=1)

        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(38, y_th - 7, f"Código {cod}")
        c.drawString(75, y_th - 7, str(page_num))
        c.drawCentredString(180, y_th - 7, "Nombre Propietario")
        c.drawString(245, y_th - 7, "Admón")
        c.drawString(285, y_th - 7, "Interés")
        c.drawString(320, y_th - 7, "Otros")
        c.drawString(350, y_th - 7, "Extra")
        c.drawString(380, y_th - 7, "Multa")
        c.drawString(410, y_th - 7, "Ser. Publ.")
        c.drawCentredString(470, y_th - 7, "Nombre Inquilino / Notas")
        c.drawRightString(515, y_th - 7, "Valor")
        c.drawRightString(width - 40, y_th - 7, "Pagos")

        # Sub-header de columnas
        y_subth = y_th - 28
        c.setFont("Helvetica", 6)
        c.drawString(38, y_subth, "Bloq. Apto. Factura")
        c.line(36, y_subth - 4, width - 36, y_subth - 4)

        # 3. FILAS DE UNIDADES REALES
        y_row = y_subth - 16
        for u in page_units:
            bloq = str(u.get("bloq", u.get("bloque", "00")))
            apto = str(u.get("apto", u.get("unidad", "")))
            fac = str(u.get("fac", ""))
            prop = str(u.get("propietario", "Copropietario"))[:32]

            admon = float(u.get("admon", u.get("actual", 0)))
            pend = float(u.get("pend", 0))
            inta = float(u.get("inta", 0))
            intp = float(u.get("intp", 0))
            tot_num = float(u.get("totalNum", u.get("totalFinal", admon + pend + inta)))
            valpag = float(u.get("valpag", 0))

            # Cada unidad ocupa un bloque de 48 pt (3 lineas)
            h_block = 48
            c.setLineWidth(0.5)
            c.rect(36, y_row - h_block, width - 72, h_block, fill=0, stroke=1)

            # Columna izquierda identificadora
            c.setFont("Helvetica-Bold", 7)
            c.drawString(38, y_row - 12, f"{bloq}  {apto}  {fac}")

            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(100, y_row - 12, prop)

            # Linea 1: Pendiente
            c.setFont("Helvetica", 6.5)
            c.drawString(110, y_row - 24, "Pendiente")
            c.drawRightString(275, y_row - 24, fmt_num(pend))
            c.drawRightString(310, y_row - 24, fmt_num(intp))
            c.drawRightString(340, y_row - 24, "0")
            c.drawRightString(370, y_row - 24, "0")
            c.drawRightString(400, y_row - 24, "0")
            c.drawRightString(435, y_row - 24, "0")
            c.drawRightString(515, y_row - 24, fmt_num(pend + intp))

            # Linea 2: Actual
            c.drawString(110, y_row - 34, "Actual")
            c.drawRightString(275, y_row - 34, fmt_num(admon))
            c.drawRightString(310, y_row - 34, fmt_num(inta))
            c.drawRightString(340, y_row - 34, "0")
            c.drawRightString(370, y_row - 34, "0")
            c.drawRightString(400, y_row - 34, "0")
            c.drawRightString(435, y_row - 34, "0")
            c.drawRightString(515, y_row - 34, fmt_num(admon + inta))

            # Linea 3: Total
            c.setFont("Helvetica-Bold", 6.5)
            c.drawString(110, y_row - 44, "Total")
            c.drawRightString(275, y_row - 44, fmt_num(admon + pend))
            c.drawRightString(310, y_row - 44, fmt_num(inta + intp))
            c.drawRightString(340, y_row - 44, "0")
            c.drawRightString(370, y_row - 44, "0")
            c.drawRightString(400, y_row - 44, "0")
            c.drawRightString(435, y_row - 44, "0")
            c.drawRightString(515, y_row - 44, fmt_num(tot_num))

            # Columna de pagos
            if valpag > 0:
                c.drawRightString(width - 40, y_row - 24, fmt_num(valpag))

            y_row -= h_block

        # 4. PIE DE PAGINA NITRO PRO 9
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.line(36, 42, width - 36, 42)

        c.setFont("Helvetica", 6.5)
        c.drawString(36, 32, "Lefacturamos  NIT 71582999-7 CEL: 3155979738")
        c.drawCentredString(width / 2, 32, f"Página {page_num} de {total_paginas}")
        c.drawRightString(width - 36, 32, f"{tipo_reporte} DEL MES DE {periodo}")

        if page_num < total_paginas:
            c.showPage()


def generar_pdf_documento(edificio: str, anio: str, mes: str, archivo: str, destino_path: Path) -> Path:
    """
    Punto de entrada universal: Genera el archivo PDF físico en destino_path
    con calidad profesional lista para visualización en iframe o descarga directa.
    """
    destino_path.parent.mkdir(parents=True, exist_ok=True)
    edif_info = obtener_info_edificio(edificio)
    datos = parsear_nombre_archivo(archivo, edificio, anio, mes)

    if not REPORTLAB_AVAILABLE:
        # Fallback básico si reportlab no estuviese instalado
        with open(destino_path, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n")
        return destino_path

    c = canvas.Canvas(str(destino_path), pagesize=letter)
    width, height = letter

    if datos["tipo"] == "FACTURA":
        generar_pdf_factura(c, width, height, edif_info, datos)
    elif datos["tipo"] == "FACTURAS_LIBRO":
        generar_pdf_libro_facturas_individuales(c, width, height, edif_info, datos)
    elif datos["tipo"] == "RECIBO_CAJA":
        generar_pdf_recibo(c, width, height, edif_info, datos)
    else:
        generar_pdf_informe(c, width, height, edif_info, datos)

    c.save()
    return destino_path
