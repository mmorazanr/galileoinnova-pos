import pyodbc
import os
import glob

bkp_dir = r"C:\ICOM\Database\Backup"
data_files = glob.glob(os.path.join(bkp_dir, "*.data.mdb")) + [os.path.join(bkp_dir, "CBODATA_SBKUP.mdb")]

for f in data_files:
    conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={f};PWD=C0mtrex;'
    try:
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        cur.execute("SELECT MIN(DateTimeStart), MAX(DateTimeStart) FROM TransactionHeader")
        min_date, max_date = cur.fetchone()
        print(f"{os.path.basename(f)}: {min_date} TO {max_date}")
        conn.close()
    except Exception as e:
        print(f"Error reading {os.path.basename(f)}: {e}")
