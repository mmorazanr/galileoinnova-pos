import mysql.connector

# Conectamos a MariaDB Cloud
try:
    conn = mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )
    cur = conn.cursor()

    # Creación de la tabla `restaurantes_punches`
    cur.execute("""
    CREATE TABLE IF NOT EXISTS restaurantes_punches (
        id INT AUTO_INCREMENT PRIMARY KEY,
        restaurante VARCHAR(128) NOT NULL,
        punch_id INT NOT NULL, /* Para matchear exactamente con el PunchID local de Access */
        comtrex_empid INT NOT NULL,
        fecha DATE NOT NULL,
        hora_entrada DATETIME NOT NULL,
        hora_salida DATETIME NULL,
        cargo VARCHAR(64) NULL,
        clock_status INT NULL,
        UNIQUE KEY uq_punch (restaurante, punch_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()
    print("Tabla `restaurantes_punches` creada o ya existente.")

    # Verificando esquema creado
    cur.execute("DESCRIBE restaurantes_punches;")
    for row in cur.fetchall():
        print(row)

except Exception as e:
    print(f"Error al crear tabla: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()
