import json
import re

# Load parsed building 7480
with open("data/edificio_7480_master.json", "r", encoding="utf-8") as f:
    cop_7480 = json.load(f)

# Format the 44 units nicely for JS
units_js_lines = []
for u in cop_7480["unidades"]:
    units_js_lines.append(
        f'      {{ unidad: "{u["unidad"]}", propietario: "{u["propietario"]}", cc: "{u["cc"]}", coeficiente: "{u["coeficiente"]}", tipo: "{u["tipo"]}", ubicacion: "{u["ubicacion"]}", saldoPendiente: "{u["saldoPendiente"]}", interesMora: "{u["interesMora"]}", cuotaMensual: "{u["cuotaMensual"]}", totalPagar: "{u["totalPagar"]}", estado: "{u["estado"]}" }}'
    )
units_js_str = ",\n".join(units_js_lines)

cj_7480_js = f'''  {{
    id: "cj_7480",
    nombre: "Edificio Manchester APTOS PH",
    codigo: "7480",
    nit: "900.777.367-7",
    direccion: "Carrera 47 No 44-71, Bello • Antioquia",
    ciudad: "Bello",
    tipo: "Edificio Residencial",
    banco: "Banco AV Villas",
    tipoCuenta: "Corriente",
    cuenta: "512168063",
    breb: "BREB-AVV-7480",
    pasarela: "Wompi (pub_prod_7480)",
    codigoAdmin: "ADM-7480",
    passwordAdmin: "Admin123*",
    administrador: "Clara Inés Guzmán",
    telefono: "6007514 / 3147593118",
    email: "edificiomanchesteraptos@gmail.com",
    interesMora: "2.16%",
    inmueblesCount: 44,
    inmueblesOcupados: 44,
    censoCount: 44,
    vehiculosAuditoria: 5,
    reservasConfirmadas: 3,
    pqrAtencion: 2,
    coeficienteTotal: "100.000%",
    recaudoTotal: "$12.310.800",
    recaudoPagos: "44 pagos procesados",
    carteraPendiente: "$48.645.651",
    totalFinalEdificio: "$60.956.451",
    carteraInmuebles: "16 inmuebles con saldo en mora",
    carteraVencida: "$48.645.651",
    carteraJuridica: "3 cuentas en cobro jurídico",
    estado: "A Paz y Salvo",
    bloqueadoMora: false,
    unidades: [
{units_js_str}
    ]
  }},'''

