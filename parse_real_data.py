import os
import json

os.makedirs("data", exist_ok=True)

# Master row for building 7480
building_7480_master = {
    "id": "cj_7480",
    "nombre": "Edificio Manchester APTOS PH",
    "codigo": "7480",
    "nit": "900.777.367-7",
    "direccion": "Carrera 47 No 44-71, Bello • Antioquia",
    "ciudad": "Bello",
    "tipo": "Edificio Residencial",
    "banco": "Banco AV Villas",
    "tipoCuenta": "Cuenta Corriente",
    "cuenta": "512168063",
    "breb": "BREB-AVV-7480",
    "pasarela": "Wompi (pub_prod_7480)",
    "codigoAdmin": "ADM-7480",
    "passwordAdmin": "Admin123*",
    "administrador": "Clara Inés Guzmán",
    "telefono": "6007514 / 3147593118",
    "email": "edificiomanchesteraptos@gmail.com",
    "interesMora": "2.16%",
    "inmueblesCount": 44,
    "inmueblesOcupados": 44,
    "censoCount": 44,
    "vehiculosAuditoria": 5,
    "reservasConfirmadas": 3,
    "pqrAtencion": 2,
    "estado": "A Paz y Salvo",
    "bloqueadoMora": False
}

units_raw = [
    # APTO, PROPIETARIO, CC_NIT, COEF, ACTUAL, UT_PQ, PEND, INTP, INTA, TOTAL, TIPO
    ("0301", "JESUS EMILIO MONSALVE", "43562219", 2.588, 329800, "", 590810, 5700, 12800, 939110, "APTO"),
    ("0302", "Claudia Patricia Rodriguez F", "43814009", 1.947, 224500, "", 0, 0, 0, 224500, "APTO"),
    ("0303", "JOHN ENRIQUE VILLA TAMAYO", "3404957", 1.232, 142100, "", 142100, 0, 3100, 287300, "APTO"),
    ("0304", "CARLOS ANDRES RIOS JARAMILLO", "1017159919", 2.425, 279500, "UT. 12", 0, 0, 0, 279500, "APTO"),
    ("0305", "Andres Felipe Calderon Orozco", "71174924", 2.116, 244000, "", 244000, 0, 5300, 493300, "APTO"),
    ("0401", "AMAURY RETERÍA CUESTA", "54258293", 2.645, 304900, "UT. 11", 377700, 1600, 8200, 692400, "APTO"),
    ("0402", "SINDICATO TEXTIL DEL HATO FABR", "890905733", 1.947, 224500, "", 0, 0, 0, 224500, "APTO"),
    ("0403", "ALVARO ANTONIO GONZALEZ", "70071941", 1.232, 142100, "", 0, 0, 0, 142100, "APTO"),
    ("0404", "EDUARDO LUENGAS ESCOBAR", "72292963", 2.369, 273200, "", 338530, 0, 7300, 619030, "APTO"),
    ("0405", "BLACA NELLY GIRALDO", "", 2.116, 244000, "", 0, 0, 0, 244000, "APTO"),
    ("0501", "LUIS FERNANDO VILLEGAS", "8408410", 2.588, 298500, "", 718470, 0, 15500, 1032470, "APTO"),
    ("0502", "SOR MARÍA BEDOLLA", "21405979", 1.947, 224500, "", 0, 0, 0, 224500, "APTO"),
    ("0503", "FABIAN RUIZ MUNERA", "71226858", 1.232, 142100, "", -142100, 0, 0, 0, "APTO"),
    ("0504", "LUIS FELIPE GUZMAN BUSTAMANTE", "1000295216", 2.369, 273200, "", 0, 0, 0, 273200, "APTO"),
    ("0505", "MARIA DEL ROSARIO MUÑOZ", "21523497", 2.116, 244000, "", 0, 0, 0, 244000, "APTO"),
    ("0601", "ERIKA GARCÍA GÓMEZ", "43817793", 3.017, 364800, "PQ. 5", 570400, 4500, 12300, 952000, "APTO"),
    ("0602", "Gilberto González López", "8393411", 1.947, 224500, "", 0, 0, 0, 224500, "APTO"),
    ("0603", "Libardo Alfonso Berrio Lopez", "8389958", 1.232, 142100, "", 0, 0, 0, 142100, "APTO"),
    ("0604", "EDDIE GOMEZ BERROCAL", "78744600", 2.369, 273000, "", 561500, 6300, 12100, 852900, "APTO"),
    ("U604", "Sandra Laverde", "1036627461", 0.076, 8900, "UT. 9", 0, 0, 0, 8900, "UTIL"),
    ("0605", "LORENA CEBALLOS", "1020400554", 2.116, 244000, "", 0, 0, 0, 244000, "APTO"),
    ("0701", "Astrid Milena Duque", "43904816", 2.588, 298500, "", 0, 0, 0, 298500, "APTO"),
    ("0702", "DIEGO DE JESUS GONZALEZ", "32322656", 1.947, 224500, "", 0, 0, 0, 224500, "APTO"),
    ("0703", "LUIS FELIPE FRANCO GÓMEZ", "98702951", 1.232, 142100, "", 0, 0, 0, 142100, "APTO"),
    ("0704", "SANDRA ELIANA LAVERDE - NEVARDO MARIN", "98710270", 2.369, 287900, "", 0, 0, 0, 287900, "APTO"),
    ("0705", "MARINA MUÑETÓN YEPEZ", "21702139", 2.116, 244000, "", 0, 0, 0, 244000, "APTO"),
    ("0801", "GUSTAVO A. MEDINA A.", "8156706", 2.588, 298500, "", 11249380, 4738460, 243600, 16737740, "APTO"),
    ("P801", "GUSTAVO A. MEDINA A.", "8156706", 0.000, 0, "PARQ", 4754300, 6530110, 103000, 11403410, "PARQ"),
    ("0802", "KELIN DANIELA SANCHEZ VÉLEZ", "1020430370", 1.947, 224500, "", 241700, 0, 5200, 471400, "APTO"),
    ("0803", "INGRID TOBÓN RAMIREZ", "1152684469", 1.232, 142100, "", 284200, 3100, 6100, 435500, "APTO"),
    ("0804", "Jose Conrado Hernandez Castill", "3412250", 2.960, 346900, "PQ. 3 UT. 8", 0, 0, 0, 346900, "APTO"),
    ("0805", "EDWIN ANDRES PALACIO LOPEZ", "98663038", 2.532, 306800, "PQ. 1", 0, 0, 0, 306800, "APTO"),
    ("0901", "Maribel Berrio Moncada", "43917844", 2.868, 330700, "UT. 7", 675836, 7600, 14600, 1028736, "APTO"),
    ("0902", "JOSE ALEXANDER RODRIGUEZ", "80164948", 2.004, 231000, "UT. 10", 0, 0, 0, 231000, "APTO"),
    ("0903", "YURI ANDREA CASTAÑO", "42693745", 1.232, 142100, "", 0, 0, 0, 142100, "APTO"),
    ("0904", "ANGELA MARGARITA IDÁRRAGA", "22068994", 2.660, 306300, "UT. 6", 0, 0, 0, 306300, "APTO"),
    ("0905", "LINA MARÍA SEPULVEDA", "42902331", 2.116, 244000, "", 0, 0, 0, 244000, "APTO"),
    ("1001", "EDWIN PALACIO LOPEZ", "98663038", 3.166, 364800, "PQ. 4 UT. 5", 0, 0, 0, 364800, "APTO"),
    ("1002", "Joaquin Albeiro Vasquez Alzate", "70976310", 2.377, 274000, "PQ. 2", 0, 0, 0, 274000, "APTO"),
    ("1003", "ASTRID MARLENY VALENCIA GARCIA", "43677766", 1.232, 142100, "", 1104450, 76900, 23900, 1347350, "APTO"),
    ("1004", "MONICA LOPERA", "43637440", 2.369, 273200, "", 0, 0, 0, 273200, "APTO"),
    ("1005", "JESUS MARÍA MARTINEZ G.", "71490369", 2.116, 244000, "", 10324375, 4809130, 223500, 15803805, "APTO"),
    ("LC01", "JUAN JOSÉ PELAEZ", "900777367-7", 7.250, 836200, "LOCAL", 0, 0, 0, 836200, "LOCAL"),
    ("LC02", "JUAN JOSÉ PELAEZ", "900777367-7", 7.473, 861900, "LOCAL", 0, 0, 0, 861900, "LOCAL")
]

