import os

path = r'c:\ICOM\Database\agente_sync_tray.pyw'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
if 'RotatingFileHandler' not in code:
    code = code.replace(
        'import logging\n',
        'import logging\nimport socket\nimport hashlib\nfrom logging.handlers import RotatingFileHandler\nAGENT_VERSION = "2.2-Tray"\n'
    )

# 2. Logger Setup & Helpers
logger_setup = """
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
"""

if 'RotatingFileHandler(' not in code:
    code = code.replace(
        'LOG_FILE = os.path.join(BASE, "agente_sync.log")\n',
        'LOG_FILE = os.path.join(BASE, "agente_sync.log")\n' + logger_setup
    )

# 3. Replace getattr usage
code = code.replace('getattr(logging, level, logging.info)(msg)', 'getattr(logger, level, logger.info)(msg)')

# 4. Heartbeat Worker (inserted before SyncWorker)
heartbeat_code = """
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

                cur.execute(\"\"\"
                    INSERT INTO sync_agents (id_sync, restaurante, ip_lan, db_path, status, last_heartbeat, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        restaurante    = VALUES(restaurante),
                        ip_lan         = VALUES(ip_lan),
                        db_path        = VALUES(db_path),
                        status         = VALUES(status),
                        last_heartbeat = VALUES(last_heartbeat),
                        version        = VALUES(version)
                \"\"\", (self.id_sync, self.cfg.get('restaurant_name','Unknown'), ip, self.cfg.get('local_db_path',''), status_str, now, AGENT_VERSION))
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
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")

            for _ in range(60):
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
        elif cmd == "restart":
            import os
            os._exit(0)

"""

if 'class HeartbeatWorker' not in code:
    code = code.replace('class SyncWorker(QThread):', heartbeat_code + 'class SyncWorker(QThread):')

# 5. Starting the heartbeat from MainWindow
setup_heartbeat = """
        self.worker.start()
        
        cfg = load_config()
        id_sync = get_or_create_id_sync(cfg)
        self.hb_worker = HeartbeatWorker(cfg, id_sync, self.worker)
        self.hb_worker.start()
"""

# Find _start_worker exactly:
orig_start = """    def _start_worker(self):
        self.worker = SyncWorker()
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._update_status)
        self.worker.start()"""

new_start = """    def _start_worker(self):
        self.worker = SyncWorker()
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._update_status)
        self.worker.start()
        
        cfg = load_config()
        id_sync = get_or_create_id_sync(cfg)
        self.hb_worker = HeartbeatWorker(cfg, id_sync, self.worker)
        self.hb_worker.start()"""

if orig_start in code:
    code = code.replace(orig_start, new_start)

# 6. Stop logic
orig_stop = """        if reply == QMessageBox.Yes:
            if self.worker:
                self.worker.stop()
                self.worker.wait(3000)
            QApplication.quit()"""

new_stop = """        if reply == QMessageBox.Yes:
            if self.worker:
                self.worker.stop()
                self.worker.wait(3000)
            try:
                if hasattr(self, 'hb_worker') and self.hb_worker:
                    self.hb_worker.stop()
                    self.hb_worker.wait(1000)
            except Exception:
                pass
            QApplication.quit()"""

if orig_stop in code:
    code = code.replace(orig_stop, new_stop)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Patching Complete.")
