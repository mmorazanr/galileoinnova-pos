import pyodbc
db_path = r'C:\ICOM\Database\Backup\CBODATA_SBKUP.mdb'
conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
cur = conn.cursor()
cur.execute("SELECT MIN(SalesDayNumber), MAX(SalesDayNumber) FROM TransactionHeader")
print("SalesDayNumber range:", cur.fetchone())
cur.execute("SELECT MIN(DateTimeStart), MAX(DateTimeStart) FROM TransactionHeader")
print("Date range:", cur.fetchone())
conn.close()
