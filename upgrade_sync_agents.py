import mysql.connector
import json
import os

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    cfg = load_config()
    conn = mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name'],
        use_pure=True
    )
    cursor = conn.cursor()

    # Añadir columnas si no existen
    alter_queries = [
        "ALTER TABLE sync_agents ADD COLUMN `last_command_args` TEXT DEFAULT NULL",
        "ALTER TABLE sync_agents ADD COLUMN `last_command_output` LONGTEXT DEFAULT NULL",
        "ALTER TABLE sync_agents ADD COLUMN `screenshot` LONGBLOB DEFAULT NULL",
        "ALTER TABLE sync_agents ADD COLUMN `screenshot_at` DATETIME DEFAULT NULL"
    ]

    for q in alter_queries:
        try:
            cursor.execute(q)
            conn.commit()
            print(f"Executed: {q}")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Column already exists
                print(f"Column already exists for query: {q}")
            else:
                print(f"Error executing {q}: {err}")

    cursor.close()
    conn.close()
    print("DB Upgrade Complete.")

if __name__ == "__main__":
    main()
