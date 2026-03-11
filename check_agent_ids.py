import pymysql

conn = pymysql.connect(
    host='hawk200.startdedicated.com',
    user='recetas',
    password='gcode2025!',
    db='Recetas',
    cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cursor:
    cursor.execute("SELECT id_sync FROM sync_agents;")
    results = cursor.fetchall()
    for row in results:
        print(row)

conn.close()
