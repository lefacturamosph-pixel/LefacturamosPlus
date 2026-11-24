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
        # Buscar todos los archivos SSyymm.DBF ordenados
        pattern = str(folder / "SS[0-9][0-9][0-9][0-9].DBF")
        files = sorted(glob.glob(pattern, recursive=False))
        if not files:
            pattern_lower = str(folder / "ss[0-9][0-9][0-9][0-9].dbf")
            files = sorted(glob.glob(pattern_lower, recursive=False))

        for fpath in files:
            fname = Path(fpath).stem.upper()
            if len(fname) != 6 or not fname.startswith("SS"):
                continue
            
            # Excluir archivo de saldo actual general del edificio como SS4901.DBF, SS7480.DBF, etc.
            if fname == f"SS{clean_cod.zfill(4)}" or fname == f"SS{clean_cod}":
                continue

            yy = fname[2:4]
            mm = fname[4:6]
            if not yy.isdigit() or not mm.isdigit():
                continue
            
            # El mes debe ser válido entre 01 y 12
            if int(mm) < 1 or int(mm) > 12:
                continue
            
            y_int = int(yy)
            anio = 2000 + y_int if y_int < 70 else 1900 + y_int
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
                    # Pagos, descuentos y saldo total
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


def obtener_estudio_cuenta_apto(codigo: str, apto_query: str) -> Dict[str, Any]:
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

    # Calcular acumulados
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
        "resumen": {
            "total_facturado": total_facturado,
            "total_pagado": total_pagado,
            "saldo_actual": saldo_actual
        }
    }
