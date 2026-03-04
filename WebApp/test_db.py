import pyodbc

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    r"DBQ=C:\ICOM\Database\CBOData_s.mdb;"
    r"PWD=C0mtrex;"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 SalesDayNumber FROM TransactionHeader")
    row = cursor.fetchone()
    print("SUCCESS", row)
    conn.close()
except Exception as e:
    print("ERROR:", e)
