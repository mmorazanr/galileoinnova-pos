import pyodbc

db_file = r'C:\ICOM\Database\POS2100.mdb'
conn_str = rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};PWD=C0mtrex;'

try:
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute("""
    SELECT PunchID, ComtrexEmpID, ClockStatus, JobDescription, ActStartTime, ActStopTime 
    FROM ActivePunchInfo
    """)
    rows = cur.fetchall()
    print("Fetched successfully!")
    for r in rows:
        print(f"PunchID={r[0]}, EmpID={r[1]}, Status={r[2]}, Job={r[3]}, In={r[4]}, Out={r[5]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
