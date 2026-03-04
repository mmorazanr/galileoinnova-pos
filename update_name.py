import mysql.connector

try:
    conn = mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )
    cursor = conn.cursor()
    cursor.execute("UPDATE restaurantes_ventas SET restaurante = 'The Lazy Donkey Restaurant' WHERE restaurante LIKE '%The Lazy Donkey Sur%'")
    cursor.execute("UPDATE restaurantes_sync_status SET restaurante = 'The Lazy Donkey Restaurant' WHERE restaurante LIKE '%The Lazy Donkey Sur%'")
    conn.commit()
    print("Database renamed to 'The Lazy Donkey Restaurant'.")
    conn.close()
except Exception as e:
    print("Error:", e)
