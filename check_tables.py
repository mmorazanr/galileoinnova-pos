import mysql.connector

def check_schema(table_name):
    conn = mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    cols = cursor.fetchall()
    print(f"Esquema de {table_name}:")
    for c in cols:
        print(f" - {c[0]} ({c[1]})")
    conn.close()

if __name__ == '__main__':
    check_schema('users')
    check_schema('admin_users')
