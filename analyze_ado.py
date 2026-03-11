import win32com.client
import os

db_files = [
    (r'C:\ICOM\Database\CBODef_s.mdb', 'C0mtrex'),
    (r'C:\ICOM\Database\POS2100.mdb', 'C0mtrex')
]

# Interesting keywords for this search
tables_to_query = {
    'TimeClock': ['ActivePunchInfo', 'TimeClock', 'TimePunch'],
    'Menu': ['ProductDefinitions', 'CategoryDefinitions', 'CategoryPOSItemProfiles', 'SubMenus', 'POSItemDefinitions', 'SizedProductDefinitions']
}

for db_file, pwd in db_files:
    if not os.path.exists(db_file): continue
    print(f"\n======================================")
    print(f"--- Checking {os.path.basename(db_file)} ---")
    
    conn = win32com.client.Dispatch("ADODB.Connection")
    conn_str = f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={db_file};Jet OLEDB:Database Password={pwd};"
    try:
        conn.Open(conn_str)
        # Get table list
        schema = conn.OpenSchema(20) # adSchemaTables
        actual_tables = []
        while not schema.EOF:
            t_name = schema.Fields("TABLE_NAME").Value
            if schema.Fields("TABLE_TYPE").Value == "TABLE":
                actual_tables.append(t_name)
            schema.MoveNext()
        
        # Look for target tables
        for category, targets in tables_to_query.items():
            print(f"\n--- Category: {category} ---")
            found = [t for t in actual_tables if any(tg.lower() in t.lower() for tg in targets)]
            for t in found:
                print(f"[{t}]")
                rs = win32com.client.Dispatch("ADODB.Recordset")
                try:
                    rs.Open(f"SELECT TOP 1 * FROM [{t}]", conn, 1, 1) # adOpenKeyset, adLockReadOnly
                    cols = [f.Name for f in rs.Fields]
                    print(f"Columns: {cols}")
                    
                    if not rs.EOF:
                        vals = []
                        for f in rs.Fields:
                            val = f.Value
                            # Handle COM types
                            vals.append(str(val))
                        print(f"Sample: {dict(zip(cols, vals))}")
                    else:
                        print("Sample: (Empty Table)")
                    rs.Close()
                except Exception as e:
                    print(f"Error querying {t}: {e}")
                    
        conn.Close()
    except Exception as e:
        print(f"Connection failed: {e}")
