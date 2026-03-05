"""
Agente DB Sync - System Tray Application
Sincronizador de datos POS POS → MariaDB Cloud
Con bandeja del sistema, log en vivo y control de pausa/reanudación.
"""
import sys
import os
import json
import time
import datetime
import logging
import socket
import hashlib
import urllib.request
from logging.handlers import RotatingFileHandler
AGENT_VERSION = "2.3-Tray"
import threading
import winreg

import pyodbc
import mysql.connector

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QSystemTrayIcon, QMenu, QAction,
    QFrame, QSizePolicy, QMessageBox, QDialog, QTableWidget,
    QTableWidgetItem, QComboBox, QHeaderView, QAbstractItemView,
    QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor, QPainter, QPixmap, QFont, QTextCursor

APP_NAME  = "Agente DB Sync"
APP_REG   = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ──────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE = get_base_dir()
LOG_FILE = os.path.join(BASE, "agente_sync.log")

# Config Log Rotativo
logger = logging.getLogger("AgentSync")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(_handler)

def save_config(cfg):
    import json
    with open(os.path.join(BASE, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def get_or_create_id_sync(cfg):
    if "id_sync" in cfg and cfg["id_sync"]:
        return cfg["id_sync"]
    raw = f"{cfg.get('restaurant_name','Unknown')}_{socket.gethostname()}"
    id_sync = hashlib.sha1(raw.encode()).hexdigest()[:16]
    cfg["id_sync"] = id_sync
    save_config(cfg)
    return id_sync

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

def get_wan_ip():
    try:
        req = urllib.request.urlopen("https://api.ipify.org", timeout=5)
        return req.read().decode("utf-8").strip()
    except Exception:
        return "unknown"


def load_config():
    try:
        with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError as e:
        msg = f"Error de sintaxis en config.json:\n\n{str(e)}\n\nPor favor, verifica que no haya comas extras al final de las líneas."
        try:
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error de Configuración")
            msg_box.setText(msg)
            msg_box.exec_()
        except:
            print(msg)
        sys.exit(1)


def make_tray_icon(color="#22c55e"):
    """Genera un ícono de 32x32 con círculo de color."""
    px = QPixmap(32, 32)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 28, 28)
    # Letra "S"
    p.setPen(QColor("white"))
    font = QFont("Arial", 14, QFont.Bold)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignCenter, "S")
    p.end()
    return QIcon(px)


ICON_GREEN  = "#22c55e"
ICON_YELLOW = "#eab308"
ICON_RED    = "#ef4444"
ICON_GRAY   = "#64748b"


# ──────────────────────────────────────────────────────────────────
#  Worker thread — lógica de sincronización
# ──────────────────────────────────────────────────────────────────

