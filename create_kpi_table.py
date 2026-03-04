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

cursor.execute("""
CREATE TABLE IF NOT EXISTS restaurantes_kpi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurante VARCHAR(255),
    fecha DATE,
    ventas_netas DECIMAL(12,2),
    total_tickets INT,
    UNIQUE KEY(restaurante, fecha)
)
""")
conn.commit()
print('restaurantes_kpi table created or already exists.')
conn.close()
