import mysql.connector, json
cfg=json.load(open('c:/ICOM/Database/config.json'))
conn=mysql.connector.connect(host=cfg['remote_db_host'], user=cfg['remote_db_user'], password=cfg['remote_db_pass'], database=cfg['remote_db_name'], use_pure=True)
c=conn.cursor()

sql = """
SELECT 
    d.fecha, d.restaurante, d.net_sales, k.total_tickets, p.meseros_count, p.total_horas
FROM restaurantes_diario_media d
LEFT JOIN restaurantes_kpi k ON d.restaurante = k.restaurante AND d.fecha = k.fecha
LEFT JOIN (
    SELECT 
        fecha, 
        restaurante, 
        COUNT(DISTINCT mesero) as meseros_count, 
        SUM(TIMESTAMPDIFF(MINUTE, hora_entrada, IFNULL(hora_salida, hora_entrada))) / 60.0 as total_horas 
    FROM restaurantes_punches 
    WHERE cargo = 'Server' OR cargo LIKE '%mesero%'
    GROUP BY fecha, restaurante
) p ON d.restaurante = p.restaurante AND d.fecha = p.fecha
WHERE d.fecha >= '2026-03-01' AND d.fecha <= '2026-03-29' 
ORDER BY d.fecha DESC, d.restaurante ASC LIMIT 5
"""
try:
    c.execute(sql)
    for r in c.fetchall():
        print(r)
except Exception as e:
    print(e)
