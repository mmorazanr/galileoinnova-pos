#!/usr/bin/env python3
"""
Script para exportar TransactionJournal a Excel
Extrae datos de las tablas de transacciones de CBODaily.mdb
"""

import pyodbc
import pandas as pd
import os
from datetime import datetime

# ==================== CONFIGURACION ====================
DB_PATH = r"C:\ICOM\Database\CBODaily.mdb"
DB_PASSWORD = "C0mtrex"
OUTPUT_DIR = r"C:\ICOM\Database\Exports"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"TransactionJournal_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx")

# ==================== CREAR CARPETA ====================
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("EXPORTADOR DE TRANSACTION JOURNAL")
print("=" * 70)
print()

try:
    # ==================== CONECTAR A BD ====================
    print("Conectando a la base de datos...")
    conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};Pwd={DB_PASSWORD};'
    conn = pyodbc.connect(conn_str, timeout=10)
    print("[OK] Conexion exitosa")
    print()

    # ==================== EXTRAER DATOS ====================
    print("Extrayendo datos de transacciones...")

    # Intenta leer la tabla principal de transacciones
    # Prueba primero con TransactionDetailsPOS (la mas completa)
    try:
        query = """
        SELECT * FROM TransactionDetailsPOS
        ORDER BY TransactionID DESC
        """
        df = pd.read_sql(query, conn)
        print(f"[OK] Extraidos {len(df)} registros de TransactionDetailsPOS")

    except Exception as e:
        print(f"[WARNING] Error con TransactionDetailsPOS: {str(e)[:100]}")
        # Alternativa: combinar header y details
        try:
            query_header = "SELECT * FROM TransactionHeaderPOS"
            query_detail = "SELECT * FROM TransactionDetailsPOS"

            df_header = pd.read_sql(query_header, conn)
            df_detail = pd.read_sql(query_detail, conn)

            print(f"[OK] TransactionHeaderPOS: {len(df_header)} registros")
            print(f"[OK] TransactionDetailsPOS: {len(df_detail)} registros")

            # Combinar por TransactionID si existe
            if 'TransactionID' in df_header.columns and 'TransactionID' in df_detail.columns:
                df = df_detail.merge(df_header, on='TransactionID', how='left', suffixes=('', '_header'))
            else:
                df = df_detail
        except Exception as e2:
            print(f"Error alternativo: {str(e2)[:100]}")
            # Ultima opcion: solo details
            df = pd.read_sql("SELECT * FROM TransactionDetailsPOS", conn)

    conn.close()
    print()

    # ==================== EXPORTAR A EXCEL ====================
    print("Exportando a Excel...")
    df.to_excel(OUTPUT_FILE, sheet_name='Transactions', index=False)

    print(f"[OK] Archivo creado:")
    print(f"  {OUTPUT_FILE}")
    print()
    print(f"Total de registros: {len(df)}")
    print(f"Total de columnas: {len(df.columns)}")
    print()
    print("=" * 70)
    print("SUCCESS: Exportacion completada")
    print("=" * 70)

except Exception as e:
    print(f"ERROR: {str(e)}")
    print()
    print("Verifica:")
    print("1. La contrasena sea correcta (C0mtrex)")
    print("2. El archivo existe en: " + DB_PATH)
    print("3. Que la carpeta de Exports exista")
    exit(1)
