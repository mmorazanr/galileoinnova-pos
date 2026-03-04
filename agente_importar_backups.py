import json
import pyodbc 
import mysql.connector
import datetime
import os
from hashlib import md5

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_remote_connection(cfg):
    return mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name']
    )

def main():
    cfg = load_config()
    remote_conn = get_remote_connection(cfg)
    push_cursor = remote_conn.cursor()
    
    # Categories from main DB
    main_conn = pyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;")
    cur_main = main_conn.cursor()
    category_map = {}
    cur_main.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions")
    for row in cur_main.fetchall():
        category_map[str(row[0])] = row[1]
    main_conn.close()

    # List of backups to process
    import glob
    bkp_dir = r"C:\\ICOM\\Database\\Backup"
    # We only process the latest data.mdb file to avoid duplicate dates, plus the 2013 one
    # E.g., 20250614.data.mdb covers May 9 to June 14, which covers almost all of what the others cover.
    # Actually, we can just process all of them, but we will "DELETE" and "INSERT" for each date.
    files_to_process = glob.glob(os.path.join(bkp_dir, "*.data.mdb")) + [os.path.join(bkp_dir, "CBODATA_SBKUP.mdb")]
    
    for db_path in files_to_process:
        print(f"\\nProcesando Respaldo: {os.path.basename(db_path)}")
        conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};PWD=C0mtrex;"
        try:
            local_conn = pyodbc.connect(conn_str)
            cur_local = local_conn.cursor()
            
            cashier_map = {}
            cur_local.execute("SELECT DISTINCT CashierNumber, CashierName FROM DailyCashierSales")
            for row in cur_local.fetchall():
                cashier_map[str(row[0])] = row[1]
                
            # Get all SalesDayNumbers and dates
            day_to_date = {}
            cur_local.execute("SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader GROUP BY SalesDayNumber")
            for row in cur_local.fetchall():
                if row[1]:
                    dt = row[1]
                    # Si el dia abre de noche (>= 17:00), el dia de negocio real es el siguiente
                    if dt.hour >= 17:
                        dt = dt + datetime.timedelta(days=1)
                    day_to_date[row[0]] = dt.strftime('%Y-%m-%d')
            
            fechas_list = list(set([d for d in day_to_date.values()]))
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            # Excluir la fecha de hoy — el dia no esta cerrado y podria importar datos parciales
            fechas_list = [f for f in fechas_list if f != today_str]
            day_nums = [d for d in day_to_date.keys() if day_to_date[d] != today_str]

            filtered_count = len(list(day_to_date.keys())) - len(day_nums)
            if filtered_count > 0:
                print(f"  (Excluido {filtered_count} dia(s) con fecha de hoy: {today_str})")

            if not day_nums:
                print("No hay fechas procesables en este archivo.")
                local_conn.close()
                continue
                
            print(f"Encontrados {len(fechas_list)} dias de operacion.")

            
            insert_sql = """
                INSERT INTO restaurantes_ventas 
                (restaurante, transaccion_id, fecha, hora, mesero, categoria, platillo, cantidad, monto_venta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            batch_data = []
            now_time = "12:00:00"

            for s_day in day_nums:
                print(f"Extrayendo d\u00eda {s_day}...")
                fecha_str = day_to_date.get(s_day)
                if not fecha_str: continue
                push_cursor.execute("DELETE FROM restaurantes_ventas WHERE restaurante = %s AND fecha = %s", (cfg['restaurant_name'], fecha_str))
                sql_extract = f"""
                    SELECT 
                        SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName,
                        SUM(MenuItemQuantity) as Qty, SUM(MenuItemAmount - MenuItemDiscAmount) as NetAmount
                    FROM DailyCashierSales
                    WHERE SalesDayNumber = {s_day}
                    GROUP BY SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName
                    HAVING SUM(MenuItemAmount - MenuItemDiscAmount) <> 0 OR SUM(MenuItemQuantity) > 0
                """
                cur_local.execute(sql_extract)
                rows_to_push = cur_local.fetchall()
                
                for row in rows_to_push:
                    cashier_id = str(row[1]) if row[1] else '0'
                    category_id = str(row[2]) if row[2] else '0'
                    prod_id = str(row[3]) if row[3] else '0'
                    prod_name = row[4]
                    qty = float(row[5] or 0)
                    amount = float(row[6] or 0)
                    
                    mesero_str = cashier_map.get(cashier_id, f"Mesero {cashier_id}")
                    cat_str = category_map.get(category_id, f"Categoria {category_id}")
                    fecha_str = day_to_date.get(s_day)
                    if not fecha_str: continue
                    
                    uid_str = f"{s_day}_{cashier_id}_{category_id}_{prod_id}"
                    trans_id = int(md5(uid_str.encode()).hexdigest()[:8], 16)

                    batch_data.append((
                        cfg['restaurant_name'], trans_id, fecha_str, now_time,
                        mesero_str, cat_str, prod_name, qty, amount
                    ))
            
            if batch_data:
                push_cursor.executemany(insert_sql, batch_data)
                
            # Process KPIs per day
            for s_day in day_nums:
                fecha_str = day_to_date.get(s_day)
                if not fecha_str: continue
                
                # 1. Global KPIs
                cols = [d[0] for d in cur_local.execute("SELECT TOP 1 * FROM HourlySalesNew").description]
                sales_col = "NetSalesin15Min" if "NetSalesin15Min" in cols else "Salesin15Min"
                
                q_fin = f"SELECT SUM({sales_col}), SUM(TranCountin15Min) FROM HourlySalesNew WHERE SalesDayNumber = {s_day}"
                cur_local.execute(q_fin)
                res_fin = cur_local.fetchone()
                if res_fin and res_fin[0] is not None:
                    push_cursor.execute("DELETE FROM restaurantes_kpi WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                    push_cursor.execute("INSERT INTO restaurantes_kpi (restaurante, fecha, ventas_netas, total_tickets) VALUES (%s, %s, %s, %s)", 
                        (cfg['restaurant_name'], fecha_str, float(res_fin[0]), int(res_fin[1])))
                
                # 2. Tickets por mesero
                q_mesero = f"SELECT CashierNumber, SUM(MiscQuantity) FROM DailyCashierMisc WHERE SalesDayNumber = {s_day} AND MiscDescription = 'Transaction Count' GROUP BY CashierNumber"
                cur_local.execute(q_mesero)
                res_mesero = cur_local.fetchall()
                if res_mesero:
                    push_cursor.execute("DELETE FROM restaurantes_kpi_mesero WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                    for row_m in res_mesero:
                        c_id = str(row_m[0])
                        tcks = int(row_m[1] or 0)
                        push_cursor.execute("INSERT INTO restaurantes_kpi_mesero (restaurante, fecha, mesero, total_tickets) VALUES (%s, %s, %s, %s)", 
                            (cfg['restaurant_name'], fecha_str, cashier_map.get(c_id, c_id), tcks))

                # 3. Media por mesero
                q_media_m = f"SELECT CashierNumber, MediaName, SUM(POSAmount) FROM DailyCashierMedia WHERE SalesDayNumber = {s_day} AND POSAmount <> 0 GROUP BY CashierNumber, MediaName"
                cur_local.execute(q_media_m)
                res_media_m = cur_local.fetchall()
                if res_media_m:
                    push_cursor.execute("DELETE FROM restaurantes_mesero_media WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                    for row_mm in res_media_m:
                        c_id = str(row_mm[0])
                        push_cursor.execute("INSERT INTO restaurantes_mesero_media (restaurante, fecha, mesero, media_name, amount) VALUES (%s, %s, %s, %s, %s)", 
                            (cfg['restaurant_name'], fecha_str, cashier_map.get(c_id, c_id), row_mm[1], float(row_mm[2] or 0)))

                # 4. Cuadre Diario Consolidado
                q_diario = f"SELECT MediaName, SUM(POSAmount) FROM DailyCashierMedia WHERE SalesDayNumber = {s_day} GROUP BY MediaName"
                cur_local.execute(q_diario)
                res_diario = cur_local.fetchall()
                if res_diario:
                    metrics = {
                        'cash': 0.0, 'employee_disc': 0.0, 'error_corrects': 0.0, 
                        'gratuity': 0.0, 'mgr_disc': 0.0, 'mgr_void': 0.0,
                        'sales_transfer_in': 0.0, 'sales_transfer_out': 0.0, 
                        'service_balance': 0.0, 'tax_1': 0.0, 'tips_paid': 0.0,
                        'net_sales': 0.0, 'change_in_gc_total': 0.0
                    }
                    mapping = {
                        'Cash': 'cash', 'Employee Disc': 'employee_disc', 'Error Corrects': 'error_corrects',
                        'Gratuity': 'gratuity', 'MGR Disc': 'mgr_disc', 'MGR Void': 'mgr_void',
                        'Sales Transfer In': 'sales_transfer_in', 'Sales Transfer Out': 'sales_transfer_out',
                        'Service Balance': 'service_balance', 'Tax 1': 'tax_1', 'Tips Paid': 'tips_paid'
                    }
                    for r_d in res_diario:
                        m_name = r_d[0].strip() if r_d[0] else ""
                        if m_name in mapping:
                            metrics[mapping[m_name]] = float(r_d[1] or 0)
                    
                    # Query DailyCashierMisc for Net Sales and Grand Control Total
                    q_misc = f"SELECT MiscDescription, SUM(MiscAmount) FROM DailyCashierMisc WHERE SalesDayNumber = {s_day} GROUP BY MiscDescription"
                    cur_local.execute(q_misc)
                    for r_m in cur_local.fetchall():
                        desc = r_m[0].strip() if r_m[0] else ""
                        val = float(r_m[1] or 0)
                        if desc == 'Net Sales':
                            metrics['net_sales'] = val
                        elif desc == 'Grand Control Total':
                            metrics['change_in_gc_total'] = val

                    push_cursor.execute("DELETE FROM restaurantes_diario_media WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                    push_cursor.execute("""
                        INSERT INTO restaurantes_diario_media 
                        (restaurante, fecha, cash, employee_disc, error_corrects, gratuity, mgr_disc, mgr_void, 
                         sales_transfer_in, sales_transfer_out, service_balance, tax_1, tips_paid,
                         net_sales, change_in_gc_total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (cfg['restaurant_name'], fecha_str, metrics['cash'], metrics['employee_disc'], metrics['error_corrects'],
                          metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'], metrics['sales_transfer_in'], 
                          metrics['sales_transfer_out'], metrics['service_balance'], metrics['tax_1'], metrics['tips_paid'],
                          metrics['net_sales'], metrics['change_in_gc_total']))

            remote_conn.commit()
            print(f"Data migrada para {os.path.basename(db_path)} - {len(batch_data)} filas subidas.")
            local_conn.close()
            
        except Exception as e:
            print(f"Error procesando {db_path}: {e}")
            
    remote_conn.close()
    print("\\nMigracion de backups Finalizada.")

if __name__ == '__main__':
    main()
