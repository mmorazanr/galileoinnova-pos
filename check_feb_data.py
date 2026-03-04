import mysql.connector, json

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

conn = mysql.connector.connect(
    host=cfg['remote_db_host'],
    user=cfg['remote_db_user'],
    password=cfg['remote_db_pass'],
    database=cfg['remote_db_name']
)
cur = conn.cursor()

print('=== restaurantes_kpi (Feb 20-28) ===')
cur.execute("""
    SELECT fecha, restaurante, ventas_netas, total_tickets
    FROM restaurantes_kpi
    WHERE fecha >= '2026-02-20'
    ORDER BY fecha ASC
""")
for row in cur.fetchall():
    print(row)

print()
print('=== restaurantes_ventas por fecha (Feb 20-28) ===')
cur.execute("""
    SELECT fecha, COUNT(*) as registros, SUM(monto_venta) as total
    FROM restaurantes_ventas
    WHERE fecha >= '2026-02-20'
    GROUP BY fecha
    ORDER BY fecha ASC
""")
for row in cur.fetchall():
    print(row)

print()
print('=== restaurantes_diario_media (Feb 20-28) ===')
cur.execute("""
    SELECT fecha, net_sales, cash, change_in_gc_total
    FROM restaurantes_diario_media
    WHERE fecha >= '2026-02-20'
    ORDER BY fecha ASC
""")
for row in cur.fetchall():
    print(row)

conn.close()
