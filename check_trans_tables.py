import pyodbc, json

with open('config.json', 'r') as f:
    cfg = json.load(f)

conn = pyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;")
cursor = conn.cursor()

tables = [t.table_name for t in cursor.tables(tableType='TABLE')]
trans_tables = [t for t in tables if 'Trans' in t or 'Detail' in t or 'Sales' in t]
print('Tablas relacionadas con transacciones/ventas:')
for t in sorted(trans_tables):
    print(' ', t)
conn.close()
