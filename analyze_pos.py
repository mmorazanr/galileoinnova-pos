import pyodbc

for db_file, pwd in [('CBODaily_temp.mdb', 'C0mtrex'), ('POS2100_temp.mdb', '1324'), ('POS2100_temp.mdb', 'C0mtrex')]:
    print(f"\n--- Checking {db_file} ---")
    conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ=C:\ICOM\Database\{db_file};PWD={pwd};'
    try:
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        
        tables = []
        try:
            for row in cur.tables(tableType='TABLE'):
                t_name = row.table_name
                if 'cashier' in t_name.lower():
                    tables.append(t_name)
        except Exception as e:
            print(f"Error reading tables: {e}")
            
        print("Tables containing 'cashier':", tables)
        
        for t in tables:
            print(f"\n[{t}]")
            cols = []
            try:
                for col in cur.columns(table=t):
                    cols.append(col.column_name)
                print(f"Schema columns: {cols}")
            except Exception as e:
                print(f"Error reading schema cols: {e}")
                
            try:
                cur.execute(f"SELECT TOP 3 * FROM [{t}]")
                rows = cur.fetchall()
                if hasattr(cur, 'description'):
                    desc_cols = [d[0] for d in cur.description]
                    for r in rows:
                        print(dict(zip(desc_cols, r)))
                else:
                    for r in rows:
                        print(r)
            except Exception as e:
                print(f"Error reading data: {e}")
                
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")
