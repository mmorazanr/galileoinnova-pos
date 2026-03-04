import mysql.connector

def create_remote_tables():
    conn = mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )
    cursor = conn.cursor()

    # Tabla principal para recolectar datos a nivel transaccional
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurantes_ventas (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        restaurante VARCHAR(150),
        transaccion_id BIGINT,
        fecha DATE,
        hora TIME,
        mesero VARCHAR(100),
        categoria VARCHAR(100),
        platillo VARCHAR(150),
        cantidad FLOAT,
        monto_venta DECIMAL(10,2),
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY idx_trans_plat (restaurante, transaccion_id, platillo, hora)
    );
    """)

    # Tabla para llevar el control de la última fecha sincronizada por sucursal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurantes_sync_status (
        restaurante VARCHAR(150) PRIMARY KEY,
        ultima_fecha_sincronizada DATETIME,
        estado VARCHAR(50)
    );
    """)

    conn.commit()
    print("Tablas 'restaurantes_ventas' y 'restaurantes_sync_status' creadas exitosamente en la base de datos MariaDB (Recetas).")
    conn.close()

if __name__ == "__main__":
    create_remote_tables()
