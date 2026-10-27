#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEFACTURAMOS - Plataforma de Administración de Propiedad Horizontal
Script de Conversión y Migración Masiva de Bases de Datos Excel a Estándar Ley 675.

Requisitos:
    pip install pandas openpyxl tabulate requests

Compatibilidad:
    - Windows 10 / 11 (PowerShell o CMD)
    - Linux / macOS
    - Backend API para Android / iOS
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Tuple
import pandas as pd

VERSION = "2.4.0-colombia"

COLUMNAS_OFICIALES = {
    "unidades": [
        "Torre", "Numero_Unidad", "Tipo_Inmueble", "Coeficiente_Porcentaje",
        "Area_M2", "Cuarto_Util", "Parqueadero_Privado", "Parqueadero_Moto"
    ],
    "propietarios": [
        "Torre", "Numero_Unidad", "Rol", "Tipo_Documento", "Numero_Documento",
        "Nombres_Apellidos", "Email_Facturacion", "Telefono_WhatsApp", "Es_Contacto_Principal"
    ],
    "cartera": [
        "Torre", "Numero_Unidad", "Cuota_Administracion", "Intereses_Mora",
        "Cuota_Extraordinaria", "Seguro_Comun", "Servicios_Publicos",
        "Notas_Debito", "Notas_Credito", "Descuento_Pronto_Pago"
    ]
}

# Diccionario de sinonimos para mapeo inteligente de columnas del cliente
SINONIMOS_COLUMNAS = {
    "Numero_Unidad": ["apto", "apartamento", "unidad", "inmueble", "predio", "numero", "nro", "casa", "local"],
    "Torre": ["bloque", "etapa", "edificio", "interior", "modulo"],
    "Coeficiente_Porcentaje": ["coeficiente", "coef", "porcentaje", "part", "participacion", "%"],
    "Area_M2": ["area", "metraje", "m2", "metros", "superficie"],
    "Cuarto_Util": ["deposito", "cuarto_util", "util", "bodega", "locker"],
    "Parqueadero_Privado": ["parqueadero", "parqueo", "garaje", "parking", "parq_privado"],
    "Nombres_Apellidos": ["propietario", "nombre", "nombre_completo", "titular", "copropietario", "cliente"],
    "Numero_Documento": ["cedula", "nit", "cc", "documento", "identificacion", "id"],
    "Telefono_WhatsApp": ["telefono", "celular", "whatsapp", "movil", "tel"],
    "Email_Facturacion": ["correo", "email", "mail", "correo_electronico"],
    "Cuota_Administracion": ["cuota", "administracion", "valor_admon", "expensa", "canon", "valor_cuota"]
}

class ConversorExcelLefacturamos:
    def __init__(self, ruta_archivo_cliente: str):
        self.ruta_archivo = ruta_archivo_cliente
        self.wb_data = None
        self.resultados = {}

    def cargar_archivo(self) -> bool:
        if not os.path.exists(self.ruta_archivo):
            print(f"[ERROR] Archivo no encontrado: {self.ruta_archivo}")
            return False
        
        print(f"[OK] Leyendo archivo Excel: {self.ruta_archivo}...")
        try:
            self.excel_file = pd.ExcelFile(self.ruta_archivo)
            print(f"[OK] Hojas detectadas: {self.excel_file.sheet_names}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al abrir Excel: {e}")
            return False

    def auto_mapear_columnas(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        mapeo = {}
        columnas_df = list(df.columns)
        
        for col in columnas_df:
            col_normalizada = str(col).lower().strip().replace(" ", "_").replace(".", "")
            for campo_oficial, alias_lista in SINONIMOS_COLUMNAS.items():
                if col_normalizada in alias_lista or any(alias in col_normalizada for alias in alias_lista):
                    mapeo[col] = campo_oficial
                    break
        
        df_renombrado = df.rename(columns=mapeo)
        return df_renombrado, mapeo

    def validar_ley_675_coeficientes(self, df_unidades: pd.DataFrame) -> Dict:
        if "Coeficiente_Porcentaje" not in df_unidades.columns:
            return {"valido": False, "mensaje": "Columna Coeficiente_Porcentaje no encontrada"}
        
        # Limpiar y convertir a flotante
        coefs = pd.to_numeric(
            df_unidades["Coeficiente_Porcentaje"].astype(str).str.replace("%", "").str.replace(",", "."),
            errors="coerce"
        ).fillna(0.0)
        
        suma = coefs.sum()
        diferencia = abs(100.0 - suma)
        
        es_valido = diferencia <= 0.05
        return {
            "valido": es_valido,
            "suma_total": round(suma, 4),
            "diferencia": round(diferencia, 4),
            "mensaje": f"Suma total de coeficientes: {suma:.4f}% (Meta Ley 675: 100.0000%)"
        }

    def generar_plantilla_estandarizada(self, ruta_salida: str):
        """Toma los datos del cliente y los emite en el formato estandar de LEFACTURAMOS"""
        print(f"\n[*] Convirtiendo datos a estándar LEFACTURAMOS...")
        writer = pd.ExcelWriter(ruta_salida, engine="openpyxl")

        for sheet_name in self.excel_file.sheet_names:
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            df_proc, mapeo = self.auto_mapear_columnas(df)
            print(f" -> Hoja '{sheet_name}': {len(df_proc)} filas procesadas. Columnas mapeadas: {mapeo}")
            df_proc.to_excel(writer, sheet_name=sheet_name[:30], index=False)

        writer.close()
        print(f"\n[ÉXITO] Archivo estandarizado guardado en: {ruta_salida}")
        print("[LISTO] Ahora puedes cargar este archivo directamente en la plataforma web LEFACTURAMOS.")

def main():
    parser = argparse.ArgumentParser(description="LEFACTURAMOS - Conversor de Bases de Datos Excel a Ley 675")
    parser.add_argument("--archivo", "-a", type=str, help="Ruta de tu archivo Excel original de copropietarios o cartera")
    parser.add_argument("--salida", "-s", type=str, default="LEFACTURAMOS_Base_Convertida.xlsx", help="Archivo de salida")
    parser.add_argument("--exportar-json", action="store_true", help="Exportar datos a JSON para API REST")

    args = parser.parse_args()

    print("=" * 70)
    print(f" LEFACTURAMOS - Conversor de Bases Excel (Python v{VERSION})")
    print(" Soporte: Windows 10/11, macOS, Linux, API Android/iOS")
    print("=" * 70)

    if not args.archivo:
        print("\nModo interactivo: Ingrese la ruta de su archivo Excel:")
        ruta = input("Ruta de archivo Excel (.xlsx/.xls): ").strip().strip('"')
    else:
        ruta = args.archivo

    conversor = ConversorExcelLefacturamos(ruta)
    if conversor.cargar_archivo():
        conversor.generar_plantilla_estandarizada(args.salida)

if __name__ == "__main__":
    main()
