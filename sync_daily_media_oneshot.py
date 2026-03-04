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

def load_config():
    config_path = os.path.join(get_base_dir(), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_remote_connection(cfg):
    return mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name']
    )

def get_local_connection(cfg):
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;"
    return pyodbc.connect(conn_str)

def get_current_business_day(local_conn):
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
        cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM K_CategoryDefinitions")
        for row in cur_local.fetchall():
            category_map[str(row[0])] = row[1]
            
        # 2. Vamos a empujar historial completo de los últimos 50 días para la demostración
        max_day = get_current_business_day(local_conn)
        start_day = max_day - 50

        # Encontrar la fecha real de la venta desde TransactionHeader usando el SalesDayNumber
        day_to_date = {}
        cur_local.execute(f"SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader WHERE SalesDayNumber >= {start_day} GROUP BY SalesDayNumber")
        for row in cur_local.fetchall():
            if row[1]:
                day_to_date[row[0]] = row[1].strftime('%Y-%m-%d')
        
        fechas_borrar_days = list(day_to_date.keys())
        push_cursor = remote_conn.cursor()

        # 4. Insertar Data de Cuadre Maestro Global (KPI Exactos)
        for s_day in fechas_borrar_days:
            fecha_str = day_to_date.get(s_day)
            if not fecha_str: continue
            print(f"Syncing {fecha_str}...")

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
        print(f"Éxito: Se re-sincronizaron Daily Media para MariaDB.")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        try: local_conn.close() 
        except: pass
        try: remote_conn.close()
        except: pass

if __name__ == "__main__":
    extract_and_push()
