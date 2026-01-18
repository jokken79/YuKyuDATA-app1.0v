import sqlite3
import pandas as pd

def inspect_data():
    conn = sqlite3.connect('yukyu.db')
    cursor = conn.cursor()

    print("--- COUNTS ---")
    rows = cursor.execute("SELECT COUNT(*) FROM employees").fetchone()
    print(f"Employees Table (Yukyu Data): {rows[0]}")

    rows = cursor.execute("SELECT COUNT(*) FROM genzai").fetchone()
    print(f"Genzai Table (Haken): {rows[0]}")

    rows = cursor.execute("SELECT COUNT(*) FROM ukeoi").fetchone()
    print(f"Ukeoi Table (Contract): {rows[0]}")
    
    rows = cursor.execute("SELECT COUNT(*) FROM staff").fetchone()
    print(f"Staff Table: {rows[0]}")

    print("\n--- SAMPLE ENHANCED DATA ---")
    # Simulate the query used in get_employees_enhanced
    query = '''
        SELECT 
            e.employee_num, 
            e.name,
            CASE 
                WHEN g.id IS NOT NULL THEN 'genzai'
                WHEN u.id IS NOT NULL THEN 'ukeoi'
                ELSE 'staff'
            END as calculated_type,
            g.id as genzai_id,
            u.id as ukeoi_id
        FROM employees e
        LEFT JOIN genzai g ON e.employee_num = g.employee_num
        LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
        LIMIT 10
    '''
    df = pd.read_sql_query(query, conn)
    print(df)
    
    print("\n--- DATA SAMPLES ---")
    print("Genzai Sample:")
    df_genzai = pd.read_sql_query("SELECT employee_num, name FROM genzai LIMIT 5", conn)
    print(df_genzai)
    
    print("Ukeoi Sample:")
    df_ukeoi = pd.read_sql_query("SELECT employee_num, name FROM ukeoi LIMIT 5", conn)
    print(df_ukeoi)

    conn.close()

if __name__ == "__main__":
    inspect_data()
