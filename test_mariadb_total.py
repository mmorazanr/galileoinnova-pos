import mysql.connector
import pandas as pd

conn = mysql.connector.connect(
    host='hawk200.startdedicated.com',
    user='recetas',
    password='gcode2025!',
    database='Recetas'
)

query = """
SELECT mesero, SUM(monto_venta) as total 
FROM restaurantes_ventas 
WHERE fecha = '2026-02-23'
GROUP BY mesero
"""
df = pd.read_sql(query, conn)
print('MariaDB for 2026-02-23:')
print(df)
print('Total:', df['total'].sum())
conn.close()
