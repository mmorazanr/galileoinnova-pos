import pyodbc
db_path = r'C:\ICOM\Database\Backup\CBODATA_SBKUP.mdb'
conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
print("DailyCashierMedia" in tables)
conn.close()
