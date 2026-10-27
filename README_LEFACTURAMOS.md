# LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal

Sistema integral multiplataforma desarrollado en **Python** para la gestión de copropiedades, conjuntos residenciales, edificios, centros comerciales y parques empresariales bajo el régimen de la **Ley 675 de 2001** de Colombia.

Compatible con **Windows (Escritorio nativo)**, **Android (APK)**, **iOS** y **Web**.

---

## 🚀 Inicio Rápido (Centro de Control en Python)

Para iniciar cualquier componente de la plataforma en Windows, abra su terminal en `C:\Users\CARLOS\LefacturamosApp` y ejecute:

```powershell
python run_lefacturamos.py
```

### Opciones de línea de comandos directas:
* **Aplicación de Escritorio Flet (Python Nativo):**
  ```powershell
  python run_lefacturamos.py --desktop
  # O directamente:
  python app_flet.py
  ```
* **Servidor Backend API (FastAPI - Puerto 8000):**
  ```powershell
  python run_lefacturamos.py --server
  ```
* **Plataforma Web / Móvil (Puerto 8080):**
  ```powershell
  python run_lefacturamos.py --web
  ```
* **Ejecutar Suite de Pruebas Automatizadas (12 Módulos):**
  ```powershell
  python run_lefacturamos.py --test
  ```
* **Compilar APK de Android (Gradle Debug Build):**
  ```powershell
  python run_lefacturamos.py --build-apk
  ```

---

## 🏛️ 1. Arquitectura Multi-Conjunto (Multi-Tenant)

La plataforma maneja múltiples conjuntos manteniendo los datos **100% aislados** entre cada copropiedad:
* **Copropiedad 7480:** `EDIFICIO MANCHESTER APTOS PH` (Bello) - Cuenta Corriente AV-Villas No. 512168063.
* **Copropiedad 2609:** `CONJUNTO RESIDENCIAL LOS SAUCES PH` (Bogotá) - Cuenta Ahorros Bancolombia No. 031-894520-11.
* **Copropiedad 0127:** `CENTRO COMERCIAL GRAN PLAZA PH` (Medellín) - Cuenta Corriente Davivienda No. 1020304050.

---

## 👥 2. Perfiles y Roles de Usuario

1. **Superadministrador:**
   * Crea conjuntos, edificios y centros comerciales con su NIT y cuenta bancaria.
   * Asigna administradores y configura pasarelas de pago (Wompi, Bold, PayU, Bre-B).
   * Monitorea métricas globales y logs de auditoría.
2. **Administrador del Conjunto:**
   * Gestiona únicamente los edificios asignados con contraseña independiente.
   * Dashboard con los **10 indicadores obligatorios** en tiempo real.
   * Administra coeficientes de propiedad (Apto, Cuarto Útil, Parqueadero).
   * Monta pagos de administración a contratistas con empresa, detalle de obras, garantía y fecha.
   * Responde PQR avanzando por los 5 estados oficiales.
   * Publica comunicados segmentados y crea votaciones de asamblea.
3. **Residente / Copropietario:**
   * Solo accede a su edificio y a su apartamento/local asignado.
   * Consulta facturación del mes desglosada (Admón, Intereses, Imprevistos, Multas, Servicios).
   * Paga mediante **Bre-B (Pagos Inmediatos Colombia)**, **PSE**, **Botón Bancolombia**, **Wompi**, **Nequi**, **Daviplata**.
   * Descarga facturas y recibos de caja en PDF directamente desde el Google Drive oficial (`LefacturamosPH@lefacturamos.com`).
   * Reserva zonas comunes y autoriza visitas con código QR temporal.
   * Registra mascotas y vota en asamblea con ponderación por coeficiente.
4. **Portería & Seguridad:**
   * Terminal de validación de visitantes en **menos de 2 segundos**.
   * Escaneo de código QR o digitación de token.
   * Levantamiento de talanquera y notificación push en vivo al residente.
   * Registro de domicilios (Rappi, mensajería), contratistas y técnicos.

---

## 🏊‍♂️ 3. Módulo de Reservas de Zonas Comunes

### Catálogo de Áreas Disponibles:
* **Zonas Húmedas:** Sauna Spa, Jacuzzi Climatizado, Baño Turco.
* **Social & Recreación:** Salón Social Principal, BBQ y Pérgola, Cine / Sala Multimedia, Salón de Juegos, Piscina Semi-Olímpica.
* **Deportes:** Cancha de Tenis, Cancha de Fútbol Sintética, Cancha Múltiple, Gimnasio & Zona Cardio.
* **Coworking:** Sala Coworking & Sala de Juntas.
* **Otras Zonas:** Configurables dinámicamente por la administración.

