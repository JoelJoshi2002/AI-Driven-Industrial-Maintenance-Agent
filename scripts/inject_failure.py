import mysql.connector
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': 'user',
    'password': 'industrial_secret_password',
    'database': 'industrial_db',
    'port': 3306
}

def break_machine():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Inject a "Heat Dissipation Failure" (HDF) for Machine 3 happening NOW
    # We set Process Temp to 450K (Very Hot) to make it realistic
    print("🔥 Sabotaging Machine 3...")
    query = """
    INSERT INTO sensor_logs 
    (machine_id, timestamp, air_temp_k, process_temp_k, rpm, torque_nm, tool_wear_min, target, failure_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = (8, datetime.now(), 310.5, 450.2, 1200, 60.5, 120, 1, "Heat Dissipation Failure")
    
    cursor.execute(query, values)
    conn.commit()
    print("✅ Machine 8 is now critically overheating!")
    
    conn.close()

if __name__ == "__main__":
    break_machine()