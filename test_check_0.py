import mysql.connector, json
cfg=json.load(open('c:/ICOM/Database/config.json'))
conn=mysql.connector.connect(host=cfg['remote_db_host'], user=cfg['remote_db_user'], password=cfg['remote_db_pass'], database=cfg['remote_db_name'], use_pure=True)
c=conn.cursor()
c.execute("SELECT COUNT(*) FROM restaurantes_diario_media WHERE restaurante='Little Mexico Bowdon' AND fecha='2026-03-28'")
print(c.fetchone()[0])
