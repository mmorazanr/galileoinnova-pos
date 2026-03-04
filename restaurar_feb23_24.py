"""
Restaura los datos correctos del 23/02/2026 y 24/02/2026
desde CBOData_s.mdb local (la fuente correcta).
"""
import json
import pyodbc
import mysql.connector
from hashlib import md5
import datetime

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

remote_conn = mysql.connector.connect(
    host=cfg['remote_db_host'],
    user=cfg['remote_db_user'],
    password=cfg['remote_db_pass'],
    database=cfg['remote_db_name'],
    use_pure=True
)

local_conn = pyodbc.connect(
    f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;"
)

cur_local = local_conn.cursor()
push = remote_conn.cursor()

# Mapas
cashier_map = {}
cur_local.execute("SELECT DISTINCT CashierNumber, CashierName FROM DailyCashierSales")
for row in cur_local.fetchall():
    cashier_map[str(row[0])] = row[1]

category_map = {}
try:
    cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions")
    for row in cur_local.fetchall():
        category_map[str(row[0])] = row[1]
except Exception:
    try:
        cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM DailyCashierSales")
        for row in cur_local.fetchall():
            if row[1]: category_map[str(row[0])] = row[1]
    except Exception:
        pass

# Obtener todos los SalesDayNumbers y sus fechas del CBOData_s.mdb local
cur_local.execute("SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader GROUP BY SalesDayNumber")
day_to_date = {}
for row in cur_local.fetchall():
    if row[1]:
        day_to_date[row[0]] = row[1].strftime('%Y-%m-%d')

print("Fechas disponibles en CBOData_s.mdb local:")
for d, f in sorted(day_to_date.items(), key=lambda x: x[1])[-10:]:
    print(f"  SalesDayNumber={d} -> {f}")

# Fechas a restaurar
target_dates = {'2026-02-23', '2026-02-24'}
days_to_restore = [(d, f) for d, f in day_to_date.items() if f in target_dates]
print(f"\nDias a restaurar: {days_to_restore}")

if not days_to_restore:
    print("ADVERTENCIA: No se encontraron esos dias en CBOData_s.mdb local.")
    print("El CBOData_s.mdb local no tiene datos para 23 y 24 de febrero.")
    local_conn.close()
    remote_conn.close()
    exit()

for s_day, fecha_str in days_to_restore:
    print(f"\nRestaurando {fecha_str} (SalesDayNumber={s_day})...")

    # --- restaurantes_ventas ---
    cur_local.execute(f"""
        SELECT SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName,
               SUM(MenuItemQuantity) as Qty, SUM(MenuItemAmount - MenuItemDiscAmount) as Net
        FROM DailyCashierSales WHERE SalesDayNumber = {s_day}
        GROUP BY SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName
        HAVING SUM(MenuItemAmount - MenuItemDiscAmount) <> 0 OR SUM(MenuItemQuantity) > 0
    """)
    rows = cur_local.fetchall()
    push.execute("DELETE FROM restaurantes_ventas WHERE restaurante=%s AND fecha=%s",
                 (cfg['restaurant_name'], fecha_str))
    batch = []
    for row in rows:
        cashier_id = str(row[1] or 0)
        cat_id = str(row[2] or 0)
        prod_id = str(row[3] or 0)
        uid = f"{s_day}_{cashier_id}_{cat_id}_{prod_id}"
        trans_id = int(md5(uid.encode()).hexdigest()[:8], 16)
        batch.append((
            cfg['restaurant_name'], trans_id, fecha_str, '12:00:00',
            cashier_map.get(cashier_id, f'Cajero {cashier_id}'),
            category_map.get(cat_id, f'Cat {cat_id}'),
            row[4], float(row[5] or 0), float(row[6] or 0)
        ))
    if batch:
        push.executemany("""
            INSERT INTO restaurantes_ventas
            (restaurante, transaccion_id, fecha, hora, mesero, categoria, platillo, cantidad, monto_venta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
    print(f"  restaurantes_ventas: {len(batch)} filas")

    # --- restaurantes_kpi ---
    cur_local.execute(f"SELECT SUM(NetSalesin15Min), SUM(TranCountin15Min) FROM HourlySalesNew WHERE SalesDayNumber = {s_day}")
    res = cur_local.fetchone()
    if res and res[0]:
        push.execute("DELETE FROM restaurantes_kpi WHERE restaurante=%s AND fecha=%s",
                     (cfg['restaurant_name'], fecha_str))
        push.execute("INSERT INTO restaurantes_kpi (restaurante, fecha, ventas_netas, total_tickets) VALUES (%s,%s,%s,%s)",
                     (cfg['restaurant_name'], fecha_str, float(res[0]), int(res[1] or 0)))
        print(f"  restaurantes_kpi: net_sales={res[0]}, tickets={res[1]}")

    # --- restaurantes_diario_media ---
    metrics = {k: 0.0 for k in ['cash','employee_disc','error_corrects','gratuity','mgr_disc',
                                  'mgr_void','sales_transfer_in','sales_transfer_out',
                                  'service_balance','tax_1','tips_paid','net_sales','change_in_gc_total']}
    mapping = {'Cash':'cash','Employee Disc':'employee_disc','Error Corrects':'error_corrects',
               'Gratuity':'gratuity','MGR Disc':'mgr_disc','MGR Void':'mgr_void',
               'Sales Transfer In':'sales_transfer_in','Sales Transfer Out':'sales_transfer_out',
               'Service Balance':'service_balance','Tax 1':'tax_1','Tips Paid':'tips_paid'}
    cur_local.execute(f"SELECT MediaName, SUM(POSAmount) FROM DailyCashierMedia WHERE SalesDayNumber={s_day} GROUP BY MediaName")
    for r in cur_local.fetchall():
        m = (r[0] or '').strip()
        if m in mapping: metrics[mapping[m]] = float(r[1] or 0)
    cur_local.execute(f"SELECT MiscDescription, SUM(MiscAmount) FROM DailyCashierMisc WHERE SalesDayNumber={s_day} GROUP BY MiscDescription")
    for r in cur_local.fetchall():
        d = (r[0] or '').strip()
        if d == 'Net Sales': metrics['net_sales'] = float(r[1] or 0)
        elif d == 'Grand Control Total': metrics['change_in_gc_total'] = float(r[1] or 0)
    push.execute("DELETE FROM restaurantes_diario_media WHERE restaurante=%s AND fecha=%s",
                 (cfg['restaurant_name'], fecha_str))
    push.execute("""INSERT INTO restaurantes_diario_media
        (restaurante, fecha, cash, employee_disc, error_corrects, gratuity, mgr_disc, mgr_void,
         sales_transfer_in, sales_transfer_out, service_balance, tax_1, tips_paid, net_sales, change_in_gc_total)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (cfg['restaurant_name'], fecha_str, metrics['cash'], metrics['employee_disc'],
         metrics['error_corrects'], metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'],
         metrics['sales_transfer_in'], metrics['sales_transfer_out'], metrics['service_balance'],
         metrics['tax_1'], metrics['tips_paid'], metrics['net_sales'], metrics['change_in_gc_total']))
    print(f"  restaurantes_diario_media: net_sales={metrics['net_sales']}")

remote_conn.commit()
local_conn.close()
remote_conn.close()
print("\nRestauración completa.")
