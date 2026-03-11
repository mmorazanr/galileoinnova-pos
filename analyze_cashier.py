import pyodbc

conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\ICOM\Database\CBODaily_temp.mdb;PWD=C0mtrex;'
try:
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    tables = [row.table_name for row in cur.tables(tableType='TABLE') if 'cashier' in row.table_name.lower()]
    print("Tables in CBODaily_temp.mdb:", tables)
    
    for t in tables:
        print(f"\nSchema for {t}:")
        for col in cur.columns(table=t):
            print(f"  - {col.column_name} ({col.type_name})")
            
        print(f"\nFirst 5 rows for {t}:")
        cur.execute(f"SELECT TOP 5 * FROM [{t}]")
        rows = cur.fetchall()
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {row}")
            if hasattr(cur, 'description'):
                cols = [d[0] for d in cur.description]
                row_dict = dict(zip(cols, row))
                print(f"   dict: {row_dict}")

    conn.close()
except Exception as e:
    print("Error with CBODaily_temp:", e)

# Also try POS2100 ?
# usually live data is in DB2000.mdb or POS2100.mdb or CBODaily.mdb
