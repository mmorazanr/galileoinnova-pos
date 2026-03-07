import mysql.connector
import bcrypt
import json

def get_db_connection():
    return mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Creando tabla dashboard_users...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dashboard_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('owner', 'manager') NOT NULL DEFAULT 'manager',
        allowed_restaurants LONGTEXT NOT NULL,
        can_view_days TINYINT(1) NOT NULL DEFAULT 0,
        can_delete_days TINYINT(1) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # Hash generator function mimicking PHP's password_hash(PASSWORD_DEFAULT)
    def hash_password(password):
        # bcrypt.hashpw returns bytes. We need a string to store in DB.
        # bcrypt format: $2b$12$... Note: PHP's default varies, usually $2y$ (which acts like 2b)
        # MySQL handles string inserts fine
        salt = bcrypt.gensalt(10) # 10 rounds is standard and fast enough
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    print("Insertando usuario 'admin' (Dueño)...")
    # Dueño: All restaurants, all permissions
    admin_hash = hash_password('gcode2025!')
    all_rests_json = json.dumps(["ALL"])
    
    cursor.execute("""
    INSERT INTO dashboard_users (username, password_hash, role, allowed_restaurants, can_view_days, can_delete_days)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        role=VALUES(role), allowed_restaurants=VALUES(allowed_restaurants),
        can_view_days=VALUES(can_view_days), can_delete_days=VALUES(can_delete_days),
        password_hash=VALUES(password_hash)
    """, ('admin', admin_hash, 'owner', all_rests_json, 1, 1))

    print("Insertando usuario 'test_manager' (Manager de prueba)...")
    # Manager: Solo un par de restaurantes, no puede borrar días.
    manager_hash = hash_password('manager123')
    manager_rests_json = json.dumps(["The Lazy Donkey Restaurant", "Lazy Donkey Downtown"])
    
    cursor.execute("""
    INSERT INTO dashboard_users (username, password_hash, role, allowed_restaurants, can_view_days, can_delete_days)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        role=VALUES(role), allowed_restaurants=VALUES(allowed_restaurants),
        can_view_days=VALUES(can_view_days), can_delete_days=VALUES(can_delete_days),
        password_hash=VALUES(password_hash)
    """, ('test_manager', manager_hash, 'manager', manager_rests_json, 1, 0))

    conn.commit()
    print("Usuarios creados exitosamente.")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    setup_database()