# 1. Update www/app.js building 7480
with open("www/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace cj_7480 block
target_7480_regex = r'  \{\s*id:\s*"cj_7480",[\s\S]*?unidades:\s*\[[\s\S]*?\]\s*\},'
if re.search(target_7480_regex, app_js):
    app_js = re.sub(target_7480_regex, cj_7480_js, app_js, count=1)
    print("[OK] Edificio 7480 actualizado en www/app.js con las 44 unidades reales!")
else:
    print("[ERROR] No se encontró el bloque regex para cj_7480 en app.js")

# 2. Update verColumnasYReglas in www/app.js to render the exact table
drawer_func_js = '''function verColumnasYReglas(tipo) {
  const drawer = document.getElementById("drawer-columnas-reglas");
  const tit = document.getElementById("drawer-cr-titulo");
  const cont = document.getElementById("drawer-cr-contenido");
  if (!drawer || !tit || !cont) return;

  const catalog = {
    unidades: {
      titulo: "ESTRUCTURA Y REGLAS: 1. UNIDADES, COEFICIENTES Y PARQUEADEROS",
      filas: [
        { col: "Torre", req: true, ej: "Torre 1", desc: "Nombre o bloque de la torre" },
        { col: "Numero_Unidad", req: true, ej: "101", desc: "Número del apartamento, local u oficina" },
        { col: "Tipo_Inmueble", req: true, ej: "Apartamento", desc: "Apartamento / Local / Oficina / Casa" },
        { col: "Coeficiente_Porcentaje", req: true, ej: "1.25", desc: "Coeficiente en porcentaje (debe sumar 100.00% el conjunto)" },
        { col: "Area_M2", req: false, ej: "78.5", desc: "Área privada construida en m2" },
        { col: "Cuarto_Util", req: false, ej: "CU-01", desc: "Identificador del depósito o cuarto útil privado" },
        { col: "Parqueadero_Privado", req: false, ej: "P-12", desc: "Número del parqueadero privado asignado" },
        { col: "Parqueadero_Moto", req: false, ej: "PM-04", desc: "Número del parqueadero de moto privado (si aplica)" }
      ]
    },
    residentes: {
      titulo: "ESTRUCTURA Y REGLAS: 2. PROPIETARIOS Y RESIDENTES",
      filas: [
        { col: "Numero_Unidad", req: true, ej: "101", desc: "Número del apartamento o unidad asociada" },
        { col: "Nombre_Completo", req: true, ej: "Carlos Andrés Restrepo", desc: "Nombres y apellidos completos del titular" },
        { col: "Tipo_Documento", req: true, ej: "CC", desc: "Tipo oficial: CC, NIT, CE, Pasaporte" },
        { col: "Numero_Documento", req: true, ej: "43562219", desc: "Documento oficial sin puntos ni guiones" },
        { col: "Telefono_Celular", req: true, ej: "3154225734", desc: "Número de 10 dígitos para citofonía y WhatsApp" },
        { col: "Correo_Electronico", req: true, ej: "propietario@email.com", desc: "Email para facturación electrónica y actas" },
        { col: "Condicion_Habitante", req: true, ej: "Propietario Residente", desc: "Propietario / Inquilino / Tenedor" },
        { col: "Recibe_Notificaciones", req: false, ej: "SI", desc: "Acepta citaciones a asamblea vía electrónica" },
        { col: "Autoriza_Datos", req: true, ej: "SI", desc: "Autorización Habeas Data Ley 1581 de 2012" }
      ]
    },
    cartera: {
      titulo: "ESTRUCTURA Y REGLAS: 3. CARTERA, FACTURAS Y SALDOS INICIALES",
      filas: [
        { col: "Numero_Unidad", req: true, ej: "101", desc: "Número de apartamento a conciliar" },
        { col: "Saldo_Anterior", req: true, ej: "590810", desc: "Saldo acumulado de meses anteriores (Mora)" },
        { col: "Cuota_Ordinaria", req: true, ej: "329800", desc: "Valor cuota de administración ordinaria del mes" },
        { col: "Intereses_Mora", req: false, ej: "12800", desc: "Intereses calculados conforme a tasa legal vigente" },
        { col: "Cuota_Extraordinaria", req: false, ej: "0", desc: "Cuotas extraordinarias vigentes aprobadas por asamblea" },
        { col: "Fondo_Imprevistos", req: false, ej: "0", desc: "Fondo imprevistos discriminado si aplica" },
        { col: "Seguro_Zonas_Comunes", req: false, ej: "0", desc: "Póliza común prorrateada por coeficiente" },
        { col: "Otros_Conceptos", req: false, ej: "0", desc: "Parqueadero de visitantes, multas o conceptos varios" },
        { col: "Total_Final", req: true, ej: "939110", desc: "Total general consolidado al corte" },
        { col: "Estado_Cartera", req: true, ej: "En Mora", desc: "Al Día / En Mora / Cobro Jurídico" }
      ]
    },
    mascotas: {
      titulo: "ESTRUCTURA Y REGLAS: 4. CENSO DE MASCOTAS Y VEHÍCULOS",
      filas: [
        { col: "Numero_Unidad", req: true, ej: "101", desc: "Unidad residencial de residencia" },
        { col: "Tipo_Mascota", req: true, ej: "Canino", desc: "Canino / Felino / Otra especie" },
        { col: "Raza", req: true, ej: "Golden Retriever", desc: "Raza (especificar razas de manejo especial)" },
        { col: "Nombre_Mascota", req: true, ej: "Max", desc: "Nombre del animal de compañía" },
        { col: "Microchip_Placa", req: false, ej: "COL-98214", desc: "Número de microchip o placa de censo" },
        { col: "Vacunas_Al_Dia", req: true, ej: "SI", desc: "Carné de vacunas y antirrábica al día (Ley 2054)" },
        { col: "Tipo_Vehiculo", req: false, ej: "Automóvil", desc: "Automóvil / Camioneta / Motocicleta" },
        { col: "Placa_Vehiculo", req: false, ej: "ABC-123", desc: "Placa registrada para control de acceso en portería" }
      ]
    },
    saldos: {
      titulo: "ESTRUCTURA Y REGLAS: 5. BASE DE DATOS DE SALDOS POR COPROPIETARIO (ssxxxx)",
      filas: [
        { col: "APTO", req: true, ej: "0301", desc: "Código de unidad residencial" },
        { col: "BLOQ", req: false, ej: "00", desc: "Bloque o torre del edificio" },
        { col: "FAC", req: true, ej: "3889", desc: "Número de factura / recibo consecutivo" },
        { col: "Admon_Pendiente", req: true, ej: "590810", desc: "Saldo acumulado pendiente de administración" },
        { col: "Admon_Actual", req: true, ej: "329800", desc: "Cuota de administración del período facturado" },
        { col: "Interes_Mora", req: false, ej: "18500", desc: "Intereses acumulados por mora" },
        { col: "Otros_Cobros", req: false, ej: "0", desc: "Cargos adicionales y multas" },
        { col: "Cuota_Extra", req: false, ej: "0", desc: "Cuota extraordinaria del período" },
        { col: "TOTAL_FINAL", req: true, ej: "939110", desc: "Gran total de la cuenta de cobro" }
      ]
    }
  };

  const item = catalog[tipo] || catalog.unidades;
  tit.innerText = item.titulo;

  cont.innerHTML = `
    <table class="w-full text-left text-xs font-sans">
      <thead class="bg-slate-950/90 text-slate-400 border-b border-slate-800 text-[10px] uppercase font-bold">
        <tr>
          <th class="py-2.5 px-3">Columna Oficial</th>
          <th class="py-2.5 px-3">Requerido</th>
          <th class="py-2.5 px-3">Ejemplo</th>
          <th class="py-2.5 px-3">Descripción / Validación</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800/80 text-white text-xs">
        ${item.filas.map(f => `
          <tr class="hover:bg-slate-950/50 transition-colors">
            <td class="py-2 px-3 font-mono font-semibold text-teal-300">${f.col}</td>
            <td class="py-2 px-3">
              ${f.req ? '<span class="px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800/60 font-bold text-[9px]">OBLIGATORIO</span>' : '<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-semibold text-[9px]">OPCIONAL</span>'}
            </td>
            <td class="py-2 px-3 font-mono text-slate-300">${f.ej}</td>
            <td class="py-2 px-3 text-slate-400 text-xs">${f.desc}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

  drawer.classList.remove("hidden");
  drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
}'''

target_ver_regex = r'function verColumnasYReglas\(tipo\) \{[\s\S]*?drawer\.scrollIntoView\(\{ behavior: "smooth", block: "nearest" \}\);\s*\}'
if re.search(target_ver_regex, app_js):
    app_js = re.sub(target_ver_regex, drawer_func_js, app_js, count=1)
    print("[OK] verColumnasYReglas actualizada en www/app.js!")
else:
    print("[ERROR] No se encontró verColumnasYReglas en app.js")

with open("www/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

# 3. Update www/index.html
with open("www/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Update badge 18 columnas to 10 columnas
html = html.replace(
    '<span class="shrink-0 px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700 font-mono text-[10px]">18 columnas</span>',
    '<span class="shrink-0 px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700 font-mono text-[10px]">10 columnas</span>'
)

# Update drawer header in index.html to match screenshot exactly
drawer_old = '<div id="drawer-columnas-reglas" class="hidden p-4 rounded-2xl bg-slate-950 border border-emerald-500/40 space-y-2.5">'
drawer_new = '''<!-- ESTRUCTURA Y REGLAS: 1. UNIDADES, COEFICIENTES Y PARQUEADEROS (SEGÚN SCREENSHOT OFICIAL) -->
        <div id="drawer-columnas-reglas" class="hidden bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 space-y-3 shadow-lg">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
            <span class="text-xs sm:text-sm font-extrabold text-white tracking-wide uppercase" id="drawer-cr-titulo">
              ESTRUCTURA Y REGLAS: 1. UNIDADES, COEFICIENTES Y PARQUEADEROS
            </span>
            <span class="text-xs font-semibold text-emerald-400">
              Cumplimiento estricto Ley 675 de 2001
            </span>
          </div>
          <div id="drawer-cr-contenido" class="overflow-x-auto">
            <!-- Tabla dinámica -->
          </div>
        </div>'''

if drawer_old in html:
    # replace drawer_old up to drawer closing
    drawer_full_old = re.search(r'<div id="drawer-columnas-reglas" class="hidden p-4 rounded-2xl bg-slate-950 border border-emerald-500/40 space-y-2\.5">[\s\S]*?</div>\s*</div>', html)
    if drawer_full_old:
        html = html.replace(drawer_full_old.group(0), drawer_new + "\n        </div>")
        print("[OK] drawer-columnas-reglas actualizado en www/index.html!")

with open("www/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Todas las modificaciones aplicadas exitosamente.")
