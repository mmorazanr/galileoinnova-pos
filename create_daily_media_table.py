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
    
    # Create the table
    sql = """
    CREATE TABLE IF NOT EXISTS restaurantes_diario_media (
        id INT AUTO_INCREMENT PRIMARY KEY,
        restaurante VARCHAR(100),
        fecha DATE,
        cash DECIMAL(12,2) DEFAULT 0,
        employee_disc DECIMAL(12,2) DEFAULT 0,
        error_corrects DECIMAL(12,2) DEFAULT 0,
        gratuity DECIMAL(12,2) DEFAULT 0,
        mgr_disc DECIMAL(12,2) DEFAULT 0,
        mgr_void DECIMAL(12,2) DEFAULT 0,
        sales_transfer_in DECIMAL(12,2) DEFAULT 0,
        sales_transfer_out DECIMAL(12,2) DEFAULT 0,
        service_balance DECIMAL(12,2) DEFAULT 0,
        tax_1 DECIMAL(12,2) DEFAULT 0,
        tips_paid DECIMAL(12,2) DEFAULT 0,
        net_sales DECIMAL(12,2) DEFAULT 0,
        change_in_gc_total DECIMAL(12,2) DEFAULT 0,
        UNIQUE KEY idx_res_fecha (restaurante, fecha)
    ) ENGINE=InnoDB;
    """
    cursor.execute(sql)
    conn.commit()
    print("Table restaurantes_diario_media created successfully.")
    conn.close()

if __name__ == '__main__':
    main()