def generar_excel_historico(codigo: str, apto: str, tipo: str = "abogado") -> Path:
    """
    Genera un archivo Excel profesional (.xlsx) con la liquidación detallada del estudio histórico.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.comments import Comment

    res = obtener_estudio_cuenta_apto(codigo, apto)
    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    es_abogado = str(tipo).lower() == "abogado"

    wb = Workbook()
    ws = wb.active
    ws.title = "Cobro_Juridico" if es_abogado else "Estado_Cuenta"
    ws.views.sheetView[0].showGridLines = True

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

    # 1. Título principal
    ws["A1"] = "CERTIFICACIÓN DE DEUDA Y LIQUIDACIÓN DISCRIMINADA DE CRÉDITO PARA COBRO JUDICIAL" if es_abogado else "ESTADO DE CUENTA HISTÓRICO Y TRAZABILIDAD DE CARTERA"
    ws["A1"].font = font_title
    ws["A2"] = "(EXPEDIDO DE CONFORMIDAD CON EL ARTÍCULO 48 DE LA LEY 675 DE 2001 - PRESTA MÉRITO EJECUTIVO)" if es_abogado else "(INFORME CONTABLE DETALLADO DE PAGOS Y CUOTAS DE ADMINISTRACIÓN)"
    ws["A2"].font = font_sub

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

    # Anchos de columna profesionales
    col_widths = {1: 22, 2: 24, 3: 24, 4: 24, 5: 26, 6: 24, 7: 24, 8: 26, 9: 45}
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

    out_dir = Path("data/drive_docs") / str(codigo) / "historicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"Cobro_Juridico_Art48_{codigo}_Apto_{apto}_{len(meses)}_Meses.xlsx" if es_abogado else f"Estado_Cuenta_Historico_{codigo}_Apto_{apto}.xlsx"
    out_path = out_dir / filename
    wb.save(out_path)
    return out_path


def generar_html_historico(codigo: str, apto: str, tipo: str = "abogado") -> str:
    """
    Genera el documento HTML completo listo para visualizar o imprimir en PDF oficial.
    """
    import datetime
    res = obtener_estudio_cuenta_apto(codigo, apto)
    edif = res.get("edificio", {})
    meses = res.get("meses", [])
    es_abogado = str(tipo).lower() == "abogado"

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

        filas_tr.append(f"""
        <tr style="border-bottom: 1px solid #cbd5e1; background-color: {bg};">
          <td style="padding: 5px 6px; font-weight: bold; color: #000;">{periodo}</td>
          <td style="padding: 5px 6px; text-align: center; font-family: monospace;">{fac}</td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace;">
            <div>{fmt(cap_ant)}</div>
            {sub_ant_html}
          </td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace;">{fmt(int_ant)}</td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace;">
            <div>{fmt(cuota)}</div>
            {sub_mes_html}
          </td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace;">{fmt(int_m)}</td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace; font-weight: bold;">{fmt(pago)}</td>
          <td style="padding: 5px 6px; text-align: right; font-family: monospace; font-weight: bold;">{fmt(tot)}</td>
        </tr>
        """)

    titulo_doc = "CERTIFICACIÓN DE DEUDA Y ESTADO DE CUENTA CRONOLÓGICO DISCRIMINADO" if es_abogado else "ESTADO DE CUENTA HISTÓRICO Y TRAZABILIDAD DE CARTERA"
    subtitulo_doc = "(TÍTULO EJECUTIVO - ARTÍCULO 48 DE LA LEY 675 DE 2001 Y ART. 422 DEL C.G.P.)" if es_abogado else "(INFORME CONTABLE DETALLADO MES A MES PARA EL COPROPIETARIO)"

    nota_legal = f"""
      <div style="border: 1px solid #94a3b8; background: #f8fafc; padding: 10px; font-size: 9px; text-align: justify; margin: 15px 0; border-radius: 4px;">
        <b>CONSTANCIA DE MÉRITO EJECUTIVO (ARTÍCULO 48 LEY 675 DE 2001):</b><br/>
        El(la) suscrito(a) Administrador(a) y Representante Legal de la copropiedad <b>{edif.get('nombre', 'EDIFICIO ' + str(codigo))}</b>, 
        certifica que la relación contable anterior corresponde fielmente a los saldos adeudados por concepto de expensas comunes ordinarias e intereses moratorios para la unidad privada <b>{res.get('apto', '')}</b>. 
        Se expide la presente liquidación para que sirva de <b>PLENA PRUEBA Y TÍTULO EJECUTIVO</b> constituyendo una obligación clara, expresa y actualmente exigible.
      </div>
    """ if es_abogado else f"""
      <div style="border: 1px solid #94a3b8; background: #f8fafc; padding: 10px; font-size: 9px; text-align: justify; margin: 15px 0; border-radius: 4px;">
        <b>ESTADO DE CUENTA INFORMATIVO PARA EL COPROPIETARIO:</b><br/>
        La presente relación refleja fielmente la trazabilidad de cuotas causadas, intereses y pagos imputados a la unidad privada <b>{res.get('apto', '')}</b>. 
        Para cualquier inquietud o conciliación de pagos, favor comunicarse con la Administración.
      </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>{titulo_doc} - Apto {res.get('apto', '')}</title>
  <style>
    @page {{ size: portrait; margin: 10mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; color: #000; padding: 10px; background: #fff; }}
    .header {{ text-align: center; border-bottom: 3px double #0f172a; padding-bottom: 8px; margin-bottom: 12px; }}
    .header h1 {{ font-size: 16px; margin: 0; font-weight: 800; text-transform: uppercase; }}
    .header p {{ margin: 2px 0; font-size: 9.5px; }}
    .meta-grid {{ display: flex; gap: 10px; margin-bottom: 12px; }}
    .meta-box {{ flex: 1; border: 1px solid #94a3b8; border-radius: 4px; padding: 8px; background: #f8fafc; font-size: 9.5px; }}
    .meta-box h4 {{ margin: 0 0 4px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; text-transform: uppercase; font-size: 9.5px; }}
    .cards {{ display: flex; gap: 8px; margin-bottom: 12px; }}
    .card {{ flex: 1; border: 1px solid #94a3b8; border-radius: 4px; padding: 6px; text-align: center; background: #fff; }}
    .card .title {{ font-size: 8px; font-weight: bold; text-transform: uppercase; }}
    .card .val {{ font-size: 13px; font-weight: 800; margin-top: 2px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 9px; margin-bottom: 15px; }}
    th {{ background: #0f172a; color: #fff; padding: 6px; text-align: left; font-size: 8px; text-transform: uppercase; border: 1px solid #0f172a; }}
    .firmas {{ display: flex; justify-content: space-between; margin-top: 30px; font-size: 9px; }}
    .firma-col {{ width: 45%; text-align: center; border-top: 1px solid #000; padding-top: 5px; }}
    @media print {{ button {{ display: none; }} }}
  </style>
</head>
<body>
  <div style="text-align: right; margin-bottom: 10px;">
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
      <h4>1. DATOS DEL INMUEBLE Y DESTINATARIO</h4>
      <p><b>UNIDAD PRIVADA:</b> Inmueble / Apto {res.get('apto', '')}</p>
      <p><b>PROPIETARIO(A):</b> {res.get('propietario', '')}</p>
      <p><b>C.C. / NIT:</b> {res.get('cc', '')}</p>
      <p><b>COEFICIENTE P.H.:</b> {res.get('coeficiente', '')}</p>
    </div>
    <div class="meta-box">
      <h4>2. CONDICIONES DE LIQUIDACIÓN</h4>
      <p><b>PERIODO ANALIZADO:</b> {len(meses)} Meses ({primer_mes.get('periodo', '')} hasta {ult_mes.get('periodo', '')})</p>
      <p><b>TASA MORA APLICADA:</b> {edif.get('interesMora', '2.10% M.V.')}</p>
      <p><b>FECHA DE EXPEDICIÓN:</b> {fecha_hoy}</p>
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
        <th>Periodo</th>
        <th style="text-align: center;">Factura</th>
        <th style="text-align: right;">Saldo Ant. Capital</th>
        <th style="text-align: right;">Int. Mora Ant.</th>
        <th style="text-align: right;">Cuota Admón</th>
        <th style="text-align: right;">Interés Mes</th>
        <th style="text-align: right;">Pago Mes (Abono)</th>
        <th style="text-align: right;">Saldo Exigible</th>
      </tr>
    </thead>
    <tbody>
      {''.join(filas_tr)}
      <tr style="background: #e2e8f0; font-weight: bold; border-top: 2px solid #0f172a;">
        <td style="padding: 6px;">TOTALES ({len(meses)} MESES)</td>
        <td style="padding: 6px; text-align: center;">-</td>
        <td style="padding: 6px; text-align: right;">{fmt(sum(float(m.get('saldo_anterior',0) or 0) for m in meses))}</td>
        <td style="padding: 6px; text-align: right;">{fmt(sum(float(m.get('interes_anterior',0) or 0) for m in meses))}</td>
        <td style="padding: 6px; text-align: right;">{fmt(sum_cuotas)}</td>
        <td style="padding: 6px; text-align: right;">{fmt(sum_int_mes)}</td>
        <td style="padding: 6px; text-align: right;">{fmt(sum_pagos)}</td>
        <td style="padding: 6px; text-align: right; color: #dc2626;">{fmt(saldo_final)}</td>
      </tr>
    </tbody>
  </table>

  {nota_legal}

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
</body>
</html>"""
    return html
