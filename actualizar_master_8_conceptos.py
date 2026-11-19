import openpyxl
import json

wb_ss = openpyxl.load_workbook("SS7480.xlsx")
ws_ss = wb_ss.active
h_ss = [ws_ss.cell(1, c).value for c in range(1, ws_ss.max_column + 1)]

with open("data/edificio_7480_master.json", "r", encoding="utf-8") as f:
    master = json.load(f)

unidades_existentes = {u["unidad"]: u for u in master.get("unidades", [])}

nuevas_unidades = []
tot_admon = 0.0
tot_interes = 0.0
tot_otros = 0.0
tot_extra = 0.0
tot_multa = 0.0
tot_ser_pub = 0.0
tot_ser_serv = 0.0
tot_notas_dc = 0.0
tot_gran_total = 0.0

def fmt_cop(val: float) -> str:
    formatted = f"{val:,.0f}".replace(",", ".")
    return f"${formatted}"

for r in range(2, ws_ss.max_row + 1):
    row_vals = [ws_ss.cell(r, c).value for c in range(1, ws_ss.max_column + 1)]
    apto = str(row_vals[h_ss.index("APTO")]).strip()
    bloq = str(row_vals[h_ss.index("BLOQ")]).strip()
    fac = row_vals[h_ss.index("FAC")]
    
    pend = float(row_vals[h_ss.index("PEND")] or 0)
    intp = float(row_vals[h_ss.index("INTP")] or 0)
    otrosp = float(row_vals[h_ss.index("OTROSP")] or 0)
    extrap = float(row_vals[h_ss.index("EXTRAP")] or 0)
    multap = float(row_vals[h_ss.index("MULTAP")] or 0)
    serpup = float(row_vals[h_ss.index("SERPUP")] or 0)
    servip = float(row_vals[h_ss.index("SERVIP")] or 0)
    ndncp = float(row_vals[h_ss.index("NDNCP")] or 0)
    
    actual = float(row_vals[h_ss.index("ACTUAL")] or 0)
    inta = float(row_vals[h_ss.index("INTA")] or 0)
    otrosa = float(row_vals[h_ss.index("OTROSA")] or 0)
    extraa = float(row_vals[h_ss.index("EXTRAA")] or 0)
    multaa = float(row_vals[h_ss.index("MULTAA")] or 0)
    serpua = float(row_vals[h_ss.index("SERPUA")] or 0)
    servia = float(row_vals[h_ss.index("SERVIA")] or 0)
    ndnca = float(row_vals[h_ss.index("NDNCA")] or 0)
    
    admon = pend + actual
    interes = intp + inta
    otros = otrosp + otrosa
    extra = extrap + extraa
    multa = multap + multaa
    ser_pub = serpup + serpua
    ser_serv = servip + servia
    notas_dc = ndncp + ndnca
    
    total_fila = admon + interes + otros + extra + multa + ser_pub + ser_serv + notas_dc
    
    tot_admon += admon
    tot_interes += interes
    tot_otros += otros
    tot_extra += extra
    tot_multa += multa
    tot_ser_pub += ser_pub
    tot_ser_serv += ser_serv
    tot_notas_dc += notas_dc
    tot_gran_total += total_fila
    
    u_prev = unidades_existentes.get(apto, {})
    prop = u_prev.get("propietario", "")
    cc = u_prev.get("cc", "")
    coef = u_prev.get("coeficiente", "0.000%")
    coef_num = u_prev.get("coefNum", 0.0)
    tipo = u_prev.get("tipo", "APTO")
    ubic = u_prev.get("ubicacion", "")
    
    nuevas_unidades.append({
        "unidad": apto,
        "apto": apto,
        "bloq": bloq,
        "fac": fac,
        "propietario": prop,
        "cc": cc,
        "coeficiente": coef,
        "coefNum": coef_num,
        "tipo": tipo,
        "ubicacion": ubic,
        "pend": pend, "intp": intp, "otrosp": otrosp, "extrap": extrap,
        "multap": multap, "serpup": serpup, "servip": servip, "ndncp": ndncp,
        "actual": actual, "inta": inta, "otrosa": otrosa, "extraa": extraa,
        "multaa": multaa, "serpua": serpua, "servia": servia, "ndnca": ndnca,
        "admon": admon,
        "interes": interes,
        "otros": otros,
        "extra": extra,
        "multa": multa,
        "ser_pub": ser_pub,
        "ser_serv": ser_serv,
        "notas_dc": notas_dc,
        "admonFmt": fmt_cop(admon),
        "interesFmt": fmt_cop(interes),
        "otrosFmt": fmt_cop(otros),
        "extraFmt": fmt_cop(extra),
        "multaFmt": fmt_cop(multa),
        "serPubFmt": fmt_cop(ser_pub),
        "serServFmt": fmt_cop(ser_serv),
        "notasDcFmt": fmt_cop(notas_dc),
        "saldoPendiente": fmt_cop(pend),
        "cuotaMensual": fmt_cop(actual),
        "totalPagar": fmt_cop(total_fila),
        "totalNum": int(total_fila),
        "estado": "En Mora" if (pend > 0 or interes > 0 or total_fila > actual) else "Al Día"
    })

master["unidades"] = nuevas_unidades
master["totales_concepto"] = {
    "admon": tot_admon,
    "interes": tot_interes,
    "otros": tot_otros,
    "extra": tot_extra,
    "multa": tot_multa,
    "ser_pub": tot_ser_pub,
    "ser_serv": tot_ser_serv,
    "notas_dc": tot_notas_dc,
    "gran_total": tot_gran_total,
    "admonFmt": fmt_cop(tot_admon),
    "interesFmt": fmt_cop(tot_interes),
    "otrosFmt": fmt_cop(tot_otros),
    "extraFmt": fmt_cop(tot_extra),
    "multaFmt": fmt_cop(tot_multa),
    "serPubFmt": fmt_cop(tot_ser_pub),
    "serServFmt": fmt_cop(tot_ser_serv),
    "notasDcFmt": fmt_cop(tot_notas_dc),
    "granTotalFmt": fmt_cop(tot_gran_total)
}

with open("data/edificio_7480_master.json", "w", encoding="utf-8") as f:
    json.dump(master, f, ensure_ascii=False, indent=2)

print(f"OK: 44 unidades con los 8 conceptos guardadas en data/edificio_7480_master.json")
print(f"Totales: Admon={fmt_cop(tot_admon)}, Interes={fmt_cop(tot_interes)}, Otros={fmt_cop(tot_otros)}, Extra={fmt_cop(tot_extra)}, GranTotal={fmt_cop(tot_gran_total)}")
