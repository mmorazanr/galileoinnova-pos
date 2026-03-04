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
CREATE TABLE IF NOT EXISTS restaurantes_mesero_media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurante VARCHAR(255),
    fecha DATE,
    mesero VARCHAR(255),
    media_name VARCHAR(255),
    amount DECIMAL(12,2),
    UNIQUE KEY(restaurante, fecha, mesero, media_name)
)
""")
conn.commit()
print('restaurantes_mesero_media table created.')
conn.close()
