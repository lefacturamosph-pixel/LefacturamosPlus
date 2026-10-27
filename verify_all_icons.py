import re
import os

with open("www/assets/lucide.js", "r", encoding="utf-8") as f:
    lucide_js = f.read()

# Extract available icons in lucide.js
start_str = "var iconAndAliases = /*#__PURE__*/Object.freeze({"
start_idx = lucide_js.find(start_str)
end_str = "});\n\n  const createIcons"
end_idx = lucide_js.find(end_str, start_idx)
block = lucide_js[start_idx:end_idx]

pascal_icons = set(re.findall(r'^\s*([A-Za-z0-9]+):', block, re.MULTILINE))
pascal_icons.discard("__proto__")

def lucide_to_pascal(string):
    out = ""
    upper_next = False
    for ch in string:
        if ch == "-" or ch == "_" or ch <= " ":
            upper_next = len(out) > 0
        else:
            if upper_next:
                out += ch.upper()
                upper_next = False
            else:
                out += ch
    if not out:
        return ""
    return out[0].upper() + out[1:]

print("="*70)
print(f"VERIFICACIÓN INTEGRAL DE ICONOS LUCIDE EN LEFACTURAMOS")
print("="*70)
print(f"Catálogo oficial de Lucide Icons disponible: {len(pascal_icons)} iconos.")

# 1. Analizar index.html
with open("www/index.html", "r", encoding="utf-8") as f:
    html_lines = f.readlines()

html_errors = []
html_icon_counts = {}

for line_no, line in enumerate(html_lines, 1):
    matches = re.finditer(r'data-lucide=["\']([^"\']*)["\']', line)
    for m in matches:
        icon_name = m.group(1).strip()
        if not icon_name:
            html_errors.append((line_no, "Icono vacío data-lucide=''", line.strip()))
            continue
        pascal = lucide_to_pascal(icon_name)
        if pascal not in pascal_icons:
            html_errors.append((line_no, f"Icono desconocido '{icon_name}' (Pascal: {pascal})", line.strip()))
        else:
            html_icon_counts[icon_name] = html_icon_counts.get(icon_name, 0) + 1

print(f"\n[HTML] Ocurrencias en index.html: {sum(html_icon_counts.values())} etiquetas <i> con {len(html_icon_counts)} iconos distintos.")
if html_errors:
    print(f"[HTML] ERRORES ENCONTRADOS: {len(html_errors)}")
    for err in html_errors:
        print(f"  Línea {err[0]}: {err[1]}")
else:
    print("  [OK] 100% de iconos en index.html son validos y reconocidos por Lucide.")

# 2. Analizar app.js
with open("www/app.js", "r", encoding="utf-8") as f:
    js_lines = f.readlines()

js_errors = []
js_icon_counts = {}

for line_no, line in enumerate(js_lines, 1):
    # data-lucide in template literals
    m1 = re.finditer(r'data-lucide=["\'`]([^"\'`]+)["\'`]', line)
    for m in m1:
        raw = m.group(1).strip()
        if "${" in raw:
            # check extracted literals inside template
            sub_literals = re.findall(r'[\'"]([a-z0-9-]+)[\'"]', raw)
            for sub in sub_literals:
                pascal = lucide_to_pascal(sub)
                if pascal not in pascal_icons:
                    js_errors.append((line_no, f"Icono en template '${{{raw}}}' -> '{sub}' no existe", line.strip()))
                else:
                    js_icon_counts[sub] = js_icon_counts.get(sub, 0) + 1
        else:
            pascal = lucide_to_pascal(raw)
            if pascal not in pascal_icons:
                js_errors.append((line_no, f"Icono desconocido '{raw}'", line.strip()))
            else:
                js_icon_counts[raw] = js_icon_counts.get(raw, 0) + 1

    # icono: "..."
    m2 = re.finditer(r'icono:\s*["\']([^"\']+)["\']', line)
    for m in m2:
        raw = m.group(1).strip()
        pascal = lucide_to_pascal(raw)
        if pascal not in pascal_icons:
            js_errors.append((line_no, f"Propiedad icono '{raw}' no existe", line.strip()))
        else:
            js_icon_counts[raw] = js_icon_counts.get(raw, 0) + 1

print(f"\n[JS] Ocurrencias en app.js: {sum(js_icon_counts.values())} referencias con {len(js_icon_counts)} iconos distintos.")
if js_errors:
    print(f"[JS] ERRORES ENCONTRADOS: {len(js_errors)}")
    for err in js_errors:
        print(f"  Línea {err[0]}: {err[1]}")
else:
    print("  [OK] 100% de iconos dinamicos y menus en app.js son validos y reconocidos por Lucide.")

# 3. Reporte de Categorías y Módulos
print("\n" + "="*70)
print("DISTRIBUCION Y COBERTURA DE ICONOS:")
total_distintos = set(html_icon_counts.keys()).union(set(js_icon_counts.keys()))
print(f"Total iconos distintos verificados: {len(total_distintos)}")
for ic in sorted(total_distintos):
    count = html_icon_counts.get(ic, 0) + js_icon_counts.get(ic, 0)
    print(f"  - {ic:<24} -> {lucide_to_pascal(ic):<24} ({count} usos)")

print("\n" + "="*70)
if not html_errors and not js_errors:
    print("RESULTADO: TODOS LOS ICONOS DEL PROGRAMA ESTAN 100% FUNCIONANDO Y VERIFICADOS.")
else:
    print("RESULTADO: SE ENCONTRARON ICONOS QUE REQUIEREN CORRECCION.")
print("="*70)
