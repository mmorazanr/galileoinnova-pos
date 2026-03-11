import pyodbc
import glob
import os

db_files = [
    (r'C:\ICOM\Database\CBODaily.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\CBOData_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\CBODef_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\POS2100.mdb', '1324'),
    (r'C:\ICOM\Database\POS2100.mdb', 'C0mtrex')
]

keywords = ['time', 'clock', 'punch', 'shift', 'labor', 'payroll', 'menu', 'product', 'item', 'category']

for db_file, pwd in db_files:
    if not os.path.exists(db_file): continue
    
    fname = os.path.basename(db_file)
    print(f"\n======================================")
    print(f"--- Checking {fname} with pwd {pwd} ---")
    
    conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD={pwd};'
    try:
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        
        tables = []
        try:
            for row in cur.tables(tableType='TABLE'):
                t_name = row.table_name.lower()
                if any(k in t_name for k in keywords):
                    tables.append(row.table_name)
        except Exception as e:
            print(f"Error reading tables: {e}")
            continue
            
        if tables:
            print("Found interesting tables:", tables)
            for t in tables[:15]: # Limiting to avoid massive output
                print(f"\n[{t}]")
                try:
                    cols = [col.column_name for col in cur.columns(table=t)]
                    print(f"Columns: {cols}")
                    
                    cur.execute(f"SELECT TOP 1 * FROM [{t}]")
                    rows = cur.fetchall()
                    if rows and hasattr(cur, 'description'):
                        desc_cols = [d[0] for d in cur.description]
                        for r in rows:
                            print("Sample:", dict(zip(desc_cols, r)))
                except Exception as e:
                    print(f"Error reading {t}: {e}")
                    
        conn.close()
    except Exception as e:
        print(f"Connection failed / bad pwd: {e}")
