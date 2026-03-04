import pyodbc
import pandas as pd
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBOData_s.mdb;PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
q = "SELECT SalesDayNumber, MIN(DateTimeStart) as StartDate FROM TransactionHeader GROUP BY SalesDayNumber ORDER BY SalesDayNumber"
df = pd.read_sql(q, conn)
print(df)
conn.close()