### Flujo Interactivo:
$$\text{Residente} \longrightarrow \text{Zona} \longrightarrow \text{Fecha} \longrightarrow \text{Disponibilidad} \longrightarrow \text{Horario} \longrightarrow \text{Acepta Reglamento} \longrightarrow \text{Reserva Confirmada}$$

---

## 📱 4. Control de Visitantes con Código QR Inteligente (2 Segundos)

* **Generación:** El residente crea una autorización con nombre, documento, fecha/hora y placa de vehículo.
* **Envío a WhatsApp:** Botón de un solo clic que abre WhatsApp con el mensaje y código de acceso.
* **Validación en Portería:** El guarda escanea el QR. El sistema verifica vigencia y destino en **1.8 segundos**.
* **Levantamiento y Trazabilidad:** Registra hora de entrada y salida en la nube y envía notificación push instantánea al residente.

---

## 💳 5. Pagos Colombianos y Conciliación Bancaria

* **Bre-B (Sistema de Pagos Inmediatos del Banco de la República):**
  * Generación de llave interoperable: `BREB-<Edificio>-<Apto>-<Valor>`.
  * Código QR interoperable para transferencias inmediatas de 0 segundos.
* **PSE & Banca Nacional:** Integración con los 16 bancos y billeteras digitales de Colombia (Bancolombia, Davivienda, AV Villas, Bogotá, BBVA, Nequi, Daviplata, Nu, Lulo).
* **Asociación Estricta:**
  $$\text{Conjunto} \longrightarrow \text{Apartamento} \longrightarrow \text{Copropietario} \longrightarrow \text{Factura} \longrightarrow \text{Pago} \longrightarrow \text{Referencia Transacción}$$
* **Conciliación Automática:** Cruce de pagos recibidos contra facturas pendientes y emisión de Recibo de Caja oficial.

---

## 🐾 6. Censo de Mascotas (Ley 1801)

Registro completo con:
* Nombre, Tipo (Perro, Gato, Ave), Raza, Sexo, Color.
* Identificación (Microchip o Placa).
* Certificación de vacunas al día y fecha de vacuna antirrábica.
* Observaciones de comportamiento o razas de manejo especial.

---

## 📢 7. Comunicados y Segmentación

Publicación de circulares, alertas, cortes de agua/energía y mantenimientos con segmentación:
* Todo el conjunto
* Una torre específica
* Un bloque específico
* Determinados apartamentos

---

## 📝 8. PQR (Peticiones, Quejas, Reclamos y Daños)

* Consecutivo único (ej: `PQR-2026-001`).
* Posibilidad de adjuntar fotografías, videos y documentos PDF.
* Flujo de 5 estados:
  $$\text{Recibida} \longrightarrow \text{En revisión} \longrightarrow \text{En proceso} \longrightarrow \text{Respondida} \longrightarrow \text{Cerrada}$$

---

## 🗳️ 9. Votaciones y Asambleas (Ley 675)

* Preguntas de asamblea (ej: *¿Aprueba el presupuesto para el año 2027?*).
* Opciones: Sí, No, Abstención.
* **Ponderación Estricta:** Cada voto pondera según el coeficiente de copropiedad de la unidad (ej: 2.588%).
* Cálculo de quórum y mayorías deliberatorias en tiempo real.

---

## ⚖️ 10. Compendio Legal de la Ley 675 de 2001

Buscador interactivo indexado por palabras clave y subíndices de resolución:
* Coeficientes de propiedad
* Expensas y cuotas comunes
* Asambleas y quórums calificados (70%)
* Funciones del Administrador
* Comité de convivencia y solución de conflictos

---

## 📂 11. Google Drive Oficial

* **Repositorio Central:** [Carpeta Google Drive Lefacturamos](https://drive.google.com/drive/folders/1-yY_fmN65Qc7bpFwYouKksE4r8fSOLjR?usp=drive_link)
* **Cuenta Administradora:** `LefacturamosPH@lefacturamos.com`
* Facturas y Recibos de caja en PDF por apartamento con control de acceso individual.
* Informes contables consolidados en PDF y Excel para el Administrador.
