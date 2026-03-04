import pyodbc
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBOData_s.mdb;PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
cur = conn.cursor()
cur.execute("SELECT DISTINCT MediaName FROM DailyCashierMedia ORDER BY MediaName")
for row in cur.fetchall():
    print(row[0])
conn.close()
