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
