#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS PLUS - SERVICIO DE ESTUDIO DE CUENTA HISTÓRICO MULTIANUAL POR COPROPIETARIO
========================================================================================
Permite compilar, consultar y exportar la trazabilidad cronológica mes a mes (meses y años)
de cada copropietario desde las tablas contables oficiales SS*.DBF de DBPlus.
"""

import os
import glob
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from dbplus_service import read_dbf_binary
except ImportError:
    read_dbf_binary = None

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    if (BASE_DIR / "data").exists():
        DATA_DIR = BASE_DIR / "data"
    elif Path(r"C:\Users\CARLOS\LefacturamosApp\data").exists():
        DATA_DIR = Path(r"C:\Users\CARLOS\LefacturamosApp\data")
    else:
        DATA_DIR = BASE_DIR / "data"
else:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"

DBPLUS_BASE = Path(r"C:\dbplus")

MESES_NOMBRES = {
    "01": "ENERO", "02": "FEBRERO", "03": "MARZO", "04": "ABRIL",
    "05": "MAYO", "06": "JUNIO", "07": "JULIO", "08": "AGOSTO",
    "09": "SEPTIEMBRE", "10": "OCTUBRE", "11": "NOVIEMBRE", "12": "DICIEMBRE"
}

def resolver_carpeta_dbplus(codigo: str) -> Optional[Path]:
    clean_cod = str(codigo).replace("cj_", "").strip()
    candidatos = [
        DBPLUS_BASE / clean_cod,
        DBPLUS_BASE / clean_cod.zfill(4),
        DBPLUS_BASE / clean_cod.upper(),
        DBPLUS_BASE / clean_cod.lower(),
    ]
    for c in candidatos:
        if c.exists() and c.is_dir():
            return c
    return None

def compilar_historico_edificio(codigo: str) -> Dict[str, Any]:
    clean_cod = str(codigo).replace("cj_", "").strip()
    folder = resolver_carpeta_dbplus(clean_cod)
    
    # Intentar cargar master para datos del edificio y copropietarios
    master_path = DATA_DIR / f"edificio_{clean_cod}_master.json"
    if not master_path.exists():
        master_path = DATA_DIR / f"edificio_{clean_cod.zfill(4)}_master.json"
    
    edificio_info = {"codigo": clean_cod, "nombre": f"EDIFICIO {clean_cod}"}
    unidades_master = {}
    if master_path.exists():
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                master_data = json.load(f)
                if "edificio" in master_data and master_data["edificio"]:
                    edificio_info = master_data["edificio"]
                elif "nombre" in master_data:
                    edificio_info["nombre"] = master_data["nombre"]
                for u in master_data.get("unidades", []):
                    u_apto = str(u.get("apto") or u.get("unidad") or "").strip()
                    if u_apto:
                        unidades_master[u_apto] = u
                        unidades_master[u_apto.lstrip("0")] = u
                        unidades_master[u_apto.zfill(4)] = u
        except Exception as e:
            print(f"Aviso leyendo master {master_path}: {e}")

    historico_por_apto: Dict[str, List[Dict[str, Any]]] = {}

    if folder and folder.exists() and read_dbf_binary:
        # Buscar todos los archivos SSyymm.DBF ordenados a partir de Diciembre 2023 (SS2312)
        ss_entries = []
        try:
            for entry in os.listdir(folder):
                e_up = entry.upper()
                if e_up.startswith("SS") and e_up.endswith(".DBF") and len(e_up) == 10:
                    stem = e_up[:-4]
                    # Excluir archivo de saldo actual general del edificio como SS4901.DBF, SS7480.DBF, etc.
                    if stem == f"SS{clean_cod.zfill(4)}" or stem == f"SS{clean_cod}":
                        continue
                    yy = stem[2:4]
                    mm = stem[4:6]
                    if yy.isdigit() and mm.isdigit():
                        m_int = int(mm)
                        if 1 <= m_int <= 12:
                            y_int = int(yy)
                            anio = 2000 + y_int if y_int < 70 else 1900 + y_int
                            ss_entries.append((anio, m_int, mm, folder / entry))
        except Exception as e_scan:
            print(f"Error escaneando carpeta {folder}: {e_scan}")

        # Ordenar cronológicamente por (año, mes)
        ss_entries.sort(key=lambda x: (x[0], x[1]))

        for anio, m_int, mm, fpath in ss_entries:
            mes_nom = MESES_NOMBRES.get(mm, f"MES {mm}")
            periodo_label = f"{mes_nom} {anio}"
            periodo_iso = f"{anio}-{mm}"

            try:
                rows = read_dbf_binary(fpath)
            except Exception as e_read:
                print(f"Error leyendo {fpath}: {e_read}")
                continue

            for r in rows:
                apto = str(r.get("APTO", "")).strip()
                if not apto:
                    continue
                
                if apto not in historico_por_apto:
                    historico_por_apto[apto] = []

                pend = float(r.get("PEND", 0) or 0)
                intp = float(r.get("INTP", 0) or 0)
                extrap = float(r.get("EXTRAP", 0) or 0)
                otrosp = float(r.get("OTROSP", 0) or 0)
                multap = float(r.get("MULTAP", 0) or 0)
                serpup = float(r.get("SERPUP", 0) or 0)
                servip = float(r.get("SERVIP", 0) or 0)
                ndncp = float(r.get("NDNCP", 0) or 0)

                actual = float(r.get("ACTUAL", 0) or 0)
                inta = float(r.get("INTA", 0) or 0)
                extraa = float(r.get("EXTRAA", 0) or 0)
                otrosa = float(r.get("OTROSA", 0) or 0)
                multaa = float(r.get("MULTAA", 0) or 0)
                serpua = float(r.get("SERPUA", 0) or 0)
                servia = float(r.get("SERVIA", 0) or 0)
                ndnca = float(r.get("NDNCA", 0) or 0)

                valdesc = float(r.get("VALDESC", 0) or 0)
                valpag = float(r.get("VALPAG", 0) or 0)
                total = float(r.get("TOTAL", 0) or 0)
                fac = str(r.get("FAC", "")).strip()

                # Saldo anterior capital y demás conceptos causados previamente (excluye mora anterior)
                saldo_ant_capital = pend + extrap + otrosp + multap + serpup + servip + ndncp
                subtotal_pendiente_ant = saldo_ant_capital + intp

                # Cargos del mes por cuota ordinaria y conceptos adicionales del mes (excluye mora del mes)
                cargos_mes_capital = actual + extraa + otrosa + multaa + serpua + servia + ndnca
                subtotal_cobro_mes = cargos_mes_capital + inta

                historico_por_apto[apto].append({
                    "anio": anio,
                    "mes": mm,
                    "mes_nombre": mes_nom,
                    "periodo": periodo_label,
                    "periodo_iso": periodo_iso,
                    "fac": fac,
                    "bloq": str(r.get("BLOQ", "AP")).strip(),
                    # Conceptos anteriores consolidados y discriminados
                    "saldo_anterior": saldo_ant_capital,
                    "interes_anterior": intp,
                    "pend_puro": pend,
                    "extra_anterior": extrap,
                    "otros_anterior": otrosp,
                    "multa_anterior": multap,
                    "serpub_anterior": serpup,
                    "serv_anterior": servip,
                    "notas_anterior": ndncp,
                    "total_pendiente_ant": subtotal_pendiente_ant,
                    # Conceptos del mes consolidados y discriminados
                    "cuota_admon": cargos_mes_capital,
                    "actual_puro": actual,
                    "interes_mes": inta,
                    "extra_mes": extraa,
                    "cuota_extra": extraa,
                    "otros_mes": otrosa,
                    "multa_mes": multaa,
                    "serpub_mes": serpua,
                    "serv_mes": servia,
                    "notas_mes": ndnca,
                    "total_cobro_mes": subtotal_cobro_mes,
                    # Pagos, descuentos y saldo total (valores reales directos de DBPlus)
                    "valdesc": valdesc,
                    "valpag": valpag,
                    "total": total,
                    "novedad": str(r.get("NOVEDAD", "")).strip()
                })

    # Guardar en data/edificio_{clean_cod}_historico.json
    salida = {
        "codigo": clean_cod,
        "edificio": edificio_info,
        "unidades_master": {k: {"propietario": v.get("propietario"), "cc": v.get("cc"), "email": v.get("email"), "tel": v.get("telefono"), "coeficiente": v.get("coeficiente")} for k, v in unidades_master.items()},
        "total_aptos": len(historico_por_apto),
        "historico_por_apto": historico_por_apto
    }

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        out_file = DATA_DIR / f"edificio_{clean_cod}_historico.json"
        with open(out_file, "w", encoding="utf-8") as f_out:
            json.dump(salida, f_out, ensure_ascii=False, indent=2)
        print(f"✅ Histórico compilado exitosamente: {out_file} ({len(historico_por_apto)} aptos)")
    except Exception as e_write:
        print(f"Aviso guardando JSON histórico: {e_write}")

    return salida


def obtener_estudio_cuenta_apto(codigo: str, apto_query: str, desde_periodo: Optional[str] = None, hasta_periodo: Optional[str] = None) -> Dict[str, Any]:
    clean_cod = str(codigo).replace("cj_", "").strip()
    apto_limpio = str(apto_query).strip()
    
    # 1. Verificar si existe JSON precompilado
    json_path = DATA_DIR / f"edificio_{clean_cod}_historico.json"
    data = None
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None
            
    # Si no existe JSON o está en entorno local con DBPlus, compilar/refrescar
    if not data or not data.get("historico_por_apto"):
        folder = resolver_carpeta_dbplus(clean_cod)
        if folder and folder.exists():
            data = compilar_historico_edificio(clean_cod)

    if not data:
        # Fallback vacío pero estructurado
        return {
            "codigo": clean_cod,
            "edificio": {"codigo": clean_cod, "nombre": f"Copropiedad {clean_cod}"},
            "apto": apto_limpio,
            "propietario": "Copropietario",
            "total_meses": 0,
            "meses": [],
            "resumen": {"total_facturado": 0, "total_pagado": 0, "saldo_actual": 0}
        }

    historico = data.get("historico_por_apto", {})
    unidades_master = data.get("unidades_master", {})
    edificio_info = data.get("edificio", {"codigo": clean_cod, "nombre": f"Edificio {clean_cod}"})

    # Buscar clave de apto (con o sin ceros a la izquierda)
    candidatos_apto = [
        apto_limpio,
        apto_limpio.zfill(4),
        apto_limpio.lstrip("0"),
        f"0{apto_limpio}",
    ]
    
    target_apto_key = None
    for cand in candidatos_apto:
        if cand in historico:
            target_apto_key = cand
            break
            
    if not target_apto_key:
        for k in historico.keys():
            if k.lstrip("0") == apto_limpio.lstrip("0") or apto_limpio in k:
                target_apto_key = k
                break

    meses = historico.get(target_apto_key, []) if target_apto_key else []
    info_u = unidades_master.get(target_apto_key or apto_limpio, {})

    # Filtrar por rango de fechas / periodo inicial si se solicita
    if desde_periodo or hasta_periodo:
        meses_filtrados = []
        for m in meses:
            p_iso = m.get("periodo_iso") or f"{m.get('anio')}-{str(m.get('mes')).zfill(2)}"
            if desde_periodo and p_iso < str(desde_periodo):
                continue
            if hasta_periodo and p_iso > str(hasta_periodo):
                continue
            meses_filtrados.append(m)
        meses = meses_filtrados

    # Calcular acumulados del periodo seleccionado
    total_facturado = sum(m.get("total_cobro_mes", 0) for m in meses)
    total_pagado = sum(m.get("valpag", 0) for m in meses)
    saldo_actual = meses[-1].get("total", 0) if meses else 0

    return {
        "codigo": clean_cod,
        "edificio": edificio_info,
        "apto": target_apto_key or apto_limpio,
        "propietario": info_u.get("propietario") or "Copropietario Registrado",
        "cc": info_u.get("cc") or "",
        "email": info_u.get("email") or "",
        "tel": info_u.get("tel") or "",
        "coeficiente": info_u.get("coeficiente") or "",
        "total_meses": len(meses),
        "meses": meses,
        "desde_periodo": desde_periodo,
        "hasta_periodo": hasta_periodo,
        "resumen": {
            "total_facturado": total_facturado,
            "total_pagado": total_pagado,
            "saldo_actual": saldo_actual
        }
    }


def generar_excel_tradicional_8conceptos(res: Dict[str, Any], codigo: str, apto: str) -> Path:
    """
    Genera un archivo Excel (.xlsx) con el formato histórico tradicional de Estado de Cuenta
    con los 8 conceptos contables oficiales de DBPlus y 3 filas por mes (Pendiente, Actual, Total).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    clean_cod = str(codigo).replace("cj_", "").strip()
    clean_apto = str(apto).strip()

    wb = Workbook()
    ws = wb.active
    ws.title = "Estado_de_Cuenta"
    ws.views.sheetView[0].showGridLines = True

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.35
    ws.page_margins.bottom = 0.35

    font_title = Font(name="Calibri", size=11, bold=True)
    font_bold = Font(name="Calibri", size=9, bold=True)
    font_regular = Font(name="Calibri", size=9)
    font_header = Font(name="Calibri", size=9, bold=True, color="000000")
    fill_header = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    nombre_edif = edif.get("nombre", f"EDIFICIO {clean_cod} P.H.")
    propietario = res.get("propietario", "Copropietario(a)")
    bloque = res.get("bloq", "AP") or "AP"
    predio_txt = f"{propietario}--Predio {clean_apto} BLO. {bloque}"

    headers = [
        "Mes / Periodo", "Factura", "Concepto", "Admón", "Interés", "Otros",
        "Extra", "Multa", "Ser. Publ.", "Ser./ Serv.", "Notas D/C", "Valor", "Pagos", "Notas/Desc."
    ]

    curr_row = 1
    num_fmt = "#,##0"

    def write_header_block(row_idx, page_num):
        # Fila 1: Título "Estado de Cuenta" combinado (Col A a D)
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=4)
        c_title = ws.cell(row=row_idx, column=1, value="Estado de Cuenta")
        c_title.font = font_title
        c_title.alignment = Alignment(horizontal="left", vertical="center")

        # Fila 2: Nombre de la Copropiedad combinado de Col B a K (Col 2 a 11) para que NUNCA se corte
        ws.merge_cells(start_row=row_idx+1, start_column=2, end_row=row_idx+1, end_column=11)
        c_edif = ws.cell(row=row_idx+1, column=2, value=nombre_edif)
        c_edif.font = font_title
        c_edif.alignment = Alignment(horizontal="left", vertical="center")

        # Fila 2: Número de Página a la derecha combinado en Col M a N (Col 13 a 14)
        ws.merge_cells(start_row=row_idx+1, start_column=13, end_row=row_idx+1, end_column=14)
        cell_pag = ws.cell(row=row_idx+1, column=13, value=f"Página {page_num}")
        cell_pag.font = font_bold
        cell_pag.alignment = Alignment(horizontal="right", vertical="center")

        # Fila 3: Predio y Propietario combinado de Col A a K (Col 1 a 11)
        ws.merge_cells(start_row=row_idx+2, start_column=1, end_row=row_idx+2, end_column=11)
        c_predio = ws.cell(row=row_idx+2, column=1, value=predio_txt)
        c_predio.font = font_bold
        c_predio.alignment = Alignment(horizontal="left", vertical="center")

        h_row = row_idx + 3
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=h_row, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_header
            cell.border = thin_border
            if col_idx in (1, 3):
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_idx == 2:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
        return h_row + 2

    page = 1
    curr_row = write_header_block(curr_row, page)
    items_on_page = 0

    for idx, m in enumerate(meses):
        if items_on_page >= 11:
            page += 1
            curr_row += 1
            curr_row = write_header_block(curr_row, page)
            items_on_page = 0

        periodo_label = m.get("periodo") or f"{m.get('mes_nombre', '')} de {m.get('anio')}"
        periodo_label = str(periodo_label).title()
        fac = m.get("fac") or ""

        # Conceptos Pendientes
        pend_admon = float(m.get("pend_puro", 0) or 0)
        pend_int = float(m.get("interes_anterior", 0) or 0)
        pend_otr = float(m.get("otros_anterior", 0) or 0)
        pend_ext = float(m.get("extra_anterior", 0) or 0)
        pend_mul = float(m.get("multa_anterior", 0) or 0)
        pend_sp = float(m.get("serpub_anterior", 0) or 0)
        pend_srv = float(m.get("serv_anterior", 0) or 0)
        pend_nd = float(m.get("notas_anterior", 0) or 0)
        val_pend = pend_admon + pend_int + pend_otr + pend_ext + pend_mul + pend_sp + pend_srv + pend_nd

        # Conceptos Actuales
        act_admon = float(m.get("actual_puro", 0) or 0)
        act_int = float(m.get("interes_mes", 0) or 0)
        act_otr = float(m.get("otros_mes", 0) or 0)
        act_ext = float(m.get("extra_mes", 0) or 0)
        act_mul = float(m.get("multa_mes", 0) or 0)
        act_sp = float(m.get("serpub_mes", 0) or 0)
        act_srv = float(m.get("serv_mes", 0) or 0)
        act_nd = float(m.get("notas_mes", 0) or 0)
        val_act = act_admon + act_int + act_otr + act_ext + act_mul + act_sp + act_srv + act_nd

        # Totales
        tot_admon = pend_admon + act_admon
        tot_int = pend_int + act_int
        tot_otr = pend_otr + act_otr
        tot_ext = pend_ext + act_ext
        tot_mul = pend_mul + act_mul
        tot_sp = pend_sp + act_sp
        tot_srv = pend_srv + act_srv
        tot_nd = pend_nd + act_nd
        val_tot = float(m.get("total", 0) or (tot_admon + tot_int + tot_otr + tot_ext + tot_mul + tot_sp + tot_srv + tot_nd))
        pagos = float(m.get("valpag", 0) or 0)
        desc = float(m.get("valdesc", 0) or 0)

        # 1. Fila Pendiente
        ws.cell(row=curr_row, column=1, value=periodo_label).font = font_bold
        if fac:
            c_fac = ws.cell(row=curr_row, column=2, value=str(fac))
            c_fac.font = font_regular
            c_fac.alignment = Alignment(horizontal="center")
        ws.cell(row=curr_row, column=3, value="Pendiente").font = font_regular

        row_vals_pend = [pend_admon, pend_int, pend_otr, pend_ext, pend_mul, pend_sp, pend_srv, pend_nd, val_pend]
        for c_idx, val in enumerate(row_vals_pend, start=4):
            c = ws.cell(row=curr_row, column=c_idx, value=val)
            c.number_format = num_fmt
            c.font = font_regular
            c.alignment = Alignment(horizontal="right")

        # 2. Fila Actual
        curr_row += 1
        ws.cell(row=curr_row, column=3, value="Actual").font = font_regular
        row_vals_act = [act_admon, act_int, act_otr, act_ext, act_mul, act_sp, act_srv, act_nd, val_act]
        for c_idx, val in enumerate(row_vals_act, start=4):
            c = ws.cell(row=curr_row, column=c_idx, value=val)
            c.number_format = num_fmt
            c.font = font_regular
            c.alignment = Alignment(horizontal="right")

        # 3. Fila Total
        curr_row += 1
        ws.cell(row=curr_row, column=3, value="Total").font = font_bold
        row_vals_tot = [tot_admon, tot_int, tot_otr, tot_ext, tot_mul, tot_sp, tot_srv, tot_nd, val_tot, pagos, desc]
        for c_idx, val in enumerate(row_vals_tot, start=4):
            c = ws.cell(row=curr_row, column=c_idx, value=val)
            c.number_format = num_fmt
            c.font = font_bold
            c.alignment = Alignment(horizontal="right")

        # 4. Fila separadora vacía
        curr_row += 2
        items_on_page += 1

    col_widths = {
        1: 20, 2: 12, 3: 12, 4: 12, 5: 12, 6: 12, 7: 12, 8: 12, 9: 11,
        10: 12, 11: 12, 12: 14, 13: 14, 14: 12
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    out_dir = DATA_DIR / "reportes_historicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"Estado_Cuenta_Tradicional_{clean_cod}_{clean_apto}.xlsx"
    try:
        wb.save(out_file)
    except PermissionError:
        import time
        ts = int(time.time()) % 100000
        out_file = out_dir / f"Estado_Cuenta_Tradicional_{clean_cod}_{clean_apto}_{ts}.xlsx"
        wb.save(out_file)
    return out_file


def generar_excel_historico(codigo: str, apto: str, tipo: str = "abogado", desde_periodo: Optional[str] = None, hasta_periodo: Optional[str] = None) -> Path:
    """
    Genera un archivo Excel profesional (.xlsx) con la liquidación detallada del estudio histórico.
    Soporta formato 'tradicional' (Estado de Cuenta con 8 conceptos) y 'abogado' (Cobro Judicial).
    Permite filtrar por periodo inicial ('desde_periodo', ej. '2024-01') o rango.
    """
    res = obtener_estudio_cuenta_apto(codigo, apto, desde_periodo=desde_periodo, hasta_periodo=hasta_periodo)
    tipo_str = str(tipo or "abogado").lower().strip()
    if tipo_str in ("tradicional", "estado_cuenta", "kardex", "copropietario_tradicional"):
        return generar_excel_tradicional_8conceptos(res, codigo, apto)

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.comments import Comment

    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    es_abogado = str(tipo).lower() == "abogado"

    wb = Workbook()
    ws = wb.active
    ws.title = "Cobro_Juridico" if es_abogado else "Estado_Cuenta"
    ws.views.sheetView[0].showGridLines = True

    # Configuración de página: HORIZONTAL (LANDSCAPE) y ajuste para que quepan todas las columnas en la página completa
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = 0.3
    ws.page_margins.right = 0.3
    ws.page_margins.top = 0.4
    ws.page_margins.bottom = 0.4

    # Estilos
    font_title = Font(name="Calibri", size=11, bold=True, color="000000")
    font_sub = Font(name="Calibri", size=9, bold=True, color="333333")
    font_header = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=9, bold=True)
    font_regular = Font(name="Calibri", size=9)
    font_notas = Font(name="Calibri", size=8.5, color="1E293B")
    fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    fill_meta = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # 1. Título principal centrado sobre toda la tabla (A1:I1 y A2:I2)
    ws["A1"] = "CERTIFICACIÓN DE DEUDA Y LIQUIDACIÓN DISCRIMINADA DE CRÉDITO PARA COBRO JUDICIAL" if es_abogado else "ESTADO DE CUENTA HISTÓRICO Y TRAZABILIDAD DE CARTERA"
    ws["A1"].font = font_title
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells("A1:I1")

    ws["A2"] = "(EXPEDIDO DE CONFORMIDAD CON EL ARTÍCULO 48 DE LA LEY 675 DE 2001 - PRESTA MÉRITO EJECUTIVO)" if es_abogado else "(INFORME CONTABLE DETALLADO DE PAGOS Y CUOTAS DE ADMINISTRACIÓN)"
    ws["A2"].font = font_sub
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells("A2:I2")

    # 2. Metadatos
    primer_mes = meses[0]["periodo"] if meses else ""
    ult_mes = meses[-1]["periodo"] if meses else ""
    periodo_txt = f"{len(meses)} MESES ({primer_mes} HASTA {ult_mes})"

    meta = [
        ("COPROPIEDAD (ACREEDORA):", edif.get("nombre", f"EDIFICIO {codigo}"), "NIT:", edif.get("nit", "901690778-9"), "CÓDIGO:", str(codigo)),
        ("DIRECCIÓN:", edif.get("direccion", "Medellín"), "CIUDAD:", edif.get("ciudad", "Medellín • Antioquia"), "ADMINISTRADOR:", edif.get("administrador", "ADMINISTRACIÓN")),
        ("DEMANDADO / PROPIETARIO:" if es_abogado else "COPROPIETARIO:", res.get("propietario", ""), "IDENTIFICACIÓN C.C./NIT:", str(res.get("cc", "")), "INMUEBLE / PREDIO:", f"APTO {res.get('apto', '')}"),
        ("COEFICIENTE:", str(res.get("coeficiente", "")), "TASA MORA:", edif.get("interesMora", "2.10% M.V."), "PERIODO LIQUIDADO:", periodo_txt)
    ]

    for idx, row_vals in enumerate(meta, start=4):
        ws.cell(row=idx, column=1, value=row_vals[0]).font = font_bold
        ws.cell(row=idx, column=2, value=row_vals[1]).font = font_regular
        ws.cell(row=idx, column=3, value=row_vals[2]).font = font_bold
        ws.cell(row=idx, column=4, value=row_vals[3]).font = font_regular
        ws.cell(row=idx, column=5, value=row_vals[4]).font = font_bold
        ws.cell(row=idx, column=6, value=row_vals[5]).font = font_regular
        for c in range(1, 10):
            ws.cell(row=idx, column=c).fill = fill_meta

    # 3. Encabezados de tabla
    headers = [
        "PERIODO (AÑO-MES)",
        "FACTURA / CUENTA COBRO NO.",
        "SALDO ANTERIOR CAPITAL",
        "INTERÉS MORA ANTERIOR",
        "CUOTA Y CARGOS MES",
        "INTERÉS MORATORIO MES",
        "PAGO MES (ABONO)",
        "SALDO TOTAL EXIGIBLE" if es_abogado else "SALDO FINAL",
        "DISCRIMINACIÓN DE CONCEPTOS / NOTAS"
    ]
    header_row = 9
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center" if col_idx <= 2 else ("left" if col_idx == 9 else "right"), vertical="center", wrap_text=True)

    # 4. Datos mes a mes
    curr_row = 10
    num_fmt = "$#,##0"
    for m in meses:
        periodo_label = m.get("periodo") or f"{m.get('anio')}-{m.get('mes')}"
        fac_num = f"Fac. {m.get('fac')}" if m.get("fac") else "-"
        cap_ant = float(m.get("saldo_anterior", 0) or 0)
        int_ant = float(m.get("interes_anterior", 0) or 0)
        cuota_m = float(m.get("cuota_admon", 0) or 0)
        int_m = float(m.get("interes_mes", 0) or 0)
        pago_m = float(m.get("valpag", 0) or 0)
        saldo_tot = float(m.get("total", 0) or 0)

        # Desglose de notas y conceptos extraordinarios
        notas_list = []
        if float(m.get("notas_mes", 0) or 0) != 0:
            notas_list.append(f"Nota D/C Mes: ${int(m['notas_mes']):,}".replace(",", "."))
        if float(m.get("notas_anterior", 0) or 0) != 0:
            notas_list.append(f"Nota D/C Pendiente: ${int(m['notas_anterior']):,}".replace(",", "."))
        if float(m.get("multa_mes", 0) or 0) != 0:
            notas_list.append(f"Multa Mes: ${int(m['multa_mes']):,}".replace(",", "."))
        if float(m.get("multa_anterior", 0) or 0) != 0:
            notas_list.append(f"Multa Pendiente: ${int(m['multa_anterior']):,}".replace(",", "."))
        if float(m.get("extra_mes", 0) or 0) != 0:
            notas_list.append(f"Cuota Extra Mes: ${int(m['extra_mes']):,}".replace(",", "."))
        if float(m.get("extra_anterior", 0) or 0) != 0:
            notas_list.append(f"Cuota Extra Pendiente: ${int(m['extra_anterior']):,}".replace(",", "."))
        if float(m.get("otros_mes", 0) or 0) != 0:
            notas_list.append(f"Otros Mes: ${int(m['otros_mes']):,}".replace(",", "."))
        if float(m.get("otros_anterior", 0) or 0) != 0:
            notas_list.append(f"Otros Pendiente: ${int(m['otros_anterior']):,}".replace(",", "."))
        if float(m.get("serpub_mes", 0) or 0) != 0:
            notas_list.append(f"Serv. Públicos Mes: ${int(m['serpub_mes']):,}".replace(",", "."))
        if float(m.get("serpub_anterior", 0) or 0) != 0:
            notas_list.append(f"Serv. Públicos Pendiente: ${int(m['serpub_anterior']):,}".replace(",", "."))
        if m.get("novedad"):
            notas_list.append(f"Novedad: {m['novedad']}")

        texto_notas = " | ".join(notas_list) if notas_list else "-"

        ws.cell(row=curr_row, column=1, value=periodo_label).font = font_bold
        ws.cell(row=curr_row, column=2, value=fac_num).alignment = Alignment(horizontal="center")
        
        c3 = ws.cell(row=curr_row, column=3, value=cap_ant)
        c4 = ws.cell(row=curr_row, column=4, value=int_ant)
        c5 = ws.cell(row=curr_row, column=5, value=cuota_m)
        c6 = ws.cell(row=curr_row, column=6, value=int_m)
        c7 = ws.cell(row=curr_row, column=7, value=pago_m)
        c8 = ws.cell(row=curr_row, column=8, value=saldo_tot)
        c9 = ws.cell(row=curr_row, column=9, value=texto_notas)

        # Comentario explicativo en celdas relevantes (ej. Nota D/C de $9.000)
        if float(m.get("notas_mes", 0) or 0) != 0:
            val_nd = int(m['notas_mes'])
            c5.comment = Comment(f"Nota D/C Mes: ${val_nd:,}".replace(",", ".") + f"\n(Cuota Base: ${int(m.get('actual_puro', cuota_m - val_nd)):,}".replace(",", ".") + f" + Nota D/C: ${val_nd:,}".replace(",", ".") + f" = Total: ${int(cuota_m):,})".replace(",", "."), "Administración")
        if float(m.get("notas_anterior", 0) or 0) != 0:
            c3.comment = Comment(f"Saldo anterior incluye Nota D/C Pendiente: ${int(m['notas_anterior']):,}".replace(",", "."), "Administración")

        for col_idx, cell in enumerate([c3, c4, c5, c6, c7, c8], start=3):
            cell.number_format = num_fmt
            cell.alignment = Alignment(horizontal="right")
            cell.font = font_bold if col_idx in (7, 8) else font_regular

        c9.font = font_notas
        c9.alignment = Alignment(horizontal="left", vertical="center")

        for c in range(1, 10):
            ws.cell(row=curr_row, column=c).border = thin_border

        curr_row += 1

    # 5. Fila de Totales
    total_row = curr_row
    ws.cell(row=total_row, column=1, value=f"TOTALES CONSOLIDADOS ({len(meses)} MESES)").font = font_bold
    ws.cell(row=total_row, column=2, value="-").alignment = Alignment(horizontal="center")
    
    for c_idx in range(3, 8):
        col_letter = get_column_letter(c_idx)
        cell = ws.cell(row=total_row, column=c_idx, value=f"=SUM({col_letter}10:{col_letter}{total_row-1})")
        cell.font = font_bold
        cell.number_format = num_fmt
        cell.alignment = Alignment(horizontal="right")
    
    # Saldo final exigible es el valor del último mes
    ult_row_idx = total_row - 1
    cell_final = ws.cell(row=total_row, column=8, value=f"=H{ult_row_idx}")
    cell_final.font = font_bold
    cell_final.number_format = num_fmt
    cell_final.alignment = Alignment(horizontal="right")

    c9_tot = ws.cell(row=total_row, column=9, value="Consolidado multianual verificado")
    c9_tot.font = font_bold
    c9_tot.alignment = Alignment(horizontal="left", vertical="center")

    for c in range(1, 10):
        ws.cell(row=total_row, column=c).fill = fill_total
        ws.cell(row=total_row, column=c).border = thin_border

    # Anchos de columna proporcionales para encajar 100% en hoja horizontal (Landscape)
    col_widths = {1: 18, 2: 22, 3: 18, 4: 16, 5: 18, 6: 16, 7: 16, 8: 18, 9: 32}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Resumen Ejecutivo de Liquidación y Conceptos Adicionales (para Juzgado / Abogado)
    curr_row += 2
    ws.cell(row=curr_row, column=1, value="DISCRIMINACIÓN DE CONCEPTOS / NOTAS Y NOVEDADES:").font = font_bold
    curr_row += 1
    
    hay_notas = False
    for m in meses:
        per = m.get("periodo") or f"{m.get('anio')}-{m.get('mes')}"
        items_m = []
        if float(m.get("notas_mes", 0) or 0) != 0:
            items_m.append(f"Nota D/C Mes: ${int(m['notas_mes']):,}".replace(",", ".") + f" (Cuota Admon Base: ${int(m.get('actual_puro', 0)):,}".replace(",", ".") + f" + Nota D/C: ${int(m['notas_mes']):,}".replace(",", ".") + f" = Total Cuota: ${int(m.get('cuota_admon', 0)):,})".replace(",", "."))
        if float(m.get("notas_anterior", 0) or 0) != 0:
            items_m.append(f"Nota D/C Pendiente: ${int(m['notas_anterior']):,}".replace(",", "."))
        if float(m.get("multa_mes", 0) or 0) != 0:
            items_m.append(f"Multa Mes: ${int(m['multa_mes']):,}".replace(",", "."))
        if float(m.get("extra_mes", 0) or 0) != 0:
            items_m.append(f"Cuota Extra: ${int(m['extra_mes']):,}".replace(",", "."))
        if items_m:
            hay_notas = True
            ws.cell(row=curr_row, column=1, value=f"• Periodo {per}:").font = font_bold
            ws.cell(row=curr_row, column=2, value=" | ".join(items_m)).font = font_regular
            curr_row += 1
    if not hay_notas:
        ws.cell(row=curr_row, column=1, value="No se registran notas ni novedades adicionales en el periodo liquidado.").font = font_regular
        curr_row += 1

    # Resumen Legal
    curr_row += 1
    ws.cell(row=curr_row, column=1, value="LIQUIDACIÓN DE CRÉDITO Y SALDO NETO EXIGIBLE (ART. 48 LEY 675 DE 2001):" if es_abogado else "RESUMEN DE LIQUIDACIÓN Y ESTADO DE CUENTA:").font = font_bold
    
    saldo_inicial_cap = float(meses[0].get("saldo_anterior", 0) or 0) if meses else 0
    int_mora_inicial = float(meses[0].get("interes_anterior", 0) or 0) if meses else 0
    sum_cuotas = sum(float(m.get("cuota_admon", 0) or 0) for m in meses)
    sum_int_mes = sum(float(m.get("interes_mes", 0) or 0) for m in meses)
    sum_pagos = sum(float(m.get("valpag", 0) or 0) for m in meses)
    saldo_final_val = float(meses[-1].get("total", 0) or 0) if meses else 0
    total_cap = saldo_inicial_cap + sum_cuotas
    total_int = int_mora_inicial + sum_int_mes

    curr_row += 1
    ws.cell(row=curr_row, column=1, value="1. TOTAL CAPITAL CAUSADO (EXPENSAS COMUNES ORDINARIAS):").font = font_regular
    c_cap = ws.cell(row=curr_row, column=4, value=total_cap)
    c_cap.number_format = num_fmt
    c_cap.font = font_bold

    curr_row += 1
    ws.cell(row=curr_row, column=1, value="2. TOTAL INTERESES MORATORIOS LIQUIDADOS (TASA M.V.):").font = font_regular
    c_int = ws.cell(row=curr_row, column=4, value=total_int)
    c_int.number_format = num_fmt
    c_int.font = font_bold

    curr_row += 1
    ws.cell(row=curr_row, column=1, value="3. MENOS: TOTAL ABONOS Y PAGOS APLICADOS:").font = font_regular
    c_pag = ws.cell(row=curr_row, column=4, value=sum_pagos)
    c_pag.number_format = num_fmt
    c_pag.font = font_bold

    curr_row += 1
    ws.cell(row=curr_row, column=1, value="4. SALDO NETO LÍQUIDO Y EXIGIBLE (TÍTULO EJECUTIVO):" if es_abogado else "4. SALDO TOTAL A LA FECHA:").font = font_bold
    c_fin = ws.cell(row=curr_row, column=4, value=saldo_final_val)
    c_fin.number_format = num_fmt
    c_fin.font = font_bold

    # 5. Declaración Juramentada y Firmas Oficiales (Rigor Legal para Juzgados)
    if es_abogado:
        curr_row += 2
        ws.cell(row=curr_row, column=1, value="CONSTANCIA DE MÉRITO EJECUTIVO - LEY 675 DE 2001 (ART. 48 Y 49) Y C.G.P. (ART. 422):").font = font_bold
        curr_row += 1
        decl_text = (
            f"El(la) suscrito(a) Administrador(a) y Representante Legal de la copropiedad {edif.get('nombre', 'EDIFICIO ' + str(codigo))}, "
            f"con NIT {edif.get('nit', '901690778-9')}, CERTIFICA BAJO LA GRAVEDAD DE JURAMENTO: "
            f"1) Que la presente liquidación de crédito fue tomada fielmente de los libros oficiales de contabilidad y software contable. "
            f"2) Que las expensas comunes ordinarias y extraordinarias fueron aprobadas por la Asamblea General de Copropietarios. "
            f"3) Que los intereses de mora fueron calculados a la tasa legal aprobada sin superar el límite de usura de la Superfinanciera (Art. 30 Ley 675/2001). "
            f"4) Que los pagos recibidos fueron imputados conforme a los Arts. 1653 del C.C. y 881 del C.Co. "
            f"5) Que la obligación es CLARA, EXPRESA Y ACTUALMENTE EXIGIBLE a cargo del deudor, PRESTANDO MÉRITO EJECUTIVO SUFICIENTE."
        )
        decl_cell = ws.cell(row=curr_row, column=1, value=decl_text)
        decl_cell.font = font_notas
        decl_cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row+1, end_column=9)
        ws.row_dimensions[curr_row].height = 35
        curr_row += 3

        # Firmas
        ws.cell(row=curr_row, column=1, value="_____________________________________________").font = font_bold
        ws.cell(row=curr_row, column=5, value="_____________________________________________").font = font_bold
        curr_row += 1
        ws.cell(row=curr_row, column=1, value=str(edif.get('administrador', 'ADMINISTRADOR(A) Y REPRESENTANTE LEGAL'))).font = font_bold
        ws.cell(row=curr_row, column=5, value="REVISOR(A) FISCAL / CONTADOR(A) PÚBLICO(A)").font = font_bold
        curr_row += 1
        ws.cell(row=curr_row, column=1, value=f"Representante Legal - {edif.get('nombre', '')}").font = font_regular
        ws.cell(row=curr_row, column=5, value="T.P. No. ___________ - Junta Central de Contadores").font = font_regular
        curr_row += 1
        ws.cell(row=curr_row, column=1, value=f"C.C. ___________________ de Medellín").font = font_regular
        ws.cell(row=curr_row, column=5, value="(Fe Pública Contable - Art. 10 Ley 43 de 1990)").font = font_notas

    # Anchos de columnas balanceados y proporcionados (evita que el título ensanche la Columna A)
    col_widths = {
        1: 20,  # Periodo (Año-Mes) - espacio exacto para ej: 'SEPTIEMBRE 2026'
        2: 15,  # Factura / Cuenta No.
        3: 17,  # Saldo Anterior Capital
        4: 15,  # Interés Mora Anterior
        5: 16,  # Cuota y Cargos Mes
        6: 15,  # Interés Moratorio Mes
        7: 15,  # Pago Mes (Abono)
        8: 18,  # Saldo Total Exigible
        9: 28   # Discriminación de Conceptos / Notas
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    out_dir = DATA_DIR / "reportes_historicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_desde_{desde_periodo}" if desde_periodo else ""
    filename = f"Cobro_Juridico_Art48_{codigo}_Apto_{apto}_{len(meses)}_Meses{suffix}.xlsx" if es_abogado else f"Estado_Cuenta_Historico_{codigo}_Apto_{apto}{suffix}.xlsx"
    out_path = out_dir / filename

    try:
        wb.save(out_path)
    except PermissionError:
        import time
        ts = int(time.time()) % 100000
        filename = filename.replace(".xlsx", f"_{ts}.xlsx")
        out_path = out_dir / filename
        wb.save(out_path)

    # Copia de seguridad en drive_docs
    try:
        drive_dir = Path("data/drive_docs") / str(codigo) / "historicos"
        drive_dir.mkdir(parents=True, exist_ok=True)
        wb.save(drive_dir / filename)
    except Exception:
        pass

    return out_path


def generar_html_tradicional_8conceptos(res: Dict[str, Any], codigo: str, apto: str) -> str:
    """
    Genera el HTML imprimible / PDF con el formato tradicional de Estado de Cuenta
    con los 8 conceptos contables oficiales y 3 filas por mes (Pendiente, Actual, Total).
    """
    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    clean_cod = str(codigo).replace("cj_", "").strip()
    clean_apto = str(apto).strip()

    nombre_edif = edif.get("nombre", f"EDIFICIO {clean_cod} P.H.")
    propietario = res.get("propietario", "Copropietario(a)")
    bloque = res.get("bloq", "AP") or "AP"
    predio_txt = f"{propietario}--Predio {clean_apto} BLO. {bloque}"

    def fmt_num(v):
        val = float(v or 0)
        if val == 0:
            return "0"
        return f"{val:,.0f}".replace(",", ".")

    chunks = [meses[i:i + 11] for i in range(0, len(meses), 11)] or [[]]
    total_pages = len(chunks)

    pages_html = []
    for page_idx, chunk in enumerate(chunks, start=1):
        rows_html = []
        for m in chunk:
            periodo_label = m.get("periodo") or f"{m.get('mes_nombre', '')} de {m.get('anio')}"
            periodo_label = str(periodo_label).title()
            fac = m.get("fac") or ""

            pend_admon = float(m.get("pend_puro", 0) or 0)
            pend_int = float(m.get("interes_anterior", 0) or 0)
            pend_otr = float(m.get("otros_anterior", 0) or 0)
            pend_ext = float(m.get("extra_anterior", 0) or 0)
            pend_mul = float(m.get("multa_anterior", 0) or 0)
            pend_sp = float(m.get("serpub_anterior", 0) or 0)
            pend_srv = float(m.get("serv_anterior", 0) or 0)
            pend_nd = float(m.get("notas_anterior", 0) or 0)
            val_pend = pend_admon + pend_int + pend_otr + pend_ext + pend_mul + pend_sp + pend_srv + pend_nd

            act_admon = float(m.get("actual_puro", 0) or 0)
            act_int = float(m.get("interes_mes", 0) or 0)
            act_otr = float(m.get("otros_mes", 0) or 0)
            act_ext = float(m.get("extra_mes", 0) or 0)
            act_mul = float(m.get("multa_mes", 0) or 0)
            act_sp = float(m.get("serpub_mes", 0) or 0)
            act_srv = float(m.get("serv_mes", 0) or 0)
            act_nd = float(m.get("notas_mes", 0) or 0)
            val_act = act_admon + act_int + act_otr + act_ext + act_mul + act_sp + act_srv + act_nd

            tot_admon = pend_admon + act_admon
            tot_int = pend_int + act_int
            tot_otr = pend_otr + act_otr
            tot_ext = pend_ext + act_ext
            tot_mul = pend_mul + act_mul
            tot_sp = pend_sp + act_sp
            tot_srv = pend_srv + act_srv
            tot_nd = pend_nd + act_nd
            val_tot = float(m.get("total", 0) or (tot_admon + tot_int + tot_otr + tot_ext + tot_mul + tot_sp + tot_srv + tot_nd))
            pagos = float(m.get("valpag", 0) or 0)
            desc = float(m.get("valdesc", 0) or 0)

            rows_html.append(f"""
            <tr class="row-pend">
              <td class="col-mes">{periodo_label}</td>
              <td class="col-fac">{fac}</td>
              <td class="col-tipo">Pendiente</td>
              <td class="col-num">{fmt_num(pend_admon)}</td>
              <td class="col-num">{fmt_num(pend_int)}</td>
              <td class="col-num">{fmt_num(pend_otr)}</td>
              <td class="col-num">{fmt_num(pend_ext)}</td>
              <td class="col-num">{fmt_num(pend_mul)}</td>
              <td class="col-num">{fmt_num(pend_sp)}</td>
              <td class="col-num">{fmt_num(pend_srv)}</td>
              <td class="col-num">{fmt_num(pend_nd)}</td>
              <td class="col-num col-valor">{fmt_num(val_pend)}</td>
              <td class="col-num"></td>
              <td class="col-num"></td>
            </tr>
            <tr class="row-act">
              <td></td>
              <td></td>
              <td class="col-tipo">Actual</td>
              <td class="col-num">{fmt_num(act_admon)}</td>
              <td class="col-num">{fmt_num(act_int)}</td>
              <td class="col-num">{fmt_num(act_otr)}</td>
              <td class="col-num">{fmt_num(act_ext)}</td>
              <td class="col-num">{fmt_num(act_mul)}</td>
              <td class="col-num">{fmt_num(act_sp)}</td>
              <td class="col-num">{fmt_num(act_srv)}</td>
              <td class="col-num">{fmt_num(act_nd)}</td>
              <td class="col-num col-valor">{fmt_num(val_act)}</td>
              <td></td>
              <td></td>
            </tr>
            <tr class="row-tot">
              <td></td>
              <td></td>
              <td class="col-tipo col-tot-label">Total</td>
              <td class="col-num col-tot-val">{fmt_num(tot_admon)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_int)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_otr)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_ext)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_mul)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_sp)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_srv)}</td>
              <td class="col-num col-tot-val">{fmt_num(tot_nd)}</td>
              <td class="col-num col-tot-val col-valor">{fmt_num(val_tot)}</td>
              <td class="col-num col-pago">{fmt_num(pagos)}</td>
              <td class="col-num">{fmt_num(desc)}</td>
            </tr>
            <tr class="row-sep"><td colspan="14"></td></tr>
            """)

        pages_html.append(f"""
        <div class="sheet-page">
          <div class="header-box">
            <div class="header-top">
              <div class="h-title">Estado de Cuenta</div>
              <div class="h-edif">{nombre_edif}</div>
              <div class="h-page">Página {page_idx} de {total_pages}</div>
            </div>
            <div class="h-predio">{predio_txt}</div>
          </div>
          <table class="tabla-estado">
            <thead>
              <tr>
                <th style="width: 14%;">Mes</th>
                <th style="width: 6%;">Factura</th>
                <th style="width: 7%;">Concepto</th>
                <th style="width: 7%;">Admón</th>
                <th style="width: 6%;">Interés</th>
                <th style="width: 7%;">Otros</th>
                <th style="width: 6%;">Extra</th>
                <th style="width: 5%;">Multa</th>
                <th style="width: 6%;">Ser. Publ.</th>
                <th style="width: 6%;">Ser./ Serv.</th>
                <th style="width: 6%;">Notas D/C</th>
                <th style="width: 8%;">Valor</th>
                <th style="width: 8%;">Pagos</th>
                <th style="width: 7%;">Notas/Desc.</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows_html)}
            </tbody>
          </table>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Estado de Cuenta - {nombre_edif} - Apto {clean_apto}</title>
  <style>
    @page {{
      size: letter landscape;
      margin: 8mm 6mm;
    }}
    * {{
      box-sizing: border-box;
      font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
    }}
    body {{
      background: #0f172a;
      color: #000;
      margin: 0;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .no-print-bar {{
      position: sticky;
      top: 10px;
      z-index: 100;
      background: #1e293b;
      padding: 10px 20px;
      border-radius: 12px;
      border: 1px solid #334155;
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .btn-act {{
      background: #059669;
      color: white;
      border: none;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: bold;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s;
    }}
    .btn-act:hover {{ background: #10b981; }}
    .btn-sec {{
      background: #334155;
      color: #e2e8f0;
      border: 1px solid #475569;
      padding: 8px 14px;
      font-size: 13px;
      font-weight: bold;
      border-radius: 8px;
      cursor: pointer;
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .btn-sec:hover {{ background: #475569; }}
    .sheet-page {{
      background: #ffffff;
      width: 100%;
      max-width: 1100px;
      padding: 15px 20px;
      margin-bottom: 25px;
      border-radius: 4px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
      page-break-after: always;
    }}
    .sheet-page:last-child {{
      page-break-after: auto;
      margin-bottom: 0;
    }}
    .header-box {{
      border-bottom: 2px solid #000;
      padding-bottom: 6px;
      margin-bottom: 8px;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .h-title {{
      font-size: 15px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .h-edif {{
      font-size: 15px;
      font-weight: 800;
      text-align: center;
      flex: 1;
    }}
    .h-page {{
      font-size: 11px;
      font-weight: bold;
      text-align: right;
    }}
    .h-predio {{
      font-size: 12px;
      font-weight: bold;
      margin-top: 4px;
      color: #1e293b;
    }}
    .tabla-estado {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9.5px;
    }}
    .tabla-estado thead th {{
      border-top: 1px solid #000;
      border-bottom: 1.5px solid #000;
      padding: 4px 3px;
      text-align: right;
      font-weight: 800;
      background: #f8fafc;
    }}
    .tabla-estado thead th:nth-child(1) {{ text-align: left; }}
    .tabla-estado thead th:nth-child(2) {{ text-align: center; }}
    .tabla-estado thead th:nth-child(3) {{ text-align: left; }}
    .tabla-estado tbody td {{
      padding: 1.5px 3px;
      white-space: nowrap;
    }}
    .col-mes {{
      font-weight: bold;
      text-align: left;
    }}
    .col-fac {{
      text-align: center;
      color: #334155;
    }}
    .col-tipo {{
      text-align: left;
      color: #475569;
    }}
    .col-tot-label {{
      font-weight: 800;
      color: #000;
    }}
    .col-num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    .col-tot-val {{
      font-weight: 800;
      color: #000;
    }}
    .col-valor {{
      background: #f1f5f9;
      font-weight: 700;
    }}
    .col-pago {{
      color: #047857;
      font-weight: 700;
    }}
    .row-tot td {{
      border-bottom: 1px dashed #cbd5e1;
      padding-bottom: 2px;
    }}
    .row-sep td {{
      height: 4px;
      border: none;
      padding: 0;
    }}
    @media print {{
      body {{
        background: transparent !important;
        padding: 0 !important;
      }}
      .no-print-bar {{ display: none !important; }}
      .sheet-page {{
        width: 100% !important;
        max-width: none !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        border-radius: 0 !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="no-print-bar">
    <button class="btn-act" onclick="window.print()">🖨️ Imprimir / Guardar PDF</button>
    <a class="btn-sec" href="/api/conjuntos/{clean_cod}/estudio-cuenta-historico/{clean_apto}/excel?tipo=tradicional" target="_blank">📥 Descargar en Excel (.xlsx)</a>
    <button class="btn-sec" onclick="window.close()">✖️ Cerrar</button>
  </div>
  {''.join(pages_html)}
</body>
</html>"""
    return html


def generar_html_historico(codigo: str, apto: str, tipo: str = "abogado", desde_periodo: Optional[str] = None, hasta_periodo: Optional[str] = None) -> str:
    """
    Genera el documento HTML completo listo para visualizar o imprimir en PDF oficial.
    Soporta 'tradicional' (Estado de Cuenta con 8 conceptos) y 'abogado' (Cobro Judicial Ejecutivo).
    Permite filtrar por periodo inicial ('desde_periodo', ej. '2024-01') o rango.
    """
    res = obtener_estudio_cuenta_apto(codigo, apto, desde_periodo=desde_periodo, hasta_periodo=hasta_periodo)
    tipo_str = str(tipo or "abogado").lower().strip()
    if tipo_str in ("tradicional", "estado_cuenta", "kardex", "copropietario_tradicional"):
        return generar_html_tradicional_8conceptos(res, codigo, apto)

    import datetime
    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    es_abogado = tipo_str == "abogado"

    primer_mes = meses[0] if meses else {}
    ult_mes = meses[-1] if meses else {}
    saldo_inicial_cap = float(primer_mes.get("saldo_anterior", 0) or 0)
    int_mora_inicial = float(primer_mes.get("interes_anterior", 0) or 0)

    sum_cuotas = sum(float(m.get("cuota_admon", 0) or 0) for m in meses)
    sum_int_mes = sum(float(m.get("interes_mes", 0) or 0) for m in meses)
    sum_pagos = sum(float(m.get("valpag", 0) or 0) for m in meses)
    saldo_final = float(ult_mes.get("total", 0) or 0)

    total_cap = saldo_inicial_cap + sum_cuotas
    total_int = int_mora_inicial + sum_int_mes
    fecha_hoy = datetime.datetime.now().strftime("%d de %B de %Y")

    def fmt(v):
        return f"${v:,.0f}".replace(",", ".")

    filas_tr = []
    for idx, m in enumerate(meses):
        bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
        periodo = m.get("periodo") or f"{m.get('anio')}-{m.get('mes')}"
        fac = f"Fac. {m.get('fac')}" if m.get("fac") else "-"
        cap_ant = float(m.get("saldo_anterior", 0) or 0)
        int_ant = float(m.get("interes_anterior", 0) or 0)
        cuota = float(m.get("cuota_admon", 0) or 0)
        int_m = float(m.get("interes_mes", 0) or 0)
        pago = float(m.get("valpag", 0) or 0)
        tot = float(m.get("total", 0) or 0)

        tags_mes = []
        if float(m.get("notas_mes", 0) or 0) != 0:
            tags_mes.append(f"Nota D/C: {fmt(float(m['notas_mes']))}")
        if float(m.get("multa_mes", 0) or 0) != 0:
            tags_mes.append(f"Multa: {fmt(float(m['multa_mes']))}")
        if float(m.get("extra_mes", 0) or 0) != 0:
            tags_mes.append(f"Extra: {fmt(float(m['extra_mes']))}")
        if float(m.get("otros_mes", 0) or 0) != 0:
            tags_mes.append(f"Otros: {fmt(float(m['otros_mes']))}")
        sub_mes_html = f'<div style="font-size: 8px; color: #0284c7; font-weight: normal; margin-top: 1px;">({" • ".join(tags_mes)})</div>' if tags_mes else ''

        tags_ant = []
        if float(m.get("notas_anterior", 0) or 0) != 0:
            tags_ant.append(f"Nota D/C pend.: {fmt(float(m['notas_anterior']))}")
        if float(m.get("multa_anterior", 0) or 0) != 0:
            tags_ant.append(f"Multa pend.: {fmt(float(m['multa_anterior']))}")
        if float(m.get("extra_anterior", 0) or 0) != 0:
            tags_ant.append(f"Extra pend.: {fmt(float(m['extra_anterior']))}")
        if float(m.get("otros_anterior", 0) or 0) != 0:
            tags_ant.append(f"Otros pend.: {fmt(float(m['otros_anterior']))}")
        sub_ant_html = f'<div style="font-size: 8px; color: #b45309; font-weight: normal; margin-top: 1px;">({" • ".join(tags_ant)})</div>' if tags_ant else ''

        novedad_str = str(m.get("novedad", "") or "").strip()
        tags_todas = tags_mes + tags_ant
        if novedad_str:
            tags_todas.append(novedad_str)
        col_notas_html = f'<div style="font-size: 7.5px; color: #334155; line-height: 1.1;">{" | ".join(tags_todas)}</div>' if tags_todas else '<span style="color: #94a3b8;">-</span>'

        filas_tr.append(f"""
        <tr style="border-bottom: 1px solid #cbd5e1; background-color: {bg};">
          <td style="padding: 4px 5px; font-weight: bold; color: #000;">{periodo}</td>
          <td style="padding: 4px 5px; text-align: center; font-family: monospace;">{fac}</td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace;">
            <div>{fmt(cap_ant)}</div>
            {sub_ant_html}
          </td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace;">{fmt(int_ant)}</td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace;">
            <div>{fmt(cuota)}</div>
            {sub_mes_html}
          </td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace;">{fmt(int_m)}</td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace; font-weight: bold;">{fmt(pago)}</td>
          <td style="padding: 4px 5px; text-align: right; font-family: monospace; font-weight: bold;">{fmt(tot)}</td>
          <td style="padding: 4px 5px; text-align: left;">{col_notas_html}</td>
        </tr>
        """)

    titulo_doc = "CERTIFICACIÓN DE ESTADO DE CUENTA Y LIQUIDACIÓN DISCRIMINADA DE CRÉDITO PARA COBRO JUDICIAL EJECUTIVO" if es_abogado else "ESTADO DE CUENTA HISTÓRICO Y TRAZABILIDAD DE CARTERA"
    subtitulo_doc = "(TÍTULO EJECUTIVO PLENO - ARTÍCULOS 48 Y 49 DE LA LEY 675 DE 2001 Y ARTÍCULO 422 DEL CÓDIGO GENERAL DEL PROCESO - LEY 1564 DE 2012)" if es_abogado else "(INFORME CONTABLE DETALLADO MES A MES PARA EL COPROPIETARIO)"

    nota_legal = f"""
      <div style="border: 2px solid #0f172a; background: #f8fafc; padding: 12px; font-size: 8.5px; text-align: justify; margin: 12px 0; border-radius: 4px; line-height: 1.45;">
        <h4 style="margin: 0 0 6px 0; font-size: 9.5px; text-transform: uppercase; color: #0f172a; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px;">
          DECLARACIÓN JURAMENTADA Y CONSTANCIA DE MÉRITO EJECUTIVO (ART. 48 Y 49 LEY 675 DE 2001 / ART. 422 C.G.P.)
        </h4>
        El(la) suscrito(a) Administrador(a) y Representante Legal de la copropiedad <b>{edif.get('nombre', 'EDIFICIO ' + str(codigo))}</b> (P.H.), con NIT {edif.get('nit', '901690778-9')}, en cumplimiento de sus deberes legales conferidos por la Ley 675 de 2001 y el Reglamento de Propiedad Horizontal, <b>CERTIFICA BAJO LA GRAVEDAD DE JURAMENTO</b>:
        <ol style="margin: 4px 0 6px 18px; padding: 0;">
          <li>Que la liquidación cronológica y discriminada que antecede fue extraída fiel y directamente de los libros de contabilidad oficiales y del software contable de la copropiedad, correspondiendo a los saldos adeudados por la unidad privada <b>Apto/Inmueble {res.get('apto', '')}</b>.</li>
          <li>Que las expensas comunes ordinarias y extraordinarias fueron aprobadas válidamente por la Asamblea General de Copropietarios conforme al presupuesto legal.</li>
          <li>Que la liquidación de intereses moratorios se realizó conforme a la tasa pactada en el Reglamento de Propiedad Horizontal y supletoriamente según el Artículo 30 de la Ley 675 de 2001, sin exceder en ningún período el límite legal de usura certificado por la Superintendencia Financiera de Colombia.</li>
          <li>Que los pagos y abonos registrados fueron imputados rigurosamente en el orden legal previsto por el Artículo 1653 del Código Civil y el Artículo 881 del Código de Comercio (costas/gastos, intereses moratorios y remanente a capital).</li>
          <li>Que la obligación aquí contenida es <b>CLARA, EXPRESA Y ACTUALMENTE EXIGIBLE</b> a cargo del demandado(a) y a favor de la copropiedad acreedora, <b>PRESTANDO MÉRITO EJECUTIVO SUFICIENTE</b> para su cobro judicial ante los Jueces Civiles de la República.</li>
        </ol>
        <div style="margin-top: 6px; padding-top: 4px; border-top: 1px dashed #cbd5e1; font-size: 8px; color: #475569;">
          <b>DOCUMENTOS ANEXOS DE RIGOR PARA EL PROCESO EJECUTIVO ANTE EL JUZGADO:</b> 
          1. Original suscrito de este Certificado de Deuda. 
          2. Certificado de Existencia y Representación Legal expedido por la Alcaldía Municipal (vigencia no mayor a 30 días). 
          3. Copia del acta de Asamblea de Copropietarios aprobatoria de las cuotas. 
          4. Certificado de Tradición y Libertad del inmueble (vigencia no mayor a 30 días).
        </div>
      </div>
    """ if es_abogado else f"""
      <div style="border: 1px solid #94a3b8; background: #f8fafc; padding: 10px; font-size: 9px; text-align: justify; margin: 15px 0; border-radius: 4px;">
        <b>ESTADO DE CUENTA INFORMATIVO PARA EL COPROPIETARIO:</b><br/>
        La presente relación refleja fielmente la trazabilidad de cuotas causadas, intereses y pagos imputados a la unidad privada <b>{res.get('apto', '')}</b>. 
        Para cualquier inquietud o conciliación de pagos, favor comunicarse con la Administración.
      </div>
    """

    firmas_html = f"""
    <div class="firmas">
      <div class="firma-col">
        <p>________________________________________________</p>
        <p><b>{edif.get('administrador', 'ADMINISTRACIÓN Y REPRESENTACIÓN LEGAL')}</b></p>
        <p>Administrador(a) y Representante Legal</p>
        <p>{edif.get('nombre', '')} • NIT: {edif.get('nit', '')}</p>
        <p style="font-size: 7.5px; color: #475569;">Certificación expedida de conformidad con el Art. 48 de la Ley 675 de 2001</p>
      </div>
      <div class="firma-col">
        <p>________________________________________________</p>
        <p><b>REVISIÓN FISCAL / CONTABILIDAD</b></p>
        <p>Contador(a) Público(a) / Revisor(a) Fiscal</p>
        <p>T.P. No. _________________ - Junta Central de Contadores</p>
        <p style="font-size: 7.5px; color: #475569;">Dictamen con presunción de Fe Pública Contable (Ley 43 de 1990, Art. 10)</p>
      </div>
    </div>
    """ if es_abogado else f"""
    <div class="firmas">
      <div class="firma-col">
        <p><b>{edif.get('administrador', 'ADMINISTRACIÓN Y REPRESENTACIÓN LEGAL')}</b></p>
        <p>Administrador(a) y Representante Legal</p>
        <p>{edif.get('nombre', '')}</p>
      </div>
      <div class="firma-col">
        <p><b>CONSTANCIA DE EMISIÓN</b></p>
        <p>Expedido en {edif.get('ciudad', 'Medellín • Colombia')}</p>
        <p>Fecha de emisión: {fecha_hoy}</p>
      </div>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>{titulo_doc} - Apto {res.get('apto', '')}</title>
  <style>
    @page {{ size: landscape; margin: 8mm; }}
    *, *:before, *:after {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 9.5px; color: #000; padding: 6px; background: #fff; width: 100%; }}
    .header {{ text-align: center; border-bottom: 3px double #0f172a; padding-bottom: 6px; margin-bottom: 10px; }}
    .header h1 {{ font-size: 15px; margin: 0; font-weight: 800; text-transform: uppercase; }}
    .header p {{ margin: 2px 0; font-size: 9px; }}
    .meta-grid {{ display: flex; gap: 10px; margin-bottom: 10px; }}
    .meta-box {{ flex: 1; border: 1px solid #94a3b8; border-radius: 4px; padding: 6px 8px; background: #f8fafc; font-size: 9px; }}
    .meta-box h4 {{ margin: 0 0 3px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; text-transform: uppercase; font-size: 9px; }}
    .cards {{ display: flex; gap: 8px; margin-bottom: 10px; }}
    .card {{ flex: 1; border: 1px solid #94a3b8; border-radius: 4px; padding: 5px; text-align: center; background: #fff; }}
    .card .title {{ font-size: 8px; font-weight: bold; text-transform: uppercase; }}
    .card .val {{ font-size: 12px; font-weight: 800; margin-top: 2px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 8.5px; margin-bottom: 12px; table-layout: fixed; }}
    th {{ background: #0f172a; color: #fff; padding: 5px 6px; text-align: left; font-size: 8px; text-transform: uppercase; border: 1px solid #0f172a; }}
    .firmas {{ display: flex; justify-content: space-between; margin-top: 20px; font-size: 8.5px; }}
    .firma-col {{ width: 45%; text-align: center; border-top: 1px solid #000; padding-top: 4px; }}
    @media print {{ button {{ display: none; }} }}
  </style>
</head>
<body>
  <div style="text-align: right; margin-bottom: 8px;">
    <button onclick="window.print()" style="padding: 6px 14px; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">🖨️ Imprimir / Guardar en PDF</button>
  </div>
  <div class="header">
    <h1>{edif.get('nombre', 'EDIFICIO ' + str(codigo))}</h1>
    <p>NIT: {edif.get('nit', '901690778-9')} • Dirección: {edif.get('direccion', 'Medellín')} • {edif.get('ciudad', 'Medellín • Colombia')}</p>
    <p><b>{titulo_doc}</b></p>
    <p style="font-size: 8.5px; color: #475569;">{subtitulo_doc}</p>
  </div>

  <div class="meta-grid">
    <div class="meta-box">
      <h4>1. DATOS DEL INMUEBLE Y DESTINATARIO (PARTE DEMANDADA)</h4>
      <p><b>UNIDAD PRIVADA:</b> Inmueble / Apto {res.get('apto', '')}</p>
      <p><b>PROPIETARIO(A):</b> {res.get('propietario', '')}</p>
      <p><b>C.C. / NIT:</b> {res.get('cc', '')}</p>
      <p><b>COEFICIENTE P.H.:</b> {res.get('coeficiente', '')}</p>
    </div>
    <div class="meta-box">
      <h4>2. CONDICIONES DE LIQUIDACIÓN DE LA OBLIGACIÓN</h4>
      <p><b>PERIODO ANALIZADO:</b> {len(meses)} Meses ({primer_mes.get('periodo', '')} hasta {ult_mes.get('periodo', '')})</p>
      <p><b>TASA MORA APLICADA:</b> {edif.get('interesMora', '2.10% M.V.')}</p>
      <p><b>FECHA DE CORTE Y EXPEDICIÓN:</b> {fecha_hoy}</p>
      <p><b>ESTADO:</b> {'OBLIGACIÓN EXIGIBLE EN MORA' if saldo_final > 0 else 'A PAZ Y SALVO'}</p>
    </div>
  </div>

  <div class="cards">
    <div class="card" style="border-left: 3px solid #0f172a;">
      <div class="title">Total Capital Causado</div>
      <div class="val">{fmt(total_cap)}</div>
    </div>
    <div class="card" style="border-left: 3px solid #d97706;">
      <div class="title">Total Intereses Mora</div>
      <div class="val">{fmt(total_int)}</div>
    </div>
    <div class="card" style="border-left: 3px solid #16a34a;">
      <div class="title">Total Pagos Imputados</div>
      <div class="val">{fmt(sum_pagos)}</div>
    </div>
    <div class="card" style="border-left: 3px solid #dc2626;">
      <div class="title">Saldo Exigible a la Fecha</div>
      <div class="val">{fmt(saldo_final)}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width: 11%;">Periodo</th>
        <th style="width: 7%; text-align: center;">Factura</th>
        <th style="width: 12%; text-align: right;">Saldo Ant. Capital</th>
        <th style="width: 9%; text-align: right;">Int. Mora Ant.</th>
        <th style="width: 13%; text-align: right;">Cuota y Cargos Mes</th>
        <th style="width: 9%; text-align: right;">Interés Mes</th>
        <th style="width: 11%; text-align: right;">Pago Mes (Abono)</th>
        <th style="width: 13%; text-align: right;">Saldo Exigible</th>
        <th style="width: 15%; text-align: left;">Discriminación / Notas</th>
      </tr>
    </thead>
    <tbody>
      {''.join(filas_tr)}
      <tr style="background: #e2e8f0; font-weight: bold; border-top: 2px solid #0f172a;">
        <td style="padding: 5px 6px;">TOTALES ({len(meses)} MESES)</td>
        <td style="padding: 5px 6px; text-align: center;">-</td>
        <td style="padding: 5px 6px; text-align: right;">{fmt(sum(float(m.get('saldo_anterior',0) or 0) for m in meses))}</td>
        <td style="padding: 5px 6px; text-align: right;">{fmt(sum(float(m.get('interes_anterior',0) or 0) for m in meses))}</td>
        <td style="padding: 5px 6px; text-align: right;">{fmt(sum_cuotas)}</td>
        <td style="padding: 5px 6px; text-align: right;">{fmt(sum_int_mes)}</td>
        <td style="padding: 5px 6px; text-align: right;">{fmt(sum_pagos)}</td>
        <td style="padding: 5px 6px; text-align: right; color: #dc2626;">{fmt(saldo_final)}</td>
        <td style="padding: 5px 6px; font-size: 8px; color: #334155;">Consolidado oficial verificado</td>
      </tr>
    </tbody>
  </table>

  {nota_legal}

  {firmas_html}
</body>
</html>"""
    return html


def generar_pdf_historico(codigo: str, apto: str, tipo: str = "abogado", desde_periodo: Optional[str] = None, hasta_periodo: Optional[str] = None) -> Path:
    """
    Genera el archivo PDF oficial de alta resolución usando el motor de renderizado
    vectorial headless de Microsoft Edge, garantizando formato de impresión legal.
    """
    import subprocess
    import tempfile
    import shutil
    import time
    import os

    clean_cod = str(codigo).replace("cj_", "").strip()
    clean_apto = str(apto).strip()
    es_abogado = str(tipo or "abogado").lower().strip() == "abogado"

    html_content = generar_html_historico(clean_cod, clean_apto, tipo=tipo, desde_periodo=desde_periodo, hasta_periodo=hasta_periodo)

    out_dir = DATA_DIR / "reportes_historicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_desde_{desde_periodo}" if desde_periodo else ""
    
    prefix = "Cobro_Juridico_Art48" if es_abogado else "Estado_Cuenta_Historico"
    pdf_filename = f"{prefix}_{clean_cod}_Apto_{clean_apto}{suffix}.pdf"
    html_filename = f"tmp_{prefix}_{clean_cod}_Apto_{clean_apto}{suffix}.html"
    
    pdf_out = out_dir / pdf_filename
    html_out = out_dir / html_filename

    # Verificar si el archivo destino existe y si está bloqueado por tenerlo abierto en un visor PDF
    if pdf_out.exists():
        try:
            with open(pdf_out, "ab"):
                pass
        except PermissionError:
            ts = int(time.time()) % 100000
            pdf_filename = f"{prefix}_{clean_cod}_Apto_{clean_apto}{suffix}_{ts}.pdf"
            pdf_out = out_dir / pdf_filename

    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Buscar ejecutable de Microsoft Edge o Chrome
    candidatos_edge = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    edge_bin = next((c for c in candidatos_edge if c.exists()), None)
    if not edge_bin:
        raise FileNotFoundError("No se encontró msedge.exe para generar el archivo PDF oficial.")

    html_url = html_out.resolve().as_uri()
    temp_profile = Path(tempfile.gettempdir()) / f"edge_pdf_profile_{os.getpid()}_{int(time.time() * 1000) % 1000000}"

    edge_args = [
        str(edge_bin),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--user-data-dir={temp_profile}",
        "--disable-dev-shm-usage",
        f"--print-to-pdf={pdf_out}",
        html_url
    ]

    try:
        subprocess.run(edge_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        # Fallback para versiones previas de Edge
        edge_args[1] = "--headless"
        subprocess.run(edge_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Esperar hasta 5 segundos a que el archivo sea terminado de escribir y cerrado en disco
    for _ in range(50):
        if pdf_out.exists() and pdf_out.stat().st_size > 0:
            break
        time.sleep(0.1)

    # Limpiar archivo temporal html y perfil temporal
    try:
        if html_out.exists():
            html_out.unlink()
    except Exception:
        pass

    try:
        if temp_profile.exists():
            shutil.rmtree(temp_profile, ignore_errors=True)
    except Exception:
        pass

    if not pdf_out.exists() or pdf_out.stat().st_size == 0:
        raise RuntimeError(f"Error generando PDF oficial en {pdf_out}")

    print(f"✅ PDF oficial generado exitosamente: {pdf_out}")
    return pdf_out
    return html


def exportar_matriz_consolidada_edificio(codigo: str, desde_periodo: Optional[str] = None) -> Path:
    """
    Genera un archivo Excel consolidado de todo el edificio con:
    1. Hoja de Resumen General de Cartera por Unidad (saldo actual, pagos totales, intereses, mora).
    2. Matriz Histórica de Saldos Mes a Mes por Unidad.
    3. Matriz Histórica de Pagos/Abonos Mes a Mes por Unidad.
    Permite filtrar por periodo inicial ('desde_periodo', ej. '2024-01').
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    clean_cod = str(codigo).replace("cj_", "").strip()
    json_path = DATA_DIR / f"edificio_{clean_cod}_historico.json"
    
    data = None
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None
            
    if not data or not data.get("historico_por_apto"):
        data = compilar_historico_edificio(clean_cod)

    edif = data.get("edificio", {})
    historico_aptos = data.get("historico_por_apto", {})
    unidades_master = data.get("unidades_master", {})

    wb = Workbook()
    
    # Fuentes y estilos
    font_title = Font(name="Calibri", size=12, bold=True, color="000000")
    font_sub = Font(name="Calibri", size=9, bold=True, color="475569")
    font_hdr = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=9, bold=True)
    font_regular = Font(name="Calibri", size=9)
    fill_hdr = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_hdr_sub = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    fill_total = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    num_fmt = "#,##0"

    # Obtener lista global de periodos ordenados
    todos_periodos = set()
    for apto_k, meses_list in historico_aptos.items():
        for m in meses_list:
            todos_periodos.add(m.get("periodo_iso") or f"{m.get('anio')}-{str(m.get('mes')).zfill(2)}")
    periodos_ordenados = sorted(list(todos_periodos))
    if desde_periodo:
        periodos_ordenados = [p for p in periodos_ordenados if p >= str(desde_periodo)]

    # ==========================================
    # HOJA 1: RESUMEN GENERAL DE CARTERA
    # ==========================================
    ws1 = wb.active
    ws1.title = "Resumen_General"
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = f"CONSOLIDADO HISTÓRICO GENERAL DE CARTERA - {edif.get('nombre', f'EDIFICIO {clean_cod}')}"
    ws1["A1"].font = font_title
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.merge_cells("A1:L1")

    ws1["A2"] = f"Código: {clean_cod} | NIT: {edif.get('nit', 'N/A')} | Total Inmuebles: {len(historico_aptos)} | Períodos: {len(periodos_ordenados)}"
    ws1["A2"].font = font_sub
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.merge_cells("A2:L2")

    headers1 = [
        "Unidad", "Propietario", "C.C. / NIT", "Teléfono", 
        "Meses Reg.", "Primer Período", "Último Período",
        "Total Cargos/Cuotas", "Total Int. Mora", "Total Pagos", "Saldo Final Exigible", "Estado"
    ]
    
    for c_idx, h in enumerate(headers1, 1):
        cell = ws1.cell(row=4, column=c_idx, value=h)
        cell.font = font_hdr
        cell.fill = fill_hdr
        cell.alignment = Alignment(horizontal="center" if c_idx in [1, 5, 6, 7, 12] else "left" if c_idx in [2, 3, 4] else "right", vertical="center")

    curr_row = 5
    tot_cargos_edif = 0.0
    tot_int_edif = 0.0
    tot_pagos_edif = 0.0
    tot_saldo_edif = 0.0

    # Ordenar unidades alfabéticamente/numéricamente
    aptos_ordenados = sorted(historico_aptos.keys(), key=lambda x: (len(x), x))

    for apto in aptos_ordenados:
        meses = historico_aptos[apto]
        u_info = unidades_master.get(apto, {}) or unidades_master.get(apto.lstrip("0"), {})
        prop = u_info.get("propietario") or "-"
        cc = u_info.get("cc") or "-"
        tel = u_info.get("tel") or "-"
        
        cant_meses = len(meses)
        primer_per = meses[0].get("periodo", "-") if meses else "-"
        ult_per = meses[-1].get("periodo", "-") if meses else "-"
        
        sum_cargos = sum(float(m.get("cuota_admon", 0) or 0) for m in meses)
        sum_int = sum(float(m.get("interes_mes", 0) or 0) for m in meses)
        sum_pag = sum(float(m.get("valpag", 0) or 0) for m in meses)
        saldo_fin = float(meses[-1].get("total", 0) or 0) if meses else 0.0
        
        tot_cargos_edif += sum_cargos
        tot_int_edif += sum_int
        tot_pagos_edif += sum_pag
        tot_saldo_edif += saldo_fin

        estado = "EN MORA" if saldo_fin > 1000 else "AL DÍA"

        row_data = [
            apto, prop, cc, tel, cant_meses, primer_per, ult_per,
            sum_cargos, sum_int, sum_pag, saldo_fin, estado
        ]

        for c_idx, val in enumerate(row_data, 1):
            cell = ws1.cell(row=curr_row, column=c_idx, value=val)
            cell.font = font_regular
            cell.border = thin_border
            if c_idx in [8, 9, 10, 11]:
                cell.number_format = num_fmt
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [1, 5, 6, 7]:
                cell.alignment = Alignment(horizontal="center")
            elif c_idx == 12:
                cell.alignment = Alignment(horizontal="center")
                cell.font = Font(name="Calibri", size=9, bold=True, color="DC2626" if estado == "EN MORA" else "16A34A")
        curr_row += 1

    # Fila de Totales
    ws1.cell(row=curr_row, column=1, value="TOTALES").font = font_bold
    ws1.cell(row=curr_row, column=8, value=tot_cargos_edif).number_format = num_fmt
    ws1.cell(row=curr_row, column=9, value=tot_int_edif).number_format = num_fmt
    ws1.cell(row=curr_row, column=10, value=tot_pagos_edif).number_format = num_fmt
    ws1.cell(row=curr_row, column=11, value=tot_saldo_edif).number_format = num_fmt
    for c in range(1, 13):
        cell = ws1.cell(row=curr_row, column=c)
        cell.font = font_bold
        cell.fill = fill_total
        cell.border = thin_border

    # ==========================================
    # HOJA 2: MATRIZ DE SALDOS FINALES MES A MES
    # ==========================================
    headers2 = ["Unidad", "Propietario"] + periodos_ordenados
    total_cols_ws2 = max(len(headers2), 6)

    ws2 = wb.create_sheet(title="Matriz_Saldos_Mensuales")
    ws2.views.sheetView[0].showGridLines = True
    ws2["A1"] = f"EVOLUCIÓN MENSUAL DE SALDOS POR UNIDAD - {edif.get('nombre', f'EDIFICIO {clean_cod}')}"
    ws2["A1"].font = font_title
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols_ws2)

    for c_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=3, column=c_idx, value=h)
        cell.font = font_hdr
        cell.fill = fill_hdr_sub
        cell.alignment = Alignment(horizontal="center" if c_idx > 2 else "left")

    for r_idx, apto in enumerate(aptos_ordenados, 4):
        u_info = unidades_master.get(apto, {}) or unidades_master.get(apto.lstrip("0"), {})
        ws2.cell(row=r_idx, column=1, value=apto).font = font_bold
        ws2.cell(row=r_idx, column=2, value=u_info.get("propietario", "-")).font = font_regular
        
        meses_dict = {m.get("periodo_iso") or f"{m.get('anio')}-{str(m.get('mes')).zfill(2)}": float(m.get("total", 0) or 0) for m in historico_aptos[apto]}
        for p_idx, per in enumerate(periodos_ordenados, 3):
            val = meses_dict.get(per, 0.0)
            cell = ws2.cell(row=r_idx, column=p_idx, value=val)
            cell.number_format = num_fmt
            cell.font = font_regular
            cell.alignment = Alignment(horizontal="right")
            cell.border = thin_border

    # ==========================================
    # HOJA 3: MATRIZ DE PAGOS MES A MES
    # ==========================================
    ws3 = wb.create_sheet(title="Matriz_Pagos_Mensuales")
    ws3.views.sheetView[0].showGridLines = True
    ws3["A1"] = f"EVOLUCIÓN MENSUAL DE PAGOS POR UNIDAD - {edif.get('nombre', f'EDIFICIO {clean_cod}')}"
    ws3["A1"].font = font_title
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    total_cols_ws3 = max(len(headers2), 6)
    ws3.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols_ws3)

    for c_idx, h in enumerate(headers2, 1):
        cell = ws3.cell(row=3, column=c_idx, value=h)
        cell.font = font_hdr
        cell.fill = fill_hdr_sub
        cell.alignment = Alignment(horizontal="center" if c_idx > 2 else "left")

    for r_idx, apto in enumerate(aptos_ordenados, 4):
        u_info = unidades_master.get(apto, {}) or unidades_master.get(apto.lstrip("0"), {})
        ws3.cell(row=r_idx, column=1, value=apto).font = font_bold
        ws3.cell(row=r_idx, column=2, value=u_info.get("propietario", "-")).font = font_regular
        
        meses_dict = {m.get("periodo_iso") or f"{m.get('anio')}-{str(m.get('mes')).zfill(2)}": float(m.get("valpag", 0) or 0) for m in historico_aptos[apto]}
        for p_idx, per in enumerate(periodos_ordenados, 3):
            val = meses_dict.get(per, 0.0)
            cell = ws3.cell(row=r_idx, column=p_idx, value=val)
            cell.number_format = num_fmt
            cell.font = font_regular
            cell.alignment = Alignment(horizontal="right")
            cell.border = thin_border

    # Anchos equilibrados y limpios para Hoja 1 (Resumen General)
    col_widths_ws1 = {
        1: 12,  # Unidad (espacio exacto para 0001, 0101 sin dejar hueco)
        2: 28,  # Propietario
        3: 16,  # C.C. / NIT
        4: 16,  # Teléfono
        5: 12,  # Meses Reg.
        6: 18,  # Primer Período
        7: 18,  # Último Período
        8: 18,  # Total Cargos/Cuotas
        9: 16,  # Total Int. Mora
        10: 16, # Total Pagos
        11: 18, # Saldo Final Exigible
        12: 14  # Estado
    }
    for col_idx, width in col_widths_ws1.items():
        ws1.column_dimensions[get_column_letter(col_idx)].width = width

    # Anchos equilibrados para Hojas 2 y 3 (Matrices Mensuales)
    for ws in [ws2, ws3]:
        ws.column_dimensions['A'].width = 12  # Unidad
        ws.column_dimensions['B'].width = 28  # Propietario
        for col_idx in range(3, len(headers2) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 16  # Periodos

    out_dir = DATA_DIR / "reportes_historicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_desde_{desde_periodo}" if desde_periodo else ""
    out_file = out_dir / f"Consolidado_Historico_Multianual_{clean_cod}{suffix}.xlsx"

    try:
        wb.save(out_file)
    except PermissionError:
        import time
        ts = int(time.time()) % 100000
        out_file = out_dir / f"Consolidado_Historico_Multianual_{clean_cod}{suffix}_{ts}.xlsx"
        wb.save(out_file)

    print(f"✅ Matriz consolidada multianual generada: {out_file}")
    return out_file
    print(f"✅ Matriz consolidada multianual generada: {out_file}")
    return out_file

