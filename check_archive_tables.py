import pyodbc
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBOData_s.mdb;PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
print([t for t in tables if 'Hist' in t or 'Arch' in t or 'Old' in t])
conn.close()
