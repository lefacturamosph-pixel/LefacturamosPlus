#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEFACTURAMOS - Generador de Plantillas Oficiales de Excel
Crea las 6 plantillas estandarizadas para alimentar la plataforma:
1. Facturación y Cartera (con la fórmula exacta SSxxxx + CAMPO_FAC)
2. Unidades y Coeficientes (Ley 675)
3. Propietarios y Residentes
4. Pagos a Proveedores de Administración
5. Zonas Comunes y Reservas
6. Registro de Mascotas
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_DIR = r"c:\Users\CARLOS\LefacturamosApp\PLANTILLAS_OFICIALES"
os.makedirs(OUT_DIR, exist_ok=True)

# Estilos corporativos LEFACTURAMOS
HEADER_FILL_PRIMARY = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid") # Esmeralda oscuro
HEADER_FILL_SECONDARY = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Pizarra
HEADER_FILL_ACCENT = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid") # Teal
HEADER_FILL_CALC = PatternFill(start_color="047857", end_color="047857", fill_type="solid") # Verde esmeralda cálculo

HEADER_FONT = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Segoe UI", size=13, bold=True, color="065F46")
SUBTITLE_FONT = Font(name="Segoe UI", size=9, italic=True, color="475569")
DATA_FONT = Font(name="Segoe UI", size=10, color="0F172A")
BOLD_DATA_FONT = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
TOTAL_FONT = Font(name="Segoe UI", size=11, bold=True, color="065F46")

THIN_BORDER = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)
TOTAL_BORDER = Border(
    top=Side(style='thin', color='065F46'),
    bottom=Side(style='double', color='065F46')
)

def ajustar_anchos(ws, max_cols=30):
    for col in range(1, max_cols + 1):
        col_letter = get_column_letter(col)
        max_len = 0
        for row in range(1, ws.max_row + 1):
            val = ws.cell(row=row, column=col).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

