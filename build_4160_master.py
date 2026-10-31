import struct, json, os, re

def read_dbf_cp850(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'rb') as f:
        header = f.read(32)
        if len(header) < 32:
            return []
        num_records, header_len, record_len = struct.unpack('<IHH', header[4:12])
        num_fields = (header_len - 33) // 32
        fields = []
        for _ in range(num_fields):
            fld = f.read(32)
            fname = fld[:11].replace(b'\x00', b'').decode('ascii', errors='ignore').strip().upper()
            ftype = chr(fld[11])
            flen = fld[16]
            fields.append((fname, ftype, flen))
        f.seek(header_len)
        records = []
        for _ in range(num_records):
            rec_bytes = f.read(record_len)
            if len(rec_bytes) < record_len or rec_bytes[0:1] == b'*':
                continue
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

basefac_rows = read_dbf_cp850('C:/dbplus/4160/BASEFAC.DBF')
edificio_rows = read_dbf_cp850('C:/dbplus/4160/EDIFICIO.DBF')
if not edificio_rows:
    edificio_rows = read_dbf_cp850('C:/dbplus/EDIFICIO.DBF')
target_ed = next((r for r in edificio_rows if str(r.get('CODIGO','')).strip() == '4160'), {})

unidades = []
total_coef = 0.0

for r in basefac_rows:
    apto = str(r.get('APTO', '')).strip()
    if not apto: continue
    prop = str(r.get('NOM', '')).strip()
    cc = str(r.get('CC_NIT', '')).strip()
    bloq = str(r.get('BLOQ', '00')).strip()
    direc_pq = str(r.get('DIREC', '')).strip() # Parking space e.g. 'PQ 10', 'PQ 4'
    tipo = str(r.get('TIPO', 'APTO')).strip()
    
    coef_float = float(r.get('COEF_URB') or 0.0)
    total_coef += coef_float
    admon = float(r.get('ACTUAL') or 0.0)
    pend = float(r.get('PEND') or 0.0)
    inta = float(r.get('INTA') or 0.0)
    intp = float(r.get('INTP') or 0.0)
    valpag = float(r.get('VALPAG') or 0.0)
    total_num = float(r.get('TOTAL') or (admon + pend + inta))
    fac = int(r.get('FAC') or 0)
    
    # Parking details
    parqueadero_num = ""
    tipo_parqueadero = "Visita"
    if direc_pq:
        parqueadero_num = direc_pq
        tipo_parqueadero = "Privado / Propietario"
    
    u_obj = {
        "unidad": apto,
        "apto": apto,
        "bloque": bloq or "00",
        "bloq": bloq or "00",
        "propietario": prop,
        "cc": cc,
        "email": f"apto{apto.lower()}@edificioriachuelo.com" if not cc else f"propietario{apto}@lefacturamos.com",
        "telefono": "3155979738",
        "coefNum": round(coef_float, 3),
        "coeficiente": f"{coef_float:.3f}%",
        "fac": fac,
        "actual": admon,
        "admon": admon,
        "admonFmt": f"${int(admon):,}".replace(",", "."),
        "pend": pend,
        "saldoPendiente": f"${int(pend):,}".replace(",", "."),
        "inta": inta,
        "intp": intp,
        "interes": inta,
        "interesFmt": f"${int(inta):,}".replace(",", "."),
        "otros": 0,
        "otrosFmt": "$0",
        "extra": 0,
        "extraFmt": "$0",
        "multa": 0,
        "multaFmt": "$0",
        "ser_pub": 0,
        "serPubFmt": "$0",
        "ser_serv": 0,
        "serServFmt": "$0",
        "notas_dc": 0,
        "notasDcFmt": "$0",
        "valdesc": 0,
        "valdescFmt": "$0",
        "valpag": valpag,
        "valpagFmt": f"${int(valpag):,}".replace(",", "."),
        "totalNum": total_num,
        "totalPagar": f"${int(total_num):,}".replace(",", "."),
        "totalFinal": total_num,
        "cuotaMensual": f"${int(admon):,}".replace(",", "."),
        "estado": "Al Día" if pend <= 0 else "En Mora",
        "tipo": tipo or "APTO",
        "ubicacion": f"Torre 1 - Piso {apto[:2] if len(apto)>=3 else '1'}",
        "parqueadero": parqueadero_num,
        "tipo_parqueadero": tipo_parqueadero,
        "direccion": direc_pq
    }
    unidades.append(u_obj)

edificio_dict = {
    "codigo": "4160",
    "nombre": "Edificio Mixto Riachuelo",
    "nit": target_ed.get("NITURBAN") or "901079657-7",
    "direccion": target_ed.get("DIREC") or "CALLE 76D SUR No 43A - 100",
    "ciudad": "Medellín • Antioquia",
    "banco": target_ed.get("BANCO") or "BANCOLOMBIA",
    "tipoCuenta": "Corriente" if "CTE" in str(target_ed.get("BANCO","")).upper() else "Ahorros",
    "cuenta": target_ed.get("CUENTA") or "436-848008-18",
    "administrador": target_ed.get("NUCODADMON") or "JAVIER MAURICIO PEREZ MESA",
    "telefono": target_ed.get("TEL") or "3221929",
    "email": target_ed.get("EMAILURBAN") or "jorgeaugustorestrepob@gmail.com;riachueloph@gmail.com;javierperezadmon@gmail.com",
    "interesMora": target_ed.get("INTPORC") or "1%",
    "tipo": "Propiedad Horizontal",
    "anios": [2026, 2025, 2024, 2023, 2022],
    "inmueblesCount": len(unidades),
    "inmueblesOcupados": len(unidades),
    "censoCount": len(unidades),
    "coeficienteTotal": f"{total_coef:.3f}%"
}

master_payload = {
    "codigo": "4160",
    "nombre": "Edificio Mixto Riachuelo",
    "edificio": edificio_dict,
    "unidades": unidades
}

os.makedirs('data', exist_ok=True)
with open('data/edificio_4160_master.json', 'w', encoding='utf-8') as f:
    json.dump(master_payload, f, ensure_ascii=False, indent=2)

print(f"Generated data/edificio_4160_master.json successfully with {len(unidades)} units! Total coef: {total_coef:.3f}%")
