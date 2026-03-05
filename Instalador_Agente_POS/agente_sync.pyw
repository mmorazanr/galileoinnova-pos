import json
import time
import datetime
import pyodbc
import mysql.connector
import logging
import os
import sys
import socket
import threading
import hashlib
from logging.handlers import RotatingFileHandler

AGENT_VERSION = "2.0"

# ── Paths ────────────────────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
LOG_FILE = os.path.join(BASE_DIR, "agente_sync.log")

# ── Rotating log (5 MB max, 3 backups) ───────────────────────────────────────
logger = logging.getLogger("AgentSync")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,   # 5 MB
    backupCount=3,
    encoding="utf-8"
)
_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(_handler)

# ── Global state flags ────────────────────────────────────────────────────────
_paused = False       # When True, skip sync but keep heartbeat alive
_stop_event = threading.Event()


# ── Config ───────────────────────────────────────────────────────────────────
def load_config():
    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    config_path = os.path.join(BASE_DIR, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)


# ── id_sync: stable across restarts ──────────────────────────────────────────
def get_or_create_id_sync(cfg):
    """Generate a stable ID from restaurant + hostname, persist in config.json."""
    if "id_sync" in cfg and cfg["id_sync"]:
        return cfg["id_sync"]
    raw = f"{cfg['restaurant_name']}_{socket.gethostname()}"
    id_sync = hashlib.sha1(raw.encode()).hexdigest()[:16]
    cfg["id_sync"] = id_sync
    save_config(cfg)
    return id_sync


# ── DB connections ────────────────────────────────────────────────────────────
def get_remote_connection(cfg):
    return mysql.connector.connect(
        host=cfg['remote_db_host'],
        user=cfg['remote_db_user'],
        password=cfg['remote_db_pass'],
        database=cfg['remote_db_name'],
        use_pure=True,
        connection_timeout=10
    )

def get_local_connection(cfg):
    conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={cfg['local_db_path']};PWD=C0mtrex;"
    return pyodbc.connect(conn_str)


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

def get_current_business_day(local_conn):
    cursor = local_conn.cursor()
    cursor.execute("SELECT MAX(SalesDayNumber) FROM DailyCashierSales")
    res = cursor.fetchone()
    return res[0] if res and res[0] else 0


# ── Heartbeat & Command Polling ───────────────────────────────────────────────
def heartbeat_loop(cfg, id_sync):
    """Background thread: update sync_agents every 60 seconds and process commands."""
    global _paused
    while not _stop_event.is_set():
        try:
            status_str = "paused" if _paused else "running"
            ip = get_lan_ip()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = get_remote_connection(cfg)
            cur = conn.cursor()

            # Upsert heartbeat row
            cur.execute("""
                INSERT INTO sync_agents (id_sync, restaurante, ip_lan, db_path, status, last_heartbeat, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    restaurante    = VALUES(restaurante),
                    ip_lan         = VALUES(ip_lan),
                    db_path        = VALUES(db_path),
                    status         = VALUES(status),
                    last_heartbeat = VALUES(last_heartbeat),
                    version        = VALUES(version)
            """, (id_sync, cfg['restaurant_name'], ip, cfg['local_db_path'], status_str, now, AGENT_VERSION))
            conn.commit()

            # Command polling
            cur.execute("SELECT pending_command FROM sync_agents WHERE id_sync = %s", (id_sync,))
            row = cur.fetchone()
            if row and row[0]:
                cmd = row[0].strip().lower()
                logger.info(f"Command received: {cmd}")
                execute_command(cmd)
                # Clear the command
                cur.execute("UPDATE sync_agents SET pending_command = NULL WHERE id_sync = %s", (id_sync,))
                conn.commit()

            cur.close()
            conn.close()

        except Exception as e:
            logger.warning(f"Heartbeat error: {e}")

        _stop_event.wait(60)  # Sleep 60 seconds, but wake immediately if stop is signaled


def execute_command(cmd):
    """Execute a remote command issued from the cloud."""
    global _paused
    if cmd == "clear_logs":
        # Truncate log file
        try:
            for h in logger.handlers:
                h.close()
            open(LOG_FILE, 'w').close()
            # Re-attach handler
            new_h = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
            new_h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(new_h)
            logger.info("Log cleared by remote command.")
        except Exception as e:
            logger.error(f"clear_logs failed: {e}")

    elif cmd == "pause":
        _paused = True
        logger.info("Agent PAUSED by remote command.")

    elif cmd == "resume":
        _paused = False
        logger.info("Agent RESUMED by remote command.")

    elif cmd == "restart":
        logger.info("RESTART command received. Exiting process.")
        _stop_event.set()
        sys.exit(0)

    else:
        logger.warning(f"Unknown command ignored: {cmd}")


