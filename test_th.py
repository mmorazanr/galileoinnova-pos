import pyodbc 
import pandas as pd
conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBOData_s.mdb;PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
q3 = """
SELECT COUNT(TransactionHeaderID) as GlobalTC
FROM (
    SELECT DISTINCT TransactionHeaderID 
    FROM TransactionHeader
    WHERE SalesDayNumber = 6348 AND TransactionTypeID <> 4
)
"""
print("Global tickets in TH:", pd.read_sql(q3, conn).iloc[0,0])

q4 = """
SELECT COUNT(TransactionHeaderID) as CleanGlobalTC
FROM (
    SELECT DISTINCT TransactionHeaderID 
    FROM TransactionHeader
    WHERE SalesDayNumber = 6348 AND TransactionTypeID = 3
)
"""
print("Global TYPE 3 tickets in TH:", pd.read_sql(q4, conn).iloc[0,0])
