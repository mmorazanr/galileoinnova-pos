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
cursor.execute("DELETE FROM restaurantes_ventas WHERE restaurante=%s", (cfg['restaurant_name'],))
conn.commit()
print('Cleared MariaDB for precise syncing.')