# ==============================================================================
# 1. PLANTILLA FACTURACIÓN Y CARTERA (SSxxxx + CAMPO_FAC)
# ==============================================================================
def crear_plantilla_facturacion():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Facturacion_y_Cartera"

    # Encabezado informativo
    ws.merge_cells("A1:W1")
    ws["A1"] = "LEFACTURAMOS - PLANTILLA OFICIAL DE FACTURACIÓN Y CARTERA (FORMATO SSxxxx + CAMPO_FAC)"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:W2")
    ws["A2"] = "Estructura calculada: PEND+ACTUAL=Admón | INTP+INTA=Interés | OTROSP+OTROSA=Otros | EXTRAP+EXTRAA=Extra | MULTAP+MULTAA=Multa | SERPUP+SERPUA=Ser_Pub | SERVIP+SERVIA=Ser_Serv | NDNCP+NDNCA=Notas_d_c"
    ws["A2"].font = SUBTITLE_FONT

    # Subencabezados agrupadores (Fila 4)
    ws.merge_cells("A4:C4")
    ws["A4"] = "DATOS INMUEBLE"
    ws["A4"].fill = HEADER_FILL_SECONDARY
    ws["A4"].font = HEADER_FONT
    ws["A4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("D4:K4")
    ws["D4"] = "SALDOS PENDIENTES (ANTERIORES)"
    ws["D4"].fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid") # Rojo oscuro
    ws["D4"].font = HEADER_FONT
    ws["D4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("L4:S4")
    ws["L4"] = "COBRO DEL MES (ACTUAL)"
    ws["L4"].fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Azul oscuro
    ws["L4"].font = HEADER_FONT
    ws["L4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("T4:AA4")
    ws["T4"] = "TOTALES LIQUIDADOS POR CONCEPTO (CAMPO_FAC)"
    ws["T4"].fill = HEADER_FILL_CALC
    ws["T4"].font = HEADER_FONT
    ws["T4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("AB4:AC4")
    ws["AB4"] = "LIQUIDACIÓN FINAL"
    ws["AB4"].fill = HEADER_FILL_PRIMARY
    ws["AB4"].font = HEADER_FONT
    ws["AB4"].alignment = Alignment(horizontal="center")

    # Fila 5: Nombres de columnas
    cols = [
        # Inmueble
        ("BLOQ", "Bloque / Torre"),
        ("APTO", "Apartamento / Local"),
        ("FAC", "No. Factura"),
        # Saldos Pendientes
        ("PEND", "PEND (Admón Ant)"),
        ("INTP", "INTP (Interés Mora Ant)"),
        ("OTROSP", "OTROSP (Otros Pend)"),
        ("EXTRAP", "EXTRAP (Extra Pend)"),
        ("MULTAP", "MULTAP (Multa Pend)"),
        ("SERPUP", "SERPUP (Ser_Pub Pend)"),
        ("SERVIP", "SERVIP (Ser_Serv Pend)"),
        ("NDNCP", "NDNCP (Notas D/C Pend)"),
        # Cobro del mes
        ("ACTUAL", "ACTUAL (Admón Mes)"),
        ("INTA", "INTA (Interés Mes)"),
        ("OTROSA", "OTROSA (Otros Mes)"),
        ("EXTRAA", "EXTRAA (Extra Mes)"),
        ("MULTAA", "MULTAA (Multa Mes)"),
        ("SERPUA", "SERPUA (Ser_Pub Mes)"),
        ("SERVIA", "SERVIA (Ser_Serv Mes)"),
        ("NDNCA", "NDNCA (Notas D/C Mes)"),
        # Totales según CAMPO_FAC (fila 2 de CAMPO_FAC)
        ("T_ADMON", "Admón (PEND+ACTUAL)"),
        ("T_INTERES", "Interés (INTP+INTA)"),
        ("T_OTROS", "Otros (OTROSP+OTROSA)"),
        ("T_EXTRA", "Extra (EXTRAP+EXTRAA)"),
        ("T_MULTA", "Multa (MULTAP+MULTAA)"),
        ("T_SER_PUB", "Ser_Pub (SERPUP+SERPUA)"),
        ("T_SER_SERV", "Ser_Serv (SERVIP+SERVIA)"),
        ("T_NOTAS_DC", "Notas_d_c (NDNCP+NDNCA)"),
        # Final
        ("TOTAL_A_PAGAR", "TOTAL FINAL A PAGAR"),
        ("ESTADO_PAGO", "Estado (Pendiente/Al Día)")
    ]

    for col_idx, (col_id, col_name) in enumerate(cols, start=1):
        cell = ws.cell(row=5, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if col_idx <= 3:
            cell.fill = HEADER_FILL_SECONDARY
        elif col_idx <= 11:
            cell.fill = PatternFill(start_color="B91C1C", end_color="B91C1C", fill_type="solid")
        elif col_idx <= 19:
            cell.fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
        elif col_idx <= 27:
            cell.fill = HEADER_FILL_CALC
        else:
            cell.fill = HEADER_FILL_PRIMARY

    # Fila de ejemplo 1
    sample_1 = [
        "00", "0301", 3889,
        590810, 5700, 0, 0, 0, 0, 0, 0,
        329800, 12800, 0, 0, 0, 0, 0, 0,
        "=D6+L6", "=E6+M6", "=F6+N6", "=G6+O6", "=H6+P6", "=I6+Q6", "=J6+R6", "=K6+S6",
        "=SUM(T6:AA6)", "Pendiente"
    ]
    # Fila de ejemplo 2 (Al día)
    sample_2 = [
        "00", "0302", 3890,
        0, 0, 0, 0, 0, 0, 0, 0,
        224500, 0, 0, 0, 0, 0, 0, 0,
        "=D7+L7", "=E7+M7", "=F7+N7", "=G7+O7", "=H7+P7", "=I7+Q7", "=J7+R7", "=K7+S7",
        "=SUM(T7:AA7)", "Al Día"
    ]

    for r_idx, sample in enumerate([sample_1, sample_2], start=6):
        for c_idx, val in enumerate(sample, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx >= 4 and c_idx <= 28:
                cell.number_format = '"$"#,##0'
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="center")

    # Fila de Totales Generales
    ws.cell(row=8, column=1, value="TOTAL GENERAL EDIFICIO").font = TOTAL_FONT
    ws.merge_cells("A8:C8")
    for c_idx in range(4, 29):
        col_let = get_column_letter(c_idx)
        cell = ws.cell(row=8, column=c_idx, value=f"=SUM({col_let}6:{col_let}7)")
        cell.font = TOTAL_FONT
        cell.border = TOTAL_BORDER
        cell.number_format = '"$"#,##0'
        cell.alignment = Alignment(horizontal="right")

    ajustar_anchos(ws, max_cols=29)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_1_FACTURACION_Y_CARTERA_LEFACTURAMOS.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

# ==============================================================================
# 2. PLANTILLA UNIDADES Y COEFICIENTES (Ley 675)
# ==============================================================================
def crear_plantilla_unidades():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Unidades_y_Coeficientes"

    ws.merge_cells("A1:K1")
    ws["A1"] = "LEFACTURAMOS - PLANTILLA OFICIAL DE UNIDADES Y COEFICIENTES (LEY 675 DE 2001)"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:K2")
    ws["A2"] = "La suma de los coeficientes del edificio o conjunto residencial debe sumar exactamente 100.0000% según la Ley 675."
    ws["A2"].font = SUBTITLE_FONT

    cols = [
        "Torre / Bloque", "Número Unidad", "Tipo Inmueble (Apto/Local/Oficina/Casa)",
        "Coeficiente Apartamento (%)", "Coeficiente Parqueadero (%)", "Coeficiente Cuarto Útil (%)",
        "Coeficiente Total Unidad (%)", "Área Privada (m²)", "No. Parqueadero", "No. Cuarto Útil", "Matrícula Inmobiliaria"
    ]

    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_PRIMARY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    samples = [
        ["00", "0301", "Apartamento", 2.588000, 0.000000, 0.000000, "=D5+E5+F5", 85.40, "P-12", "CU-04", "001-123456"],
        ["00", "0302", "Apartamento", 1.947000, 0.000000, 0.000000, "=D6+E6+F6", 64.20, "P-13", "CU-05", "001-123457"],
    ]

    for r_idx, s in enumerate(samples, start=5):
        for c_idx, val in enumerate(s, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx in [4, 5, 6, 7]:
                cell.number_format = '0.0000"%"'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 8:
                cell.number_format = '0.00'
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="center")

    # Fila de validación 100%
    ws.cell(row=7, column=1, value="SUMA COEFICIENTES (Validación Ley 675)").font = TOTAL_FONT
    ws.merge_cells("A7:C7")
    for c_idx in [4, 5, 6, 7]:
        col_let = get_column_letter(c_idx)
        cell = ws.cell(row=7, column=c_idx, value=f"=SUM({col_let}5:{col_let}6)")
        cell.font = TOTAL_FONT
        cell.border = TOTAL_BORDER
        cell.number_format = '0.0000"%"'
        cell.alignment = Alignment(horizontal="right")

    ajustar_anchos(ws, max_cols=11)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_2_UNIDADES_Y_COEFICIENTES_LEFACTURAMOS.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

# ==============================================================================
# 3. PLANTILLA PROPIETARIOS Y RESIDENTES
# ==============================================================================
def crear_plantilla_propietarios():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Propietarios_y_Residentes"

    ws.merge_cells("A1:J1")
    ws["A1"] = "LEFACTURAMOS - DIRECTORIO OFICIAL DE PROPIETARIOS Y RESIDENTES"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:J2")
    ws["A2"] = "Permite registrar propietarios, arrendatarios y contactos principales con validación de celular para notificaciones WhatsApp y Push."
    ws["A2"].font = SUBTITLE_FONT

    cols = [
        "Torre / Bloque", "Número Unidad", "Rol (Propietario / Residente / Inquilino)",
        "Tipo Documento (CC / NIT / CE / Pasaporte)", "Número Documento",
        "Nombres y Apellidos Completos", "Celular / WhatsApp (10 dígitos)",
        "Correo Electrónico (Facturación)", "Clave Inicial Acceso App", "Es Contacto Principal (SÍ / NO)"
    ]

    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_PRIMARY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    samples = [
        ["00", "0301", "Propietario", "CC", "43562219", "JESUS EMILIO MONSALVE", "3001234567", "edificiomanchesteraptos@gmail.com", "1234", "SÍ"],
        ["00", "0302", "Propietario", "CC", "79845120", "CARLOS ALBERTO SÁNCHEZ", "3159876543", "carlos.sanchez@ejemplo.com", "1234", "SÍ"],
    ]

    for r_idx, s in enumerate(samples, start=5):
        for c_idx, val in enumerate(s, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center" if c_idx in [1, 2, 3, 4, 9, 10] else "left")

    ajustar_anchos(ws, max_cols=10)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_3_PROPIETARIOS_Y_RESIDENTES_LEFACTURAMOS.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

# ==============================================================================
# 4. PLANTILLA PAGOS A PROVEEDORES (ADMINISTRACIÓN)
# ==============================================================================
def crear_plantilla_pagos_proveedores():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pagos_Proveedores"

    ws.merge_cells("A1:H1")
    ws["A1"] = "LEFACTURAMOS - REGISTRO DE PAGOS DE ADMINISTRACIÓN A PROVEEDORES Y CONTRATISTAS"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:H2")
    ws["A2"] = "El Administrador registra cada pago realizado a empresas contratistas: detalle del trabajo ejecutado, garantías, fecha y soportes."
    ws["A2"].font = SUBTITLE_FONT

    cols = [
        "Empresa Proveedora / Contratista", "NIT / Cédula Proveedor", "Concepto / Detalle de la Labor Ejecutada",
        "Garantía del Trabajo (Meses o Fecha Límite)", "Fecha del Pago (AAAA-MM-DD)",
        "Valor Pagado (COP)", "Medio / Banco de Pago (Transferencia / Cheque / Bre-B)", "No. Factura o Cuenta de Cobro"
    ]

    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_PRIMARY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    samples = [
        ["Ascensores Schindler Andino S.A.", "860.005.123-4", "Mantenimiento preventivo mensual de 2 torres de ascensores", "Garantía 12 meses", "2026-10-05", 1450000, "Transferencia Bancolombia", "FAC-98412"],
        ["Seguridad Privada Segurcol Ltda", "900.124.555-8", "Servicio de vigilancia y control de acceso 24/7 mes de Octubre", "Póliza de Cumplimiento No. 44521", "2026-10-02", 4800000, "Transferencia AV-Villas", "FAC-11029"],
        ["Impermeabilizaciones y Cubiertas SAS", "901.442.118-2", "Reparación de filtración en terraza comunal y pergola", "Garantía 24 meses por escrito", "2026-09-28", 920000, "PSE Wompi", "CC-045"]
    ]

    for r_idx, s in enumerate(samples, start=5):
        for c_idx, val in enumerate(s, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx == 6:
                cell.number_format = '"$"#,##0'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [2, 5, 8]:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

    # Total pagado
    ws.cell(row=8, column=1, value="TOTAL PAGOS A PROVEEDORES").font = TOTAL_FONT
    ws.merge_cells("A8:E8")
    cell_tot = ws.cell(row=8, column=6, value="=SUM(F5:F7)")
    cell_tot.font = TOTAL_FONT
    cell_tot.border = TOTAL_BORDER
    cell_tot.number_format = '"$"#,##0'
    cell_tot.alignment = Alignment(horizontal="right")

    ajustar_anchos(ws, max_cols=8)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_4_PAGOS_A_PROVEEDORES_ADMINISTRACION.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

# ==============================================================================
# 5. PLANTILLA ZONAS COMUNES Y RESERVAS
# ==============================================================================
def crear_plantilla_zonas_comunes():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Zonas_Comunes_y_Reservas"

    ws.merge_cells("A1:I1")
    ws["A1"] = "LEFACTURAMOS - CATÁLOGO DE ZONAS COMUNES Y PARÁMETROS DE RESERVA"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:I2")
    ws["A2"] = "Configura todas las áreas comunes: Zonas Húmedas (Sauna, Jacuzzi, Turco), Salón Social, Canchas, Gimnasio, BBQ, Coworking, etc."
    ws["A2"].font = SUBTITLE_FONT

    cols = [
        "Nombre de la Zona Común", "Categoría (Zonas Húmedas / Deportes / Social / Coworking)",
        "Horario Apertura (HH:MM)", "Horario Cierre (HH:MM)", "Aforo / Capacidad Máxima (Personas)",
        "Tiempo Máximo por Reserva (Horas)", "Anticipación Mínima (Días)",
        "Cobro por Utilización (COP)", "Reglas de Uso y Condiciones"
    ]

    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_PRIMARY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    samples = [
        ["Zonas Húmedas (Sauna, Jacuzzi, Turco)", "Zonas Húmedas", "06:00", "21:00", 8, 2, 1, 0, "Uso obligatorio de traje de baño y gorro. Menores de 12 años con adulto."],
        ["Salón Social Principal", "Social", "09:00", "23:00", 80, 6, 3, 120000, "Depósito de aseo reembolsable. Música moderada después de las 22:00."],
        ["Cancha de Tenis", "Deportes", "06:00", "20:00", 4, 1.5, 1, 0, "Calzado deportivo de tenis obligatorio. Máximo 1 reserva activa por apto."],
        ["Cancha Múltiple", "Deportes", "07:00", "21:00", 15, 2, 1, 0, "Baloncesto, voleibol y microfútbol."],
        ["Cancha de Fútbol", "Deportes", "07:00", "21:00", 16, 2, 1, 0, "Calzado para césped sintético. No taches metálicos."],
        ["Gimnasio & Zona Cardio", "Deportes", "05:00", "22:00", 15, 1.5, 0, 0, "Uso de toalla obligatorio. Limpieza de máquinas al terminar."],
        ["BBQ y Pérgola", "Social", "10:00", "20:00", 25, 4, 2, 50000, "Entrega de carbón por cuenta del usuario. Dejar parrilla limpia."],
        ["Piscina Climatizada", "Zonas Húmedas", "08:00", "19:00", 20, 2, 0, 0, "Ducha previa obligatoria. Prohibido alimentos y envases de vidrio."],
        ["Salón de Juegos", "Social", "10:00", "21:00", 20, 2, 0, 0, "Mesa de billar, tenis de mesa y juegos de mesa."],
        ["Cine / Sala Multimedia", "Social", "14:00", "22:00", 25, 3, 2, 30000, "Proyección de películas familiares y eventos deportivos."],
        ["Sala Coworking & Sala de Juntas", "Coworking", "07:00", "20:00", 12, 3, 1, 0, "Internet de alta velocidad y pantalla HDMI para presentaciones."],
    ]

    for r_idx, s in enumerate(samples, start=5):
        for c_idx, val in enumerate(s, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx == 8:
                cell.number_format = '"$"#,##0'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [3, 4, 5, 6, 7]:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

    ajustar_anchos(ws, max_cols=9)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_5_ZONAS_COMUNES_Y_RESERVAS.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

# ==============================================================================
# 6. PLANTILLA REGISTRO DE MASCOTAS
# ==============================================================================
def crear_plantilla_mascotas():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Censo_Mascotas"

    ws.merge_cells("A1:K1")
    ws["A1"] = "LEFACTURAMOS - CENSO Y REGISTRO OFICIAL DE MASCOTAS DEL CONJUNTO"
    ws["A1"].font = TITLE_FONT

    ws.merge_cells("A2:K2")
    ws["A2"] = "Registro obligatorio conforme a la Ley 675 y el Código Nacional de Convivencia: vacunación, identificación y razas especiales."
    ws["A2"].font = SUBTITLE_FONT

    cols = [
        "Torre / Bloque", "Apartamento / Local", "Propietario / Tenedor Responsable",
        "Nombre de la Mascota", "Tipo / Especie (Perro / Gato / Otro)", "Raza",
        "Sexo (Macho / Hembra)", "Color Principal", "Fecha de Nacimiento (AAAA-MM-DD)",
        "Identificación / Microchip", "Vacunas al Día (SÍ / NO)", "Observaciones / Póliza RPA"
    ]

    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=4, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_PRIMARY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    samples = [
        ["00", "0301", "Jesus Emilio Monsalve", "Rocky", "Perro", "Golden Retriever", "Macho", "Dorado", "2021-04-15", "CHIP-9840012", "SÍ", "Carné de vacunación al día. Comportamiento dócil."],
        ["00", "0302", "Carlos Alberto Sánchez", "Misi", "Gato", "Siamés", "Hembra", "Blanco y Café", "2022-08-10", "N/A", "SÍ", "Esterilizada. Permanece al interior del apartamento."],
    ]

    for r_idx, s in enumerate(samples, start=5):
        for c_idx, val in enumerate(s, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            if c_idx in [1, 2, 5, 7, 9, 10, 11]:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

    ajustar_anchos(ws, max_cols=12)
    filepath = os.path.join(OUT_DIR, "PLANTILLA_6_REGISTRO_MASCOTAS.xlsx")
    wb.save(filepath)
    print(f"[OK] Creada plantilla: {filepath}")

if __name__ == "__main__":
    print("=" * 70)
    print(" GENERADOR DE PLANTILLAS OFICIALES LEFACTURAMOS")
    print("=" * 70)
    crear_plantilla_facturacion()
    crear_plantilla_unidades()
    crear_plantilla_propietarios()
    crear_plantilla_pagos_proveedores()
    crear_plantilla_zonas_comunes()
    crear_plantilla_mascotas()
    print("=" * 70)
    print(f"[ÉXITO] Todas las plantillas fueron generadas en: {OUT_DIR}")
