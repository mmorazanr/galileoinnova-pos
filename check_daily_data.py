import mysql.connector
import json

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    cfg = load_config()
    conn = mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name']
    )
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, restaurante, cash FROM restaurantes_diario_media ORDER BY fecha ASC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == '__main__':
    main()
