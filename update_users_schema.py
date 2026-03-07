import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='hawk200.startdedicated.com',
        user='recetas',
        password='gcode2025!',
        database='Recetas'
    )

def execute_migration():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Adding can_delete_admin_data to dashboard_users...")
    try:
        cursor.execute("ALTER TABLE dashboard_users ADD COLUMN can_delete_admin_data TINYINT(1) NOT NULL DEFAULT 0 AFTER can_delete_days;")
        print("Column successfully added.")
    except mysql.connector.errors.ProgrammingError as e:
        if "Duplicate column name" in str(e):
            print("Column 'can_delete_admin_data' already exists.")
        else:
            raise e

    # Update owner roles to have this permission by default just in case
    cursor.execute("UPDATE dashboard_users SET can_delete_admin_data = 1 WHERE role = 'owner'")
    print(f"Updated {cursor.rowcount} owner rows to have can_delete_admin_data = 1.")

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    execute_migration()
