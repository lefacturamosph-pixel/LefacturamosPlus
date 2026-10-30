#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal
Módulo de Base de Datos Multi-Conjunto y Repositorio de Datos
Soporta: SQLite nativo en Python, compatible con Windows, Android (vía API/Flet) e iOS.
"""

import sqlite3
import json
import os
import hashlib
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lefacturamos.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_base_datos():
    """Crea todas las tablas necesarias para la arquitectura multi-conjunto de LEFACTURAMOS"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabla de Conjuntos / Edificios / Centros Comerciales (Multi-tenant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conjuntos (
        id TEXT PRIMARY KEY,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        tipo TEXT DEFAULT 'Residencial', -- Residencial, Edificio, Centro Comercial, Mixto
        nit TEXT NOT NULL,
        direccion TEXT,
        telefono TEXT,
        email TEXT,
        banco TEXT,
        tipo_cuenta TEXT DEFAULT 'Corriente', -- Ahorros, Corriente
        numero_cuenta TEXT,
        titular_cuenta TEXT,
        wompi_public_key TEXT,
        wompi_private_key TEXT,
        bold_api_key TEXT,
        payu_merchant_id TEXT,
        bre_b_codigo_entidad TEXT,
        google_drive_folder_id TEXT DEFAULT '1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E',
        drive_email TEXT DEFAULT 'LefacturamosPH@lefacturamos.com',
        clave_porteria TEXT DEFAULT 'Porteria123*',
        activo INTEGER DEFAULT 1,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tabla de Usuarios y Roles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT, -- NULL para superadmin
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        email TEXT NOT NULL,
        telefono TEXT,
        rol TEXT NOT NULL, -- superadmin, admin, residente, porteria
        unidad_id TEXT, -- Para residentes (apto/local)
        activo INTEGER DEFAULT 1,
        ultimo_acceso TIMESTAMP,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 3. Unidades (Apartamentos, Casas, Locales, Oficinas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unidades (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        torre_bloque TEXT NOT NULL,
        numero_unidad TEXT NOT NULL, -- 0101, 0502, Local 12
        tipo_inmueble TEXT DEFAULT 'Apartamento', -- Apartamento, Casa, Local, Oficina
        cuarto_util TEXT,
        parqueadero TEXT,
        coeficiente REAL DEFAULT 1.0, -- Coeficiente Ley 675
        propietario_nombre TEXT,
        propietario_doc TEXT,
        propietario_email TEXT,
        propietario_telefono TEXT,
        residente_nombre TEXT,
        saldo_actual REAL DEFAULT 0.0,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 4. Facturación Mensual y Conceptos Detallados (Ley 675 / DBPlus)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        numero_factura TEXT NOT NULL,
        periodo_mes TEXT NOT NULL, -- ej: Octubre 2026
        anio INTEGER DEFAULT 2026,
        fecha_emision DATE NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        fecha_pronto_pago DATE,
        descuento_pronto_pago REAL DEFAULT 0.0,
        
        -- Conceptos desagregados DBPlus / Homologación
        val_admon REAL DEFAULT 0.0,
        val_interes REAL DEFAULT 0.0,
        val_otros REAL DEFAULT 0.0,
        val_extra REAL DEFAULT 0.0,
        val_multa REAL DEFAULT 0.0,
        val_ser_pub REAL DEFAULT 0.0,
        val_ser_serv REAL DEFAULT 0.0,
        val_notas_dc REAL DEFAULT 0.0,
        
        saldo_anterior REAL DEFAULT 0.0,
        total_a_pagar REAL NOT NULL,
        valor_pronto_pago REAL NOT NULL,
        
        cufe TEXT,
        estado TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, PAGADA, ANULADA
        pdf_drive_url TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 5. Pagos, Transacciones y Pasarelas de Pago
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        factura_id TEXT,
        monto REAL NOT NULL,
        metodo_pago TEXT NOT NULL, -- Bre-B, PSE, Tarjeta, Wompi, Bold, PayU, Nequi, Daviplata, Bancolombia, Efectivo
        referencia_transaccion TEXT UNIQUE NOT NULL,
        estado TEXT DEFAULT 'INICIADO', -- INICIADO, PENDIENTE, APROBADO, RECHAZADO, REEMBOLSADO
        banco_origen TEXT,
        codigo_aprobacion TEXT,
        fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        recibo_caja_numero TEXT,
        drive_recibo_url TEXT,
        comprobante_url TEXT,
        auditoria_webhook TEXT,
        conciliado INTEGER DEFAULT 0,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id),
        FOREIGN KEY (factura_id) REFERENCES facturas(id)
    );
    """)

    # 6. Zonas Comunes del Conjunto
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zonas_comunes (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL, -- Zonas Humedas, Deportes, Social, Coworking, Otras
        capacidad_maxima INTEGER DEFAULT 10,
        tiempo_max_horas REAL DEFAULT 2.0,
        anticipacion_min_horas INTEGER DEFAULT 24,
        costo_alquiler REAL DEFAULT 0.0,
        reglas_uso TEXT,
        dias_disponibles TEXT DEFAULT 'Lunes,Martes,Miercoles,Jueves,Viernes,Sabado,Domingo',
        hora_apertura TEXT DEFAULT '06:00',
        hora_cierre TEXT DEFAULT '22:00',
        activo INTEGER DEFAULT 1,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 7. Reservas de Zonas Comunes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        zona_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        residente_nombre TEXT NOT NULL,
        fecha_reserva DATE NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        personas_estimadas INTEGER DEFAULT 1,
        costo REAL DEFAULT 0.0,
        condiciones_aceptadas INTEGER DEFAULT 1,
        estado TEXT DEFAULT 'CONFIRMADA', -- CONFIRMADA, COMPLETADA, CANCELADA, PENALIZADA
        notas TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (zona_id) REFERENCES zonas_comunes(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 8. Autorizaciones de Visitantes y Códigos QR Inteligentes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visitantes_autorizaciones (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        residente_nombre TEXT NOT NULL,
        visitante_nombre TEXT NOT NULL,
        visitante_doc TEXT NOT NULL,
        visitante_telefono TEXT,
        fecha_esperada DATE NOT NULL,
        hora_esperada TEXT,
        duracion_estimada_horas REAL DEFAULT 4.0,
        placa_vehiculo TEXT,
        numero_acompanantes INTEGER DEFAULT 0,
        tipo_visita TEXT DEFAULT 'Social', -- Social, Frecuente, Domicilio, Tecnico, Contratista
        observaciones TEXT,
        token_qr TEXT UNIQUE NOT NULL,
        estado TEXT DEFAULT 'AUTORIZADO', -- AUTORIZADO, INGRESADO, FINALIZADO, VENCIDO, ANULADO
        ingreso_timestamp TIMESTAMP,
        salida_timestamp TIMESTAMP,
        guardia_porteria TEXT,
        notificado_residente INTEGER DEFAULT 0,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 9. Registro de Mascotas (Censo de la Copropiedad)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mascotas (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL, -- Perro, Gato, Ave, Otro
        raza TEXT,
        sexo TEXT, -- Macho, Hembra
        color TEXT,
        fecha_nacimiento TEXT,
        identificacion_placa TEXT, -- Microchip o No. Placa
        vacunas_al_dia INTEGER DEFAULT 1,
        fecha_antirrabica DATE,
        fotografia_url TEXT,
        observaciones TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 10. Comunicados, Noticias, Circulares y Alertas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comunicados (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        titulo TEXT NOT NULL,
        categoria TEXT NOT NULL, -- Noticia, Comunicado, Circular, Alerta, Mantenimiento, Corte Agua, Corte Energia, Evento, Asamblea
        contenido TEXT NOT NULL,
        alcance TEXT DEFAULT 'TODO_EL_CONJUNTO', -- TODO_EL_CONJUNTO, TORRE, BLOQUE, DETERMINADOS_APTOS
        alcance_detalle TEXT, -- ej: "Torre 1" o "0101,0102,0201"
        prioridad TEXT DEFAULT 'NORMAL', -- BAJA, NORMAL, URGENTE, EMERGENCIA
        autor TEXT NOT NULL,
        adjunto_url TEXT,
        fecha_publicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notificacion_push_enviada INTEGER DEFAULT 1,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 11. PQR (Peticiones, Quejas, Reclamos, Solicitudes, Reportes de Daño)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pqr (
        id TEXT PRIMARY KEY,
        consecutivo TEXT UNIQUE NOT NULL, -- PQR-2026-001
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        residente_nombre TEXT NOT NULL,
        categoria TEXT NOT NULL, -- Peticion, Queja, Reclamo, Solicitud, Reporte de daño
        asunto TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        archivos_adjuntos TEXT, -- JSON con URLs
        estado TEXT DEFAULT 'RECIBIDA', -- RECIBIDA, EN_REVISION, EN_PROCESO, RESPONDIDA, CERRADA
        responsable TEXT,
        respuesta TEXT,
        fecha_respuesta TIMESTAMP,
        historial TEXT, -- JSON con eventos de cambio de estado
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 12. Votaciones y Asambleas (Ley 675 con Voto Ponderado por Coeficiente)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votaciones (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        titulo TEXT NOT NULL, -- ej: ¿Aprueba el presupuesto para el año 2027?
        descripcion TEXT,
        opciones TEXT DEFAULT '["Sí", "No", "Voto en Blanco"]', -- JSON list
        estado TEXT DEFAULT 'ABIERTA', -- ABIERTA, CERRADA, PROGRAMADA
        fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_fin TIMESTAMP,
        quorum_minimo REAL DEFAULT 51.0, -- Porcentaje
        requiere_paz_y_salvo INTEGER DEFAULT 0,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votos (
        id TEXT PRIMARY KEY,
        votacion_id TEXT NOT NULL,
        conjunto_id TEXT NOT NULL,
        unidad_id TEXT NOT NULL,
        opcion_seleccionada TEXT NOT NULL,
        coeficiente_aplicado REAL NOT NULL, -- Ponderación Ley 675
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_registro TEXT,
        UNIQUE(votacion_id, unidad_id),
        FOREIGN KEY (votacion_id) REFERENCES votaciones(id),
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id),
        FOREIGN KEY (unidad_id) REFERENCES unidades(id)
    );
    """)

    # 13. Pagos de Administración a Proveedores y Contratistas (Gastos PH)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos_proveedores (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        empresa_proveedor TEXT NOT NULL,
        nit_proveedor TEXT,
        concepto_servicio TEXT NOT NULL,
        detalle_trabajos TEXT NOT NULL,
        garantia_meses INTEGER DEFAULT 0,
        valor_pagado REAL NOT NULL,
        fecha_pago DATE NOT NULL,
        soporte_url TEXT,
        aprobado_por TEXT,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 14. Compendio Legal de la Ley 675 de 2001 (Buscador y Subíndices de Resolución)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ley_675 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        capitulo TEXT NOT NULL,
        articulo INTEGER NOT NULL,
        titulo TEXT NOT NULL,
        subindice TEXT NOT NULL,
        pregunta_resolucion TEXT NOT NULL,
        resolucion_practica TEXT NOT NULL,
        aplicable_a TEXT DEFAULT 'Ambos',
        contenido TEXT NOT NULL,
        palabras_clave TEXT
    );
    """)

    # Migración de columnas si la tabla ya existía
    cursor.execute("PRAGMA table_info(ley_675)")
    cols_ley = [c[1] for c in cursor.fetchall()]
    if "pregunta_resolucion" not in cols_ley:
        cursor.execute("ALTER TABLE ley_675 ADD COLUMN pregunta_resolucion TEXT")
    if "resolucion_practica" not in cols_ley:
        cursor.execute("ALTER TABLE ley_675 ADD COLUMN resolucion_practica TEXT")
    if "aplicable_a" not in cols_ley:
        cursor.execute("ALTER TABLE ley_675 ADD COLUMN aplicable_a TEXT DEFAULT 'Ambos'")

    # 15. Informes Oficiales y Actas de Asambleas (Ley 675)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asambleas_informes (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        titulo_asamblea TEXT NOT NULL,
        fecha_asamblea DATE NOT NULL,
        tipo_convocatoria TEXT DEFAULT 'Ordinaria',
        quorum_inicial_coef REAL DEFAULT 0.0,
        total_preguntas INTEGER DEFAULT 0,
        contenido_acta TEXT NOT NULL,
        datos_consolidados TEXT NOT NULL,
        creado_por TEXT NOT NULL,
        drive_url TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conjunto_id) REFERENCES conjuntos(id)
    );
    """)

    # 16. Auditoría de Seguridad y Registro de Actividades
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS minuta_porteria (
        id TEXT PRIMARY KEY,
        conjunto_id TEXT NOT NULL,
        tipo TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        inmueble TEXT NOT NULL,
        portero TEXT NOT NULL,
        titulo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        token_qr TEXT,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS log_auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conjunto_id TEXT,
        usuario TEXT,
        rol TEXT,
        accion TEXT NOT NULL,
        modulo TEXT NOT NULL,
        detalle TEXT,
        ip_origen TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("[OK] Base de datos de LEFACTURAMOS inicializada exitosamente.")

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def sembrar_datos_iniciales():
    """Siembra los edificios reales detectados (7480 Manchester, 2609 Sauces), usuarios, zonas, Ley 675, etc."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si ya existen conjuntos
    cursor.execute("SELECT COUNT(*) as c FROM conjuntos")
    if cursor.fetchone()["c"] > 0:
        cursor.execute("SELECT COUNT(*) as c FROM ley_675")
        if cursor.fetchone()["c"] < 20:
            sembrar_ley_675(conn)
        conn.close()
        return

    print("[*] Sembrando datos de arranque multi-conjunto para LEFACTURAMOS...")

    # 1. Conjunto 1: EDIFICIO MANCHESTER APTOS PH (Código 7480)
    conjunto_7480_id = "cj_7480"
    cursor.execute("""
    INSERT INTO conjuntos (id, codigo, nombre, tipo, nit, direccion, telefono, email, banco, tipo_cuenta, numero_cuenta, titular_cuenta, wompi_public_key, wompi_private_key, bre_b_codigo_entidad)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conjunto_7480_id, "7480", "EDIFICIO MANCHESTER APTOS PH", "Edificio Residencial",
        "900777367-7", "Carrera 47 No 44-71 BELLO", "6007514", "edificiomanchesteraptos@gmail.com",
        "AV-VILLAS", "Corriente", "512168063", "EDIFICIO MANCHESTER APTOS PH",
        "pub_test_wompi_7480", "prv_test_wompi_7480", "BREB-AVV-7480"
    ))

    # 2. Conjunto 2: CONJUNTO RESIDENCIAL LOS SAUCES (Código 2609)
    conjunto_4901_id = "cj_4901"
    cursor.execute("""
    INSERT INTO conjuntos (id, codigo, nombre, tipo, nit, direccion, telefono, email, banco, tipo_cuenta, numero_cuenta, titular_cuenta, wompi_public_key, wompi_private_key, bre_b_codigo_entidad)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conjunto_4901_id, "4901", "EDIFICIO ROBLE ALTO P.H.", "Propiedad Horizontal",
        "901690778-9", "DG 79A  No 76-250/252/254/256 MEDELLÍN", "6045011727", "admonedificioroblealto@gmail.com",
        "BANCOLOMBIA", "Ahorros", "991-000017-17", "EDIFICIO ROBLE ALTO P.H.",
        "pub_test_wompi_4901", "prv_test_wompi_4901", "BREB-BAN-4901"
    ))

    # 3. Conjunto 3: CENTRO COMERCIAL GRAN PLAZA (Código 0127)
    conjunto_0127_id = "cj_0127"
    cursor.execute("""
    INSERT INTO conjuntos (id, codigo, nombre, tipo, nit, direccion, telefono, email, banco, tipo_cuenta, numero_cuenta, titular_cuenta, wompi_public_key, wompi_private_key, bre_b_codigo_entidad)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conjunto_0127_id, "0127", "EDIFICIO CLASS 48 P. H.", "Propiedad Horizontal",
        "901686161-1", "Calle 48 No 65-12 MEDELLÍN", "4441234", "administracion@class48.com",
        "BANCOLOMBIA", "Ahorros", "00567955788", "EDIFICIO CLASS 48 P. H.",
        "pub_test_wompi_0127", "prv_test_wompi_0127", "BREB-BAN-0127"
    ))

    # Sembrar Usuarios de Ejemplo con contraseñas seguras (default: 123456)
    # 1. Superadmin (Acceso total)
    cursor.execute("""
    INSERT INTO usuarios (id, conjunto_id, username, password_hash, nombre_completo, email, telefono, rol)
    VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
    """, (
        "usr_superadmin", "superadmin", hash_pw("admin123"), "Super Administrador LEFACTURAMOS",
        "LefacturamosPH@lefacturamos.com", "3001234567", "superadmin"
    ))

    # 2. Administrador del Edificio Manchester (7480)
    cursor.execute("""
    INSERT INTO usuarios (id, conjunto_id, username, password_hash, nombre_completo, email, telefono, rol)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "usr_admin_7480", conjunto_7480_id, "admin7480", hash_pw("7480"), "Administración Manchester",
        "edificiomanchesteraptos@gmail.com", "6007514", "admin"
    ))

    # 3. Administrador de Roble Alto (4901)
    cursor.execute("""
    INSERT INTO usuarios (id, conjunto_id, username, password_hash, nombre_completo, email, telefono, rol)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "usr_admin_4901", conjunto_4901_id, "admin4901", hash_pw("4901"), "Administración Roble Alto",
        "admonedificioroblealto@gmail.com", "6045011727", "admin"
    ))

    # 4. Portería Manchester (7480)
    cursor.execute("""
    INSERT INTO usuarios (id, conjunto_id, username, password_hash, nombre_completo, email, telefono, rol)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "usr_porteria_7480", conjunto_7480_id, "porteria7480", hash_pw("porteria"), "Portería Principal Manchester",
        "porteria7480@lefacturamos.com", "6007515", "porteria"
    ))

    # 5. Residente Manchester Apto 0301 (Jesús Emilio Monsalve)
    cursor.execute("""
    INSERT INTO usuarios (id, conjunto_id, username, password_hash, nombre_completo, email, telefono, rol, unidad_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "usr_res_0301", conjunto_7480_id, "apto0301", hash_pw("0301"), "JESUS EMILIO MONSALVE",
        "jesus.monsalve@email.com", "3119876543", "residente", "u_7480_0301"
    ))

    # Sembrar Zonas Comunes requeridas en cada conjunto
    zonas_catalogo = [
        # Zonas Húmedas
        ("Sauna Spa", "Zonas Humedas", 8, 1.5, 12, 0.0, "Uso exclusivo residentes. Ducha previa obligatoria."),
        ("Jacuzzi Climatizado", "Zonas Humedas", 6, 2.0, 12, 0.0, "Capacidad máx 6 personas. Prohibido consumo de bebidas en envase de vidrio."),
        ("Baño Turco", "Zonas Humedas", 10, 1.5, 12, 0.0, "Uso con toalla personal y vestido de baño reglamentario."),
        
        # Social
        ("Salón Social Principal", "Social", 80, 6.0, 48, 150000.0, "Depósito de garantía reembolsable $200.000. Música hasta las 02:00 AM."),
        ("Salón de Juegos", "Social", 20, 3.0, 12, 0.0, "Mesa de billar, ping pong y futbolito. Menores de 12 acompañados."),
        ("Cine / Sala Multimedia", "Social", 25, 3.0, 24, 0.0, "Proyector 4K y sonido envolvente. Reservas para funciones familiares."),
        ("BBQ y Pérgola", "Social", 30, 4.0, 24, 50000.0, "Incluye parrilla a carbón, mesón y lavaplatos. Dejar aseado al finalizar."),
        
        # Deportes
        ("Cancha de Tenis", "Deportes", 4, 1.5, 24, 0.0, "Calzado adecuado sin taches. Máximo 4 jugadores."),
        ("Cancha Múltiple", "Deportes", 14, 2.0, 12, 0.0, "Baloncesto, voleibol y microfútbol recreativo."),
        ("Cancha de Fútbol Sintética", "Deportes", 12, 1.5, 24, 40000.0, "Iluminación nocturna incluida. Tenis de suela lisa."),
        ("Gimnasio & Zona Cardio", "Deportes", 15, 1.5, 6, 0.0, "Toalla personal obligatoria y desinfección de máquinas tras su uso."),
        
        # Coworking
        ("Sala Coworking & Sala de Juntas", "Coworking", 12, 4.0, 12, 0.0, "Wi-Fi de alta velocidad, pantalla para presentaciones y tomas eléctricas."),
        
        # Piscina
        ("Piscina Semi-Olímpica", "Social", 40, 3.0, 12, 0.0, "Gorro de baño obligatorio. Horario: 06:00 a 20:00. Lunes cerrado por mantenimiento.")
    ]

    for i, (z_nom, z_cat, z_cap, z_max_h, z_antic, z_costo, z_reglas) in enumerate(zonas_catalogo, start=1):
        clean_slug = z_nom.lower().replace(" ", "_").replace("&", "y").replace("/", "_")[:20]
        zid = f"z_7480_{i}_{clean_slug}"
        cursor.execute("""
        INSERT INTO zonas_comunes (id, conjunto_id, nombre, categoria, capacidad_maxima, tiempo_max_horas, anticipacion_min_horas, costo_alquiler, reglas_uso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (zid, conjunto_7480_id, z_nom, z_cat, z_cap, z_max_h, z_antic, z_costo, z_reglas))

    # Cargar Unidades Reales desde LEFACTURAMOS_CONVERTIDO_7480_SEPTIEMBRE_DE_2026.json si existe
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LEFACTURAMOS_CONVERTIDO_7480_SEPTIEMBRE_DE_2026.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data_json = json.load(f)
                unidades_list = data_json.get("unidades", [])
                for u in unidades_list:
                    uid = f"u_7480_{u.get('apto')}"
                    apto_num = u.get("apto", "")
                    bloq_num = u.get("bloq", "00")
                    prop_nom = u.get("propietario", f"Propietario {apto_num}")
                    prop_doc = u.get("documento", "")
                    coef = float(u.get("coeficiente", 1.0))
                    
                    # Totales del mes
                    totales_conc = u.get("totales_concepto", {})
                    cobro_mes = u.get("cobro_mes", {})
                    pend = u.get("pendientes", {})
                    
                    val_admon = float(totales_conc.get("admon", 329800.0))
                    val_interes = float(totales_conc.get("interes", 0.0))
                    val_otros = float(totales_conc.get("otros", 0.0))
                    val_extra = float(totales_conc.get("extra", 0.0))
                    val_multa = float(totales_conc.get("multa", 0.0))
                    total_pagar = float(u.get("total_a_pagar", val_admon))
                    saldo_ant = float(pend.get("pend", 0.0))
                    
                    # Insertar unidad
                    cursor.execute("""
                    INSERT INTO unidades (id, conjunto_id, torre_bloque, numero_unidad, tipo_inmueble, cuarto_util, parqueadero, coeficiente, propietario_nombre, propietario_doc, residente_nombre, saldo_actual)
                    VALUES (?, ?, ?, ?, 'Apartamento', ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        uid, conjunto_7480_id, f"Torre {bloq_num}", apto_num,
                        "", None, coef,
                        prop_nom, prop_doc, prop_nom, total_pagar
                    ))
                    
                    # Insertar factura vigente
                    fac_id = f"fac_7480_{apto_num}_202610"
                    cufe_hash = hashlib.sha256(f"FE-7480-{apto_num}-2026-10-{total_pagar}".encode()).hexdigest()
                    cursor.execute("""
                    INSERT INTO facturas (
                        id, conjunto_id, unidad_id, numero_factura, periodo_mes, anio,
                        fecha_emision, fecha_vencimiento, fecha_pronto_pago, descuento_pronto_pago,
                        val_admon, val_interes, val_otros, val_extra, val_multa,
                        saldo_anterior, total_a_pagar, valor_pronto_pago, cufe, estado, pdf_drive_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fac_id, conjunto_7480_id, uid, f"FE-{u.get('fac', '3889')}",
                        "Octubre 2026", 2026,
                        "2026-10-01", "2026-10-25", "2026-10-15", 0.10,
                        val_admon, val_interes, val_otros, val_extra, val_multa,
                        saldo_ant, total_pagar, round(total_pagar * 0.90, 2),
                        cufe_hash, "PENDIENTE",
                        f"https://drive.google.com/drive/folders/1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E?apto={apto_num}"
                    ))
        except Exception as e:
            print(f"[!] Error cargando unidades JSON en DB: {e}")

    # Sembrar Mascotas de ejemplo
    cursor.execute("""
    INSERT INTO mascotas (id, conjunto_id, unidad_id, nombre, tipo, raza, sexo, color, fecha_nacimiento, identificacion_placa, vacunas_al_dia, fecha_antirrabica, observaciones)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '2026-05-10', 'Dócil y cariñoso, usa collar verde')
    """, ("m_1", conjunto_7480_id, "u_7480_0301", "Max", "Perro", "Golden Retriever", "Macho", "Dorado", "2022-03-15", "CHIP-9840012"))

    cursor.execute("""
    INSERT INTO mascotas (id, conjunto_id, unidad_id, nombre, tipo, raza, sexo, color, fecha_nacimiento, identificacion_placa, vacunas_al_dia, fecha_antirrabica, observaciones)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '2026-06-20', 'Esterilizada, vacunación completa')
    """, ("m_2", conjunto_7480_id, "u_7480_0301", "Luna", "Gato", "Siamés", "Hembra", "Blanco y Café", "2023-08-10", "CHIP-5521990"))

    # Sembrar Comunicados Oficiales
    cursor.execute("""
    INSERT INTO comunicados (id, conjunto_id, titulo, categoria, contenido, alcance, prioridad, autor)
    VALUES (?, ?, ?, ?, ?, 'TODO_EL_CONJUNTO', 'NORMAL', 'Administración')
    """, (
        "com_1", conjunto_7480_id, "Mantenimiento Preventivo de Bombas de Agua", "Mantenimiento",
        "Se informa a todos los residentes que el próximo jueves se realizará lavado y desinfección de tanques de agua de 08:00 a 16:00.",
    ))
    cursor.execute("""
    INSERT INTO comunicados (id, conjunto_id, titulo, categoria, contenido, alcance, prioridad, autor)
    VALUES (?, ?, ?, ?, ?, 'TODO_EL_CONJUNTO', 'URGENTE', 'Administración')
    """, (
        "com_2", conjunto_7480_id, "Convocatoria a Asamblea General Extraordinaria 2027", "Asamblea",
        "Se convoca a todos los copropietarios a la Asamblea General Mixta (Presencial y Virtual) el día 28 de Noviembre a las 19:00 horas.",
    ))

    # Sembrar Votación de Asamblea
    cursor.execute("""
    INSERT INTO votaciones (id, conjunto_id, titulo, descripcion, opciones, estado, quorum_minimo)
    VALUES (?, ?, ?, ?, '["Sí", "No", "Voto en Blanco"]', 'ABIERTA', 51.0)
    """, (
        "vot_1", conjunto_7480_id,
        "¿Aprueba el presupuesto ordinario para el año 2027?",
        "Aprobación del presupuesto de ingresos y gastos de la copropiedad presentado en asamblea conforme al Artículo 38 de la Ley 675."
    ))

    # Sembrar PQR de Ejemplo
    cursor.execute("""
    INSERT INTO pqr (id, consecutivo, conjunto_id, unidad_id, residente_nombre, categoria, asunto, descripcion, estado, responsable, respuesta, fecha_respuesta)
    VALUES (?, 'PQR-2026-001', ?, 'u_7480_0301', 'JESUS EMILIO MONSALVE', 'Mantenimiento', 'Revisión luminaria pasillo piso 3', 'La bombilla frente al apartamento 0301 presenta intermitencia.', 'EN_PROCESO', 'Técnico Eléctrico', 'Se programó cambio de balastro para el martes.', '2026-10-14 10:00:00')
    """, ("pqr_1", conjunto_7480_id))

    # Sembrar Pagos a Proveedores de Administración
    cursor.execute("""
    INSERT INTO pagos_proveedores (id, conjunto_id, empresa_proveedor, nit_proveedor, concepto_servicio, detalle_trabajos, garantia_meses, valor_pagado, fecha_pago, aprobado_por)
    VALUES (?, ?, 'ASCENSORES SCHINDLER DE COLOMBIA S.A.S.', '860.005.123-1', 'Mantenimiento Bimensual Ascensores', 'Cambio de guayas de tracción y calibración de freno magnético en torre 1.', 12, 4850000.0, '2026-10-10', 'Administrador General')
    """, ("pp_1", conjunto_7480_id))

    cursor.execute("""
    INSERT INTO pagos_proveedores (id, conjunto_id, empresa_proveedor, nit_proveedor, concepto_servicio, detalle_trabajos, garantia_meses, valor_pagado, fecha_pago, aprobado_por)
    VALUES (?, ?, 'SEGURIDAD ATLAS LTDA.', '890.104.555-9', 'Servicio de Vigilancia y Portería 24/7', 'Turnos 24/7 con control biométrico y monitoreo circuito cerrado TV.', 1, 14200000.0, '2026-10-05', 'Administrador General')
    """, ("pp_2", conjunto_7480_id))

    # Sembrar Compendio de Subíndices de Resolución de la Ley 675 de 2001
    sembrar_ley_675(conn)

    conn.commit()
    conn.close()
    print("[OK] Datos iniciales sembrados con éxito en lefacturamos.db")

def sembrar_ley_675(conn=None):
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ley_675")
    articulos_ley_675 = [
        # 1. Mora y Cobros
        ("Capítulo VII: De las Expensas Comunes", 30, "Incumplimiento en el Pago de Expensas", "Mora y Cobros",
         "¿Puede el administrador cobrar intereses de mora y cuál es la tasa máxima permitida?",
         "SÍ. La ley autoriza cobrar intereses de mora equivalentes a una y media veces (1.5x) el interés bancario corriente certificado por la Superfinanciera para el mes respectivo, o la tasa menor pactada en asamblea. Jamás puede superar la tasa de usura.",
         "Ambos",
         "El retardo en el pago de expensas causará intereses de mora, equivalentes a una y media veces el interés bancario corriente certificado por la Superintendencia Bancaria, sin perjuicio de que la asamblea general establezca un interés inferior.",
         "mora, intereses, usura, superfinanciera, retraso pago, expensas, cobro"),

        ("Capítulo VII: De las Expensas Comunes", 30, "Publicación de Lista de Morosos", "Mora y Cobros",
         "¿Es legal publicar la lista de copropietarios morosos en la cartelera del edificio?",
         "SÍ ES LEGAL. La Corte Constitucional (Sentencia T-366/99) y la Ley 675 avalan la publicación interna en carteleras cerradas o actas accesibles únicamente a los copropietarios o residentes, pues se trata de información veraz de interés común. Está prohibido publicarla en porterías abiertas a la calle o redes sociales públicas.",
         "Ambos",
         "El administrador podrá publicar en lugares cerrados de amplia circulación de la edificación o conjunto la lista de los propietarios con indicación de las cuotas en mora.",
         "lista morosos, cartelera, boleteo, habeas data, buen nombre, publicacion, cobro"),

        ("Capítulo VII: De las Expensas Comunes", 29, "Prohibición de Vías de Hecho contra Morosos", "Mora y Cobros",
         "¿Puede la administración suspender el citófono, apagar el chip del ascensor o impedir el ingreso al moroso?",
         "ROTUNDAMENTE NO. La Corte Constitucional (C-318/02 y T-630/97) prohíbe suspender servicios esenciales como ingreso al predio, ascensor, citofonía para emergencias o correspondencia, y servicios públicos domiciliarios. Constituye una vía de hecho ilegal tutelable.",
         "Ambos",
         "La exigibilidad de las expensas se tramitará por vía ejecutiva judicial. No se admiten vías de hecho que vulneren la dignidad humana, la salud o la intimidad de los moradores.",
         "cortar citofono, suspender ascensor, chip moroso, impedir entrada, via de hecho, tutela, derechos fundamentales"),

        ("Capítulo VII: De las Expensas Comunes", 30, "Restricción de Bienes Comunes No Esenciales", "Mora y Cobros",
         "¿Se puede suspender el acceso a piscinas, sauna, turco, BBQ o salón social por mora?",
         "SÍ ES LEGAL. La copropiedad puede suspender reglamentariamente el uso y reserva de bienes y zonas comunes recreativas o no esenciales a los deudores morosos, siempre que esté estipulado en el reglamento de PH o aprobado por la asamblea general.",
         "Ambos",
         "El reglamento de propiedad horizontal podrá autorizar la suspensión del uso de bienes comunes no esenciales para los propietarios o tenedores que incurran en mora.",
         "zonas humedas morosos, piscina sauna moroso, salon comunal deudor, bienes no esenciales, suspension"),

        ("Capítulo VII: De las Expensas Comunes", 29, "Solidaridad del Nuevo Adquirente", "Mora y Cobros",
         "¿Quién responde por las deudas de administración al comprar un apartamento usado?",
         "EXISTE RESPONSABILIDAD SOLIDARIA. El nuevo adquirente responde solidariamente con el antiguo propietario por todas las cuotas de administración adeudadas. Por ello, el comprador debe exigir siempre el certificado de paz y salvo emitido por el administrador antes de firmar escrituras.",
         "Copropietarios",
         "El adquirente a cualquier título de un bien de dominio particular será solidariamente responsable con el tradente del pago de las expensas comunes no pagadas por este.",
         "deudas anteriores, comprador responde, solidaridad, paz y salvo, compraventa apto, expensas"),

        # 2. Asambleas y Quórum
        ("Capítulo VIII: De la Asamblea General", 39, "Convocatoria a Asamblea Ordinaria", "Asambleas y Quórum",
         "¿Con cuántos días de anticipación debe convocarse a la Asamblea General Ordinaria?",
         "MÍNIMO 15 DÍAS CALENDARIO. La citación debe enviarse por escrito a la dirección física o electrónica registrada, anexando obligatoriamente los estados financieros del año anterior, el proyecto de presupuesto y el informe de gestión para garantizar el derecho de inspección.",
         "Administradores",
         "La asamblea se reunirá ordinariamente por lo menos una vez al año, dentro de los tres (3) meses siguientes al vencimiento de cada período presupuestal, previa convocatoria del administrador con mínimo 15 días calendario.",
         "convocatoria asamblea, 15 dias calendario, citacion asamblea, estados financieros, presupuesto, antelacion"),

        ("Capítulo VIII: De la Asamblea General", 41, "Segunda Convocatoria por Falta de Quórum", "Asambleas y Quórum",
         "¿Qué se hace si no hay quórum en la primera citación de la asamblea?",
         "SE REÚNE AL TERCER DÍA HÁBIL. Si no hay más del 50% de coeficientes, se levanta acta y se sesiona el tercer día hábil siguiente a las 8:00 PM. Esta segunda asamblea sesionará y decidirá válidamente con cualquier número plural de coeficientes presentes.",
         "Ambos",
         "Si convocada la asamblea esta no puede sesionar por falta de quórum, se convocará a una nueva reunión que se realizará el tercer día hábil siguiente a las ocho de la noche, y deliberará válidamente con cualquier número plural de coeficientes.",
         "segunda convocatoria, falta de quorum, tercer dia habil, decidir cualquier quorum, asamblea"),

        ("Capítulo VIII: De la Asamblea General", 46, "Decisiones que Exigen Mayoría Calificada del 70%", "Asambleas y Quórum",
         "¿Cuáles decisiones exigen obligatoriamente mayoría calificada del 70% de coeficientes?",
         "LISTA TAXATIVA DEL 70%: 1) Cambios en la destinación de bienes comunes; 2) Imposición de expensas extraordinarias mayores a 4 cuotas mensuales ordinarias; 3) Desafectación de bienes comunes no esenciales; 4) Reconstrucción o demolición del edificio; 5) Reformas a los estatutos y reglamento; 6) Adquisición de inmuebles para la copropiedad; 7) Liquidación y disolución.",
         "Ambos",
         "Las decisiones que se adopten respecto de los siguientes casos exigirán una mayoría calificada del setenta por ciento (70%) de los coeficientes que integran el edificio o conjunto: cambios de destinación, desafectación, cuotas mayores a 4 veces la ordinaria.",
         "mayoria calificada 70%, reforma estatutos, cuota extraordinaria 4 veces, desafectacion, reconstruccion, quorum"),

        ("Capítulo VIII: De la Asamblea General", 37, "Poderes y Representación en Asamblea", "Asambleas y Quórum",
         "¿Puede el administrador o el revisor fiscal recibir poderes para votar en la asamblea?",
         "PROHIBIDO POR CONFLICTO DE INTERESES. Ni el administrador ni el revisor fiscal deben actuar como apoderados de propietarios, ya que no pueden votar sobre la aprobación o desaprobación de sus propios informes, cuentas y balances de gestión.",
         "Ambos",
         "La asamblea general la constituirán los propietarios de bienes privados, o sus representantes o delegados debidamente acreditados por escrito.",
         "poderes asamblea, apoderado, conflicto intereses, representacion administrador, revisor fiscal poderes"),

        # 3. Mascotas y Animales
        ("Capítulo XI: De la Solución de Conflictos", 74, "Mascotas y Tenencia en Unidades Privadas", "Mascotas y Animales",
         "¿Puede el reglamento o la administración prohibir tener perros o gatos en los apartamentos?",
         "ROTUNDAMENTE NO. La Corte Constitucional (Sentencias T-035/97, T-155/12) y la Ley 1774 de 2016 establecen que tener mascotas es un derecho fundamental derivado del libre desarrollo de la personalidad y la intimidad familiar. Toda norma de reglamento que prohíba mascotas es inconstitucional y nula.",
         "Copropietarios",
         "La tenencia de animales domésticos en bienes de dominio particular no podrá ser prohibida por el reglamento de propiedad horizontal, garantizando la salubridad y la tranquilidad de los vecinos.",
         "prohibir mascotas, perros gatos apto, prohibicion mascotas nula, libre desarrollo personalidad, animales domesticos"),

        ("Capítulo XI: De la Solución de Conflictos", 74, "Reglas para Mascotas en Áreas Comunes", "Mascotas y Animales",
         "¿Cuáles son las obligaciones legales de los propietarios de mascotas en zonas comunes?",
         "OBLIGACIONES TAXATIVAS (Código de Policía Ley 1801): 1) Caninos siempre con correa o traílla; 2) Razas de manejo especial con bozal y póliza vigente; 3) Recolección inmediata y obligatoria de heces; 4) Carné de vacunas vigente. No se puede cobrar cuota extra de administración por tener mascotas.",
         "Ambos",
         "Los tenedores de ejemplares caninos están obligados a recoger los excrementos, a llevarlos con correa en zonas comunes y con bozal a las razas de manejo especial conforme al Código Nacional de Seguridad y Convivencia.",
         "correa bozal perro, razas manejo especial, recoger heces, vacunas caninas, zonas comunes mascotas, ley 1801"),

        ("Capítulo XI: De la Solución de Conflictos", 74, "Mascotas en Ascensores", "Mascotas y Animales",
         "¿Se puede prohibir a los residentes subir con su mascota por el ascensor?",
         "NO SE PUEDE PROHIBIR. La jurisprudencia constitucional protege el uso del ascensor con animales sujetos con traílla. Solo se puede reglamentar la cortesía y ceder el turno si un vecino manifiesta fobia o alergia médica justificada.",
         "Ambos",
         "El acceso a bienes comunes de transporte vertical no podrá ser restringido arbitrariamente para animales domésticos debidamente controlados con su respectiva traílla.",
         "mascotas ascensor, subir perro ascensor, prohibir ascensor mascota, fobia alergia"),

        # 4. Convivencia y Sanciones
        ("Capítulo XI: De la Solución de Conflictos", 59, "Debido Proceso en Multas y Sanciones", "Convivencia y Sanciones",
         "¿Cuál es el procedimiento legal obligatorio antes de cobrar una multa por ruidos o faltas?",
         "DEBIDO PROCESO OBLIGATORIO (Art. 29 CN y C-318/02): 1) Notificación previa y escrita de la queja con fecha, hora y hechos; 2) Término razonable (3 a 5 días) para presentar descargos y pruebas; 3) Decisión motivada emitida por el Consejo o Asamblea; 4) Recurso de reposición. Facturar una multa sin descargos es ILEGAL y tutelable.",
         "Ambos",
         "Para la imposición de sanciones por incumplimiento de obligaciones no pecuniarias se requerirá la garantía previa del debido proceso, el derecho a ser oído y controvertir las pruebas.",
         "debido proceso multas, procedimiento sancionatorio, descargos multa, derecho defensa, nulidad multa, ruidos"),

        ("Capítulo XI: De la Solución de Conflictos", 60, "Tope Máximo de Multas Económicas", "Convivencia y Sanciones",
         "¿Cuál es el valor máximo en dinero que se puede cobrar por una multa en propiedad horizontal?",
         "TOPES MÁXIMOS ESTRICTOS: 1) Cada multa individual no puede superar dos (2) cuotas de administración mensuales ordinarias; 2) La suma total de multas impuestas en un año calendario a un mismo propietario no puede superar diez (10) cuotas ordinarias.",
         "Administradores",
         "En ningún caso el valor de cada una de las multas podrá ser superior a dos veces el valor de la expensa mensual, ni podrán superar en su conjunto el equivalente a diez expensas en el año.",
         "monto maximo multa, limite multas ley 675, valor sancion dinero, dos cuotas admon, tope anual"),

        ("Capítulo XI: De la Solución de Conflictos", 58, "Límites del Comité de Convivencia", "Convivencia y Sanciones",
         "¿Puede el Comité de Convivencia sancionar o poner multas a los vecinos?",
         "NO. El Comité de Convivencia es exclusivamente un mediador amigable para buscar fórmulas de conciliación entre vecinos. No tiene funciones policivas, sancionatorias ni potestad de fijar multas. La sanción compete al Consejo o a la Asamblea General.",
         "Ambos",
         "El comité de convivencia tendrá como única función presentar fórmulas de arreglo y mediación orientadas a dirimir las controversias y fortalecer las relaciones de vecindad. Sus decisiones no son obligatorias ni imponen sanciones.",
         "comite convivencia sanciones, mediacion vecinal, conciliar vecinos, quien multa, amigable componedor"),

        # 5. Parqueaderos
        ("Capítulo V: De los Bienes Comunes", 24, "Cobro por Parqueadero de Visitantes", "Parqueaderos",
         "¿Puede el conjunto residencial cobrar tarifa por el parqueadero de visitantes?",
         "SÍ ES LEGAL. Se requiere aprobación de la Asamblea General con mayoría calificada del 70% de coeficientes como explotación de bien común no esencial. Todos los recursos recaudados deben ingresar a la contabilidad común para sufragar expensas generales.",
         "Ambos",
         "La explotación económica de bienes comunes no esenciales podrá ser aprobada por la asamblea general con el quórum del 70% de coeficientes, destinando los ingresos a expensas comunes.",
         "cobro parqueadero visitantes, tarifa parqueo, explotacion bien comun, parqueadero visitas, mayoria 70"),

        ("Capítulo V: De los Bienes Comunes", 22, "Asignación de Parqueaderos Comunales", "Parqueaderos",
         "¿Cómo deben asignarse los parqueaderos comunales de uso exclusivo?",
         "ASIGNACIÓN ROTATIVA Y EQUITATIVA. Mediante sorteos periódicos transparentes (semestrales o anuales). Ningún propietario tiene propiedad perpetua sobre bahías comunes. Debe priorizarse a personas con discapacidad o adultos mayores según la ley de accesibilidad.",
         "Ambos",
         "Los parqueaderos comunales destinados a los vehículos de los propietarios se asignarán de manera rotativa, equitativa y transitoria según lo dispuesto en el reglamento de propiedad horizontal.",
         "sorteo parqueaderos, asignacion parqueaderos comunes, rotacion bahias, movilidad reducida, garajes comunes"),

        ("Capítulo IV: De los Bienes Privados", 18, "Prohibición de Retención de Vehículos por Mora", "Parqueaderos",
         "¿Puede la administración retener un vehículo dentro del parqueadero si el propietario no paga la cuota?",
         "JAMÁS. La retención de un vehículo o motocicleta por deudas de administración es completamente ilegal y puede tipificar el delito penal de retención indebida o constreñimiento ilegal. La única vía legal para cobrar cartera es el proceso ejecutivo judicial ante los juzgados civiles.",
         "Administradores",
         "La exigibilidad de las obligaciones pecuniarias solo procede ante la jurisdicción ordinaria mediante proceso ejecutivo con título valor certificado.",
         "retener carro, no dejar sacar vehiculo, retencion indebida, deudor parqueadero, secuestro vehiculo"),

        # 6. Administrador y Consejo
        ("Capítulo IX: Del Administrador", 50, "Nombramiento y Remoción del Administrador", "Administrador y Consejo",
         "¿Quién nombra y quién tiene la facultad de remover al Administrador del edificio?",
         "NOMBRA Y REMUEVE EL CONSEJO (o la Asamblea si no hay Consejo). El órgano que lo nombró tiene la potestad legal de removerlo en cualquier momento sin justa causa, liquidando el contrato conforme a la ley civil o comercial.",
         "Ambos",
         "La representación legal y administración corresponderá al administrador designado por el consejo de administración o por la asamblea. Podrá ser removido libremente en cualquier tiempo por el órgano nominador.",
         "remover administrador, nombramiento administrador, destituir administrador, consejo administracion, libre remocion"),

        ("Capítulo IX: Del Administrador", 50, "Responsabilidad Patrimonial del Administrador", "Administrador y Consejo",
         "¿Responde el Administrador con su propio patrimonio personal ante negligencia o daños?",
         "SÍ RESPONDE. El administrador responderá por los perjuicios que por dolo, culpa leve o grave ocasione a la persona jurídica, copropietarios o terceros. Se presume su culpa si violó estatutos, desvió fondos o desatendió el mantenimiento preventivo obligatorio.",
         "Ambos",
         "El administrador responderá por los perjuicios que por dolo, culpa leve o grave, ocasione a la persona jurídica, a los propietarios o a terceros. Se presumirá la culpa en los casos de extralimitación de funciones.",
         "responsabilidad administrador, demanda administrador, responder patrimonio, culpa negligencia, perjuicios"),

        ("Capítulo VIII: De la Asamblea General", 47, "Derecho de Inspección de Libros y Actas", "Administrador y Consejo",
         "¿Tienen los copropietarios derecho a revisar actas, contratos y extractos bancarios?",
         "SÍ, DERECHO PERMANENTE. Todo copropietario tiene derecho a solicitar y revisar las actas de asamblea, los libros de contabilidad, extractos bancarios y contratos con empresas de vigilancia, aseo y ascensores. La administración debe ponerlos a disposición física o digital.",
         "Copropietarios",
         "El administrador pondrá a disposición de los propietarios el libro de actas, los comprobantes de egreso, contratos y soportes contables durante los días de convocatoria previa a la asamblea y en cualquier tiempo conforme al reglamento.",
         "derecho inspeccion, pedir actas, extractos bancarios ph, libros contables, contratos proveedores, transparencia"),

        ("Capítulo IX: Del Administrador", 53, "Obligatoriedad del Consejo de Administración", "Administrador y Consejo",
         "¿En qué casos es obligatorio conformar el Consejo de Administración?",
         "OBLIGATORIO EN MÁS DE 30 UNIDADES. En edificios y conjuntos residenciales o mixtos con más de treinta (30) bienes privados (sin contar garajes ni cuartos útiles). En conjuntos de 30 o menos unidades privadas es opcional.",
         "Administradores",
         "El consejo de administración será obligatorio en los edificios o conjuntos de uso comercial o mixto integrados por más de treinta bienes privados, y en los residenciales de más de treinta unidades particulares.",
         "consejo obligatorio, mas 30 aptos, cuando hay consejo, funciones consejo, 30 unidades privadas"),

        # 7. Obras, Fachadas y Humedades
        ("Capítulo IV: De los Bienes Privados", 18, "Filtraciones de Agua y Humedades entre Pisos", "Obras y Fachadas",
         "¿Quién paga las reparaciones por goteras o filtraciones entre apartamentos vecinos?",
         "REGLA DE ORIGEN DE LA FUGA: 1) Si la fuga proviene de tubería privada interna (baño, sifón o piso del apartamento superior), PAGA EL VECINO DE ARRIBA; 2) Si la filtración proviene de tubos matrices comunes o fachada/cubierta exterior, PAGA LA ADMINISTRACIÓN con fondos comunes.",
         "Ambos",
         "Los propietarios están obligados a reparar inmediatamente los daños originados en sus bienes privados que afecten a otras unidades o a bienes comunes. La administración responderá por los daños derivados de tuberías e instalaciones matrices comunes.",
         "humedad vecino, filtracion goteras, piso arriba dano, quien paga humedad, tuberia rota, filtraciones"),

        ("Capítulo IV: De los Bienes Privados", 18, "Modificación de Fachadas y Balcones", "Obras y Fachadas",
         "¿Puede un residente cerrar su balcón, pintar la fachada o cambiar la ventanería?",
         "NO SIN AUTORIZACIÓN CALIFICADA. Las fachadas y balcones son bienes comunes que preservan la estética y seguridad. Cerrar balcones o cambiar color requiere autorización de la asamblea con quórum del 70% y licencia de construcción si modifica volúmenes.",
         "Ambos",
         "Los propietarios no podrán realizar actos que comprometan la seguridad, solidez o afecten la estética exterior del edificio, ni modificar las fachadas sin la aprobación de la asamblea con mayoría calificada.",
         "cerrar balcon, pintar fachada, cambiar ventanas, reforma estetica edificio, alteracion fachada"),

        # 8. Expensas y Coeficientes
        ("Capítulo VI: De los Coeficientes", 25, "Cálculo y Fijación de Coeficientes de Copropiedad", "Expensas y Coeficientes",
         "¿Cómo se determina el coeficiente de copropiedad de cada apartamento o local?",
         "PROPORCIONAL AL ÁREA PRIVADA. Se calcula dividiendo el área privada construida de cada unidad por el área total privada de la copropiedad. Las áreas comunes de uso exclusivo no se computan para el coeficiente pero pueden pagar expensa de mantenimiento.",
         "Copropietarios",
         "Los coeficientes de copropiedad se calcularán con base en el área privada construida de cada bien de dominio particular respecto del área total privada del edificio o conjunto.",
         "coeficiente calculo, como se calcula coeficiente, area privada, porcentaje copropiedad, coeficientes"),

        ("Capítulo VII: De las Expensas Comunes", 35, "Fondo de Imprevistos Obligatorio", "Expensas y Coeficientes",
         "¿Para qué sirve el Fondo de Imprevistos y cuánto debe ahorrarse obligatoriamente?",
         "MÍNIMO 1% ANUAL PARA EMERGENCIAS. La copropiedad debe apropiar anualmente mínimo el 1% del presupuesto ordinario. Este dinero solo puede utilizarse para contingencias no planificadas o emergencias graves, y no para nómina o gastos corrientes ordinarios.",
         "Ambos",
         "La persona jurídica constituirá un fondo para atender obligaciones o expensas imprevistas, el cual se formará con un porcentaje no inferior al uno por ciento (1%) sobre el presupuesto anual de gastos comunes.",
         "fondo imprevistos 1%, reserva emergencias, uso fondo imprevistos, imprevistos ley 675, presupuesto"),

        # 9. Arrendatarios e Inquilinos
        ("Capítulo VIII: De la Asamblea General", 37, "Derechos de Arrendatarios e Inquilinos", "Arrendatarios e Inquilinos",
         "¿Qué derechos tienen los arrendatarios frente a la administración y asambleas?",
         "DERECHO AL USO DE BIENES COMUNES Y CONCILIACIÓN. Los inquilinos pueden usar todas las zonas comunes reglamentarias y acudir al Comité de Convivencia. No tienen voz ni voto en asambleas a menos que cuenten con poder escrito del propietario.",
         "Ambos",
         "Los tenedores de bienes privados gozarán de los bienes comunes con sujeción a las normas del reglamento de propiedad horizontal, y podrán acudir a los mecanismos de solución de conflictos.",
         "derechos arrendatario, inquilino asamblea, poder inquilino, zonas comunes arrendatario, manual convivencia")
    ]

    for cap, art, tit, sub, preg, resol, apl, cont, keys in articulos_ley_675:
        cursor.execute("""
        INSERT INTO ley_675 (capitulo, articulo, titulo, subindice, pregunta_resolucion, resolucion_practica, aplicable_a, contenido, palabras_clave)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cap, art, tit, sub, preg, resol, apl, cont, keys))

    conn.commit()
    if should_close:
        conn.close()
    print(f"[OK] {len(articulos_ley_675)} subíndices de resolución de Ley 675 sembrados con éxito.")

if __name__ == "__main__":
    inicializar_base_datos()
    sembrar_datos_iniciales()
