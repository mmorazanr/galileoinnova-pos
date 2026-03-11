import pymysql

conn = pymysql.connect(
    host='hawk200.startdedicated.com',
    user='recetas',
    password='gcode2025!',
    db='Recetas',
    cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM dashboard_users;")
    results = cursor.fetchall()
    for row in results:
        print(row)

conn.close()
