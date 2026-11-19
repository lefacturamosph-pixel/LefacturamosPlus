# LEFACTURAMOS PLUS 🏢
### Plataforma Integral de Facturación y Administración de Propiedad Horizontal (Ley 675 de 2001)

Bienvenido a **LefacturamosPlus**, el sistema independiente desarrollado en Python para gestionar la facturación completa, liquidación de mora, descuentos, emisión de listados contables oficiales y consulta de facturas/recibos para copropietarios.

---

## 📁 Rutas de Archivos en su Computador

1. **Código Fuente del Proyecto y Servidor:**  
   `C:\Users\CARLOS\LefacturamosPlus\`
2. **Directorio Local de Facturación (Mes Actual):**  
   `C:\LefacturamosPlus\`  
   *(Donde se generan y guardan automáticamente los 6 listados y las facturas del mes en curso)*
3. **Histórico y Backups por Año y Mes:**  
   `C:\LefacturamosPlus\Backup\<AÑO>\<MES>\`  
   *(Ejemplo: `C:\LefacturamosPlus\Backup\2027\Enero\`)*
4. **Base de Datos SQLite:**  
   `C:\LefacturamosPlus\lefacturamos_plus.db`

---

## 🚀 Cómo Iniciar el Sistema

* **Para el Administrador (Panel Completo):**
  Haga doble clic en:
  👉 `C:\Users\CARLOS\LefacturamosPlus\iniciar_lefacturamos_plus.bat`  
  *(Abre automáticamente en `http://127.0.0.1:8100/`)*

* **Para los Copropietarios (Portal Móvil de Consulta de Facturas y Recibos):**
  Haga doble clic en:
  👉 `C:\Users\CARLOS\LefacturamosPlus\iniciar_portal_residentes.bat`  
  *(Abre en `http://127.0.0.1:8100/portal`)*

* **Compilar APK de Android:**
  Haga doble clic en:
  👉 `C:\Users\CARLOS\LefacturamosPlus\build_apk.bat`  
  *(Compila `LefacturamosPlus_Android.apk`)*

---

## 🏛️ Módulos Completados del Sistema

1. **🏢 Configuración de Copropiedades (Edificios):**
   * Código de 4 dígitos alfanumérico.
   * Nombre completo, NIT, Tipo de copropiedad (Residencial, Comercial, Mixta, etc.).
   * Tipo de interés y tasa mensual de mora (Ley 675).
   * Consecutivos de facturas y recibos de caja.
   * Descuento por pronto pago y fecha de vencimiento.
   * Mes actual y mes anterior de facturación.
   * Cuentas bancarias oficiales para recaudo.

2. **📋 Personalización de los 15 Ítems de Facturación:**
   * Ítem 1: Cuota Ordinaria de Administración.
   * Ítem 2: Interés de Mora del Mes.
   * Ítems 3 al 15: Configurables libremente (Cuotas extras, fondo de imprevistos, servicios, seguros, sanciones, etc.).

3. **👥 Copropietarios y Coeficientes:**
   * Tipos de inmueble: `AP` (Apartamento), `CA` (Casa), `OF` (Oficina), `CO` (Consultorio), `LC` (Local), `UT` (Útil), `PQ` (Parqueadero), `BJ` (Burbuja).
   * Coeficientes individuales por cada bien privado con cálculo automático del **Coeficiente Total**.
   * Nombre de copropietario, nombre de inquilino, celular y correos de contacto.
   * Descarga de plantilla oficial en Excel y carga masiva por archivo `.xlsx`.

4. **⚡ Motor de Facturación y Liquidación:**
   * Liquidación automática de cuotas e intereses de mora.
   * Aplicación de descuentos por pronto pago.
   * Clasificación de cartera por edades (<30 días, 60 días, 90 días, >90 días).
   * Botón directo de envío por **WhatsApp** a cada residente.

5. **📄 Generación de los 6 Listados y Documentos Oficiales en PDF:**
   * `[EDIFICIO].-- LISTADO DE FACTURACION  -- [MES].PDF`
   * `[EDIFICIO].-- LISTADO DE PENDIENTES  -- [MES].PDF` (Detallado y totalizado por edades y conceptos).
   * `[EDIFICIO].-- LISTADO DE DESCUENTOS  -- [MES].PDF`
   * `[EDIFICIO].-- LISTADO DE PAGOS  -- [MES_ANTERIOR].PDF`
   * `[EDIFICIO].-- LISTADO DE RECIBOS DE CAJA  -- [MES_ANTERIOR].PDF`
   * `[EDIFICIO].-- RECIBOS DE CAJA  -- [MES_ANTERIOR].PDF`
   * `FACTURAS DE COBRO [EDIFICIO] -- [MES].PDF` (Formato doble cuerpo Propietario / Administración).

6. **📱 Portal Web / Móvil para Copropietarios:**
   * Búsqueda por unidad.
   * Búsqueda en `C:\LefacturamosPlus\` si es el mes actual.
   * Búsqueda en `C:\LefacturamosPlus\Backup\<AÑO>\<MES>\` si es un mes anterior.
   * Descarga instantánea de facturas y recibos de caja.
