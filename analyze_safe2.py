import pyodbc

db_files = [
    (r'C:\ICOM\Database\CBODaily.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\CBOData_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\CBODef_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\POS2100.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\POS2100.mdb', '1324')
]

if hasattr(pyodbc, 'setdecoding'):
    pyodbc.setdecoding(pyodbc.SQL_CHAR, encoding='latin1', errors='replace')
    pyodbc.setdecoding(pyodbc.SQL_WCHAR, encoding='latin1', errors='replace')
    pyodbc.setencoding(encoding='latin1')

tables_to_query = {
    'TimeClock': ['activepunch', 'timeclock', 'timepunch'],
    'Menu': ['productdefinitions', 'categorydefinitions', 'categorypositemprofiles', 'submenus', 'positemdefinitions', 'sizedproductdefinitions']
}

for db_file, pwd in db_files:
    print(f"\n======================================")
    print(f"--- Checking {db_file} ---")
    
    conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD={pwd};'
    try:
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        
        tables = []
        try:
            for row in cur.tables(tableType='TABLE'):
                t_name = row.table_name
                # Check if any keyword matches
                if any(tg in t_name.lower() for cat in tables_to_query.values() for tg in cat):
                    tables.append(t_name)
        except:
            pass
            
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
                            row_dict = {}
                            for i, c in enumerate(desc_cols):
                                try:
                                    row_dict[c] = str(r[i])
                                except Exception as e:
                                    row_dict[c] = "<error>"
                            print("Sample:", row_dict)
                except Exception as e:
                    print(f"Error reading {t}: {e}")
                    
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")
