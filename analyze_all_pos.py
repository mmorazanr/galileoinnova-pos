import pyodbc
import glob
import os

db_files = glob.glob(r'C:\ICOM\Database\*.mdb')
db_files = [f for f in db_files if 'temp' not in f.lower() and 'backup' not in f.lower()]

for db_file in db_files:
    fname = os.path.basename(db_file)
    print(f"\n--- Checking {fname} ---")
    
    # Try both common passwords
    found = False
    for pwd in ['C0mtrex', '1324']:
        conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD={pwd};'
        try:
            conn = pyodbc.connect(conn_str)
            cur = conn.cursor()
            
            tables = []
            try:
                for row in cur.tables(tableType='TABLE'):
                    t_name = row.table_name.lower()
                    if 'daily' in t_name or 'dayly' in t_name or 'cashier' in t_name:
                        tables.append(row.table_name)
            except Exception as e:
                pass
                
            if tables:
                print(f"[{pwd}] Matches in {fname}:", tables)
            conn.close()
            break
        except Exception as e:
            pass
