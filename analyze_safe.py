import pyodbc

db_files = [
    (r'C:\ICOM\Database\CBODef_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\POS2100.mdb', 'C0mtrex')
]

# Configure pyodbc to ignore decoding errors for legacy Jet databases
pyodbc.setSQLCHAR(pyodbc.SQL_CHAR, encoding='latin1', errors='replace')
pyodbc.setSQLWCHAR(pyodbc.SQL_WCHAR, encoding='latin1', errors='replace')

tables_to_query = {
    'TimeClock': ['TimeClock', 'TimePunch', 'ActivePunch'],
    'Menu': ['ProductDefinitions', 'CategoryDefinitions', 'CategoryPOSItemProfiles', 'SubMenus', 'POSItemDefinitions', 'SizedProductDefinitions']
}

for db_file, pwd in db_files:
    print(f"\n======================================")
    print(f"--- Checking {db_file} ---")
    
    conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD={pwd};'
    try:
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        
        tables = []
        for row in cur.tables(tableType='TABLE'):
            t_name = row.table_name
            # Check if any keyword matches
            if any(tg.lower() in t_name.lower() for cat in tables_to_query.values() for tg in cat):
                tables.append(t_name)
        
        if tables:
            print("Found interesting tables:", tables)
            for t in tables:
                print(f"\n[{t}]")
                try:
                    cols = [col.column_name for col in cur.columns(table=t)]
                    print(f"Columns: {cols}")
                    
                    cur.execute(f"SELECT TOP 1 * FROM [{t}]")
                    rows = cur.fetchall()
                    if rows and hasattr(cur, 'description'):
                        desc_cols = [d[0] for d in cur.description]
                        for r in rows:
                            # Safely print each row
                            print("Sample:", dict(zip(desc_cols, r)))
                except Exception as e:
                    print(f"Error reading {t}: {e}")
                    
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")
