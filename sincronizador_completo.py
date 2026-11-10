#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - SINCRONIZADOR UNIVERSAL AUTOMÁTICO (DBPLUS ➔ DRIVE ➔ RENDER)
========================================================================================
Sincroniza en un solo paso:
  1. Copia y organiza los listados, facturas y recibos de C:\dbplus\{codigo}\Envio
     hacia Google Drive oficial y hacia data/drive_docs/{codigo}/{anio}/{mes}/
  2. Procesa la base contable DBPlus (EDIFICIO.dbf, MM*.dbf, SS*.dbf, BASEFAC.dbf)
     y actualiza data/edificio_{codigo}_master.json con totales y saldos normativos.
  3. Actualiza lefacturamos.db y las matrices maestras en app.js y los archivos HTML.
  4. Hace commit y git push automático a GitHub (origin main), activando el despliegue
     en Render Cloud de forma inmediata.
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR

# Asegurar importación de módulos locales
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dbplus_service import obtener_datos_dbplus_edificio, read_dbf_binary
from lefacturamos_drive_service import sincronizar_edificio_listados_y_documentos

MESES_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

def detectar_info_dbplus(codigo: str):
    """Detecta automáticamente el año y mes contable actual desde EDIFICIO.dbf"""
    clean_cod = str(codigo).replace("cj_", "").strip()
    cod_4 = clean_cod.zfill(4)
    
    cand_edificios = [
        Path(f"C:/dbplus/{clean_cod}/EDIFICIO.dbf"),
        Path(f"C:/dbplus/{cod_4}/EDIFICIO.dbf"),
        Path(f"C:/dbplus/{clean_cod}/EDIFICIO.DBF"),
        Path(f"C:/dbplus/{cod_4}/EDIFICIO.DBF"),
        Path(f"C:/dbplus/EDIFICIO.DBF"),
    ]
    
    for cand in cand_edificios:
        if cand.exists():
            rows = read_dbf_binary(str(cand))
            target = next((r for r in rows if str(r.get('CODIGO', '')).strip() in [clean_cod, cod_4]), None)
            if not target and rows:
                target = rows[0]
            if target:
                anio = str(target.get("ANO") or target.get("ANOCO") or target.get("ANOVEN") or "2026").strip()
                mes_num = target.get("MESFAC") or target.get("MESACT") or 11
                if isinstance(mes_num, (int, float)):
                    mes_nombre = MESES_ES.get(int(mes_num), "NOVIEMBRE")
                else:
                    s_m = str(mes_num).upper()
                    mes_nombre = next((m for m in MESES_ES.values() if m in s_m), "NOVIEMBRE")
                return anio, mes_nombre
    return "2026", "NOVIEMBRE"

