#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - SERVICIO DE IMPORTACIÓN Y PARSER NATIVO DBPLUS (.DBF)
========================================================================================
Lee, procesa y fusiona los archivos contables de DBPLUS ubicados en C:\\dbplus\\{codigo}
- EDIFICIO.DBF: Directorio general, bancos, cuentas, NIT, administradores, interés de mora
- MMxxxx.DBF: Inmuebles, propietarios, coeficientes Ley 675, correos, teléfonos
- SSxxxx.DBF: Cartera, saldos iniciales y los 8 conceptos normativos de la Ley 675
"""

import os
import glob
import struct
import re
import json
from typing import Dict, List, Any, Optional

def read_dbf_binary(filepath: str) -> List[Dict[str, Any]]:
    """Lee un archivo DBF de dBASE III/IV directamente desde disco binario."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'rb') as f:
            header = f.read(32)
            if len(header) < 32:
                return []
            num_records, header_len, record_len = struct.unpack('<IHH', header[4:12])
            num_fields = (header_len - 33) // 32
            fields = []
            for _ in range(num_fields):
                fld = f.read(32)
                fname = fld[:11].replace(b'\x00', b'').decode('latin1', errors='ignore').strip().upper()
                ftype = chr(fld[11])
                flen = fld[16]
                fields.append((fname, ftype, flen))
            f.seek(header_len)
            records = []
            for _ in range(num_records):
                rec_bytes = f.read(record_len)
                if len(rec_bytes) < record_len:
                    break
                if rec_bytes[0:1] == b'*':
                    continue  # Registro marcado para borrar
                rec = {}
                offset = 1
                for fname, ftype, flen in fields:
                    raw_val = rec_bytes[offset:offset+flen]
                    try:
                        val_str = raw_val.decode('cp850').strip()
                    except:
                        val_str = raw_val.decode('latin1', errors='replace').strip()
                    if ftype == 'N':
                        try:
                            rec[fname] = float(val_str) if '.' in val_str else int(val_str)
                        except:
                            rec[fname] = 0
                    else:
                        rec[fname] = val_str
                    offset += flen
                records.append(rec)
            return records
    except Exception as e:
        print(f"Error leyendo DBF {filepath}: {e}")
        return []

