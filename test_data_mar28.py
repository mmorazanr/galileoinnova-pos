import mysql.connector, json
cfg=json.load(open('c:/ICOM/Database/config.json'))
conn=mysql.connector.connect(host=cfg['remote_db_host'], user=cfg['remote_db_user'], password=cfg['remote_db_pass'], database=cfg['remote_db_name'])
c=conn.cursor()
c.execute("SELECT restaurante, id_sync FROM sync_agents")
for r in c.fetchall():
    print('AGENT:', r[0], 'ID:', r[1])
c.execute("SELECT restaurante, net_sales FROM restaurantes_diario_media WHERE fecha='2026-03-28'")
print('--- DIARIO MEDIA 2026-03-28 ---')
for r in c.fetchall():
    print(r)
