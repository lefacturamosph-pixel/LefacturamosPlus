# LEFACTURAMOS - Suite de Integración en Python
## Para Windows, Android, iOS y Servidores Locales

Esta suite en Python está diseñada para que puedas:
1. **Convertir masivamente tus bases de datos actuales en Excel** a las plantillas oficiales de **LEFACTURAMOS** sin tener que digitar registro por registro.
2. **Validar automáticamente los coeficientes de copropiedad** según la **Ley 675 de 2001 de Colombia** (asegurando que la suma de todas las unidades dé exactamente el 100.00%).
3. **Ejecutar el backend en Windows** o como API REST para clientes móviles (Android e iOS).

---

### Paso 1: Instalación en Windows
Abre tu consola de comandos (PowerShell o CMD) y escribe:
```bash
pip install pandas openpyxl tabulate fastapi uvicorn requests
```

---

### Paso 2: Conversión Automática de tu Excel
Coloca tu archivo de Excel (por ejemplo: `Mis_Copropietarios_2026.xlsx`) en la misma carpeta del script y ejecuta:
```bash
python lefacturamos_excel_migrator.py --archivo "Mis_Copropietarios_2026.xlsx"
```

El script auto-detectará tus columnas actuales (como "Apto", "Dueño", "Metros", "Valor Cuota") y generará el archivo oficial `LEFACTURAMOS_Base_Convertida.xlsx`.

---

### Paso 3: Carga en la Plataforma
Abre la plataforma web **LEFACTURAMOS**, ve al menú **"Plantillas & Conversor Excel"**, sube el archivo generado y en **1 solo clic** tendrás todas las torres, apartamentos, propietarios y estados de cartera listos.
