import pyodbc
import pandas as pd
import os

db_path = r'C:\ICOM\Database\Backup\20250607.data.mdb'
conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=C0mtrex;'
try:
    conn = pyodbc.connect(conn_str)
    
    # Check tables
    cursor = conn.cursor()
    tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
    print("Tables:", [t for t in tables if t in ['DailyCashierSales', 'TransactionHeader', 'DailyCashierMedia', 'DailyCashierMisc', 'HourlySalesNew', 'K_CategoryDefinitions']])
    
    q = "SELECT MAX(SalesDayNumber) FROM DailyCashierSales"
    print("Max Day:", cursor.execute(q).fetchone())
except Exception as e:
    print("Error:", e)