unidades_list = []
tot_pend = 0
tot_mes = 0
tot_final = 0
tot_coef = 0.0

for u in units_raw:
    apto, prop, cc, coef, act, ut_pq, pend, intp, inta, tot, tipo = u
    tot_pend += pend + intp
    tot_mes += act + inta
    tot_final += tot
    tot_coef += coef

    estado = "Al Día" if (pend + intp) <= 0 else "En Mora"
    unidades_list.append({
        "unidad": apto,
        "propietario": prop,
        "cc": cc,
        "coeficiente": f"{coef:.3f}%",
        "coefNum": coef,
        "tipo": tipo,
        "ubicacion": ut_pq,
        "saldoPendiente": f"${pend:,.0f}".replace(",", "."),
        "interesMora": f"${(intp + inta):,.0f}".replace(",", "."),
        "cuotaMensual": f"${act:,.0f}".replace(",", "."),
        "totalPagar": f"${tot:,.0f}".replace(",", "."),
        "totalNum": tot,
        "estado": estado
    })

building_7480_master["unidades"] = unidades_list
building_7480_master["coeficienteTotal"] = f"{tot_coef:.3f}%"
building_7480_master["recaudoTotal"] = f"${tot_mes:,.0f}".replace(",", ".")
building_7480_master["carteraPendiente"] = f"${tot_pend:,.0f}".replace(",", ".")
building_7480_master["totalCarteraFinal"] = f"${tot_final:,.0f}".replace(",", ".")
building_7480_master["recaudoPagos"] = "44 pagos procesados"
building_7480_master["carteraInmuebles"] = f"{len([u for u in unidades_list if u['estado'] == 'En Mora'])} inmuebles con saldo en mora"
building_7480_master["carteraVencida"] = "$48.219.051"
building_7480_master["carteraJuridica"] = "3 cuentas en cobro jurídico"

with open("data/edificio_7480_master.json", "w", encoding="utf-8") as f:
    json.dump(building_7480_master, f, ensure_ascii=False, indent=2)

print("Edificio 7480 generado exitosamente en data/edificio_7480_master.json")