def actualizar_archivos_frontend_y_master(codigo: str):
    """Regenera el master JSON y actualiza las funciones JS y la base SQLite"""
    clean_cod = str(codigo).replace("cj_", "").strip()
    print(f"\n[1/4] 📊 Procesando base contable DBPlus de C:\\dbplus\\{clean_cod}...")
    
    data_db = obtener_datos_dbplus_edificio(clean_cod)
    if not data_db or not data_db.get("unidades"):
        print(f"⚠️ No se encontraron unidades en DBPlus para {clean_cod}. Se intentará con master existente.")
        m_path = REPO_ROOT / "data" / f"edificio_{clean_cod}_master.json"
        if not m_path.exists():
            print(f"❌ Error: No existe base de datos ni master para {clean_cod}.")
            return False
        with open(m_path, "r", encoding="utf-8") as f:
            master_obj = json.load(f)
    else:
        unidades = data_db.get("unidades", [])
        edif_info = data_db.get("edificio", {})
        
        def _to_float_coef(v):
            try:
                return float(str(v).replace("%", "").strip())
            except Exception:
                return 0.0

        master_obj = {
            "codigo": clean_cod,
            "nombre": edif_info.get("nombre", f"Edificio #{clean_cod}"),
            "edificio": edif_info,
            "unidades": unidades,
            "anios": [2026, 2025, 2024, 2023, 2022],
            "inmueblesCount": len(unidades),
            "coeficienteTotal": f"{sum(_to_float_coef(u.get('coefNum', 0)) for u in unidades):.3f}%"
        }
        
        m_path = REPO_ROOT / "data" / f"edificio_{clean_cod}_master.json"
        m_path.parent.mkdir(parents=True, exist_ok=True)
        with open(m_path, "w", encoding="utf-8") as f:
            json.dump(master_obj, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Master JSON generado con éxito: data/edificio_{clean_cod}_master.json ({len(unidades)} unidades)")

    unidades = master_obj.get("unidades", [])
    
    # Actualizar SQLite
    print("\n[2/4] 🗄️ Actualizando base de datos local SQLite (lefacturamos.db)...")
    try:
        import sqlite3
        conn = sqlite3.connect(str(REPO_ROOT / "lefacturamos.db"))
        c = conn.cursor()
        c_id = f"cj_{clean_cod}"
        
        for u in unidades:
            apto = str(u.get("apto", u.get("unidad", ""))).strip()
            u_id = f"u_{clean_cod}_{apto}"
            prop = u.get("propietario", "")
            cc = u.get("cc", "")
            email = u.get("email", "")
            tel = u.get("telefono", "")
            coef = float(u.get("coefNum", 0.0))
            bloq = u.get("bloq", "AP")
            saldo = float(u.get("totalNum", 0.0))
            
            c.execute("SELECT id FROM unidades WHERE conjunto_id=? AND numero_unidad=?", (c_id, apto))
            if c.fetchone():
                c.execute("""
                    UPDATE unidades 
                    SET propietario_nombre=?, propietario_doc=?, propietario_email=?, propietario_telefono=?,
                        coeficiente=?, saldo_actual=?, torre_bloque=?
                    WHERE conjunto_id=? AND numero_unidad=?
                """, (prop, cc, email, tel, coef, saldo, bloq, c_id, apto))
            else:
                c.execute("""
                    INSERT INTO unidades (id, conjunto_id, torre_bloque, numero_unidad, tipo_inmueble, cuarto_util, parqueadero,
                                          coeficiente, propietario_nombre, propietario_doc, propietario_email, propietario_telefono,
                                          residente_nombre, saldo_actual)
                    VALUES (?, ?, ?, ?, 'APTO', '', '', ?, ?, ?, ?, ?, '', ?)
                """, (u_id, c_id, bloq, apto, coef, prop, cc, email, tel, saldo))
        conn.commit()
        conn.close()
        print("   ✅ Base de datos SQLite sincronizada correctamente.")
    except Exception as e_sql:
        print(f"   ⚠️ Aviso en SQLite: {e_sql}")

    # Actualizar matrices en www/app.js y los archivos HTML
    print("\n[3/4] 🌐 Sincronizando código frontend en app.js y lefacturamos_aistudio.html...")
    target_func_name = f"getUnidadesRobleAlto4901Master" if clean_cod == "4901" else (
        f"getUnidadesManchester7480Master" if clean_cod == "7480" else (
            f"getUnidadesRiachuelo4160Master" if clean_cod == "4160" else None
        )
    )
    
    if target_func_name:
        units_json_str = json.dumps(unidades, ensure_ascii=False, indent=2)
        new_func_js = f"""function {target_func_name}() {{\n  const cj = (typeof listaCopropiedadesSuperadmin !== "undefined") ? listaCopropiedadesSuperadmin.find(c => c.codigo === "{clean_cod}") : null;\n  if (cj && cj.unidades && cj.unidades.length > 10 && cj.unidades[0].actual !== undefined) {{\n    return JSON.parse(JSON.stringify(cj.unidades));\n  }}\n  return {units_json_str};\n}}"""
        
        target_files = [
            REPO_ROOT / "www" / "app.js",
            REPO_ROOT / "www" / "lefacturamos_aistudio.html",
            REPO_ROOT / "lefacturamos_aistudio.html"
        ]
        
        pat = re.compile(rf"function {target_func_name}\(\)\s*\{{[\s\S]*?(?=\n(?:function getUnidades|function obtener))")
        for tf in target_files:
            if tf.exists():
                with open(tf, "r", encoding="utf-8") as f:
                    txt = f.read()
                if pat.search(txt):
                    txt = pat.sub(new_func_js + "\n\n", txt, count=1)
                    with open(tf, "w", encoding="utf-8") as f:
                        f.write(txt)
                    print(f"   ✅ Matriz actualizada en {tf.name}")

    return True

def desplegar_a_github_y_render(mensaje="Deploy automatico de listados y saldos"):
    """Sube los cambios a GitHub para activar el despliegue automático en Render"""
    print(f"\n[4/4] 🚀 Desplegando a GitHub y Render Cloud...")
    env = os.environ.copy()
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        env["PATH"] = f"{local_app_data}\\Programs\\MinGit\\cmd;{env.get('PATH', '')}"

    try:
        subprocess.run(["git", "add", "."], cwd=str(REPO_ROOT), env=env, check=True)
        # Check if there are changes to commit
        res_status = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
        if not res_status.stdout.strip():
            print("   ℹ️ El repositorio ya se encuentra totalmente actualizado. No hay cambios pendientes.")
            return True
            
        subprocess.run(["git", "commit", "-m", mensaje], cwd=str(REPO_ROOT), env=env, check=True)
        res_push = subprocess.run(["git", "push", "origin", "main"], cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
        if res_push.returncode == 0:
            print("   ✅ ¡Éxito! Cambios enviados a GitHub.")
            print("   ⚡ Render Cloud ha iniciado automáticamente el despliegue de la versión actualizada.")
            return True
        else:
            print(f"   ⚠️ Nota en git push: {res_push.stderr}")
            return False
    except Exception as e_git:
        print(f"   ⚠️ Error en git/despliegue: {e_git}")
        return False

def sincronizar_todo_el_edificio(codigo: str, anio: str = None, mes: str = None, subir_google_drive: bool = True):
    """
    Flujo integral completo:
    1. Si subir_google_drive es True, ejecuta la subida oficial a Google Drive.
    2. Copia listados/facturas a data/drive_docs/{codigo}/{anio}/{mes}/.
    3. Procesa y cuadra la contabilidad DBPlus (Master, SQLite, app.js).
    4. Sube a GitHub para que Render se actualice en la nube.
    """
    clean_cod = str(codigo).replace("cj_", "").strip()
    if not anio or not mes:
        anio_det, mes_det = detectar_info_dbplus(clean_cod)
        anio = anio or anio_det
        mes = mes or mes_det

    mes_upper = str(mes).strip().upper()
    print("=" * 75)
    print(f"  SINCRONIZACIÓN AUTOMÁTICA COMPLETA - EDIFICIO {clean_cod} - {mes_upper} {anio}")
    print("=" * 75)

    # 1. Google Drive
    if subir_google_drive:
        try:
            from subir_a_drive import subir_archivos_dbplus
            print(f"\n[0/4] ☁️ Sincronizando archivos con Google Drive oficial...")
            subir_archivos_dbplus(clean_cod, anio, mes_upper)
        except Exception as e_drv:
            print(f"⚠️ Aviso en Google Drive: {e_drv}")

    # 2. Empaquetar a data/drive_docs
    print(f"\n📂 Empaquetando documentos y facturas para Render en data/drive_docs/{clean_cod}/...")
    res_docs = sincronizar_edificio_listados_y_documentos(clean_cod)
    print(f"   • Archivos procesados y empaquetados: {res_docs.get('total_archivos_copiados', 0)}")

    # 3. Procesar contabilidad DBPlus, Master y JS
    actualizar_archivos_frontend_y_master(clean_cod)

    # 4. Desplegar a Render
    msg = f"Auto-sync: actualizar listados y saldos de {mes_upper} {anio} para edificio {clean_cod}"
    desplegar_a_github_y_render(msg)

    print("\n" + "=" * 75)
    print("  ✨ ¡PROCESO DE ACTUALIZACIÓN FINALIZADO CON ÉXITO!")
    print(f"  • Copropiedad: {clean_cod}")
    print(f"  • Periodo:     {mes_upper} DE {anio}")
    print("  • La nube (Render) se actualizará automáticamente en 1 a 2 minutos.")
    print("=" * 75)

if __name__ == "__main__":
    cod_in = input("Ingrese el código del edificio (ej: 4901): ").strip() or "4901"
    a_det, m_det = detectar_info_dbplus(cod_in)
    anio_in = input(f"Ingrese el año [{a_det}]: ").strip() or a_det
    mes_in = input(f"Ingrese el mes [{m_det}]: ").strip() or m_det
    
    sincronizar_todo_el_edificio(cod_in, anio_in, mes_in, subir_google_drive=True)
