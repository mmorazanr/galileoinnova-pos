import mysql.connector, json
cfg=json.load(open('c:/ICOM/Database/config.json'))
conn=mysql.connector.connect(host=cfg['remote_db_host'], user=cfg['remote_db_user'], password=cfg['remote_db_pass'], database=cfg['remote_db_name'], use_pure=True)
c=conn.cursor()
c.execute("SELECT id_sync, fecha_ciclo, detalle FROM agent_sync_history WHERE detalle LIKE '%2026-03-28%' ORDER BY fecha_ciclo DESC LIMIT 10")
for r in c.fetchall():
    print(r)
