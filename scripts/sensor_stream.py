"""
Sensor Stream Simulator
Processes CSV data as "live" time-shifted events to simulate real-time IoT stream.
"""
import csv
import time
import random
import os
from datetime import datetime, timedelta
from typing import Optional
import mysql.connector
from sqlmodel import Session, select
from database.connection import engine
from database.models import SensorLog, Machine

# Configuration
CSV_PATH = "data/real_sensors.csv"
DB_CONFIG = {
    'host': 'localhost',
    'user': 'user',
    'password': 'industrial_secret_password',
    'database': 'industrial_db',
    'port': 3306
}

# Time-shifting configuration
TIME_ACCELERATION = 1.0  # 1.0 = real-time, 10.0 = 10x faster
BASE_TIME_OFFSET_DAYS = 30  # Start simulation from 30 days ago

def get_machine_ids() -> list:
    """Get all available machine IDs from database using ORM."""
    try:
        with Session(engine) as session:
            statement = select(Machine.id)
            results = session.exec(statement).all()
            return [r for r in results] if results else list(range(1, 11))
    except Exception as e:
        print(f"Warning: Could not fetch machine IDs: {e}")
        return list(range(1, 11))

def insert_sensor_log(machine_id: int, timestamp: datetime, air_temp: float, 
                      proc_temp: float, rpm: float, torque: float, 
                      tool_wear: float, target: int, failure_type: str):
    """Insert a sensor log entry into the database (Raw SQL for speed)."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        INSERT INTO sensor_logs 
        (machine_id, timestamp, air_temp_k, process_temp_k, rpm, torque_nm, tool_wear_min, target, failure_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            machine_id, timestamp, air_temp, proc_temp, rpm, torque, tool_wear, target, failure_type
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting log: {e}")
        return False

def stream_csv_data(speed_multiplier: float = 1.0, start_from: Optional[int] = None):
    # Locate CSV dynamically based on execution path
    # If run from root, it's data/real_sensor_data.csv
    if os.path.exists(CSV_PATH):
        csv_file = CSV_PATH
    elif os.path.exists(f"../{CSV_PATH}"):
        csv_file = f"../{CSV_PATH}"
    else:
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return
    
    print(f"📡 Starting Sensor Stream Simulation")
    print(f"   Source: {csv_file}")
    print(f"   Speed: {speed_multiplier}x real-time")

    machine_ids = get_machine_ids()
    base_time = datetime.now() - timedelta(days=BASE_TIME_OFFSET_DAYS)
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            # Fast-forward if requested
            if start_from:
                for _ in range(start_from):
                    try:
                        next(reader)
                    except StopIteration:
                        break
            
            row_count = start_from or 0
            
            for row in reader:
                row_count += 1
                try:
                    # AI4I Dataset Mapping:
                    # [3] Air Temp, [4] Process Temp, [5] RPM, [6] Torque, [7] Tool Wear, [8] Target
                    air_temp = float(row[3])
                    proc_temp = float(row[4])
                    rpm = int(row[5])
                    torque = float(row[6])
                    wear = int(row[7])
                    target = int(row[8])
                    
                    # Determine failure type string based on flags
                    failure_type = "Normal"
                    if target == 1:
                        if len(row) > 9 and int(row[9]) == 1: failure_type = "Tool Wear Failure (TWF)"
                        elif len(row) > 10 and int(row[10]) == 1: failure_type = "Heat Dissipation Failure (HDF)"
                        elif len(row) > 11 and int(row[11]) == 1: failure_type = "Power Failure (PWF)"
                        elif len(row) > 12 and int(row[12]) == 1: failure_type = "Overstrain Failure (OSF)"
                        elif len(row) > 13 and int(row[13]) == 1: failure_type = "Random Failure (RNF)"
                        else: failure_type = "Unknown Failure"
                    
                    machine_id = random.choice(machine_ids)
                    
                    # Shift time to "Now"
                    minutes_offset = row_count * 5
                    timestamp = base_time + timedelta(minutes=minutes_offset)
                    
                    success = insert_sensor_log(
                        machine_id, timestamp, air_temp, proc_temp, 
                        rpm, torque, wear, target, failure_type
                    )
                    
                    if success:
                        if row_count % 10 == 0:
                            status_icon = "🔥" if failure_type != "Normal" else "✓"
                            print(f"   {status_icon} Row {row_count}: M{machine_id} | Temp: {proc_temp:.1f}K | RPM: {rpm}")
                        
                        # Wait logic
                        time.sleep((5 * 60) / 1000) # Fast playback by default for testing
                        
                except Exception as e:
                    print(f"   ⚠️ Skipping row {row_count}: {e}")
                    continue

    except FileNotFoundError:
        print(f"❌ Error: Could not find '{csv_file}'")
    except KeyboardInterrupt:
        print("\n⏸️  Stream stopped.")

if __name__ == "__main__":
    stream_csv_data()