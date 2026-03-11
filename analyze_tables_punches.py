import win32com.client
import os

files = [
    r"C:\ICOM\Database\POS2100.mdb",
    r"C:\ICOM\Database\CBOData_s.mdb",
    r"C:\ICOM\Database\CBOHist_s.mdb"
]

for db in files:
    if not os.path.exists(db):
        print(f"NOT FOUND: {db}")
        continue
    
    print(f"\n--- Checking {os.path.basename(db)} ---")
    try:
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open(f"Provider=Microsoft.Jet.OLEDB.4.0;Data Source={db};Jet OLEDB:Database Password=C0mtrex;")
        
        # 20 = adSchemaTables
        rs = conn.OpenSchema(20)
        found = False
        while not rs.EOF:
            t = rs.Fields('TABLE_NAME').Value
            # Only user tables (not system)
            t_type = rs.Fields('TABLE_TYPE').Value
            if t_type == "TABLE" or t_type == "VIEW":
                if any(x in t.lower() for x in ['punch', 'shift', 'labor', 'time', 'emp', 'clock', 'att']):
                    print(f"  Found table: {t}")
                    found = True
            rs.MoveNext()
            
        if not found:
            print("  No relevant tables found.")
            
        conn.Close()
    except Exception as e:
        print(f"  Error reading {db}: {e}")
