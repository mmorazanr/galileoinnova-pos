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

# Contar antes
cur.execute("SELECT COUNT(*) FROM restaurantes_ventas WHERE fecha = '2026-02-28'")
count = cur.fetchone()[0]
print(f'Registros a eliminar con fecha 2026-02-28: {count}')

# Eliminar los registros falsos del 28 de febrero
cur.execute("DELETE FROM restaurantes_ventas WHERE fecha = '2026-02-28'")
conn.commit()
print(f'Eliminados: {cur.rowcount} registros')

# Verificar total restante y fecha maxima
cur.execute("SELECT COUNT(*), MAX(fecha) FROM restaurantes_ventas")
row = cur.fetchone()
print(f'Total restante: {row[0]} registros, fecha maxima: {row[1]}')

# Verificar tambien restaurantes_kpi por si acaso
cur.execute("SELECT COUNT(*) FROM restaurantes_kpi WHERE fecha = '2026-02-28'")
kpi_count = cur.fetchone()[0]
print(f'Registros en restaurantes_kpi con fecha 2026-02-28: {kpi_count}')

if kpi_count > 0:
    cur.execute("DELETE FROM restaurantes_kpi WHERE fecha = '2026-02-28'")
    conn.commit()
    print(f'Eliminados {cur.rowcount} registros falsos de restaurantes_kpi')

# Verificar restaurantes_kpi_mesero
cur.execute("SELECT COUNT(*) FROM restaurantes_kpi_mesero WHERE fecha = '2026-02-28'")
km_count = cur.fetchone()[0]
print(f'Registros en restaurantes_kpi_mesero con fecha 2026-02-28: {km_count}')

if km_count > 0:
    cur.execute("DELETE FROM restaurantes_kpi_mesero WHERE fecha = '2026-02-28'")
    conn.commit()
    print(f'Eliminados {cur.rowcount} registros falsos de restaurantes_kpi_mesero')

conn.close()
print('Listo.')