def obtener_datos_dbplus_edificio(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Busca y procesa los archivos DBF para el código de edificio en C:\\dbplus\\{codigo}
    """
    clean_cod = str(codigo).replace('cj_', '').strip()
    base_dirs = ['C:/dbplus', 'c:/dbplus', os.path.abspath('./dbplus')]
    folder = None
    for bd in base_dirs:
        for candidate in [f"{bd}/{clean_cod}", f"{bd}/{clean_cod.lower()}", f"{bd}/{clean_cod.upper()}"]:
            if os.path.exists(candidate) and os.path.isdir(candidate):
                folder = candidate
                break
        if folder:
            break
            
    if not folder:
        # Respaldo automático desde JSON master si no existe C:\dbplus en este entorno (ej: Render Linux Cloud)
        cand_paths = [
            f"data/edificio_{clean_cod}_master.json",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"edificio_{clean_cod}_master.json")
        ]
        for cp in cand_paths:
            if os.path.exists(cp):
                try:
                    with open(cp, "r", encoding="utf-8") as mf:
                        mdata = json.load(mf)
                        ed_info = mdata.get("edificio") or {}
                        units = mdata.get("unidades") or []
                        return {
                            "status": "success",
                            "codigo": clean_cod,
                            "directorio": f"C:\\dbplus\\{clean_cod}",
                            "edificio": ed_info,
                            "unidades": units,
                            "total": len(units),
                            "archivos": {
                                "edificio": "EDIFICIO.DBF",
                                "inmuebles": f"MM{clean_cod}.DBF",
                                "cartera": f"SS{clean_cod}.DBF"
                            }
                        }
                except Exception as ex:
                    print(f"Error cargando master {cp}: {ex}")
        return None

    # 1. Leer EDIFICIO.DBF
    ed_path = os.path.join(folder, 'EDIFICIO.DBF')
    if not os.path.exists(ed_path):
        for bd in base_dirs:
            candidate_ed = f"{bd}/EDIFICIO.DBF"
            if os.path.exists(candidate_ed):
                ed_path = candidate_ed
                break
    ed_rows = read_dbf_binary(ed_path) if os.path.exists(ed_path) else []
    target_ed = next((r for r in ed_rows if str(r.get('CODIGO','')).strip() == clean_cod), {})
    if not target_ed and ed_rows:
        target_ed = ed_rows[0]

    # 2. Leer Inmuebles MMxxxx.DBF
    mm_files = (glob.glob(f'{folder}/MM*.DBF') + 
                glob.glob(f'{folder}/mm*.dbf') + 
                glob.glob(f'{folder}/*MM*.DBF'))
    mm_rows = read_dbf_binary(mm_files[0]) if mm_files else []

    # 3. Leer Cartera SSxxxx.DBF (priorizar archivo del mes contable más reciente SSYYMM.DBF, ej: SS2611.DBF)
    all_ss = (glob.glob(f'{folder}/SS*.DBF') + glob.glob(f'{folder}/ss*.dbf') +
              glob.glob(f'{folder}/Envio/SS*.DBF') + glob.glob(f'{folder}/Envio/ss*.dbf') +
              glob.glob(f'{folder}/envio/SS*.DBF') + glob.glob(f'{folder}/envio/ss*.dbf'))
    all_ss = list(dict.fromkeys(all_ss))
    
    monthly_ss = []
    other_ss = []
    for f in all_ss:
        fname = os.path.basename(f)
        m = re.match(r'^[Ss][Ss](\d{4})\.[Dd][Bb][Ff]$', fname)
        if m:
            monthly_ss.append((m.group(1), f))
        else:
            other_ss.append(f)
            
    if monthly_ss:
        monthly_ss.sort(key=lambda x: x[0], reverse=True)
        ss_chosen = monthly_ss[0][1]
    elif other_ss:
        cod_ss = [f for f in other_ss if f'{clean_cod}'.lower() in os.path.basename(f).lower()]
        if cod_ss:
            ss_chosen = cod_ss[0]
        else:
            other_ss.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            ss_chosen = other_ss[0]
    else:
        ss_chosen = None
        
    ss_rows = read_dbf_binary(ss_chosen) if ss_chosen else []
    ss_map = {str(r.get('APTO','')).strip(): r for r in ss_rows}

    # Metadatos del Edificio
    nom_edif = str(target_ed.get('NOMURBAN') or target_ed.get('NOMADMON') or target_ed.get('NOM') or f"Edificio {clean_cod}").strip()
    nit_edif = str(target_ed.get('NITURBAN') or target_ed.get('NIT') or "901690778-9").strip()
    banco_edif = str(target_ed.get('BANCO') or "BANCOLOMBIA AHO").strip()
    cta_edif = str(target_ed.get('CUENTA') or "").strip()
    admin_edif = str(target_ed.get('NOMTEL') or target_ed.get('ADMINISTRADOR') or "Administración").strip()
    tel_edif = str(target_ed.get('TEL') or "").strip()
    if tel_edif == '0': tel_edif = ""
    email_edif = str(target_ed.get('EMAILURBAN') or target_ed.get('EMAIL') or "").strip()
    dir_edif = str(target_ed.get('DIREC') or "").strip()
    mora_val = target_ed.get('MORA') or target_ed.get('INTPORC') or '2.118%'
    if str(mora_val).upper() == "SUPER" or not mora_val:
        mora_val = target_ed.get('INTPORC') or '2.118%'
    mora_edif = f"{mora_val}%" if "%" not in str(mora_val) else str(mora_val)

    edificio_info = {
        "codigo": clean_cod,
        "nombre": nom_edif,
        "nit": nit_edif,
        "direccion": dir_edif or f"Copropiedad #{clean_cod}",
        "ciudad": "Medellín • Antioquia",
        "banco": banco_edif,
        "tipoCuenta": "Ahorros" if "AHO" in banco_edif.upper() else "Corriente",
        "cuenta": cta_edif,
        "administrador": admin_edif,
        "telefono": tel_edif,
        "email": email_edif,
        "interesMora": mora_edif or "2.118%",
        "tipo": "Propiedad Horizontal"
    }

    # Procesar unidades fusionando MM y SS
    unidades = []
    tot_coef = 0.0
    for m in mm_rows:
        apto = str(m.get('APTO', '')).strip()
        if not apto:
            continue
        bloq = str(m.get('BLOQ', 'AP')).strip()
        prop = str(m.get('NOM', '')).strip() or f"Propietario Apto {apto}"
        cc = str(m.get('CC_NIT', '')).strip()
        email = str(m.get('EMAIL', '')).strip()
        tel = str(m.get('TEL') or m.get('BEP_CEL') or '').strip()
        if tel == '0': tel = ''
        
        # En DBPLUS MM, COEF_URB es el coeficiente principal de la unidad
        raw_c = float(m.get('COEF_URB') or 0.0) or float(m.get('COEF_APA') or 0.0) or float(m.get('COEF') or 0.0)
        tot_coef += raw_c
        admon = float(m.get('ACTUAL') or 0.0)
        fac = m.get('FAC') or ''

        s = ss_map.get(apto, {})
        p_admon = float(s.get('ACTUAL') or admon or 0.0)
        p_pend = float(s.get('PEND') or 0.0)
        p_inta = float(s.get('INTA') or 0.0)
        p_intp = float(s.get('INTP') or 0.0)
        p_int = p_inta + p_intp
        p_otrosa = float(s.get('OTROSA') or 0.0)
        p_otrosp = float(s.get('OTROSP') or 0.0)
        p_otr = p_otrosa + p_otrosp
        p_extraa = float(s.get('EXTRAA') or 0.0)
        p_extrap = float(s.get('EXTRAP') or 0.0)
        p_ext = p_extraa + p_extrap
        p_multaa = float(s.get('MULTAA') or 0.0)
        p_multap = float(s.get('MULTAP') or 0.0)
        p_mul = p_multaa + p_multap
        p_serpua = float(s.get('SERPUA') or 0.0)
        p_serpup = float(s.get('SERPUP') or 0.0)
        p_sp = p_serpua + p_serpup
        p_servia = float(s.get('SERVIA') or 0.0)
        p_servip = float(s.get('SERVIP') or 0.0)
        p_ss = p_servia + p_servip
        p_ndnca = float(s.get('NDNCA') or 0.0)
        p_ndncp = float(s.get('NDNCP') or 0.0)
        p_nd = p_ndnca + p_ndncp
        p_valdesc = float(s.get('VALDESC') or s.get('DESCUENTO') or s.get('DESC') or 0.0)
        p_tot = float(s.get('TOTAL') or (p_admon + p_pend + p_int + p_otr + p_ext + p_mul + p_sp + p_ss + p_nd - p_valdesc))
        p_valpag = float(s.get('VALPAG') or s.get('VALOR_PAGAR') or (p_tot - p_valdesc))

        unidades.append({
            "unidad": apto,
            "apto": apto,
            "bloque": bloq,
            "bloq": bloq,
            "propietario": prop,
            "cc": cc,
            "email": email,
            "telefono": tel,
            "coefNum": round(raw_c, 3),
            "coeficiente": f"{raw_c:.3f}%",
            "fac": fac,
            "actual": p_admon,
            "pend": p_pend,
            "inta": p_inta,
            "intp": p_intp,
            "otrosa": p_otrosa,
            "otrosp": p_otrosp,
            "extraa": p_extraa,
            "extrap": p_extrap,
            "multaa": p_multaa,
            "multap": p_multap,
            "serpua": p_serpua,
            "serpup": p_serpup,
            "servia": p_servia,
            "servip": p_servip,
            "ndnca": p_ndnca,
            "ndncp": p_ndncp,
            "admon": p_admon,
            "admonFmt": f"${p_admon:,.0f}".replace(",", "."),
            "interes": p_int,
            "interesFmt": f"${p_int:,.0f}".replace(",", "."),
            "otros": p_otr,
            "otrosFmt": f"${p_otr:,.0f}".replace(",", "."),
            "extra": p_ext,
            "extraFmt": f"${p_ext:,.0f}".replace(",", "."),
            "multa": p_mul,
            "multaFmt": f"${p_mul:,.0f}".replace(",", "."),
            "ser_pub": p_sp,
            "serPubFmt": f"${p_sp:,.0f}".replace(",", "."),
            "ser_serv": p_ss,
            "serServFmt": f"${p_ss:,.0f}".replace(",", "."),
            "notas_dc": p_nd,
            "notasDcFmt": f"${p_nd:,.0f}".replace(",", "."),
            "valdesc": p_valdesc,
            "valdescFmt": f"${p_valdesc:,.0f}".replace(",", "."),
            "valpag": p_valpag,
            "valpagFmt": f"${p_valpag:,.0f}".replace(",", "."),
            "saldoPendiente": f"${p_pend:,.0f}".replace(",", "."),
            "cuotaMensual": f"${p_admon:,.0f}".replace(",", "."),
            "totalNum": p_tot,
            "totalPagar": f"${p_tot:,.0f}".replace(",", "."),
            "totalFinal": p_tot,
            "estado": "En Mora" if (p_pend > 0 or p_inta > 0 or p_intp > 0 or p_tot > p_admon) else "Al Día",
            "tipo": "APTO"
        })

    # Quórum: Ajuste matemático exacto al 100.000% Ley 675
    if unidades:
        if tot_coef == 0.0:
            c_base = round(100.0 / len(unidades), 3)
            acum = 0.0
            for idx, u in enumerate(unidades):
                c = round(100.0 - acum, 3) if idx == len(unidades) - 1 else c_base
                acum += c
                u["coefNum"] = c
                u["coeficiente"] = f"{c:.3f}%"
        elif abs(tot_coef - 100.0) > 0.05 and tot_coef > 0:
            factor = 100.0 / tot_coef
            acum = 0.0
            for idx, u in enumerate(unidades):
                if idx == len(unidades) - 1:
                    c = round(100.0 - acum, 3)
                else:
                    c = round(u["coefNum"] * factor, 3)
                    acum += c
                u["coefNum"] = c
                u["coeficiente"] = f"{c:.3f}%"

    # Actualizar automáticamente data/edificio_{clean_cod}_master.json para sincronización perfecta con Render Cloud
    try:
        master_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"edificio_{clean_cod}_master.json")
        if clean_cod != "7480" or not os.path.exists(master_path):
            existing = {}
            if os.path.exists(master_path):
                try:
                    with open(master_path, "r", encoding="utf-8") as exf:
                        existing = json.load(exf)
                except Exception:
                    pass

            unidades_save = unidades
            master_obj = dict(existing)
            master_obj.update({
                "codigo": clean_cod,
                "nombre": edificio_info.get("nombre", f"Edificio #{clean_cod}"),
                "edificio": edificio_info,
                "unidades": unidades_save,
                "anios": existing.get("anios", [2026, 2025, 2024, 2023, 2022]),
                "inmueblesCount": len(unidades_save),
                "coeficienteTotal": f"{tot_coef:.3f}%" if tot_coef > 0 else "100.000%"
            })
            os.makedirs(os.path.dirname(master_path), exist_ok=True)
            with open(master_path, "w", encoding="utf-8") as f:
                json.dump(master_obj, f, ensure_ascii=False, indent=2)
    except Exception as ex_m:
        print(f"Error guardando master para {clean_cod}: {ex_m}")

    return {
        "status": "success",
        "codigo": clean_cod,
        "directorio": folder,
        "edificio": edificio_info,
        "unidades": unidades,
        "total": len(unidades),
        "archivos": {
            "edificio": os.path.basename(ed_path),
            "inmuebles": os.path.basename(mm_files[0]) if mm_files else "No encontrado",
            "cartera": os.path.basename(ss_chosen) if ss_chosen else "No encontrado"
        }
    }

def listar_edificios_dbplus() -> List[Dict[str, Any]]:
    """Lista todos los edificios disponibles en C:\\dbplus con carpetas y archivos contables."""
    disponibles = []
    base_dir = "C:/dbplus"
    if os.path.exists(base_dir):
        for entry in os.listdir(base_dir):
            full_p = os.path.join(base_dir, entry)
            if os.path.isdir(full_p):
                dbfs = glob.glob(f"{full_p}/*.DBF") + glob.glob(f"{full_p}/*.dbf")
                if dbfs:
                    disponibles.append({
                        "codigo": entry,
                        "archivos_count": len(dbfs),
                        "ruta": full_p
                    })
    return disponibles