# ── Heartbeat & Command Polling ───────────────────────────────────────────────
class HeartbeatWorker(QThread):
    def __init__(self, cfg, id_sync, sync_worker):
        super().__init__()
        self.cfg = cfg
        self.id_sync = id_sync
        self.sync_worker = sync_worker
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        public_ip = get_wan_ip()
        consecutive_errors = 0
        while self._running:
            try:
                status_str = "paused" if self.sync_worker.is_paused else "running"
                ip = get_lan_ip()
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                conn = mysql.connector.connect(
                    host=self.cfg['remote_db_host'],
                    user=self.cfg['remote_db_user'],
                    password=self.cfg['remote_db_pass'],
                    database=self.cfg['remote_db_name'],
                    use_pure=True,
                    connection_timeout=10
                )
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO sync_agents (id_sync, restaurante, ip_lan, ip_public, db_path, status, last_heartbeat, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        restaurante    = VALUES(restaurante),
                        ip_lan         = VALUES(ip_lan),
                        ip_public      = VALUES(ip_public),
                        db_path        = VALUES(db_path),
                        status         = VALUES(status),
                        last_heartbeat = VALUES(last_heartbeat),
                        version        = VALUES(version)
                """, (self.id_sync, self.cfg.get('restaurant_name','Unknown'), ip, public_ip, self.cfg.get('local_db_path',''), status_str, now, AGENT_VERSION))
                conn.commit()

                cur.execute("SELECT pending_command FROM sync_agents WHERE id_sync = %s", (self.id_sync,))
                row = cur.fetchone()
                if row and row[0]:
                    cmd = row[0].strip().lower()
                    logger.info(f"Command received: {cmd}")
                    self.execute_command(cmd)
                    cur.execute("UPDATE sync_agents SET pending_command = NULL WHERE id_sync = %s", (self.id_sync,))
                    conn.commit()

                cur.close()
                conn.close()
                consecutive_errors = 0
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")
                consecutive_errors += 1
                if "1129" in str(e):
                    consecutive_errors = max(10, consecutive_errors)

            # Sleep base is 60s. Back-off exponent si hay errores para no bloquear IP.
            sleep_time = 60 if consecutive_errors < 3 else min(600, 60 * consecutive_errors)
            for _ in range(sleep_time):
                if not self._running:
                    break
                import time
                time.sleep(1)

    def execute_command(self, cmd):
        if cmd == "clear_logs":
            try:
                for h in logger.handlers:
                    h.close()
                open(LOG_FILE, 'w').close()
                new_h = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
                new_h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                logger.addHandler(new_h)
            except Exception as e:
                pass
        elif cmd == "pause":
            self.sync_worker.pause()
        elif cmd == "resume":
            self.sync_worker.resume()
        elif cmd == "sync_now":
            self.sync_worker.force_sync()

class SyncWorker(QThread):
    log_signal    = pyqtSignal(str, str)   # (mensaje, nivel)
    status_signal = pyqtSignal(str, str)   # (texto_estado, color_icono)
    done_signal   = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._paused  = False
        self._running = True
        self._force_sync = False
        self._lock    = threading.Lock()

    def force_sync(self):
        self._force_sync = True
        self.status_signal.emit("⚡ Sync Forzado", ICON_GREEN)
        self.log_signal.emit("Sincronización manual forzada desde Dashboard.", "info")

    def pause(self):
        self._paused = True
        self.status_signal.emit("⏸  Pausado", ICON_YELLOW)
        self.log_signal.emit("Sincronización pausada por el usuario.", "warning")

    def resume(self):
        self._paused = False
        self.status_signal.emit("▶  Activo", ICON_GREEN)
        self.log_signal.emit("Sincronización reanudada.", "info")

    def stop(self):
        self._running = False
        self._paused  = False

    @property
    def is_paused(self):
        return self._paused

    def _log(self, msg, level="info"):
        self.log_signal.emit(msg, level)
        getattr(logger, level, logger.info)(msg)

    def run(self):
        from hashlib import md5
        DAYS_ES_W = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles',
                     'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}
        MEDIA_MAP  = {'Cash':'cash','Employee Disc':'employee_disc','Error Corrects':'error_corrects',
                      'Gratuity':'gratuity','MGR Disc':'mgr_disc','MGR Void':'mgr_void',
                      'Sales Transfer In':'sales_transfer_in','Sales Transfer Out':'sales_transfer_out',
                      'Service Balance':'service_balance','Tax 1':'tax_1','Tips Paid':'tips_paid'}

        self.status_signal.emit("▶  Iniciando…", ICON_GREEN)

        while self._running:
            while self._paused and self._running:
                time.sleep(0.5)
            if not self._running:
                break

            try:
                cfg      = load_config()
                interval = int(cfg.get('sync_interval_seconds', 300))
                rest     = cfg['restaurant_name']
                today_str = datetime.date.today().strftime('%Y-%m-%d')

                self._log("─" * 48, "info")
                self._log(f"🔄 Iniciando ciclo de sincronización — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", "info")

                # ── Conexión Access ──────────────────────────────────────
                self._log("🔌 Conectando a Access (POS local)…", "info")
                self.status_signal.emit("🔌 Conectando a Access…", ICON_YELLOW)
                local_conn = pyodbc.connect(
                    f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                    f"DBQ={cfg['local_db_path']};PWD=C0mtrex;"
                )
                self._log("✔ Access OK", "info")

                # ── Conexión MariaDB ─────────────────────────────────────
                self._log("🔌 Conectando a MariaDB Cloud…", "info")
                self.status_signal.emit("🔌 Conectando a MariaDB…", ICON_YELLOW)
                remote_conn = mysql.connector.connect(
                    host=cfg['remote_db_host'], user=cfg['remote_db_user'],
                    password=cfg['remote_db_pass'], database=cfg['remote_db_name'],
                    use_pure=True
                )
                self._log("✔ MariaDB OK", "info")

                cur_local   = local_conn.cursor()
                push_cursor = remote_conn.cursor()

                # ── Mapas de nombres ─────────────────────────────────────
                cashier_map = {}
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
                            if row[1]: category_map[str(row[0])] = row[1]
                    except Exception:
                        pass

                # ── Rango de días ────────────────────────────────────────
                cur_local.execute("SELECT MAX(SalesDayNumber) FROM DailyCashierSales")
                res       = cur_local.fetchone()
                max_day   = res[0] if res and res[0] else 0
                start_day = max_day - 50

                # ── Mapa SalesDayNumber → fecha ──────────────────────────
                day_to_date = {}
                cur_local.execute(
                    f"SELECT DISTINCT SalesDayNumber, MIN(DateTimeStart) "
                    f"FROM TransactionHeader WHERE SalesDayNumber >= {start_day} "
                    f"GROUP BY SalesDayNumber"
                )
                for row in cur_local.fetchall():
                    if row[1]:
                        dt = row[1]
                        if dt.hour >= 17:
                            dt = dt + datetime.timedelta(days=1)
                        day_to_date[row[0]] = dt.strftime('%Y-%m-%d')

                # Filtrar hoy y ordenar
                days_to_sync = sorted(
                    [(d, f) for d, f in day_to_date.items() if f != today_str],
                    key=lambda x: x[1]
                )
                total_days = len(days_to_sync)
                self._log(f"📋 {total_days} días encontrados en Access (SalesDay {start_day}–{max_day})", "info")

                # ── Caché: qué fechas ya existen en MariaDB ──────────────
                push_cursor.execute(
                    "SELECT fecha, net_sales FROM restaurantes_diario_media WHERE restaurante=%s", (rest,)
                )
                remote_existing = {str(r[0]): float(r[1] or 0) for r in push_cursor.fetchall()}

                # ── Detectar columa sales ────────────────────────────────
                cols = [d[0] for d in cur_local.execute("SELECT TOP 1 * FROM HourlySalesNew").description]
                sales_col = "NetSalesin15Min" if "NetSalesin15Min" in cols else "Salesin15Min"

                # ── Procesar cada día ────────────────────────────────────
                total_rows_new = 0
                dias_nuevos    = 0
                dias_ya_sync   = 0
                dias_actualizados = 0
                dias_sincronizados_nombres = []

                for idx, (s_day, fecha_str) in enumerate(days_to_sync, 1):
                    if not self._running:
                        break
                    while self._paused and self._running:
                        time.sleep(0.5)

                    day_en = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%A')
                    day_es = DAYS_ES_W.get(day_en, day_en)
                    prefix = f"[{idx:02d}/{total_days}] {fecha_str} {day_es}"

                    self.status_signal.emit(
                        f"⬆ {fecha_str} ({day_es}) — {idx}/{total_days}", ICON_YELLOW
                    )

                    # Ventas en Access para este día
                    # Nota: Access ODBC no soporta COALESCE — se maneja None en Python
                    cur_local.execute(f"""
                        SELECT COUNT(*), SUM(MenuItemAmount - MenuItemDiscAmount)
                        FROM DailyCashierSales WHERE SalesDayNumber = {s_day}
                        AND (MenuItemAmount - MenuItemDiscAmount) <> 0
                    """)
                    access_res = cur_local.fetchone()
                    access_cnt = int(access_res[0] or 0)
                    access_net = float(access_res[1] or 0) if access_res and access_res[1] is not None else 0.0

                    # Net Sales (DailyCashierMisc)
                    cur_local.execute(
                        f"SELECT SUM(MiscAmount) FROM DailyCashierMisc "
                        f"WHERE SalesDayNumber={s_day} AND MiscDescription='Net Sales'"
                    )
                    ns_res   = cur_local.fetchone()
                    net_sales_access = float(ns_res[0] or 0) if ns_res and ns_res[0] else access_net

                    # Comparar con MariaDB
                    remote_net = remote_existing.get(fecha_str)

                    if remote_net is not None and abs(remote_net - net_sales_access) < 0.02:
                        # Ya sincronizado y coincide
                        self._log(
                            f"  ✔ {prefix} — Ya sincronizado | "
                            f"Net Sales: ${net_sales_access:,.2f} | {access_cnt} items",
                            "info"
                        )
                        dias_ya_sync += 1
                        continue

                    # Necesita actualización
                    if remote_net is not None:
                        self._log(
                            f"  🔄 {prefix} — Actualizando "
                            f"(${remote_net:,.2f} → ${net_sales_access:,.2f}) | {access_cnt} items…",
                            "warning"
                        )
                        dias_actualizados += 1
                    else:
                        self._log(
                            f"  ⬆ {prefix} — Nuevo día | "
                            f"Net Sales: ${net_sales_access:,.2f} | {access_cnt} items…",
                            "info"
                        )
                        dias_nuevos += 1

                    # ── Ventas detalle ───────────────────────────────────
                    cur_local.execute(f"""
                        SELECT SalesDayNumber, CashierNumber, CategoryNumber,
                               ProductNumber, ProductName,
                               SUM(MenuItemQuantity), SUM(MenuItemAmount - MenuItemDiscAmount)
                        FROM DailyCashierSales WHERE SalesDayNumber = {s_day}
                        GROUP BY SalesDayNumber, CashierNumber, CategoryNumber, ProductNumber, ProductName
                        HAVING SUM(MenuItemAmount - MenuItemDiscAmount) <> 0 OR SUM(MenuItemQuantity) > 0
                    """)
                    ventas_rows = cur_local.fetchall()

                    push_cursor.execute(
                        "DELETE FROM restaurantes_ventas WHERE restaurante=%s AND fecha=%s",
                        (rest, fecha_str)
                    )
                    now_time = datetime.datetime.now().strftime('%H:%M:%S')
                    batch = []
                    for row in ventas_rows:
                        cid = str(row[1] or 0); catid = str(row[2] or 0); pid = str(row[3] or 0)
                        uid = f"{s_day}_{cid}_{catid}_{pid}"
                        trans_id = int(md5(uid.encode()).hexdigest()[:8], 16)
                        batch.append((
                            rest, trans_id, fecha_str, now_time,
                            cashier_map.get(cid, f"Cajero {cid}"),
                            category_map.get(catid, f"Cat {catid}"),
                            row[4], float(row[5] or 0), float(row[6] or 0)
                        ))
                    if batch:
                        push_cursor.executemany("""
                            INSERT INTO restaurantes_ventas
                            (restaurante, transaccion_id, fecha, hora, mesero, categoria, platillo, cantidad, monto_venta)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """, batch)
                    total_rows_new += len(batch)

                    # ── KPI HourlySales ──────────────────────────────────
                    cur_local.execute(
                        f"SELECT SUM({sales_col}), SUM(TranCountin15Min) "
                        f"FROM HourlySalesNew WHERE SalesDayNumber={s_day}"
                    )
                    res_fin = cur_local.fetchone()
                    if res_fin and res_fin[0] is not None:
                        push_cursor.execute(
                            "DELETE FROM restaurantes_kpi WHERE restaurante=%s AND fecha=%s",
                            (rest, fecha_str)
                        )
                        push_cursor.execute(
                            "INSERT INTO restaurantes_kpi (restaurante, fecha, ventas_netas, total_tickets) VALUES (%s,%s,%s,%s)",
                            (rest, fecha_str, float(res_fin[0]), int(res_fin[1] or 0))
                        )

                    # ── KPI Mesero ───────────────────────────────────────
                    cur_local.execute(
                        f"SELECT CashierNumber, SUM(MiscQuantity) FROM DailyCashierMisc "
                        f"WHERE SalesDayNumber={s_day} AND MiscDescription='Transaction Count' "
                        f"GROUP BY CashierNumber"
                    )
                    res_m = cur_local.fetchall()
                    if res_m:
                        push_cursor.execute(
                            "DELETE FROM restaurantes_kpi_mesero WHERE restaurante=%s AND fecha=%s",
                            (rest, fecha_str)
                        )
                        for rm in res_m:
                            push_cursor.execute(
                                "INSERT INTO restaurantes_kpi_mesero (restaurante, fecha, mesero, total_tickets) VALUES (%s,%s,%s,%s)",
                                (rest, fecha_str, cashier_map.get(str(rm[0]), str(rm[0])), int(rm[1] or 0))
                            )

                    # ── Media por mesero ─────────────────────────────────
                    cur_local.execute(
                        f"SELECT CashierNumber, MediaName, SUM(POSAmount) FROM DailyCashierMedia "
                        f"WHERE SalesDayNumber={s_day} AND POSAmount<>0 GROUP BY CashierNumber, MediaName"
                    )
                    res_mm = cur_local.fetchall()
                    if res_mm:
                        push_cursor.execute(
                            "DELETE FROM restaurantes_mesero_media WHERE restaurante=%s AND fecha=%s",
                            (rest, fecha_str)
                        )
                        for rmm in res_mm:
                            push_cursor.execute(
                                "INSERT INTO restaurantes_mesero_media (restaurante, fecha, mesero, media_name, amount) VALUES (%s,%s,%s,%s,%s)",
                                (rest, fecha_str, cashier_map.get(str(rmm[0]), str(rmm[0])), rmm[1], float(rmm[2] or 0))
                            )

                    # ── Diario media ─────────────────────────────────────
                    metrics = {k: 0.0 for k in ['cash','employee_disc','error_corrects','gratuity',
                                                  'mgr_disc','mgr_void','sales_transfer_in','sales_transfer_out',
                                                  'service_balance','tax_1','tips_paid','net_sales','change_in_gc_total']}
                    cur_local.execute(
                        f"SELECT MediaName, SUM(POSAmount) FROM DailyCashierMedia "
                        f"WHERE SalesDayNumber={s_day} GROUP BY MediaName"
                    )
                    for r in cur_local.fetchall():
                        m = (r[0] or '').strip()
                        if m in MEDIA_MAP: metrics[MEDIA_MAP[m]] = float(r[1] or 0)
                    cur_local.execute(
                        f"SELECT MiscDescription, SUM(MiscAmount) FROM DailyCashierMisc "
                        f"WHERE SalesDayNumber={s_day} GROUP BY MiscDescription"
                    )
                    for r in cur_local.fetchall():
                        d = (r[0] or '').strip()
                        if d == 'Net Sales': metrics['net_sales'] = float(r[1] or 0)
                        elif d == 'Grand Control Total': metrics['change_in_gc_total'] = float(r[1] or 0)

                    push_cursor.execute("DELETE FROM restaurantes_diario_media WHERE restaurante=%s AND fecha=%s", (rest, fecha_str))
                    push_cursor.execute("""INSERT INTO restaurantes_diario_media
                        (restaurante, fecha, cash, employee_disc, error_corrects, gratuity, mgr_disc, mgr_void,
                         sales_transfer_in, sales_transfer_out, service_balance, tax_1, tips_paid, net_sales, change_in_gc_total)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (rest, fecha_str, metrics['cash'], metrics['employee_disc'],
                         metrics['error_corrects'], metrics['gratuity'], metrics['mgr_disc'], metrics['mgr_void'],
                         metrics['sales_transfer_in'], metrics['sales_transfer_out'], metrics['service_balance'],
                         metrics['tax_1'], metrics['tips_paid'], metrics['net_sales'], metrics['change_in_gc_total']))

                    remote_conn.commit()
                    dias_sincronizados_nombres.append(fecha_str)

                # ── Resumen ciclo ────────────────────────────────────────
                self._log("─" * 48, "info")
                self._log(
                    f"✅ Ciclo completo | {total_days} días revisados: "
                    f"{dias_ya_sync} ya sincronizados, "
                    f"{dias_nuevos} nuevos, "
                    f"{dias_actualizados} actualizados | "
                    f"{total_rows_new} filas subidas",
                    "info"
                )

                # ── Enviar Histórico de Ejecución a MariaDB ────────────────
                try:
                    c_cursor = remote_conn.cursor()
                    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if dias_sincronizados_nombres:
                        dt_desc = f"día{'s' if len(dias_sincronizados_nombres)>1 else ''} {', '.join(dias_sincronizados_nombres)} sincronizado{'s' if len(dias_sincronizados_nombres)>1 else ''}."
                    else:
                        dt_desc = "0 dias sincronizados."
                        
                    c_cursor.execute("""
                        INSERT INTO agent_sync_history (id_sync, fecha_ciclo, dias_sincronizados, detalle)
                        VALUES (%s, %s, %s, %s)
                    """, (cfg.get('id_sync', 'Unknown'), ahora, len(dias_sincronizados_nombres), dt_desc))
                    remote_conn.commit()
                    c_cursor.close()
                except Exception as log_e:
                    self._log(f"Error al guardar agent_sync_history: {log_e}", "error")

                ts_ok = datetime.datetime.now().strftime('%H:%M:%S')
                self.status_signal.emit(f"✅ Sync OK {ts_ok} — próx. en {interval}s", ICON_GREEN)

                local_conn.close()
                remote_conn.close()

                # ── Cuenta regresiva visible ─────────────────────────────
                for remaining in range(interval, 0, -1):
                    if not self._running or self._paused:
                        break
                    
                    if self._force_sync:
                        self._force_sync = False
                        self._log("⚡ Interrumpiendo espera para Sincronizar Ahora", "info")
                        break

                    if remaining % 30 == 0:
                        self._log(f"⏱  Próxima sincronización en {remaining}s…", "info")
                        self.status_signal.emit(
                            f"⏳ Próx. sync en {remaining}s", ICON_GREEN
                        )
                    time.sleep(1)

            except mysql.connector.Error as db_e:
                self._log(f"❌ Error MariaDB: {db_e}", "error")
                self.status_signal.emit("❌ Error DB", ICON_RED)
                time.sleep(30)
            except Exception as e:
                self._log(f"❌ Error de integración: {e}", "error")
                self.status_signal.emit("❌ Error", ICON_RED)
                time.sleep(30)