# ── Main Sync Logic ───────────────────────────────────────────────────────────
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
            try:
                cur_local.execute("SELECT DISTINCT CategoryNumber, CategoryName FROM DailyCashierSales")
                for row in cur_local.fetchall():
                    if row[1]:
                        category_map[str(row[0])] = row[1]
            except Exception:
                pass

        # 2. Push últimos 50 días
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
            logger.info("Sin ventas recientes.")
            local_conn.close()
            remote_conn.close()
            return

        # 3. Fechas reales de negocio por SalesDayNumber
        day_to_date = {}
        cur_local.execute(f"SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) FROM TransactionHeader WHERE SalesDayNumber >= {start_day} GROUP BY SalesDayNumber")
        for row in cur_local.fetchall():
            if row[1]:
                dt = row[1]
                if dt.hour >= 17:
                    dt = dt + datetime.timedelta(days=1)
                day_to_date[row[0]] = dt.strftime('%Y-%m-%d')

        push_cursor = remote_conn.cursor()
        fechas_borrar = list(set(day_to_date.values()))
        fechas_borrar_days = list(day_to_date.keys())

        if fechas_borrar:
            placeholders = ','.join(['%s'] * len(fechas_borrar))
            del_sql = f"DELETE FROM restaurantes_ventas WHERE restaurante = %s AND fecha IN ({placeholders})"
            del_params = [cfg['restaurant_name']] + fechas_borrar
            push_cursor.execute(del_sql, del_params)

        insert_sql = """
            INSERT INTO restaurantes_ventas
            (restaurante, transaccion_id, fecha, hora, mesero, categoria, platillo, cantidad, monto_venta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        batch_data = []
        from hashlib import md5
        now_time = datetime.datetime.now().strftime('%H:%M:%S')

        for row in rows_to_push:
            s_day     = row[0]
            cashier_id = str(row[1]) if row[1] else '0'
            category_id = str(row[2]) if row[2] else '0'
            prod_id   = str(row[3]) if row[3] else '0'
            prod_name = row[4]
            qty       = float(row[5] or 0)
            amount    = float(row[6] or 0)

            mesero_str = cashier_map.get(cashier_id, f"Desconocido DB {cashier_id}")
            cat_str    = category_map.get(category_id, f"Categoria DB {category_id}")
            fecha_str  = day_to_date.get(s_day, datetime.datetime.now().strftime('%Y-%m-%d'))

            uid_str  = f"{s_day}_{cashier_id}_{category_id}_{prod_id}"
            trans_id = int(md5(uid_str.encode()).hexdigest()[:8], 16)

            batch_data.append((
                cfg['restaurant_name'], trans_id, fecha_str, now_time,
                mesero_str, cat_str, prod_name, qty, amount
            ))

        push_cursor.executemany(insert_sql, batch_data)
        remote_conn.commit()

        # 4. KPI + Media por día
        for s_day in fechas_borrar_days:
            fecha_str = day_to_date.get(s_day)
            if not fecha_str:
                continue

            # KPI Global
            cur_local.execute(f"""
                SELECT SUM(NetSalesin15Min) as TotalNet, SUM(TranCountin15Min) as TotalTransactions
                FROM HourlySalesNew WHERE SalesDayNumber = {s_day}
            """)
            res_fin = cur_local.fetchone()
            if res_fin and res_fin[0] is not None:
                push_cursor.execute("DELETE FROM restaurantes_kpi WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                push_cursor.execute("""
                    INSERT INTO restaurantes_kpi (restaurante, fecha, ventas_netas, total_tickets)
                    VALUES (%s, %s, %s, %s)
                """, (cfg['restaurant_name'], fecha_str, float(res_fin[0]), int(res_fin[1])))

            # KPI por Mesero
            cur_local.execute(f"""
                SELECT CashierNumber, SUM(MiscQuantity) as Qty
                FROM DailyCashierMisc
                WHERE SalesDayNumber = {s_day} AND MiscDescription = 'Transaction Count'
                GROUP BY CashierNumber
            """)
            res_mesero = cur_local.fetchall()
            if res_mesero:
                push_cursor.execute("DELETE FROM restaurantes_kpi_mesero WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                for row_m in res_mesero:
                    num = str(row_m[0])
                    nombre = cashier_map.get(num, f"Desconocido DB {num}")
                    push_cursor.execute("""
                        INSERT INTO restaurantes_kpi_mesero (restaurante, fecha, mesero, total_tickets)
                        VALUES (%s, %s, %s, %s)
                    """, (cfg['restaurant_name'], fecha_str, nombre, int(row_m[1] or 0)))

            # Media por Mesero
            cur_local.execute(f"""
                SELECT CashierNumber, MediaName, SUM(POSAmount) as QtyAmount
                FROM DailyCashierMedia
                WHERE SalesDayNumber = {s_day} AND POSAmount <> 0
                GROUP BY CashierNumber, MediaName
            """)
            res_media_m = cur_local.fetchall()
            if res_media_m:
                push_cursor.execute("DELETE FROM restaurantes_mesero_media WHERE restaurante=%s AND fecha=%s", (cfg['restaurant_name'], fecha_str))
                for row_mm in res_media_m:
                    num = str(row_mm[0])
                    nombre = cashier_map.get(num, f"Desconocido DB {num}")
                    push_cursor.execute("""
                        INSERT INTO restaurantes_mesero_media (restaurante, fecha, mesero, media_name, amount)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (cfg['restaurant_name'], fecha_str, nombre, row_mm[1], float(row_mm[2] or 0)))

            # Diario Consolidado
            cur_local.execute(f"""
                SELECT MediaName, SUM(POSAmount) as TotalAmount
                FROM DailyCashierMedia WHERE SalesDayNumber = {s_day} GROUP BY MediaName
            """)
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
                    'Cash': 'cash', 'Employee Disc': 'employee_disc',
                    'Error Corrects': 'error_corrects', 'Gratuity': 'gratuity',
                    'MGR Disc': 'mgr_disc', 'MGR Void': 'mgr_void',
                    'Sales Transfer In': 'sales_transfer_in', 'Sales Transfer Out': 'sales_transfer_out',
                    'Service Balance': 'service_balance', 'Tax 1': 'tax_1', 'Tips Paid': 'tips_paid'
                }
                for r_d in res_diario:
                    m_name = r_d[0].strip() if r_d[0] else ""
                    m_val  = float(r_d[1] or 0)
                    if m_name in mapping:
                        metrics[mapping[m_name]] = m_val

                cur_local.execute(f"""
                    SELECT MiscDescription, SUM(MiscAmount) as TotalAmount
                    FROM DailyCashierMisc WHERE SalesDayNumber = {s_day}
                    GROUP BY MiscDescription
                """)
                for r_m in cur_local.fetchall():
                    desc = r_m[0].strip() if r_m[0] else ""
                    val  = float(r_m[1] or 0)
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
                """, (
                    cfg['restaurant_name'], fecha_str,
                    metrics['cash'], metrics['employee_disc'], metrics['error_corrects'],
                    metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'],
                    metrics['sales_transfer_in'], metrics['sales_transfer_out'],
                    metrics['service_balance'], metrics['tax_1'], metrics['tips_paid'],
                    metrics['net_sales'], metrics['change_in_gc_total']
                ))

        remote_conn.commit()
        logger.info(f"OK: {len(batch_data)} lineas sincronizadas a MariaDB.")

    except Exception as e:
        logger.error(f"Sync error: {e}")

    finally:
        try: local_conn.close()
        except: pass
        try: remote_conn.close()
        except: pass


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(">>> Iniciando Agente DB Sync v2.0 <<<")
    cfg = load_config()
    id_sync = get_or_create_id_sync(cfg)
    logger.info(f"id_sync: {id_sync} | host: {socket.gethostname()} | ip: {get_lan_ip()}")

    delay = int(cfg.get('sync_interval_seconds', 300))

    # Start heartbeat in background thread
    hb_thread = threading.Thread(target=heartbeat_loop, args=(cfg, id_sync), daemon=True)
    hb_thread.start()
    logger.info("Heartbeat thread started (60s interval).")

    while True:
        if not _paused:
            extract_and_push()
        else:
            logger.info("Sync skipped (paused).")
        time.sleep(delay)
