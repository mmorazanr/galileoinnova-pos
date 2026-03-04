import pyodbc

cbodata = r"C:\ICOM\Database\Marzo6026\CBOData_s.mdb"
conn = pyodbc.connect(
    f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cbodata};PWD=C0mtrex;"
)
cur = conn.cursor()

for s_day in [6348, 6349]:
    print(f"\n=== SalesDayNumber={s_day} ===")
    cur.execute(f"SELECT MIN(DateTimeStart), MAX(DateTimeStart) FROM TransactionHeader WHERE SalesDayNumber={s_day}")
    r = cur.fetchone()
    print(f"  Rango horario: {r[0]} - {r[1]}")

    cur.execute(f"SELECT SUM(NetSalesin15Min), SUM(TranCountin15Min) FROM HourlySalesNew WHERE SalesDayNumber={s_day}")
    r2 = cur.fetchone()
    print(f"  HourlySalesNew: net_sales={r2[0]}, tickets={r2[1]}")

    cur.execute(f"SELECT MiscDescription, SUM(MiscAmount) FROM DailyCashierMisc WHERE SalesDayNumber={s_day} AND MiscDescription IN ('Net Sales','Grand Control Total') GROUP BY MiscDescription")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

conn.close()
