import pyodbc

db_file = r'C:\ICOM\Database\CBOData_s.mdb'
tables = ['DailyCashierMedia', 'DailyCashierMisc', 'DailyCashierSales']

conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD=C0mtrex;'
conn = pyodbc.connect(conn_str)
cur = conn.cursor()

for t in tables:
    print(f"\n--- {t} ---")
    try:
        cur.execute(f"SELECT TOP 3 * FROM [{t}]")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print(f"Columns: {cols}")
        for r in rows:
            print(dict(zip(cols, r)))
    except Exception as e:
        print(f"Error querying {t}:", e)

conn.close()
