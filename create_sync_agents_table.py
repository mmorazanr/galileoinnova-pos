"""
create_sync_agents_table.py
One-time migration: creates the sync_agents table in MariaDB.
Run this once from any machine that has access to the cloud DB.
"""
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

    create_sql = """
    CREATE TABLE IF NOT EXISTS sync_agents (
        id_sync         VARCHAR(64)   NOT NULL,
        restaurante     VARCHAR(128)  NOT NULL,
        ip_lan          VARCHAR(45)   DEFAULT NULL,
        db_path         VARCHAR(512)  DEFAULT NULL,
        status          VARCHAR(32)   DEFAULT 'stopped',
        last_heartbeat  DATETIME      DEFAULT NULL,
        version         VARCHAR(16)   DEFAULT '1.0',
        pending_command VARCHAR(32)   DEFAULT NULL,
        PRIMARY KEY (id_sync)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    cursor.execute(create_sql)
    conn.commit()
    print("OK: Table 'sync_agents' created (or already exists).")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
