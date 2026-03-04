import pyodbc
db_path = r'C:\ICOM\Database\Backup\CBODATA_SBKUP.mdb'
conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=C0mtrex;'
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    for t in ['DailyCashierMisc', 'DailyCashierMedia']:
        try:
            print(f"\n{t}:")
            cursor.execute(f"SELECT TOP 1 * FROM {t}")
            print([d[0] for d in cursor.description])
        except:
            print(f"{t} not found")
    
except Exception as e:
    print("Error:", e)
