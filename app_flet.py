#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal
Aplicación Multiplataforma en Python Puro (Flet / Flutter Engine)
100% MODO OSCURO (Dark Theme) con Menús Especializados por Rol:
  1. Superadministrador (Gestión multi-conjunto, NIT, pasarelas, webhooks, bancos)
  2. Administrador del Conjunto (10 indicadores, cartera, gastos, proveedores, PQR)
  3. Propietario / Residente (Inmueble, pagos Bre-B/PSE, reservas, visitas QR, Drive)
  4. Portería / Seguridad (Validación QR en 2 segundos, talanquera, domicilios)
========================================================================================
"""

import os
import sys
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional

import flet as ft
from lefacturamos_db import get_db_connection, hash_pw

# Compatibilidad Flet 1.0+ (Métodos de borde, ElevatedButton y compatibilidad de argumento text en botones)
if hasattr(ft, "Border"):
    if not hasattr(ft.border, "all") and hasattr(ft.Border, "all"):
        ft.border.all = ft.Border.all
    if not hasattr(ft.border, "only") and hasattr(ft.Border, "only"):
        ft.border.only = ft.Border.only
    if not hasattr(ft.border, "symmetric") and hasattr(ft.Border, "symmetric"):
        ft.border.symmetric = ft.Border.symmetric

if not hasattr(ft, "ElevatedButton") and hasattr(ft, "FilledButton"):
    ft.ElevatedButton = ft.FilledButton

for _btn_cls in [getattr(ft, "FilledButton", None), getattr(ft, "OutlinedButton", None), getattr(ft, "TextButton", None)]:
    if _btn_cls is not None:
        _orig_init = _btn_cls.__init__
        def _make_init(orig):
            def _new_init(self, *args, **kwargs):
                if "text" in kwargs:
                    if "content" not in kwargs or kwargs["content"] is None:
                        kwargs["content"] = kwargs.pop("text")
                    else:
                        kwargs.pop("text")
                return orig(self, *args, **kwargs)
            return _new_init
        _btn_cls.__init__ = _make_init(_orig_init)

# ==============================================================================
# PALETA DE COLORES PROFESIONAL MODO OSCURO (DARK MODE)
# ==============================================================================
COLOR_PRIMARY = "#10b981"         # Esmeralda 500 (Acento principal brillante)
COLOR_PRIMARY_DARK = "#059669"    # Esmeralda 600
COLOR_PRIMARY_LIGHT = "#34d399"   # Esmeralda 400
COLOR_BG = "#020617"              # Slate 950 (Fondo ultra oscuro de la app)
COLOR_SURFACE = "#0b1329"         # Azul marino oscuro profundo
COLOR_CARD_BG = "#0f172a"         # Slate 900 (Fondo de tarjetas e inputs)
COLOR_CARD_BORDER = "#1e293b"     # Slate 800 (Bordes sutiles)
COLOR_SIDEBAR = "#030712"         # Gray 950 (Barra lateral oscura)
COLOR_TEXT_MAIN = "#f8fafc"       # Slate 50 (Texto blanco de alto contraste)
COLOR_TEXT_MUTED = "#94a3b8"      # Slate 400 (Texto secundario)
COLOR_GOLD = "#fbbf24"            # Ámbar brillante
COLOR_RED = "#f43f5e"             # Rose 500
COLOR_BLUE = "#38bdf8"            # Sky 400

def main(page: ft.Page):
    page.title = "LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BG
    try:
        if hasattr(page, "window") and page.window is not None:
            page.window.width = 1200
            page.window.height = 860
            page.window.min_width = 420
            page.window.min_height = 620
    except Exception:
        pass
    page.padding = 0

    # Estado de la Sesión
    session_state = {
        "rol": "residente", # superadmin, admin, residente, porteria
        "conjunto_id": "cj_7480",
        "unidad_id": "u_7480_0301",
        "apto_numero": "0301",
        "usuario_nombre": "JESUS EMILIO MONSALVE",
        "menu_seleccionado": "inicio"
    }

    # Helpers de base de datos
    def db_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        try:
            conn = get_db_connection()
            rows = conn.execute(sql, params).fetchall()
            res = [dict(r) for r in rows]
            conn.close()
            return res
        except Exception as e:
            print(f"[!] Error db_query: {e}")
            return []

    def db_execute(sql: str, params: tuple = ()):
        try:
            conn = get_db_connection()
            conn.execute(sql, params)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error db_execute: {e}")

    # SnackBar Notificaciones Dark Mode
    def show_toast(mensaje: str, es_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
            bgcolor=COLOR_RED if es_error else COLOR_PRIMARY_DARK,
            duration=3500
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # Contenedores dinámicos
    sidebar_container = ft.Container(width=250, bgcolor=COLOR_SIDEBAR, padding=ft.Padding(12, 16, 12, 16), border=ft.Border.only(right=ft.BorderSide(1, COLOR_CARD_BORDER)))
    body_container = ft.Container(expand=True, bgcolor=COLOR_BG, padding=ft.Padding(20, 20, 20, 20))

    # Helper de tarjetas oscuras
    def dark_card(content: ft.Control, padding: int = 18):
        return ft.Container(
            bgcolor=COLOR_CARD_BG,
            border=ft.Border.all(1, COLOR_CARD_BORDER),
            border_radius=14,
            padding=ft.Padding(padding, padding, padding, padding),
            content=content
        )

    # ==========================================================================
    # 1. VISTAS DEL SUPERADMINISTRADOR
    # ==========================================================================
    def build_vista_superadmin():
        conjuntos = db_query("SELECT * FROM conjuntos ORDER BY creado_en DESC")
        total_aptos = db_query("SELECT COUNT(*) as c FROM unidades")[0]["c"]
        total_recaudo = db_query("SELECT COALESCE(SUM(monto), 0) as c FROM pagos WHERE estado = 'APROBADO'")[0]["c"]

        indicadores_sa = ft.ResponsiveRow([
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Conjuntos en Plataforma", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(len(conjuntos)), size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Total Unidades / Locales", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(total_aptos), size=24, weight=ft.FontWeight.BOLD, color=COLOR_BLUE)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Recaudo Global Bancario", size=11, color=COLOR_TEXT_MUTED), ft.Text(f"${total_recaudo:,.0f}", size=20, weight=ft.FontWeight.BOLD, color=COLOR_GOLD)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Pasarelas & Webhooks", size=11, color=COLOR_TEXT_MUTED), ft.Text("4 Activas (100%)", size=20, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
        ])

        # Formulario para Crear Nuevo Conjunto
        nom_tf = ft.TextField(label="Nombre del Conjunto / Edificio / C. Comercial", width=360, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        cod_tf = ft.TextField(label="Código (ej: 0450)", width=160, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        nit_tf = ft.TextField(label="NIT del Conjunto", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        tipo_dd = ft.Dropdown(
            label="Tipo de Copropiedad",
            value="Edificio Residencial",
            options=[ft.dropdown.Option("Edificio Residencial"), ft.dropdown.Option("Conjunto Residencial"), ft.dropdown.Option("Centro Comercial"), ft.dropdown.Option("Parque Empresarial"), ft.dropdown.Option("Copropiedad Mixta")],
            width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER
        )
        banco_tf = ft.TextField(label="Banco (ej: AV Villas, Bancolombia)", width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        cuenta_tipo_dd = ft.Dropdown(label="Tipo Cuenta", value="Corriente", options=[ft.dropdown.Option("Corriente"), ft.dropdown.Option("Ahorros")], width=160, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        cuenta_num_tf = ft.TextField(label="Número de Cuenta", width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        wompi_tf = ft.TextField(label="Wompi Key (Sandbox/Prod)", width=240, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        breb_tf = ft.TextField(label="Código Entidad Bre-B", value="BREB-COL-001", width=200, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

        def crear_conjunto_sa(e):
            if not nom_tf.value or not cod_tf.value or not nit_tf.value:
                show_toast("Complete el nombre, código y NIT del conjunto.", es_error=True)
                return
            cid = f"cj_{cod_tf.value.strip()}"
            db_execute("""
            INSERT INTO conjuntos (id, codigo, nombre, tipo, nit, direccion, telefono, email, banco, tipo_cuenta, numero_cuenta, titular_cuenta, wompi_public_key, bre_b_codigo_entidad, google_drive_folder_id)
            VALUES (?, ?, ?, ?, ?, 'Dirección Principal', '6010000', 'admin@lefacturamos.com', ?, ?, ?, ?, ?, ?, '1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E')
            """, (cid, cod_tf.value.strip(), nom_tf.value.strip(), tipo_dd.value, nit_tf.value.strip(), banco_tf.value.strip(), cuenta_tipo_dd.value, cuenta_num_tf.value.strip(), nom_tf.value.strip(), wompi_tf.value.strip(), breb_tf.value.strip()))
            
            show_toast(f"Copropiedad '{nom_tf.value}' creada con éxito en la plataforma.")
            nom_tf.value = ""
            cod_tf.value = ""
            nit_tf.value = ""
            navegar_a("superadmin_dash")

        # Tabla de Conjuntos Registrados
        filas_conj = []
        for c in conjuntos:
            filas_conj.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(c["codigo"], font_family="monospace", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)),
                    ft.DataCell(ft.Text(c["nombre"], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(c["nit"])),
                    ft.DataCell(ft.Text(f"{c['banco']} ({c['numero_cuenta']})")),
                    ft.DataCell(ft.Text(c["bre_b_codigo_entidad"] or f"BREB-{c['codigo']}", color=COLOR_GOLD)),
                    ft.DataCell(ft.Container(padding=ft.Padding(6, 2, 6, 2), bgcolor=COLOR_SURFACE, border_radius=4, content=ft.Text("ACTIVO", size=10, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)))
                ])
            )

        tabla_conj = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Nombre Copropiedad")),
                ft.DataColumn(ft.Text("NIT")),
                ft.DataColumn(ft.Text("Banco / Cuenta")),
                ft.DataColumn(ft.Text("Código Bre-B")),
                ft.DataColumn(ft.Text("Estado")),
            ],
            rows=filas_conj,
            border=ft.Border.all(1, COLOR_CARD_BORDER)
        )

        return ft.ListView([
            ft.Text("Panel de Control del Superadministrador", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            ft.Text("Administración global multi-copropiedad, configuración de bancos, pasarelas y auditoría de la plataforma.", size=12, color=COLOR_TEXT_MUTED),
            indicadores_sa,
            dark_card(
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.ADD_BUSINESS, color=COLOR_PRIMARY), ft.Text("Dar de Alta Nueva Copropiedad / Edificio", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Row([nom_tf, cod_tf, nit_tf], wrap=True),
                    ft.Row([tipo_dd, banco_tf, cuenta_tipo_dd, cuenta_num_tf], wrap=True),
                    ft.Row([wompi_tf, breb_tf], wrap=True),
                    ft.FilledButton(text="Crear Copropiedad y Asignar Módulos", icon=ft.Icons.SAVE, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=crear_conjunto_sa)
                ], spacing=12)
            ),
            dark_card(
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.APARTMENT, color=COLOR_BLUE), ft.Text("Copropiedades Activas en la Plataforma", size=16, weight=ft.FontWeight.BOLD)]),
                    tabla_conj
                ], spacing=12)
            )
        ], spacing=16)

    # ==========================================================================
    # 2. VISTAS DEL ADMINISTRADOR DEL CONJUNTO
    # ==========================================================================
    def build_vista_admin():
        conj = db_query("SELECT * FROM conjuntos WHERE id = ?", (session_state["conjunto_id"],))
        conj_data = conj[0] if conj else {}

        # 10 Indicadores requeridos
        num_aptos = db_query("SELECT COUNT(*) as c FROM unidades WHERE conjunto_id = ?", (session_state["conjunto_id"],))[0]["c"]
        hoy_str = datetime.date.today().isoformat()
        vis_hoy = db_query("SELECT COUNT(*) as c FROM visitantes_autorizaciones WHERE conjunto_id = ? AND fecha_esperada = ?", (session_state["conjunto_id"], hoy_str))[0]["c"]
        res_hoy = db_query("SELECT COUNT(*) as c FROM reservas WHERE conjunto_id = ? AND fecha_reserva = ?", (session_state["conjunto_id"], hoy_str))[0]["c"]
        pqr_abiertas = db_query("SELECT COUNT(*) as c FROM pqr WHERE conjunto_id = ? AND estado NOT IN ('CERRADA', 'RESPONDIDA')", (session_state["conjunto_id"],))[0]["c"]
        cartera_row = db_query("SELECT COUNT(*) as c, COALESCE(SUM(total_a_pagar), 0) as tot FROM facturas WHERE conjunto_id = ? AND estado = 'PENDIENTE'", (session_state["conjunto_id"],))[0]
        pagos_recibidos = db_query("SELECT COALESCE(SUM(monto), 0) as tot FROM pagos WHERE conjunto_id = ? AND estado = 'APROBADO'", (session_state["conjunto_id"],))[0]["tot"]
        comunicados_tot = db_query("SELECT COUNT(*) as c FROM comunicados WHERE conjunto_id = ?", (session_state["conjunto_id"],))[0]["c"]
        coef_total = db_query("SELECT COALESCE(SUM(coeficiente), 0) as tot FROM unidades WHERE conjunto_id = ?", (session_state["conjunto_id"],))[0]["tot"]

        indicadores_grid = ft.ResponsiveRow([
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Total Unidades", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(num_aptos), size=22, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Visitantes del Día", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(vis_hoy), size=22, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Reservas del Día", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(res_hoy), size=22, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("PQR Abiertas", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(pqr_abiertas), size=22, weight=ft.FontWeight.BOLD, color=COLOR_GOLD)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Facturas Pendientes", size=11, color=COLOR_TEXT_MUTED), ft.Text(str(cartera_row['c']), size=22, weight=ft.FontWeight.BOLD, color=COLOR_RED)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Cartera Total COP", size=11, color=COLOR_TEXT_MUTED), ft.Text(f"${cartera_row['tot']:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=COLOR_RED)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Pagos Recibidos Mes", size=11, color=COLOR_TEXT_MUTED), ft.Text(f"${pagos_recibidos:,.0f}", size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT)]))),
            ft.Container(col={"sm": 6, "md": 3}, content=dark_card(ft.Column([ft.Text("Coeficiente Total", size=11, color=COLOR_TEXT_MUTED), ft.Text(f"{coef_total:.2f}%", size=20, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)]))),
        ])

        # Formulario de Registro de Pagos de Administración a Proveedores
        empresa_tf = ft.TextField(label="Empresa / Proveedor", width=350, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        nit_tf = ft.TextField(label="NIT Proveedor", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        concepto_tf = ft.TextField(label="Concepto de Servicio", width=250, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        detalle_tf = ft.TextField(label="Detalle de Trabajos Realizados", width=400, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        garantia_tf = ft.TextField(label="Garantía (Meses)", value="12", width=140, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        monto_pago_tf = ft.TextField(label="Valor Pagado COP", value="1500000", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

        def registrar_pago_admin(e):
            if not empresa_tf.value or not concepto_tf.value:
                show_toast("Complete la empresa y concepto del servicio.", es_error=True)
                return
            pp_id = f"pp_{uuid.uuid4().hex[:8]}"
            fecha_hoy = datetime.date.today().isoformat()
            db_execute("""
            INSERT INTO pagos_proveedores (id, conjunto_id, empresa_proveedor, nit_proveedor, concepto_servicio, detalle_trabajos, garantia_meses, valor_pagado, fecha_pago, aprobado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Administrador General')
            """, (pp_id, session_state["conjunto_id"], empresa_tf.value, nit_tf.value, concepto_tf.value, detalle_tf.value, int(garantia_tf.value or 0), float(monto_pago_tf.value or 0), fecha_hoy))
            show_toast(f"Gasto registrado: Pago a {empresa_tf.value} por ${float(monto_pago_tf.value):,.0f}")
            empresa_tf.value = ""
            detalle_tf.value = ""
            navegar_a("admin")

        gastos = db_query("SELECT * FROM pagos_proveedores WHERE conjunto_id = ? ORDER BY fecha_pago DESC", (session_state["conjunto_id"],))
        gastos_rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(g["empresa_proveedor"], weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(g["concepto_servicio"])),
                ft.DataCell(ft.Text(f"{g['garantia_meses']} meses")),
                ft.DataCell(ft.Text(f"${g['valor_pagado']:,.0f}", weight=ft.FontWeight.BOLD, color=COLOR_GOLD)),
                ft.DataCell(ft.Text(g["fecha_pago"]))
            ]) for g in gastos
        ]

        return ft.ListView([
            ft.Text(f"Panel Administrativo: {conj_data.get('nombre')}", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            ft.Text(f"NIT: {conj_data.get('nit')} • Cuenta: {conj_data.get('banco')} {conj_data.get('numero_cuenta')} ({conj_data.get('tipo_cuenta')})", size=12, color=COLOR_TEXT_MUTED),
            indicadores_grid,
            dark_card(
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.PAYMENTS, color=COLOR_GOLD), ft.Text("Montar Pago de Administración a Empresa / Contratista", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Text("Muestra la empresa a la que le va a pagar, detalle de lo que hicieron, garantía y fecha.", size=12, color=COLOR_TEXT_MUTED),
                    ft.Row([empresa_tf, nit_tf, concepto_tf], wrap=True),
                    ft.Row([detalle_tf, garantia_tf, monto_pago_tf], wrap=True),
                    ft.FilledButton(text="Registrar Pago y Garantía", icon=ft.Icons.CHECK, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=registrar_pago_admin)
                ], spacing=12)
            ),
            dark_card(
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.HISTORY, color=COLOR_BLUE), ft.Text("Historial de Gastos y Contratos del Conjunto", size=15, weight=ft.FontWeight.BOLD)]),
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Empresa / Proveedor")),
                            ft.DataColumn(ft.Text("Concepto")),
                            ft.DataColumn(ft.Text("Garantía")),
                            ft.DataColumn(ft.Text("Monto")),
                            ft.DataColumn(ft.Text("Fecha")),
                        ],
                        rows=gastos_rows,
                        border=ft.Border.all(1, COLOR_CARD_BORDER)
                    )
                ], spacing=10)
            )
        ], spacing=16)

    # ==========================================================================
    # 3. VISTAS DEL PROPIETARIO / RESIDENTE
    # ==========================================================================
    def build_vista_inicio():
        conj = db_query("SELECT * FROM conjuntos WHERE id = ?", (session_state["conjunto_id"],))
        conj_data = conj[0] if conj else {}
        unidad = db_query("SELECT * FROM unidades WHERE id = ?", (session_state["unidad_id"],))
        u_data = unidad[0] if unidad else {}
        factura = db_query("SELECT * FROM facturas WHERE unidad_id = ? ORDER BY anio DESC, fecha_emision DESC", (session_state["unidad_id"],))
        fac_data = factura[0] if factura else {}

        total_pagar = fac_data.get("total_a_pagar", u_data.get("saldo_actual", 329800.0))
        pronto_pago = fac_data.get("valor_pronto_pago", round(total_pagar * 0.9, 2))

        card_inmueble = dark_card(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.APARTMENT, color=COLOR_PRIMARY, size=32),
                    ft.Column([
                        ft.Text(conj_data.get("nombre", "EDIFICIO MANCHESTER APTOS PH"), size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
                        ft.Text(f"NIT: {conj_data.get('nit', '900777367-7')} • Régimen Ley 675", size=12, color=COLOR_TEXT_MUTED)
                    ], spacing=2)
                ]),
                ft.Divider(height=16, color=COLOR_CARD_BORDER),
                ft.ResponsiveRow([
                    ft.Column([
                        ft.Text("Inmueble / Unidad", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{u_data.get('torre_bloque', 'Torre 00')} - Apto {u_data.get('numero_unidad', session_state['apto_numero'])}", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
                    ], col={"sm": 6, "md": 3}),
                    ft.Column([
                        ft.Text("Titular Copropietario", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        ft.Text(u_data.get("propietario_nombre", session_state["usuario_nombre"]), size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
                    ], col={"sm": 6, "md": 3}),
                    ft.Column([
                        ft.Text("Coeficiente Ley 675", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{u_data.get('coeficiente', 2.588)}%", size=14, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
                    ], col={"sm": 6, "md": 3}),
                    ft.Column([
                        ft.Text("Cuarto Útil & Parqueadero", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{u_data.get('cuarto_util') or 'No tiene'} / {u_data.get('parqueadero') or 'No tiene'}", size=14, color=COLOR_TEXT_MAIN)
                    ], col={"sm": 6, "md": 3}),
                ])
            ], spacing=10)
        )

        card_cuenta = dark_card(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PAYMENTS, color=COLOR_GOLD, size=28),
                    ft.Text("Estado de Cuenta & Facturación", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
                ]),
                ft.Divider(height=12, color=COLOR_CARD_BORDER),
                ft.Row([
                    ft.Column([
                        ft.Text(f"Periodo: {fac_data.get('periodo_mes', 'Octubre 2026')}", size=13, weight=ft.FontWeight.W_500, color=COLOR_TEXT_MAIN),
                        ft.Text("Vence: 2026-10-25 | Pronto Pago: 2026-10-15 (10% Dcto)", size=11, color=COLOR_TEXT_MUTED),
                        ft.Text(f"CUFE DIAN: {fac_data.get('cufe', '4f8b2d7e9a1c3e5f')[:24]}...", size=10, font_family="monospace", color=COLOR_TEXT_MUTED)
                    ], expand=True),
                    ft.Column([
                        ft.Text(f"${total_pagar:,.0f} COP", size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                        ft.Text(f"Con Pronto Pago: ${pronto_pago:,.0f} COP", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD)
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ]),
                ft.Row([
                    ft.FilledButton(
                        text="💳 Pagar con Bre-B / PSE",
                        icon=ft.Icons.PAYMENT,
                        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK),
                        on_click=lambda e: navegar_a("pagos")
                    ),
                    ft.OutlinedButton(
                        text="📄 Factura PDF Google Drive",
                        icon=ft.Icons.CLOUD_DOWNLOAD,
                        on_click=lambda e: show_toast("Abriendo factura en Google Drive oficial de LefacturamosPH@lefacturamos.com...")
                    )
                ], spacing=10)
            ], spacing=10)
        )

        accesos = ft.ResponsiveRow([
            ft.Container(col={"sm": 6, "md": 3}, content=ft.ElevatedButton(content=ft.Column([ft.Icon(ft.Icons.POOL, size=26, color=COLOR_PRIMARY), ft.Text("Reservas Áreas", weight=ft.FontWeight.BOLD, size=12)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), height=85, style=ft.ButtonStyle(bgcolor=COLOR_CARD_BG), on_click=lambda e: navegar_a("reservas"))),
            ft.Container(col={"sm": 6, "md": 3}, content=ft.ElevatedButton(content=ft.Column([ft.Icon(ft.Icons.QR_CODE_2, size=26, color=COLOR_PRIMARY), ft.Text("Visitantes & QR", weight=ft.FontWeight.BOLD, size=12)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), height=85, style=ft.ButtonStyle(bgcolor=COLOR_CARD_BG), on_click=lambda e: navegar_a("visitantes"))),
            ft.Container(col={"sm": 6, "md": 3}, content=ft.ElevatedButton(content=ft.Column([ft.Icon(ft.Icons.PETS, size=26, color=COLOR_PRIMARY), ft.Text("Mis Mascotas", weight=ft.FontWeight.BOLD, size=12)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), height=85, style=ft.ButtonStyle(bgcolor=COLOR_CARD_BG), on_click=lambda e: navegar_a("mascotas"))),
            ft.Container(col={"sm": 6, "md": 3}, content=ft.ElevatedButton(content=ft.Column([ft.Icon(ft.Icons.SUPPORT_AGENT, size=26, color=COLOR_PRIMARY), ft.Text("Radicar PQR", weight=ft.FontWeight.BOLD, size=12)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), height=85, style=ft.ButtonStyle(bgcolor=COLOR_CARD_BG), on_click=lambda e: navegar_a("pqr"))),
        ])

        return ft.ListView([
            card_inmueble,
            card_cuenta,
            ft.Text("Accesos Rápidos del Propietario", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            accesos,
        ], spacing=16)

    # Vista Pagos Propietario
    def build_vista_pagos():
        conj = db_query("SELECT * FROM conjuntos WHERE id = ?", (session_state["conjunto_id"],))[0]
        unidad = db_query("SELECT * FROM unidades WHERE id = ?", (session_state["unidad_id"],))[0]
        factura = db_query("SELECT * FROM facturas WHERE unidad_id = ? ORDER BY anio DESC, fecha_emision DESC", (session_state["unidad_id"],))[0]
        total_pagar = factura.get("total_a_pagar", 329800.0)

        metodo_dd = ft.Dropdown(
            label="Método de Pago Electrónico (Colombia)",
            value="Bre-B",
            options=[
                ft.dropdown.Option("Bre-B", "Bre-B (Pagos Inmediatos Colombia - 0 seg)"),
                ft.dropdown.Option("PSE", "PSE - Débito en Cuenta (30 Bancos)"),
                ft.dropdown.Option("Bancolombia", "Botón Bancolombia Directo"),
                ft.dropdown.Option("Wompi", "Wompi Bancolombia (Tarjetas/PSE/Nequi)"),
                ft.dropdown.Option("Bold", "Bold Colombia (Tarjetas/Datáfono)"),
                ft.dropdown.Option("PayU", "PayU Colombia (Pasarela)"),
                ft.dropdown.Option("Nequi", "Nequi (Billetera Digital)"),
                ft.dropdown.Option("Daviplata", "Daviplata (Davivienda)"),
                ft.dropdown.Option("Efectivo", "Efectivo (Efecty / Baloto / SuRed)")
            ],
            width=420, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER
        )

        bancos_col = [
            "Bancolombia", "Banco de Bogotá", "Davivienda", "Banco AV Villas",
            "Banco de Occidente", "Banco Popular", "Scotiabank Colpatria",
            "BBVA Colombia", "Banco Itaú Colombia", "Banco Caja Social",
            "Banco Agrario de Colombia", "Banco Falabella", "Banco Pichincha",
            "Banco Santander Colombia", "Banco GNB Sudameris", "Banco Serfinanza",
            "Banco Finandina", "Banco Coopcentral", "Bancamía", "Banco W",
            "Lulo Bank", "Nu Colombia", "Nequi", "Daviplata", "Dale!", "Movii"
        ]
        banco_dd = ft.Dropdown(
            label="Banco de Origen (Colombia)",
            value="Banco AV Villas",
            options=[ft.dropdown.Option(b) for b in bancos_col],
            width=420, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER
        )
        res_pago_box = ft.Container(visible=False, padding=10)

        def abrir_banco_oficial(e):
            url_map = {
                "Bancolombia": "https://www.bancolombia.com/personas",
                "Banco de Bogotá": "https://www.bancodebogota.com",
                "Davivienda": "https://www.davivienda.com",
                "Banco AV Villas": "https://www.avvillas.com.co",
                "Banco de Occidente": "https://www.bancodeoccidente.com.co",
                "Banco Popular": "https://www.bancopopular.com.co",
                "Scotiabank Colpatria": "https://www.scotiabankcolpatria.com",
                "BBVA Colombia": "https://www.bbva.com.co",
                "Nequi": "https://transacciones.nequi.com/billetera/",
                "Daviplata": "https://www.daviplata.com"
            }
            u = url_map.get(banco_dd.value, "https://www.pse.com.co/persona")
            page.launch_url(u)

        def pagar(e):
            ref = f"LF-{conj['codigo']}-{unidad['numero_unidad']}-{uuid.uuid4().hex[:6].upper()}"
            pid = f"pg_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO pagos (id, conjunto_id, unidad_id, factura_id, monto, metodo_pago, referencia_transaccion, estado, banco_origen, recibo_caja_numero, conciliado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'APROBADO', ?, ?, 1)
            """, (pid, session_state["conjunto_id"], session_state["unidad_id"], factura["id"], total_pagar, metodo_dd.value, ref, banco_dd.value, f"RC-2026-{pid[-4:]}"))
            db_execute("UPDATE facturas SET estado = 'PAGADA' WHERE id = ?", (factura["id"],))

            res_pago_box.visible = True
            res_pago_box.content = ft.Container(
                bgcolor=COLOR_SURFACE,
                border=ft.Border.all(1, COLOR_PRIMARY),
                border_radius=10,
                padding=14,
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=COLOR_PRIMARY_LIGHT, size=26), ft.Text("¡Pago Aprobado y Conciliado en Contabilidad!", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)]),
                    ft.Text(f"Referencia: {ref} • Método: {metodo_dd.value} ({banco_dd.value})", size=12, color=COLOR_TEXT_MUTED),
                    ft.Text(f"Valor: ${total_pagar:,.0f} COP • Factura FE-3889 Cancelada", size=13, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                    ft.Text(f"Recibo de Caja sincronizado con Google Drive: RC-2026-{pid[-4:]}.pdf", size=11, color=COLOR_GOLD)
                ], spacing=4)
            )
            page.update()
            show_toast("Pago procesado y conciliado con éxito. Recibo emitido.")

        return ft.ListView([
            ft.Text("Facturación & Pasarela Multi-Método (Colombia)", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            dark_card(
                ft.Column([
                    ft.Text("Cuenta Bancaria Receptora Oficial de la Copropiedad", size=14, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                    ft.Row([
                        ft.Text(f"Banco: {conj.get('banco', 'Banco AV Villas')}", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(" • ", size=12),
                        ft.Text(f"Tipo: {conj.get('tipo_cuenta', 'Corriente')}", size=12),
                        ft.Text(" • ", size=12),
                        ft.Text(f"No: {conj.get('numero_cuenta', '512168063')}", size=12, color=COLOR_PRIMARY_LIGHT, weight=ft.FontWeight.BOLD),
                        ft.Text(" • ", size=12),
                        ft.Text(f"NIT: {conj.get('nit', '900.777.367-7')}", size=12)
                    ]),
                    ft.Text(f"Llave Interoperable Bre-B: {conj.get('bre_b_codigo_entidad', 'BREB-AVV-7480')}/{unidad['numero_unidad']}/329800", size=11, color=COLOR_TEXT_MUTED)
                ], spacing=4)
            ),
            dark_card(
                ft.Column([
                    ft.Text("Conceptos Facturados del Mes", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Cuota Ordinaria de Administración: ${factura.get('val_admon', 329800):,.0f} COP", size=13),
                    ft.Text(f"TOTAL A PAGAR: ${total_pagar:,.0f} COP", size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                    ft.Divider(height=10, color=COLOR_CARD_BORDER),
                    metodo_dd,
                    banco_dd,
                    ft.Row([
                        ft.FilledButton(text=f"Procesar Pago de ${total_pagar:,.0f} COP", icon=ft.Icons.SECURITY, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=pagar),
                        ft.OutlinedButton(text="Ir a Web Oficial del Banco", icon=ft.Icons.OPEN_IN_BROWSER, on_click=abrir_banco_oficial)
                    ], spacing=10),
                    res_pago_box
                ], spacing=10)
            ),
            dark_card(
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.CLOUD, color=COLOR_GOLD), ft.Text("Expediente Digital Oficial en Google Drive", size=15, weight=ft.FontWeight.BOLD)]),
                    ft.Text("Descargue sus facturas y recibos en PDF desde la carpeta oficial de LefacturamosPH@lefacturamos.com.", size=12, color=COLOR_TEXT_MUTED),
                    ft.Row([
                        ft.OutlinedButton(text="Factura PDF Google Drive", icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda e: show_toast("Descargando factura en PDF...")),
                        ft.OutlinedButton(text="Recibo de Caja PDF", icon=ft.Icons.RECEIPT, on_click=lambda e: show_toast("Descargando recibo en PDF..."))
                    ], spacing=10)
                ], spacing=8)
            )
        ], spacing=16)

    # Vista Reservas
    def build_vista_reservas():
        zonas = db_query("SELECT * FROM zonas_comunes WHERE conjunto_id = ? AND activo = 1", (session_state["conjunto_id"],))
        zona_dd = ft.Dropdown(
            label="Zona Común a Reservar",
            options=[ft.dropdown.Option(z["id"], f"{z['nombre']} ({z['categoria']}) - ${z['costo_alquiler']:,.0f} COP" if z["costo_alquiler"] > 0 else f"{z['nombre']} (Gratuito)") for z in zonas],
            value=zonas[0]["id"] if zonas else None,
            width=420,
            bgcolor=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER
        )
        fecha_tf = ft.TextField(label="Fecha (AAAA-MM-DD)", value="2026-10-22", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        hora_ini = ft.Dropdown(label="Hora Inicio", value="14:00", options=[ft.dropdown.Option(f"{h:02d}:00") for h in range(6, 22)], width=140, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        hora_fin = ft.Dropdown(label="Hora Fin", value="16:00", options=[ft.dropdown.Option(f"{h:02d}:00") for h in range(7, 23)], width=140, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        tarifa_info = ft.Text(f"Tarifa Oficial fijada por Administración: ${zonas[0]['costo_alquiler']:,.0f} COP" if (zonas and zonas[0]["costo_alquiler"] > 0) else "Tarifa: Gratuita (Incluida en Expensas de Administración)", size=12, color=COLOR_PRIMARY_LIGHT, weight=ft.FontWeight.BOLD)
        cond_cb = ft.Checkbox(label="Acepto el reglamento y condiciones de uso de la zona", value=True)
        res_box = ft.Container(visible=False, padding=8)

        def actualizar_tarifa_label(e):
            sel_z = next((z for z in zonas if z["id"] == zona_dd.value), None)
            if sel_z:
                tarifa_info.value = f"Tarifa Oficial fijada por Administración: ${sel_z['costo_alquiler']:,.0f} COP" if sel_z["costo_alquiler"] > 0 else "Tarifa: Gratuita (Incluida en Expensas de Administración)"
                page.update()

        zona_dd.on_change = actualizar_tarifa_label

        def reservar(e):
            sel_z = next((z for z in zonas if z["id"] == zona_dd.value), None)
            if not sel_z:
                show_toast("Seleccione una zona común.", es_error=True)
                return

            if hora_ini.value >= hora_fin.value:
                show_toast("La hora de inicio debe ser anterior a la hora de fin.", es_error=True)
                return

            # CONTROL ESTRICTO ANTI-SOLAPAMIENTO: Mirar que no se pida la misma reserva que ya se ha hecho por otro copropietario
            solapada = db_query("""
            SELECT r.*, u.numero_unidad, z.nombre as zona_nom
            FROM reservas r
            LEFT JOIN unidades u ON r.unidad_id = u.id
            JOIN zonas_comunes z ON r.zona_id = z.id
            WHERE r.zona_id = ? AND r.fecha_reserva = ? AND r.estado = 'CONFIRMADA'
            AND ((r.hora_inicio < ? AND r.hora_fin > ?) OR (r.hora_inicio >= ? AND r.hora_inicio < ?))
            """, (sel_z["id"], fecha_tf.value, hora_fin.value, hora_ini.value, hora_ini.value, hora_fin.value))

            if solapada:
                apto_c = solapada[0]["numero_unidad"] or "otro copropietario"
                h_ini_c = solapada[0]["hora_inicio"]
                h_fin_c = solapada[0]["hora_fin"]
                res_box.visible = True
                res_box.content = ft.Container(
                    bgcolor=ft.Colors.RED_900,
                    border=ft.Border.all(1, ft.Colors.RED_500),
                    border_radius=8,
                    padding=12,
                    content=ft.Column([
                        ft.Text(f"⚠️ CONFLICTO DE RESERVA: HORARIO NO DISPONIBLE", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"La zona {sel_z['nombre']} ya se encuentra reservada por el Apartamento {apto_c} el {fecha_tf.value} de {h_ini_c} a {h_fin_c}. Por favor seleccione otro horario.", size=12, color=ft.Colors.RED_100)
                    ])
                )
                page.update()
                show_toast(f"⚠️ Conflicto: Horario ya reservado por el Apto {apto_c}.", es_error=True)
                return

            rid = f"res_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO reservas (id, conjunto_id, zona_id, unidad_id, residente_nombre, fecha_reserva, hora_inicio, hora_fin, costo, condiciones_aceptadas, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'CONFIRMADA')
            """, (rid, session_state["conjunto_id"], sel_z["id"], session_state["unidad_id"], session_state["usuario_nombre"], fecha_tf.value, hora_ini.value, hora_fin.value, sel_z["costo_alquiler"]))

            res_box.visible = True
            costo_txt = f"${sel_z['costo_alquiler']:,.0f} COP" if sel_z["costo_alquiler"] > 0 else "Gratuito"
            res_box.content = ft.Container(
                bgcolor=COLOR_SURFACE,
                border=ft.Border.all(1, COLOR_PRIMARY),
                border_radius=8,
                padding=12,
                content=ft.Text(f"✅ ¡Reserva #{rid} Confirmada Exitosamente!\nZona: {sel_z['nombre']} • Fecha: {fecha_tf.value} ({hora_ini.value} a {hora_fin.value}). Tarifa oficial: {costo_txt}. Notificación enviada.", color=COLOR_PRIMARY_LIGHT, size=13)
            )
            page.update()
            show_toast("Reserva confirmada.")

        # Sección de gestión de tarifas para el Administrador
        admin_tarifa_controls = []
        if session_state.get("rol") in ("admin", "superadmin"):
            tf_inputs = {}
            for z in zonas:
                tf_inputs[z["id"]] = ft.TextField(label=f"{z['nombre']}", value=str(int(z["costo_alquiler"])), width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

            def guardar_tarifas_admin(e):
                for zid, inp in tf_inputs.items():
                    try:
                        n_costo = float(inp.value)
                        db_execute("UPDATE zonas_comunes SET costo_alquiler = ? WHERE id = ?", (n_costo, zid))
                    except ValueError:
                        pass
                show_toast("Tarifas de zonas comunes actualizadas exitosamente.")
                navegar_a("reservas")

            admin_tarifa_controls.append(
                dark_card(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ATTACH_MONEY, color=COLOR_PRIMARY),
                            ft.Text("Gestión de Tarifas de Zonas Comunes (Exclusivo Administrador)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
                        ]),
                        ft.Text("El administrador es quien da y actualiza los valores de alquiler de cada reserva:", size=12, color=COLOR_TEXT_MUTED),
                        ft.Row(list(tf_inputs.values()), wrap=True, spacing=10),
                        ft.FilledButton(text="Guardar Tarifas Oficiales", icon=ft.Icons.SAVE, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=guardar_tarifas_admin)
                    ], spacing=10)
                )
            )

        return ft.ListView([
            ft.Text("Módulo de Reservas de Zonas Comunes", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            *admin_tarifa_controls,
            dark_card(
                ft.Column([
                    ft.Text("Solicitud de Reserva y Control de Disponibilidad", size=15, weight=ft.FontWeight.BOLD),
                    zona_dd,
                    tarifa_info,
                    ft.Row([fecha_tf, hora_ini, hora_fin], wrap=True),
                    cond_cb,
                    ft.FilledButton(text="Confirmar Reserva y Notificar", icon=ft.Icons.CHECK, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=reservar),
                    res_box
                ], spacing=12)
            )
        ], spacing=16)

    # Vista Visitantes Propietario
    def build_vista_visitantes():
        nom_v = ft.TextField(label="Nombre Completo Visitante", width=350, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        doc_v = ft.TextField(label="Documento de Identidad", width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        tel_v = ft.TextField(label="Celular (para WhatsApp)", width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        placa_v = ft.TextField(label="Placa de Vehículo (opcional)", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        qr_box = ft.Container(visible=False, padding=10)

        def generar(e):
            if not nom_v.value or not doc_v.value:
                show_toast("Ingrese nombre y cédula.", es_error=True)
                return
            token = f"QR-{uuid.uuid4().hex[:8].upper()}"
            vid = f"vis_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO visitantes_autorizaciones (id, conjunto_id, unidad_id, residente_nombre, visitante_nombre, visitante_doc, visitante_telefono, fecha_esperada, placa_vehiculo, token_qr, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'AUTORIZADO')
            """, (vid, session_state["conjunto_id"], session_state["unidad_id"], session_state["usuario_nombre"], nom_v.value, doc_v.value, tel_v.value, datetime.date.today().isoformat(), placa_v.value or "Peatonal", token))

            qr_box.visible = True
            qr_box.content = ft.Container(
                bgcolor=COLOR_SURFACE, border=ft.Border.all(1, COLOR_PRIMARY), border_radius=10, padding=14,
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.QR_CODE_2, color=COLOR_PRIMARY_LIGHT, size=32), ft.Text(f"Código QR Generado: {token}", size=16, font_family="monospace", weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)]),
                    ft.Text(f"Visitante: {nom_v.value} • Destino: Apto {session_state['apto_numero']}", size=13),
                    ft.Text("Validación en portería en menos de 2 segundos sin contacto.", size=11, color=COLOR_TEXT_MUTED),
                    ft.FilledButton(text="📲 Enviar Enlace por WhatsApp", icon=ft.Icons.SEND, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700), on_click=lambda ev: show_toast(f"Enlace de WhatsApp generado con token {token}"))
                ], spacing=6)
            )
            page.update()
            show_toast(f"Autorización creada. Token: {token}")

        return ft.ListView([
            ft.Text("Control de Visitantes & Código QR Inteligente", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            dark_card(
                ft.Column([
                    ft.Text("Autorizar Visita Anticipada", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([nom_v, doc_v], wrap=True),
                    ft.Row([tel_v, placa_v], wrap=True),
                    ft.FilledButton(text="Generar Código QR y Enlace WhatsApp", icon=ft.Icons.QR_CODE, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=generar),
                    qr_box
                ], spacing=12)
            )
        ], spacing=16)

    # ==========================================================================
    # 4. VISTAS DE PORTERÍA & SEGURIDAD (VALIDACIÓN 2 SEGUNDOS)
    # ==========================================================================
    def build_vista_porteria():
        token_tf = ft.TextField(label="Escanee Código QR o Digite Token", width=380, autofocus=True, bgcolor=COLOR_CARD_BG, border_color=COLOR_PRIMARY)
        res_port = ft.Container(visible=False, padding=10)

        def escanear(e):
            tok = token_tf.value.strip().upper()
            if not tok:
                show_toast("Ingrese un código QR.", es_error=True)
                return
            t_ini = datetime.datetime.now()
            v_row = db_query("SELECT v.*, u.numero_unidad FROM visitantes_autorizaciones v JOIN unidades u ON v.unidad_id = u.id WHERE v.token_qr = ?", (tok,))
            if not v_row:
                res_port.visible = True
                res_port.content = ft.Container(bgcolor=COLOR_CARD_BG, border=ft.Border.all(1, COLOR_RED), border_radius=10, padding=14, content=ft.Row([ft.Icon(ft.Icons.BLOCK, color=COLOR_RED, size=28), ft.Text("ACCESO DENEGADO - Código Inexistente", weight=ft.FontWeight.BOLD, color=COLOR_RED)]))
                page.update()
                show_toast("Acceso denegado.", es_error=True)
                return

            vis = v_row[0]
            db_execute("UPDATE visitantes_autorizaciones SET estado = 'INGRESADO', ingreso_timestamp = ? WHERE id = ?", (datetime.datetime.now().isoformat(), vis["id"]))
            t_seg = (datetime.datetime.now() - t_ini).total_seconds()

            res_port.visible = True
            res_port.content = ft.Container(
                bgcolor=COLOR_SURFACE, border=ft.Border.all(1, COLOR_PRIMARY), border_radius=10, padding=16,
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=COLOR_PRIMARY, size=32), ft.Text(f"✅ ACCESO CONCEDIDO (Validado en {t_seg:.2f} segundos)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)]),
                    ft.Text(f"Visitante: {vis['visitante_nombre']} (Doc: {vis['visitante_doc']}) • Destino: Apto {vis['numero_unidad']}", size=13),
                    ft.Text(f"Vehículo: {vis['placa_vehiculo']} • Talanquera levantada automáticamente.", size=12, color=COLOR_PRIMARY_LIGHT),
                    ft.Text(f"Notificación Push despachada al residente del Apto {vis['numero_unidad']}.", size=11, color=COLOR_GOLD)
                ], spacing=6)
            )
            token_tf.value = ""
            page.update()
            show_toast("Ingreso concedido en 2 segundos.")

        return ft.ListView([
            ft.Text("Puesto de Control y Portería 24/7 (Modo Oscuro)", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            dark_card(
                ft.Column([
                    ft.Text("Validación Rápida de Acceso con Código QR", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([token_tf, ft.FilledButton(text="⚡ Validar QR (2 Seg)", icon=ft.Icons.SECURITY, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=escanear)], wrap=True),
                    res_port
                ], spacing=12)
            ),
            dark_card(
                ft.Column([
                    ft.Text("Acciones Rápidas del Guarda", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.OutlinedButton(text="Registrar Domicilio (Rappi)", icon=ft.Icons.DELIVERY_DINING, on_click=lambda e: show_toast("Domicilio Rappi registrado con aviso al apto")),
                        ft.OutlinedButton(text="Registrar Contratista ARL", icon=ft.Icons.CONSTRUCTION, on_click=lambda e: show_toast("Contratista verificado con planilla ARL")),
                        ft.OutlinedButton(text="Alerta Inmediata PH", icon=ft.Icons.WARNING, on_click=lambda e: show_toast("Alerta de seguridad emitida")),
                    ], spacing=10, wrap=True)
                ], spacing=8)
            )
        ], spacing=16)

    # Vista PQR
    def build_vista_pqr():
        pqrs = db_query("SELECT * FROM pqr WHERE conjunto_id = ? ORDER BY creado_en DESC", (session_state["conjunto_id"],))
        asunto_tf = ft.TextField(label="Asunto de la PQR / Reporte de Daño", width=380, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        desc_tf = ft.TextField(label="Descripción Detallada", multiline=True, min_lines=3, width=550, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        cat_dd = ft.Dropdown(label="Categoría", value="Peticion", options=[ft.dropdown.Option("Peticion"), ft.dropdown.Option("Queja"), ft.dropdown.Option("Reclamo"), ft.dropdown.Option("Reporte de daño")], width=200, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

        def radicar(e):
            if not asunto_tf.value or not desc_tf.value:
                show_toast("Complete los campos de la solicitud.", es_error=True)
                return
            consec = f"PQR-2026-{uuid.uuid4().hex[:4].upper()}"
            pid = f"pqr_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO pqr (id, consecutivo, conjunto_id, unidad_id, residente_nombre, categoria, asunto, descripcion, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'RECIBIDA')
            """, (pid, consec, session_state["conjunto_id"], session_state["unidad_id"], session_state["usuario_nombre"], cat_dd.value, asunto_tf.value, desc_tf.value))
            show_toast(f"PQR radicada con consecutivo: {consec}")
            navegar_a("pqr")

        pqr_cards = [
            dark_card(
                ft.Column([
                    ft.Row([ft.Text(p["consecutivo"], font_family="monospace", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT), ft.Container(padding=ft.Padding(6, 2, 6, 2), bgcolor=COLOR_SURFACE, border_radius=4, content=ft.Text(p["estado"], color=COLOR_GOLD, size=11, weight=ft.FontWeight.BOLD))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(p["asunto"], size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
                    ft.Text(p["descripcion"], size=12, color=COLOR_TEXT_MUTED)
                ], spacing=4)
            ) for p in pqrs
        ]

        return ft.ListView([
            ft.Text("Módulo de PQR y Reportes de Daño", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            dark_card(
                ft.Column([
                    ft.Text("Radicar Nueva PQR (5 Estados Oficiales)", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([asunto_tf, cat_dd], wrap=True),
                    desc_tf,
                    ft.FilledButton(text="Radicar Solicitud", icon=ft.Icons.SEND, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=radicar)
                ], spacing=10)
            ),
            *pqr_cards
        ], spacing=16)

    # Vista Mascotas
    def build_vista_mascotas():
        mascotas = db_query("SELECT m.*, u.numero_unidad FROM mascotas m JOIN unidades u ON m.unidad_id = u.id WHERE m.conjunto_id = ?", (session_state["conjunto_id"],))
        nom_m = ft.TextField(label="Nombre Mascota", width=220, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        tipo_m = ft.Dropdown(label="Tipo", value="Perro", options=[ft.dropdown.Option("Perro"), ft.dropdown.Option("Gato"), ft.dropdown.Option("Ave")], width=160, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        raza_m = ft.TextField(label="Raza", width=180, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        chip_m = ft.TextField(label="Microchip / Placa", width=200, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

        def registrar_m(e):
            if not nom_m.value:
                show_toast("Ingrese el nombre.", es_error=True)
                return
            mid = f"masc_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO mascotas (id, conjunto_id, unidad_id, nombre, tipo, raza, identificacion_placa, vacunas_al_dia)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (mid, session_state["conjunto_id"], session_state["unidad_id"], nom_m.value, tipo_m.value, raza_m.value, chip_m.value))
            show_toast(f"Mascota '{nom_m.value}' registrada.")
            navegar_a("mascotas")

        masc_cards = [
            dark_card(
                ft.Row([
                    ft.Icon(ft.Icons.PETS, color=COLOR_PRIMARY, size=30),
                    ft.Column([
                        ft.Text(f"{m['nombre']} ({m['tipo']} - {m['raza']})", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
                        ft.Text(f"Apto: {m['numero_unidad']} • Placa/Chip: {m['identificacion_placa']} • Vacunas al Día", size=12, color=COLOR_PRIMARY_LIGHT)
                    ], expand=True)
                ])
            ) for m in mascotas
        ]

        return ft.ListView([
            ft.Text("Censo y Registro Oficial de Mascotas", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
            dark_card(
                ft.Column([
                    ft.Text("Registrar Mascota", size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([nom_m, tipo_m, raza_m, chip_m], wrap=True),
                    ft.FilledButton(text="Guardar Mascota", icon=ft.Icons.SAVE, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=registrar_m)
                ], spacing=10)
            ),
            *masc_cards
        ], spacing=16)

    # Vista Votaciones Ley 675
    def build_vista_votaciones():
        vots = db_query("SELECT * FROM votaciones WHERE conjunto_id = ? ORDER BY fecha_inicio DESC", (session_state["conjunto_id"],))

        def votar_btn(vid, opt):
            u_row = db_query("SELECT coeficiente FROM unidades WHERE id = ?", (session_state["unidad_id"],))
            coef = float(u_row[0]["coeficiente"] if u_row else 1.0)
            ya_voto = db_query("SELECT COUNT(*) as c FROM votos WHERE votacion_id = ? AND unidad_id = ?", (vid, session_state["unidad_id"],))[0]["c"]
            if ya_voto > 0:
                show_toast("Esta unidad ya emitió su voto en esta pregunta.", es_error=True)
                return
            db_execute("INSERT INTO votos (id, votacion_id, conjunto_id, unidad_id, opcion_seleccionada, coeficiente_aplicado) VALUES (?, ?, ?, ?, ?, ?)", (f"vt_{uuid.uuid4().hex[:8]}", vid, session_state["conjunto_id"], session_state["unidad_id"], opt, coef))
            show_toast(f"Voto '{opt}' registrado con ponderación de {coef}%.")
            navegar_a("votaciones")

        # Formulario para que el Administrador formule las preguntas de la asamblea
        admin_preg_controls = []
        if session_state.get("rol") in ("admin", "superadmin"):
            tit_preg_tf = ft.TextField(label="Pregunta Oficial que se somete a Votación en Asamblea", hint_text="Ej: ¿Aprueba los Estados Financieros de la vigencia 2026?", width=500, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
            desc_preg_tf = ft.TextField(label="Sustentación Jurídica (Ley 675)", hint_text="Ej: Ley 675 Art. 38 Num. 2. Aprobación por mayoría ordinaria.", width=350, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
            quorum_dd = ft.Dropdown(label="Quórum Requerido", value="51", options=[ft.dropdown.Option("51", "Quórum Ordinario (51%)"), ft.dropdown.Option("70", "Quórum Calificado (70% Art. 46)")], width=240, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)

            def crear_preg(e):
                if not tit_preg_tf.value:
                    show_toast("Escriba la pregunta de la asamblea.", es_error=True)
                    return
                vid = f"vot_{uuid.uuid4().hex[:8]}"
                db_execute("""
                INSERT INTO votaciones (id, conjunto_id, titulo, descripcion, opciones, estado, quorum_minimo)
                VALUES (?, ?, ?, ?, '["Sí", "No", "Abstención"]', 'ABIERTA', ?)
                """, (vid, session_state["conjunto_id"], tit_preg_tf.value, desc_preg_tf.value or "Formulado por el Administrador", float(quorum_dd.value)))
                show_toast("Pregunta de asamblea publicada para votación.")
                navegar_a("votaciones")

            admin_preg_controls.append(
                dark_card(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.HOW_TO_VOTE, color=COLOR_PRIMARY),
                            ft.Text("Formular Preguntas para la Asamblea (Exclusivo Administrador)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
                        ]),
                        ft.Text("El administrador formula las preguntas, muestra los totales en tiempo real y guarda las votaciones en el informe:", size=12, color=COLOR_TEXT_MUTED),
                        tit_preg_tf,
                        ft.Row([desc_preg_tf, quorum_dd], wrap=True),
                        ft.FilledButton(text="Publicar Pregunta para Votación", icon=ft.Icons.ADD_TASK, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=crear_preg)
                    ], spacing=10)
                )
            )

        # Informe de Asamblea
        acta_box = ft.Container(visible=False, padding=10)

        def generar_informe_asamblea(e):
            hoy_str = datetime.now().strftime("%Y-%m-%d")
            total_preguntas = len(vots)
            lineas_preg = []
            for idx, v in enumerate(vots):
                v_res = db_query("SELECT opcion_seleccionada, SUM(coeficiente_aplicado) as coef, COUNT(*) as c FROM votos WHERE votacion_id = ? GROUP BY opcion_seleccionada", (v["id"],))
                tot_c = sum(r["c"] for r in v_res)
                tot_coef = sum(r["coef"] for r in v_res)
                res_det = ", ".join([f"{r['opcion_seleccionada']}: {r['c']} votos ({r['coef']:.3f}% coef)" for r in v_res])
                lineas_preg.append(f"PREGUNTA {idx+1}: {v['titulo']}\n  Participación: {tot_c} unidades ({tot_coef:.3f}% quórum)\n  Desglose: {res_det or 'Sin votos registrados'}\n")

            acta_txt = f"""================================================================================
INFORME OFICIAL Y ACTA DE ASAMBLEA GENERAL - LEY 675 DE 2001
================================================================================
Copropiedad: EDIFICIO MANCHESTER APTOS PH (Código: 7480)
NIT:         900.777.367-7
Fecha:       {hoy_str}
Total Preguntas Votadas: {total_preguntas}
Administrador: {session_state['usuario_nombre']}
Google Drive: https://drive.google.com/drive/folders/1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E?usp=drive_link

RESULTADOS CONSOLIDADOS DE VOTACIÓN:
{chr(10).join(lineas_preg)}
================================================================================
Firmas: Presidente de Asamblea • Secretario de Asamblea • Administrador
================================================================================"""

            inf_id = f"acta_{uuid.uuid4().hex[:8]}"
            db_execute("""
            INSERT INTO asambleas_informes (id, conjunto_id, titulo_asamblea, fecha_asamblea, total_preguntas, contenido_acta, datos_consolidados, creado_por, drive_url)
            VALUES (?, ?, ?, ?, ?, ?, '[]', ?, ?)
            """, (inf_id, session_state["conjunto_id"], f"Acta Oficial de Asamblea {hoy_str}", hoy_str, total_preguntas, acta_txt, session_state["usuario_nombre"], "https://drive.google.com/drive/folders/1x9dAsErwPBQrZuawj4PFxOS9O4_VBj1E?usp=drive_link"))

            acta_box.visible = True
            acta_box.content = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1, COLOR_PRIMARY),
                border_radius=8,
                padding=12,
                content=ft.Column([
                    ft.Text("📑 Acta e Informe Oficial Consolidado de la Asamblea:", size=14, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                    ft.Text(acta_txt, size=11, font_family="monospace", color=COLOR_TEXT_MAIN)
                ])
            )
            page.update()
            show_toast("Informe oficial de asamblea generado y guardado exitosamente.")

        vot_cards = []
        for v in vots:
            opcs = json.loads(v["opciones"])
            votos_res = db_query("SELECT opcion_seleccionada, SUM(coeficiente_aplicado) as coef, COUNT(*) as c FROM votos WHERE votacion_id = ? GROUP BY opcion_seleccionada", (v["id"],))
            total_coef = sum(vr["coef"] for vr in votos_res)
            total_votos = sum(vr["c"] for vr in votos_res)

            desglose_txt = " • ".join([f"{vr['opcion_seleccionada']}: {vr['c']} votos ({vr['coef']:.3f}%)" for vr in votos_res]) if votos_res else "Sin votos aún"

            vot_cards.append(
                dark_card(
                    ft.Column([
                        ft.Row([
                            ft.Text("Asamblea General de Copropietarios (Ley 675)", size=12, color=COLOR_TEXT_MUTED),
                            ft.Container(padding=ft.Padding(6, 2, 6, 2), bgcolor=COLOR_SURFACE, border_radius=4, content=ft.Text("ABIERTA", color=COLOR_PRIMARY, size=11, weight=ft.FontWeight.BOLD))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(v["titulo"], size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
                        ft.Text(v["descripcion"] or "", size=12, color=COLOR_TEXT_MUTED),
                        ft.Container(
                            bgcolor=COLOR_SURFACE,
                            border_radius=6,
                            padding=8,
                            content=ft.Column([
                                ft.Text(f"📊 Totales: {total_votos} unidades han votado • Quórum Acumulado: {total_coef:.3f}% de coeficientes", size=12, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT),
                                ft.Text(f"Resultados: {desglose_txt}", size=11, color=COLOR_TEXT_MAIN)
                            ], spacing=4)
                        ),
                        ft.Row([
                            ft.FilledButton(text=o, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK if o == "Sí" else (COLOR_RED if o == "No" else COLOR_CARD_BG)), on_click=lambda e, opt=o, vid=v["id"]: votar_btn(vid, opt))
                            for o in opcs
                        ], spacing=8)
                    ], spacing=8)
                )
            )

        top_header_controls = [
            ft.Text("Votaciones en Asamblea General (Ley 675)", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)
        ]
        if session_state.get("rol") in ("admin", "superadmin"):
            top_header_controls.append(
                ft.FilledButton(text="Generar Informe de Asamblea", icon=ft.Icons.DESCRIPTION, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=generar_informe_asamblea)
            )

        return ft.ListView([
            ft.Row(top_header_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Text("Ponderación matemática exacta por coeficiente de propiedad de cada unidad.", size=12, color=COLOR_TEXT_MUTED),
            *admin_preg_controls,
            acta_box,
            *vot_cards
        ], spacing=16)

    # Vista Ley 675 con Subíndices de Resolución
    def build_vista_ley_675():
        search_tf = ft.TextField(
            label="Buscar duda o conflicto (ej: morosos, citófono, mascotas, multas, quórum, parqueadero...)",
            prefix_icon=ft.Icons.SEARCH,
            width=480,
            bgcolor=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER
        )

        subindices_lista = [
            "Todos los Subíndices",
            "Mora y Cobros",
            "Asambleas y Quórum",
            "Mascotas y Animales",
            "Convivencia y Sanciones",
            "Parqueaderos",
            "Administrador y Consejo",
            "Obras y Fachadas",
            "Expensas y Coeficientes",
            "Arrendatarios e Inquilinos"
        ]

        subindice_dd = ft.Dropdown(
            label="Subíndice de Resolución",
            options=[ft.dropdown.Option(s) for s in subindices_lista],
            value="Todos los Subíndices",
            width=230,
            bgcolor=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER
        )

        perfil_dd = ft.Dropdown(
            label="Dirigido a",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Copropietarios"),
                ft.dropdown.Option("Administradores")
            ],
            value="Todos",
            width=180,
            bgcolor=COLOR_CARD_BG,
            border_color=COLOR_CARD_BORDER
        )

        res_col = ft.Column(spacing=12)

        def buscar(e=None):
            q = (search_tf.value or "").strip().lower()
            sub = subindice_dd.value or "Todos los Subíndices"
            perf = perfil_dd.value or "Todos"

            sql = "SELECT * FROM ley_675 WHERE 1=1"
            params = []

            if sub != "Todos los Subíndices":
                sql += " AND subindice LIKE ?"
                params.append(f"%{sub}%")

            if perf != "Todos":
                sql += " AND (aplicable_a = ? OR aplicable_a = 'Ambos')"
                params.append(perf)

            if q:
                sql += " AND (titulo LIKE ? OR pregunta_resolucion LIKE ? OR resolucion_practica LIKE ? OR contenido LIKE ? OR palabras_clave LIKE ?)"
                qw = f"%{q}%"
                params.extend([qw, qw, qw, qw, qw])

            sql += " ORDER BY articulo ASC"
            arts = db_query(sql, tuple(params))
            res_col.controls.clear()

            if not arts:
                res_col.controls.append(
                    dark_card(
                        ft.Column([
                            ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color=COLOR_GOLD, size=24), ft.Text("No se encontraron resoluciones con los filtros aplicados.", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN)]),
                            ft.Text("Intente buscar con términos más generales como: mora, mascotas, multas, quórum, fachada, asamblea o parqueaderos.", size=12, color=COLOR_TEXT_MUTED)
                        ], spacing=6)
                    )
                )
            else:
                for a in arts:
                    preg = a.get("pregunta_resolucion") or a.get("titulo")
                    resol = a.get("resolucion_practica") or a.get("contenido")
                    apl = a.get("aplicable_a") or "Ambos"

                    color_badge = COLOR_PRIMARY_LIGHT if apl == "Copropietarios" else (COLOR_BLUE if apl == "Administradores" else COLOR_GOLD)

                    card_content = ft.Column([
                        # Cabecera: Subíndice y Etiquetas
                        ft.Row([
                            ft.Row([
                                ft.Container(
                                    padding=ft.Padding(8, 3, 8, 3),
                                    bgcolor=COLOR_SURFACE,
                                    border_radius=6,
                                    border=ft.Border.all(1, COLOR_PRIMARY_DARK),
                                    content=ft.Text(f"📌 {a['subindice']}", size=11, color=COLOR_PRIMARY_LIGHT, weight=ft.FontWeight.BOLD)
                                ),
                                ft.Container(
                                    padding=ft.Padding(8, 3, 8, 3),
                                    bgcolor=COLOR_CARD_BORDER,
                                    border_radius=6,
                                    content=ft.Text(f"Para: {apl}", size=11, color=color_badge, weight=ft.FontWeight.BOLD)
                                )
                            ], spacing=6),
                            ft.Text(f"Artículo {a['articulo']} • {a['capitulo']}", size=11, color=COLOR_TEXT_MUTED)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        # Pregunta de Consulta Frecuente
                        ft.Row([
                            ft.Icon(ft.Icons.HELP_OUTLINE, color=COLOR_GOLD, size=22),
                            ft.Text(preg, size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN, expand=True)
                        ], cross_axis_alignment=ft.CrossAxisAlignment.START, spacing=8),

                        # Caja Destacada: Dictamen y Resolución Práctica Inmediata
                        ft.Container(
                            bgcolor=COLOR_SURFACE,
                            border=ft.Border.all(1, COLOR_PRIMARY_DARK),
                            border_radius=10,
                            padding=14,
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.GAVEL, color=COLOR_PRIMARY_LIGHT, size=18),
                                    ft.Text("DICTAMEN Y RESOLUCIÓN PRÁCTICA:", size=11, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT)
                                ], spacing=6),
                                ft.Text(resol, size=13, color=COLOR_TEXT_MAIN, weight=ft.FontWeight.W_500)
                            ], spacing=6)
                        ),

                        # Fundamento Jurídico Textual de la Ley 675
                        ft.Column([
                            ft.Text(f"Fundamento Legal: {a['titulo']}", size=12, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MUTED),
                            ft.Text(f'"{a["contenido"]}"', size=11, color=COLOR_TEXT_MUTED, italic=True)
                        ], spacing=3),

                        # Botones de Acción
                        ft.Row([
                            ft.OutlinedButton(
                                text="Copiar Resolución",
                                icon=ft.Icons.COPY,
                                on_click=lambda ev, p=preg, r=resol, art=a['articulo']: show_toast(f"Resolución del Art. {art} copiada.")
                            ),
                            ft.FilledButton(
                                text="Compartir por WhatsApp",
                                icon=ft.Icons.SHARE,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_800),
                                on_click=lambda ev, p=preg, art=a['articulo']: show_toast(f"Texto del Art. {art} listo para compartir por WhatsApp.")
                            )
                        ], spacing=8)
                    ], spacing=10)

                    res_col.controls.append(dark_card(card_content, padding=16))

            page.update()

        def set_pregunta_rapida(termino):
            search_tf.value = termino
            subindice_dd.value = "Todos los Subíndices"
            perfil_dd.value = "Todos"
            buscar(None)

        # Chips de preguntas frecuentes rápidas
        chips_rapidos = ft.Row([
            ft.TextButton(text="🚨 ¿Cortar citófono a moroso?", on_click=lambda e: set_pregunta_rapida("citófono")),
            ft.TextButton(text="🐾 ¿Prohibir mascotas en apto?", on_click=lambda e: set_pregunta_rapida("mascotas")),
            ft.TextButton(text="🚗 ¿Cobrar parqueadero visitas?", on_click=lambda e: set_pregunta_rapida("parqueadero visitantes")),
            ft.TextButton(text="📜 ¿Mayoría calificada 70%?", on_click=lambda e: set_pregunta_rapida("70%")),
            ft.TextButton(text="🔨 ¿Procedimiento para multas?", on_click=lambda e: set_pregunta_rapida("debido proceso multas")),
            ft.TextButton(text="💧 ¿Quién paga humedades?", on_click=lambda e: set_pregunta_rapida("humedades"))
        ], wrap=True, spacing=6)

        search_tf.on_submit = buscar
        subindice_dd.on_change = buscar
        perfil_dd.on_change = buscar

        buscar(None)

        return ft.ListView([
            ft.Column([
                ft.Text("Buscador y Subíndices de Resolución - Ley 675 de 2001", size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MAIN),
                ft.Text("Respuestas y dictámenes jurídicos inmediatos para Copropietarios y Administradores ante conflictos y dudas de la copropiedad.", size=12, color=COLOR_TEXT_MUTED)
            ], spacing=2),
            dark_card(
                ft.Column([
                    ft.Row([search_tf, subindice_dd, perfil_dd, ft.FilledButton(text="Buscar", icon=ft.Icons.SEARCH, style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_DARK), on_click=buscar)], wrap=True, spacing=10),
                    ft.Divider(height=10, color=COLOR_CARD_BORDER),
                    ft.Text("Preguntas Frecuentes de Resolución Rápida:", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_MUTED),
                    chips_rapidos
                ], spacing=10)
            ),
            res_col
        ], spacing=16)

    # ==========================================================================
    # ENRUTAMIENTO Y REGENERACIÓN DE SIDEBAR POR ROL
    # ==========================================================================
    def btn_nav(texto: str, icon: Any, ruta: str):
        return ft.TextButton(
            content=ft.Row([
                ft.Icon(icon, color=COLOR_PRIMARY_LIGHT, size=18),
                ft.Text(texto, color=COLOR_TEXT_MAIN, size=12, weight=ft.FontWeight.W_500)
            ], spacing=8),
            on_click=lambda e: navegar_a(ruta)
        )

    def actualizar_sidebar_por_rol(rol: str):
        sidebar_container.content = None
        controles = []

        if rol == "superadmin":
            controles = [
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_GOLD),
                    content=ft.Row([
                        ft.Icon(ft.Icons.WORKSPACE_PREMIUM, color=COLOR_GOLD, size=18),
                        ft.Text("MENÚ SUPERADMIN", size=11, weight=ft.FontWeight.BOLD, color=COLOR_GOLD)
                    ], spacing=6)
                ),
                ft.Divider(height=8, color=COLOR_CARD_BORDER),
                btn_nav("Dashboard Global", ft.Icons.DASHBOARD, "superadmin_dash"),
                btn_nav("Crear Copropiedad & NIT", ft.Icons.DOMAIN, "superadmin_dash"),
                btn_nav("Bancos & Cuentas PH", ft.Icons.ACCOUNT_BALANCE, "superadmin_dash"),
                btn_nav("Pasarelas & Webhooks", ft.Icons.PAYMENTS, "superadmin_dash"),
                btn_nav("Conciliación Bancaria", ft.Icons.SYNC, "superadmin_dash"),
                btn_nav("Buscador Ley 675", ft.Icons.GAVEL, "ley675"),
            ]
        elif rol == "admin":
            controles = [
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_PRIMARY_LIGHT),
                    content=ft.Row([
                        ft.Icon(ft.Icons.BUSINESS, color=COLOR_PRIMARY_LIGHT, size=18),
                        ft.Text("MENÚ ADMINISTRADOR", size=11, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY_LIGHT)
                    ], spacing=6)
                ),
                ft.Divider(height=8, color=COLOR_CARD_BORDER),
                btn_nav("10 Indicadores de Gestión", ft.Icons.INSIGHTS, "admin"),
                btn_nav("Pagos a Proveedores", ft.Icons.PAYMENTS, "admin"),
                btn_nav("Gestión de Reservas", ft.Icons.POOL, "reservas"),
                btn_nav("Control de Visitantes", ft.Icons.QR_CODE, "visitantes"),
                btn_nav("Gestión de PQR", ft.Icons.SUPPORT_AGENT, "pqr"),
                btn_nav("Censo de Mascotas", ft.Icons.PETS, "mascotas"),
                btn_nav("Votaciones de Asamblea", ft.Icons.HOW_TO_VOTE, "votaciones"),
                btn_nav("Buscador Ley 675", ft.Icons.GAVEL, "ley675"),
            ]
        elif rol == "porteria":
            controles = [
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_BLUE),
                    content=ft.Row([
                        ft.Icon(ft.Icons.SECURITY, color=COLOR_BLUE, size=18),
                        ft.Text("MENÚ SEGURIDAD & PORTERÍA", size=10, weight=ft.FontWeight.BOLD, color=COLOR_BLUE)
                    ], spacing=6)
                ),
                ft.Divider(height=8, color=COLOR_CARD_BORDER),
                btn_nav("Validación QR (2 Seg)", ft.Icons.SECURITY, "porteria"),
                btn_nav("Bitácora de Ingresos", ft.Icons.VIEW_LIST, "porteria"),
                btn_nav("Registro Domicilios", ft.Icons.DELIVERY_DINING, "porteria"),
                btn_nav("Alerta Inmediata PH", ft.Icons.WARNING, "porteria"),
            ]
        else: # residente / copropietario
            controles = [
                ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_PRIMARY),
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=COLOR_PRIMARY, size=18),
                        ft.Text("MENÚ DEL COPROPIETARIO", size=10, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
                    ], spacing=6)
                ),
                ft.Divider(height=8, color=COLOR_CARD_BORDER),
                btn_nav("Inicio / Mi Inmueble", ft.Icons.HOME, "inicio"),
                btn_nav("Pagar Cuota (Bre-B/PSE)", ft.Icons.PAYMENTS, "pagos"),
                btn_nav("Reservar Zona Común", ft.Icons.POOL, "reservas"),
                btn_nav("Autorizar Visita (QR)", ft.Icons.QR_CODE_2, "visitantes"),
                btn_nav("Radicar PQR", ft.Icons.SUPPORT_AGENT, "pqr"),
                btn_nav("Mis Mascotas", ft.Icons.PETS, "mascotas"),
                btn_nav("Votación Asamblea", ft.Icons.HOW_TO_VOTE, "votaciones"),
                btn_nav("Consultar Ley 675", ft.Icons.GAVEL, "ley675"),
            ]

        sidebar_container.content = ft.Column(controles, spacing=4)
        if hasattr(sidebar_container, "update"):
            try:
                sidebar_container.update()
            except Exception:
                pass
        page.update()

    def navegar_a(ruta: str):
        session_state["menu_seleccionado"] = ruta
        if ruta == "superadmin_dash":
            body_container.content = build_vista_superadmin()
        elif ruta == "admin":
            body_container.content = build_vista_admin()
        elif ruta == "inicio":
            body_container.content = build_vista_inicio()
        elif ruta == "pagos":
            body_container.content = build_vista_pagos()
        elif ruta == "reservas":
            body_container.content = build_vista_reservas()
        elif ruta == "visitantes":
            body_container.content = build_vista_visitantes()
        elif ruta == "porteria":
            body_container.content = build_vista_porteria()
        elif ruta == "pqr":
            body_container.content = build_vista_pqr()
        elif ruta == "mascotas":
            body_container.content = build_vista_mascotas()
        elif ruta == "votaciones":
            body_container.content = build_vista_votaciones()
        elif ruta == "ley675":
            body_container.content = build_vista_ley_675()
        page.update()

    # Barra superior oscura y selectores
    conjuntos_disponibles = db_query("SELECT id, codigo, nombre FROM conjuntos")
    conj_dropdown = ft.Dropdown(
        value=session_state["conjunto_id"],
        options=[ft.dropdown.Option(c["id"], f"{c['codigo']} - {c['nombre'][:24]}") for c in conjuntos_disponibles],
        width=250, text_size=11, bgcolor=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER
    )
    def cambiar_conjunto(e):
        session_state["conjunto_id"] = conj_dropdown.value
        show_toast(f"Copropiedad activa: {conj_dropdown.value}")
        navegar_a(session_state["menu_seleccionado"])
    conj_dropdown.on_change = cambiar_conjunto

    rol_dropdown = ft.Dropdown(
        value=session_state["rol"],
        options=[
            ft.dropdown.Option("residente", "👤 Copropietario"),
            ft.dropdown.Option("admin", "🏢 Administrador"),
            ft.dropdown.Option("porteria", "🛡️ Portería")
        ],
        width=175, text_size=11, bgcolor=COLOR_SURFACE, border_color=COLOR_PRIMARY
    )

    def cambiar_rol_func(nuevo_rol: str):
        session_state["rol"] = nuevo_rol
        rol_dropdown.value = nuevo_rol
        nombres_roles = {
            "admin": "ADMINISTRADOR DEL CONJUNTO",
            "residente": "COPROPIETARIO / RESIDENTE",
            "porteria": "SEGURIDAD Y PORTERÍA"
        }
        show_toast(f"Perfil cambiado a: {nombres_roles.get(nuevo_rol, nuevo_rol)}")
        actualizar_sidebar_por_rol(nuevo_rol)
        if nuevo_rol == "admin":
            navegar_a("admin")
        elif nuevo_rol == "porteria":
            navegar_a("porteria")
        else:
            navegar_a("inicio")
        if hasattr(rol_dropdown, "update"):
            try:
                rol_dropdown.update()
            except Exception:
                pass

    def on_dropdown_rol_change(e):
        val = e.control.value if e and hasattr(e, "control") and e.control else rol_dropdown.value
        cambiar_rol_func(val)

    rol_dropdown.on_change = on_dropdown_rol_change

    # Botones directos de 1 clic para cambiar entre los 3 roles
    btn_res = ft.TextButton(
        content=ft.Row([ft.Icon(ft.Icons.PERSON, color=COLOR_PRIMARY, size=15), ft.Text("Copropietario", size=11, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD)], spacing=4),
        on_click=lambda e: cambiar_rol_func("residente")
    )
    btn_adm = ft.TextButton(
        content=ft.Row([ft.Icon(ft.Icons.BUSINESS, color=COLOR_PRIMARY_LIGHT, size=15), ft.Text("Admin PH", size=11, color=COLOR_PRIMARY_LIGHT, weight=ft.FontWeight.BOLD)], spacing=4),
        on_click=lambda e: cambiar_rol_func("admin")
    )
    btn_por = ft.TextButton(
        content=ft.Row([ft.Icon(ft.Icons.SECURITY, color=COLOR_BLUE, size=15), ft.Text("Portería", size=11, color=COLOR_BLUE, weight=ft.FontWeight.BOLD)], spacing=4),
        on_click=lambda e: cambiar_rol_func("porteria")
    )

    logo_widget = ft.Container(
        content=ft.Image(
            src=os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "logo_lefacturamos.png")),
            height=34,
            fit=ft.BoxFit.CONTAIN if hasattr(ft, "BoxFit") else "contain"
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        padding=ft.Padding(8, 2, 8, 2),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color="#0f172a")
    )

    top_appbar = ft.Container(
        bgcolor=COLOR_SIDEBAR,
        padding=ft.Padding(14, 8, 14, 8),
        border=ft.Border.only(bottom=ft.BorderSide(1, COLOR_CARD_BORDER)),
        content=ft.Row([
            ft.Row([
                logo_widget,
                ft.Column([
                    ft.Text("Plataforma de Administración de Propiedad Horizontal", color=COLOR_TEXT_MAIN, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("Ley 675 de 2001 • Pagos Bre-B / PSE • Google Drive Oficial", color=COLOR_PRIMARY_LIGHT, size=10)
                ], spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            ft.Row([
                ft.Container(
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_CARD_BORDER),
                    padding=ft.Padding(6, 2, 6, 2),
                    content=ft.Row([btn_res, btn_adm, btn_por], spacing=4)
                ),
                conj_dropdown,
                rol_dropdown
            ], spacing=8)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    # Layout Principal
    page.add(
        top_appbar,
        ft.Row([sidebar_container, body_container], expand=True, spacing=0)
    )

    # Inicializar con Menú del Propietario en Modo Oscuro
    actualizar_sidebar_por_rol(session_state["rol"])
    navegar_a("inicio")

if __name__ == "__main__":
    print("[*] Iniciando LEFACTURAMOS en Modo Oscuro con 3 Menús Especializados (Copropietario, Administrador y Portería)...")
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