# ──────────────────────────────────────────────────────────────────
#  Administrador de Días Contables
# ──────────────────────────────────────────────────────────────────
TABLAS = [
    'restaurantes_ventas',
    'restaurantes_kpi',
    'restaurantes_kpi_mesero',
    'restaurantes_mesero_media',
    'restaurantes_diario_media',
]
DAYS_ES = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles',
            'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}


class AdminDialog(QDialog):
    STYLE = """
        QDialog, QWidget { background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI'; }
        QComboBox { background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
                    border-radius: 6px; padding: 6px 10px; font-size: 13px; min-width: 260px; }
        QComboBox QAbstractItemView { background: #1e293b; color: #e2e8f0; }
        QTableWidget { background: #020617; color: #cbd5e1; gridline-color: #1e293b;
                       border: 1px solid #1e293b; border-radius: 8px; font-size: 12px; }
        QTableWidget::item:selected { background: #1d4ed8; color: white; }
        QHeaderView::section { background: #1e293b; color: #94a3b8; padding: 6px;
                               border: none; font-weight: bold; font-size: 11px; }
        QPushButton { border-radius: 8px; font-weight: bold; font-size: 12px; padding: 7px 16px; }
        QPushButton#btnDel    { background: #b45309; color: white; }
        QPushButton#btnDel:hover    { background: #f59e0b; }
        QPushButton#btnDelAll { background: #7f1d1d; color: white; }
        QPushButton#btnDelAll:hover { background: #ef4444; }
        QPushButton#btnRef    { background: #1e3a5f; color: white; }
        QPushButton#btnRef:hover    { background: #2563eb; }
        QPushButton#btnClose  { background: #1e293b; color: #94a3b8; }
        QPushButton#btnClose:hover  { background: #334155; }
        QLabel#lblInfo { color: #64748b; font-size: 11px; }
        QLabel#lblWarn { color: #f87171; font-size: 11px; font-weight: bold; }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrador de Días Contables")
        self.setMinimumSize(820, 560)
        self.resize(900, 620)
        self.setModal(True)
        self.setStyleSheet(self.STYLE)
        self._conn = None
        self._build_ui()
        self._connect_db()

    # ── UI ───────────────────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Title
        title = QLabel("🗂  Administrador de Días Contables")
        title.setStyleSheet("font-size:17px; font-weight:bold; color:#f1f5f9;")
        lay.addWidget(title)

        warn = QLabel("⚠️  Las eliminaciones son permanentes. El sync puede restaurar datos desde el POS local.")
        warn.setObjectName("lblWarn")
        warn.setWordWrap(True)
        lay.addWidget(warn)

        # Restaurant selector row
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Restaurante:"))
        self.cbo_rest = QComboBox()
        self.cbo_rest.currentTextChanged.connect(self._load_days)
        sel_row.addWidget(self.cbo_rest)
        sel_row.addStretch()
        self.lbl_total = QLabel("")
        self.lbl_total.setObjectName("lblInfo")
        sel_row.addWidget(self.lbl_total)
        lay.addLayout(sel_row)

        # Table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(['Fecha', 'Día', 'Net Sales', '# Ventas', '# KPI'])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setSortingEnabled(True)
        lay.addWidget(self.tbl, stretch=1)

        # Info
        info = QLabel("Ctrl+Click o Shift+Click para seleccionar múltiples fechas.")
        info.setObjectName("lblInfo")
        lay.addWidget(info)

        # Button row
        btn_row = QHBoxLayout()

        btn_ref = QPushButton("🔄 Actualizar")
        btn_ref.setObjectName("btnRef")
        btn_ref.clicked.connect(self._refresh)
        btn_row.addWidget(btn_ref)

        btn_row.addStretch()

        self.btn_del = QPushButton("🗑  Eliminar Días Seleccionados")
        self.btn_del.setObjectName("btnDel")
        self.btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.btn_del)

        self.btn_del_all = QPushButton("💣 Eliminar TODO del Restaurante")
        self.btn_del_all.setObjectName("btnDelAll")
        self.btn_del_all.clicked.connect(self._delete_all)
        btn_row.addWidget(self.btn_del_all)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)

        lay.addLayout(btn_row)

    # ── DB ───────────────────────────────────────────────────────────
    def _connect_db(self):
        try:
            cfg = load_config()
            self._conn = mysql.connector.connect(
                host=cfg['remote_db_host'], user=cfg['remote_db_user'],
                password=cfg['remote_db_pass'], database=cfg['remote_db_name'],
                use_pure=True
            )
            self._load_restaurants()
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión",
                f"No se pudo conectar a MariaDB:\n{e}")

    def _load_restaurants(self):
        if not self._conn:
            return
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT DISTINCT restaurante FROM restaurantes_diario_media ORDER BY restaurante")
            rests = [r[0] for r in cur.fetchall()]
            self.cbo_rest.blockSignals(True)
            self.cbo_rest.clear()
            self.cbo_rest.addItems(rests)
            self.cbo_rest.blockSignals(False)
            if rests:
                self._load_days(rests[0])
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _load_days(self, restaurante):
        if not self._conn or not restaurante:
            return
        try:
            self._conn.reconnect()
            cur = self._conn.cursor()

            # Net sales + count ventas por fecha
            cur.execute("""
                SELECT dm.fecha,
                       COALESCE(dm.net_sales, 0) as net_sales,
                       COALESCE(v.cnt, 0)        as cnt_ventas,
                       COALESCE(k.cnt, 0)        as cnt_kpi
                FROM restaurantes_diario_media dm
                LEFT JOIN (
                    SELECT fecha, COUNT(*) as cnt FROM restaurantes_ventas
                    WHERE restaurante = %s GROUP BY fecha
                ) v ON v.fecha = dm.fecha
                LEFT JOIN (
                    SELECT fecha, COUNT(*) as cnt FROM restaurantes_kpi
                    WHERE restaurante = %s GROUP BY fecha
                ) k ON k.fecha = dm.fecha
                WHERE dm.restaurante = %s
                ORDER BY dm.fecha DESC
            """, (restaurante, restaurante, restaurante))
            rows = cur.fetchall()

            self.tbl.setSortingEnabled(False)
            self.tbl.setRowCount(0)
            total_ns = 0.0
            for fecha, net_sales, cnt_v, cnt_k in rows:
                r = self.tbl.rowCount()
                self.tbl.insertRow(r)
                fecha_str = str(fecha)
                day_en = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').strftime('%A')
                day_es = DAYS_ES.get(day_en, day_en)

                self.tbl.setItem(r, 0, QTableWidgetItem(fecha_str))
                day_item = QTableWidgetItem(day_es)
                # Color por día
                day_colors = {'Lunes':'#93c5fd','Martes':'#c4b5fd','Miércoles':'#86efac',
                              'Jueves':'#fdba74','Viernes':'#7dd3fc','Sábado':'#f9a8d4','Domingo':'#fca5a5'}
                day_item.setForeground(QColor(day_colors.get(day_es, '#e2e8f0')))
                self.tbl.setItem(r, 1, day_item)

                ns_item = QTableWidgetItem(f"${float(net_sales):,.2f}")
                ns_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                ns_item.setForeground(QColor('#4ade80'))
                self.tbl.setItem(r, 2, ns_item)

                cnt_v_item = QTableWidgetItem(str(cnt_v))
                cnt_v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl.setItem(r, 3, cnt_v_item)

                cnt_k_item = QTableWidgetItem(str(cnt_k))
                cnt_k_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl.setItem(r, 4, cnt_k_item)

                total_ns += float(net_sales)

            self.tbl.setSortingEnabled(True)
            self.lbl_total.setText(
                f"{len(rows)} días  |  Total Net Sales: ${total_ns:,.2f}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Error cargando días", str(e))

    def _refresh(self):
        self._load_days(self.cbo_rest.currentText())

    def _selected_dates(self):
        rows = self.tbl.selectionModel().selectedRows()
        return [self.tbl.item(r.row(), 0).text() for r in rows]

    # ── Delete selected days ─────────────────────────────────────────
    def _delete_selected(self):
        restaurante = self.cbo_rest.currentText()
        fechas = self._selected_dates()
        if not fechas:
            QMessageBox.information(self, "Sin selección",
                "Seleccione al menos un día en la tabla.")
            return

        # Confirmación 1 — lista de fechas
        lista = '\n'.join(f"  • {f}" for f in sorted(fechas))
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Eliminar los siguientes {len(fechas)} día(s) de\n"
            f"'{restaurante}'?\n\n{lista}\n\n"
            "Esta acción eliminará los registros de TODAS las tablas.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Confirmación 2 — escribir CONFIRMAR
        text, ok = QInputDialog.getText(
            self, "Segunda Confirmación",
            f"Escriba  CONFIRMAR  (en mayúsculas) para proceder:",
            QLineEdit.Normal, ""
        )
        if not ok or text.strip() != 'CONFIRMAR':
            QMessageBox.warning(self, "Cancelado",
                "Texto incorrecto. Operación cancelada.")
            return

        try:
            self._conn.reconnect()
            cur = self._conn.cursor()
            placeholders = ','.join(['%s'] * len(fechas))
            total_del = 0
            for tabla in TABLAS:
                try:
                    cur.execute(
                        f"DELETE FROM {tabla} WHERE restaurante=%s AND fecha IN ({placeholders})",
                        [restaurante] + fechas
                    )
                    total_del += cur.rowcount
                except Exception:
                    pass
            self._conn.commit()
            QMessageBox.information(
                self, "✅ Eliminado",
                f"Se eliminaron {total_del} registros de {len(fechas)} día(s).\n"
                "Puede sincronizar nuevamente desde el agente."
            )
            self._refresh()
        except Exception as e:
            self._conn.rollback()
            QMessageBox.critical(self, "Error", str(e))

    # ── Delete ALL for restaurant ────────────────────────────────────
    def _delete_all(self):
        restaurante = self.cbo_rest.currentText()
        if not restaurante:
            return

        # Confirmación 1
        reply = QMessageBox.critical(
            self, "⚠️  ADVERTENCIA CRÍTICA",
            f"Está a punto de ELIMINAR TODOS LOS DATOS del restaurante:\n\n"
            f"   '{restaurante}'\n\n"
            "Esto borrará todos los días contables de todas las tablas.\n"
            "¿Desea continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Confirmación 2 — nombre del restaurante
        text2, ok2 = QInputDialog.getText(
            self, "Confirmación — Nombre del Restaurante",
            f"Escriba exactamente el nombre del restaurante para confirmar:\n'{restaurante}'",
            QLineEdit.Normal, ""
        )
        if not ok2 or text2.strip() != restaurante:
            QMessageBox.warning(self, "Cancelado",
                "El nombre no coincide. Operación cancelada.")
            return

        # Confirmación 3 — ELIMINAR TODO
        text3, ok3 = QInputDialog.getText(
            self, "Confirmación Final",
            "Escriba  ELIMINAR TODO  para confirmar la eliminación total:",
            QLineEdit.Normal, ""
        )
        if not ok3 or text3.strip() != 'ELIMINAR TODO':
            QMessageBox.warning(self, "Cancelado",
                "Texto incorrecto. Operación cancelada.")
            return

        try:
            self._conn.reconnect()
            cur = self._conn.cursor()
            total_del = 0
            for tabla in TABLAS:
                try:
                    cur.execute(f"DELETE FROM {tabla} WHERE restaurante=%s", (restaurante,))
                    total_del += cur.rowcount
                except Exception:
                    pass
            self._conn.commit()
            QMessageBox.information(
                self, "✅ Eliminado",
                f"Se eliminaron {total_del} registros de '{restaurante}'.\n"
                "Puede re-sincronizar desde el agente."
            )
            self._load_restaurants()
        except Exception as e:
            self._conn.rollback()
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        event.accept()


# ──────────────────────────────────────────────────────────────────
#  Ventana principal
# ──────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, tray):
        super().__init__()
        self.tray    = tray
        self.worker  = None
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(620, 480)
        self.resize(700, 520)
        self._build_ui()
        self._setup_logging()
        self._start_worker()

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0f172a; color: #e2e8f0; font-family: 'Segoe UI'; }
            QTextEdit  { background: #020617; color: #94a3b8; border: 1px solid #1e293b;
                         border-radius: 8px; font-family: 'Consolas', monospace; font-size: 12px; padding: 6px; }
            QPushButton { border-radius: 8px; font-weight: bold; font-size: 13px; padding: 8px 20px; }
            QPushButton#btnPause  { background: #ca8a04; color: white; }
            QPushButton#btnPause:hover { background: #eab308; }
            QPushButton#btnResume { background: #16a34a; color: white; }
            QPushButton#btnResume:hover { background: #22c55e; }
            QPushButton#btnForce { background: #0284c7; color: white; }
            QPushButton#btnForce:hover { background: #0369a1; }
            QPushButton#btnLog    { background: #1e40af; color: white; }
            QPushButton#btnLog:hover { background: #2563eb; }
            QPushButton#btnExit   { background: #7f1d1d; color: white; }
            QPushButton#btnExit:hover { background: #ef4444; }
            QLabel#statusLabel { font-size: 13px; font-weight: bold; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QFrame()
        header.setStyleSheet("background: #1e293b; border-radius: 12px;")
        header_layout = QHBoxLayout(header)
        title = QLabel("🔄  Agente DB Sync")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9;")
        subtitle = QLabel("POS POS → MariaDB Cloud")
        subtitle.setStyleSheet("font-size: 11px; color: #64748b;")
        title_block = QVBoxLayout()
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch()
        layout.addWidget(header)

        # Status bar
        status_bar = QFrame()
        status_bar.setStyleSheet("background: #0f172a;")
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel("⏳ Iniciando…")
        self.status_label.setObjectName("statusLabel")
        sb_layout.addWidget(self.status_label)
        layout.addWidget(status_bar)

        # Log
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view, stretch=1)

        # Buttons Row 1
        btn_row1 = QHBoxLayout()
        self.btn_force = QPushButton("⚡ Sincronizar Ahora")
        self.btn_force.setObjectName("btnForce")
        self.btn_force.clicked.connect(self._force_sync)
        btn_row1.addWidget(self.btn_force)

        self.btn_pause = QPushButton("⏸  Pausar")
        self.btn_pause.setObjectName("btnPause")
        self.btn_pause.clicked.connect(self._toggle_pause)
        btn_row1.addWidget(self.btn_pause)

        btn_log = QPushButton("📄 Abrir Log")
        btn_log.setObjectName("btnLog")
        btn_log.clicked.connect(lambda: os.startfile(LOG_FILE) if os.path.exists(LOG_FILE) else None)
        btn_row1.addWidget(btn_log)
        btn_row1.addStretch()
        layout.addLayout(btn_row1)

        # Buttons Row 2
        btn_row2 = QHBoxLayout()
        btn_startup = QPushButton("🚀 Inicio con Windows")
        btn_startup.setObjectName("btnLog")
        btn_startup.clicked.connect(self._toggle_startup)
        btn_row2.addWidget(btn_startup)
        self.btn_startup = btn_startup

        btn_admin = QPushButton("🗂  Administrar Datos")
        btn_admin.setObjectName("btnLog")
        btn_admin.clicked.connect(self._open_admin)
        btn_row2.addWidget(btn_admin)

        btn_row2.addStretch()

        btn_exit = QPushButton("✖  Cerrar Programa")
        btn_exit.setObjectName("btnExit")
        btn_exit.clicked.connect(self._confirm_exit)
        btn_row2.addWidget(btn_exit)
        layout.addLayout(btn_row2)
        self._refresh_startup_label()

    def _setup_logging(self):
        logging.basicConfig(
            filename=LOG_FILE, level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _start_worker(self):
        self.worker = SyncWorker()
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._update_status)
        self.worker.start()
        
        cfg = load_config()
        id_sync = get_or_create_id_sync(cfg)
        self.hb_worker = HeartbeatWorker(cfg, id_sync, self.worker)
        self.hb_worker.start()

    def _toggle_pause(self):
        if not self.worker:
            return
        if self.worker.is_paused:
            self.worker.resume()
            self.btn_pause.setText("⏸  Pausar")
            self.btn_pause.setObjectName("btnPause")
            self.btn_pause.setStyleSheet("")
            self._refresh_style()
        else:
            self.worker.pause()
            self.btn_pause.setText("▶  Reanudar")
            self.btn_pause.setObjectName("btnResume")
            self._refresh_style()

    def _force_sync(self):
        if self.worker:
            self.worker.force_sync()

    def _refresh_style(self):
        self.btn_pause.style().unpolish(self.btn_pause)
        self.btn_pause.style().polish(self.btn_pause)

    def _append_log(self, msg, level):
        colors = {"info": "#94a3b8", "warning": "#fbbf24", "error": "#f87171"}
        color  = colors.get(level, "#94a3b8")
        ts     = datetime.datetime.now().strftime("%H:%M:%S")
        html   = f'<span style="color:#475569">[{ts}]</span> <span style="color:{color}">{msg}</span><br>'
        self.log_view.moveCursor(QTextCursor.End)
        self.log_view.insertHtml(html)
        self.log_view.moveCursor(QTextCursor.End)

    def _update_status(self, text, icon_color):
        color_map = {ICON_GREEN:"#22c55e", ICON_YELLOW:"#eab308",
                     ICON_RED:"#ef4444",   ICON_GRAY:"#64748b"}
        c = color_map.get(icon_color, "#94a3b8")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size:13px; font-weight:bold; color:{c};")
        self.tray.setIcon(make_tray_icon(icon_color))
        self.tray.setToolTip(f"{APP_NAME} — {text}")

    # ── Startup with Windows ────────────────────────────────────────
    def _is_startup_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _toggle_startup(self):
        if self._is_startup_enabled():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG, 0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, APP_NAME)
                winreg.CloseKey(key)
                self._append_log("Eliminado del inicio de Windows.", "warning")
            except Exception as e:
                self._append_log(f"Error al eliminar del inicio: {e}", "error")
        else:
            try:
                exe_path = sys.executable if not getattr(sys,'frozen',False) else sys.executable
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG, 0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
                self._append_log("✅ Registrado para iniciar con Windows.", "info")
            except Exception as e:
                self._append_log(f"Error al registrar inicio: {e}", "error")
        self._refresh_startup_label()

    def _refresh_startup_label(self):
        if self._is_startup_enabled():
            self.btn_startup.setText("🚀 Inicio con Windows ✅")
        else:
            self.btn_startup.setText("🚀 Inicio con Windows")

    # ── Ventana → bandeja al presionar X ───────────────────────────
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            APP_NAME,
            "El agente sigue corriendo en la bandeja del sistema.",
            QSystemTrayIcon.Information, 3000
        )

    def _open_admin(self):
        dlg = AdminDialog(self)
        dlg.exec_()

    def _confirm_exit(self):
        reply = QMessageBox.question(
            self, "Cerrar Agente",
            "¿Deseas detener la sincronización y cerrar el programa?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.worker:
                self.worker.stop()
                self.worker.wait(3000)
            try:
                if hasattr(self, 'hb_worker') and self.hb_worker:
                    self.hb_worker.stop()
                    self.hb_worker.wait(1000)
            except Exception:
                pass
            QApplication.quit()


# ──────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)

    # Tray icon
    tray = QSystemTrayIcon()
    tray.setIcon(make_tray_icon(ICON_GRAY))
    tray.setToolTip(APP_NAME)

    # Main window
    win = MainWindow(tray)

    # Tray menu
    menu = QMenu()
    act_show   = QAction("📋 Mostrar / Ocultar")
    act_pause  = QAction("⏸  Pausar Sync")
    act_log    = QAction("📄 Abrir Log")
    act_exit   = QAction("✖  Cerrar Programa")

    act_show.triggered.connect(lambda: win.show() if win.isHidden() else win.hide())
    act_admin  = QAction("🗂  Administrar Datos")
    act_pause.triggered.connect(win._toggle_pause)
    act_admin.triggered.connect(lambda: (win.show(), AdminDialog(win).exec_()))
    act_log.triggered.connect(lambda: os.startfile(LOG_FILE) if os.path.exists(LOG_FILE) else None)
    act_exit.triggered.connect(win._confirm_exit)

    menu.addAction(act_show)
    menu.addSeparator()
    menu.addAction(act_pause)
    menu.addAction(act_admin)
    menu.addAction(act_log)
    menu.addSeparator()
    menu.addAction(act_exit)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: win.show() if reason == QSystemTrayIcon.DoubleClick else None)
    tray.show()

    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
