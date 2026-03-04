import pyodbc 
import pandas as pd
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBOData_s.mdb;PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
q = """
SELECT CashierNumber, MediaName, SUM(POSAmount) as QtyAmount
FROM DailyCashierMedia
WHERE SalesDayNumber = 6348 AND POSAmount <> 0
GROUP BY CashierNumber, MediaName
"""
try:
    print(pd.read_sql(q, conn))
except Exception as e:
    print("Error:", e)
