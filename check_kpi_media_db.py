import mysql.connector
import json

with open('config.json', 'r') as f:
    cfg = json.load(f)

conn = mysql.connector.connect(
    host=cfg['remote_db_host'],
    user=cfg['remote_db_user'],
    password=cfg['remote_db_pass'],
    database=cfg['remote_db_name']
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM restaurantes_mesero_media WHERE fecha = '2026-02-23' LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    print(r)
conn.close()
