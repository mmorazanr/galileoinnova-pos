import json
import time
import datetime
import pyodbc 
import mysql.connector
import logging
import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

LOG_FILE = os.path.join(get_base_dir(), "agente_sync.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    config_path = os.path.join(get_base_dir(), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_remote_connection(cfg):
    return mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name'],
        use_pure=True
    )

def get_local_connection(cfg):
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;"
    return pyodbc.connect(conn_str)

def get_current_business_day(local_conn):
    # Returns the largest day number in DB (today's business day)
    cursor = local_conn.cursor()
    cursor.execute("SELECT MAX(SalesDayNumber) FROM DailyCashierSales")
    res = cursor.fetchone()
    return res[0] if res and res[0] else 0

def extract_and_push():
    try:
        cfg = load_config()
        remote_conn = get_remote_connection(cfg)
        local_conn = get_local_connection(cfg)
        
        # 1. Mapeos
        cashier_map = {}
        cur_local = local_conn.cursor()
        cur_local.execute("SELECT DISTINCT CashierNumber, CashierName FROM DailyCashierSales")
        for row in cur_local.fetchall():
            cashier_map[str(row[0])] = row[1]
            
        category_map = {}
        try:
            cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions")
            for row in cur_local.fetchall():
                category_map[str(row[0])] = row[1]
        except Exception:
            # K_CategoryDefinitions es una linked table de CBODef_s.mdb
            # Si no esta accesible, se usa el numero de categoria como nombre
            try:
                cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM DailyCashierSales")
                for row in cur_local.fetchall():
                    if row[1]:
                        category_map[str(row[0])] = row[1]
            except Exception:
                pass
            
        # 2. Vamos a empujar historial completo de los últimos 50 días para la demostración
        max_day = get_current_business_day(local_conn)
        start_day = max_day - 50

        sql_extract = f"""
            SELECT 
                SalesDayNumber,
                CashierNumber,
                CategoryNumber,
                ProductNumber,
                ProductName,
                SUM(MenuItemQuantity) as Qty,
                SUM(MenuItemAmount - MenuItemDiscAmount) as NetAmount
            FROM DailyCashierSales
            WHERE SalesDayNumber >= {start_day}
            GROUP BY SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName
            HAVING SUM(MenuItemAmount - MenuItemDiscAmount) <> 0 OR SUM(MenuItemQuantity) > 0
        """
        cur_local.execute(sql_extract)
        rows_to_push = cur_local.fetchall()
        
        if not rows_to_push:
            logging.info("Sin ventas recientes.")
            local_conn.close()
            remote_conn.close()
            return
            
        # Encontrar la fecha real de la venta desde TransactionHeader usando el SalesDayNumber
        day_to_date = {}
        cur_local.execute(f"SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader WHERE SalesDayNumber >= {start_day} GROUP BY SalesDayNumber")
        for row in cur_local.fetchall():
            if row[1]:
                dt = row[1]
                # Si el dia abre de noche (>= 17:00), el dia de negocio real es el siguiente
                if dt.hour >= 17:
                    dt = dt + datetime.timedelta(days=1)
                day_to_date[row[0]] = dt.strftime('%Y-%m-%d')
        
        # Borrar en la nube los últimos días cargados para esta sucursal (Replace strategy to keep it 100% matched with Excel)
        push_cursor = remote_conn.cursor()
        fechas_borrar = list(set([d for d in day_to_date.values()]))
        fechas_borrar_days = list(day_to_date.keys())
        
        if fechas_borrar:
            placeholders = ','.join(['%s']*len(fechas_borrar))
            del_sql = f"DELETE FROM restaurantes_ventas WHERE restaurante = %s AND fecha IN ({placeholders})"
            del_params = [cfg['restaurant_name']] + fechas_borrar
            push_cursor.execute(del_sql, del_params)
        
        # 3. Insertar Data Limpia
        insert_sql = """
            INSERT INTO restaurantes_ventas 
            (restaurante, transaccion_id, fecha, hora, mesero, categoria, platillo, cantidad, monto_venta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        batch_data = []
        # Generamos un ID virtual uniendo dia + cajero + category + producto
        from hashlib import md5
        
        now_time = datetime.datetime.now().strftime('%H:%M:%S')

        for row in rows_to_push:
            s_day = row[0]
            cashier_id = str(row[1]) if row[1] else '0'
            category_id = str(row[2]) if row[2] else '0'
            prod_id = str(row[3]) if row[3] else '0'
            prod_name = row[4]
            qty = float(row[5] or 0)
            amount = float(row[6] or 0)
            
            mesero_str = cashier_map.get(cashier_id, f"Desconocido DB {cashier_id}")
            cat_str = category_map.get(category_id, f"Categoria DB {category_id}")
            fecha_str = day_to_date.get(s_day, datetime.datetime.now().strftime('%Y-%m-%d'))
            
            uid_str = f"{s_day}_{cashier_id}_{category_id}_{prod_id}"
            trans_id = int(md5(uid_str.encode()).hexdigest()[:8], 16) # Hash as trans_id

            batch_data.append((
                cfg['restaurant_name'],
                trans_id,
                fecha_str,
                now_time,
                mesero_str,
                cat_str,
                prod_name,
                qty,
                amount
            ))
            
        push_cursor.executemany(insert_sql, batch_data)
        remote_conn.commit()
        
        # 4. Insertar Data de Cuadre Maestro Global (KPI Exactos)
        for s_day in fechas_borrar_days:
            fecha_str = day_to_date.get(s_day)
            if not fecha_str: continue
            
            # Obtener ventas netas sumando de HourlySalesNew (ignora la hora)
            q_fin = f"""
                SELECT 
                    SUM(NetSalesin15Min) as TotalNet,
                    SUM(TranCountin15Min) as TotalTransactions
                FROM HourlySalesNew
                WHERE SalesDayNumber = {s_day}
            """
            cur_local.execute(q_fin)
            res_fin = cur_local.fetchone()
            if res_fin and res_fin[0] is not None:
                net_sales = res_fin[0]
                tickets = res_fin[1]
                
                push_cursor.execute("DELETE FROM restaurantes_kpi WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                push_cursor.execute("""
                    INSERT INTO restaurantes_kpi (restaurante, fecha, ventas_netas, total_tickets)
                    VALUES (%s, %s, %s, %s)
                """, (cfg['restaurant_name'], fecha_str, float(net_sales), int(tickets)))
                
            # Obtener tickets reales contados por mesero
            q_mesero = f"""
                SELECT CashierNumber, SUM(MiscQuantity) as Qty
                FROM DailyCashierMisc
                WHERE SalesDayNumber = {s_day} AND MiscDescription = 'Transaction Count'
                GROUP BY CashierNumber
            """
            cur_local.execute(q_mesero)
            res_mesero = cur_local.fetchall()
            
            if res_mesero:
                push_cursor.execute("DELETE FROM restaurantes_kpi_mesero WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                for row_m in res_mesero:
                    num_cajero = str(row_m[0])
                    tickets_cajero = int(row_m[1] or 0)
                    nombre_cajero = cashier_map.get(num_cajero, f"Desconocido DB {num_cajero}")
                    
                    push_cursor.execute("""
                        INSERT INTO restaurantes_kpi_mesero (restaurante, fecha, mesero, total_tickets)
                        VALUES (%s, %s, %s, %s)
                    """, (cfg['restaurant_name'], fecha_str, nombre_cajero, tickets_cajero))

            # Obtener desglose de Media por mesero (Cash, Errors, Discounts, etc.)
            q_media_m = f"""
                SELECT CashierNumber, MediaName, SUM(POSAmount) as QtyAmount
                FROM DailyCashierMedia
                WHERE SalesDayNumber = {s_day} AND POSAmount <> 0
                GROUP BY CashierNumber, MediaName
            """
            cur_local.execute(q_media_m)
            res_media_m = cur_local.fetchall()
            
            if res_media_m:
                push_cursor.execute("DELETE FROM restaurantes_mesero_media WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                for row_mm in res_media_m:
                    num_cajero = str(row_mm[0])
                    media_name = row_mm[1]
                    amount     = float(row_mm[2] or 0)
                    nombre_cajero = cashier_map.get(num_cajero, f"Desconocido DB {num_cajero}")
                    
                    push_cursor.execute("""
                        INSERT INTO restaurantes_mesero_media (restaurante, fecha, mesero, media_name, amount)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (cfg['restaurant_name'], fecha_str, nombre_cajero, media_name, amount))

            # 5. Nuevo: Cuadre Diario Consolidado para el Reporte Comparativo
            q_diario = f"""
                SELECT 
                    MediaName, SUM(POSAmount) as TotalAmount
                FROM DailyCashierMedia
                WHERE SalesDayNumber = {s_day}
                GROUP BY MediaName
            """
            cur_local.execute(q_diario)
            res_diario = cur_local.fetchall()
            
            if res_diario:
                # Diccionario para mapear los campos requeridos
                # Cash, Employee Disc, Error Corrects, Gratuity, MGR Disc, MGR Void, 
                # Sales Transfer In, Sales Transfer Out, Service Balance, Tax 1, Tips Paid
                metrics = {
                    'cash': 0.0, 'employee_disc': 0.0, 'error_corrects': 0.0, 
                    'gratuity': 0.0, 'mgr_disc': 0.0, 'mgr_void': 0.0,
                    'sales_transfer_in': 0.0, 'sales_transfer_out': 0.0, 
                    'service_balance': 0.0, 'tax_1': 0.0, 'tips_paid': 0.0,
                    'net_sales': 0.0, 'change_in_gc_total': 0.0
                }
                
                mapping = {
                    'Cash': 'cash',
                    'Employee Disc': 'employee_disc',
                    'Error Corrects': 'error_corrects',
                    'Gratuity': 'gratuity',
                    'MGR Disc': 'mgr_disc',
                    'MGR Void': 'mgr_void',
                    'Sales Transfer In': 'sales_transfer_in',
                    'Sales Transfer Out': 'sales_transfer_out',
                    'Service Balance': 'service_balance',
                    'Tax 1': 'tax_1',
                    'Tips Paid': 'tips_paid'
                }
                
                for r_d in res_diario:
                    m_name = r_d[0].strip() if r_d[0] else ""
                    m_val  = float(r_d[1] or 0)
                    if m_name in mapping:
                        metrics[mapping[m_name]] = m_val
                
                # Query DailyCashierMisc for Net Sales and Grand Control Total
                q_misc = f"""
                    SELECT 
                        MiscDescription, SUM(MiscAmount) as TotalAmount
                    FROM DailyCashierMisc
                    WHERE SalesDayNumber = {s_day}
                    GROUP BY MiscDescription
                """
                cur_local.execute(q_misc)
                for r_m in cur_local.fetchall():
                    desc = r_m[0].strip() if r_m[0] else ""
                    val = float(r_m[1] or 0)
                    if desc == 'Net Sales':
                        metrics['net_sales'] = val
                    elif desc == 'Grand Control Total':
                        metrics['change_in_gc_total'] = val
                
                push_cursor.execute("DELETE FROM restaurantes_diario_media WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                sql_diario = """
                    INSERT INTO restaurantes_diario_media 
                    (restaurante, fecha, cash, employee_disc, error_corrects, gratuity, mgr_disc, mgr_void, 
                     sales_transfer_in, sales_transfer_out, service_balance, tax_1, tips_paid,
                     net_sales, change_in_gc_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                push_cursor.execute(sql_diario, (
                    cfg['restaurant_name'], fecha_str,
                    metrics['cash'], metrics['employee_disc'], metrics['error_corrects'],
                    metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'],
                    metrics['sales_transfer_in'], metrics['sales_transfer_out'],
                    metrics['service_balance'], metrics['tax_1'], metrics['tips_paid'],
                    metrics['net_sales'], metrics['change_in_gc_total']
                ))

        remote_conn.commit()
        
        logging.info(f"Éxito: Se re-sincronizaron {len(batch_data)} líneas de detalle y Cuadres Maestros KPI perfectos a MariaDB.")
        
    except Exception as e:
        logging.error(f"Error de Integración: {e}")
        
    finally:
        try: local_conn.close() 
        except: pass
        try: remote_conn.close()
        except: pass

if __name__ == "__main__":
    logging.info(">>> Iniciando Agente DB Sync de Cuadre Exacto <<<")
    cfg = load_config()
    delay = int(cfg.get('sync_interval_seconds', 300))
    while True:
        extract_and_push()
        time.sleep(delay)
