import mysql.connector
import csv
import random
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION
# ==========================================
CSV_PATH = "data/real_sensors.csv"
DB_CONFIG = {
    'host': 'localhost',
    'user': 'user',
    'password': 'industrial_secret_password',
    'database': 'industrial_db',
    'port': 3306
}

def import_csv():
    print(f"📂 Reading real data from {CSV_PATH}...")
    
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Open the CSV file
        # encoding='utf-8-sig' handles BOM if present in Excel-saved CSVs
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader) # Skip Header Row
            
            data_to_insert = []
            
            # Start simulation 30 days ago
            base_time = datetime.now() - timedelta(days=30)
            
            print("   Processing rows...", end=" ")
            
            # Process rows
            for i, row in enumerate(reader):
                # Limit to 5000 rows for speed (The full dataset is 10k)
                if i >= 5000: break 
                
                # --- 1. ASSIGN TO MACHINE ---
                # Randomly assign this data point to one of your 10 printers
                machine_id = random.randint(1, 10)
                
                # --- 2. CREATE TIMESTAMP ---
                # Increment time by 5 minutes for each row to create a timeline
                timestamp = base_time + timedelta(minutes=i*5)
                
                # --- 3. PARSE SENSOR DATA ---
                # AI4I Dataset Column Mapping:
                # [3] Air Temp, [4] Process Temp, [5] RPM, [6] Torque, [7] Tool Wear, [8] Target
                air_temp = float(row[3])
                proc_temp = float(row[4])
                rpm = int(row[5])
                torque = float(row[6])
                wear = int(row[7])
                target = int(row[8]) # 0 = No Failure, 1 = Failure
                
                # --- 4. DETERMINE FAILURE TYPE ---
                # The dataset has binary columns for specific failures:
                # [9]TWF, [10]HDF, [11]PWF, [12]OSF, [13]RNF
                failure_type = "Normal"
                
                if target == 1:
                    if int(row[9]) == 1: failure_type = "Tool Wear Failure (TWF)"
                    elif int(row[10]) == 1: failure_type = "Heat Dissipation Failure (HDF)"
                    elif int(row[11]) == 1: failure_type = "Power Failure (PWF)"
                    elif int(row[12]) == 1: failure_type = "Overstrain Failure (OSF)"
                    elif int(row[13]) == 1: failure_type = "Random Failure (RNF)"
                    else: failure_type = "Unknown Failure"

                # Add to batch
                data_to_insert.append((
                    machine_id, timestamp, air_temp, proc_temp, rpm, torque, wear, target, failure_type
                ))

        # --- 5. BULK INSERT ---
        print(f"\n   💾 Inserting {len(data_to_insert)} records into SQL...")
        
        query = """
        INSERT INTO sensor_logs 
        (machine_id, timestamp, air_temp_k, process_temp_k, rpm, torque_nm, tool_wear_min, target, failure_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(query, data_to_insert)
        conn.commit()
        print(f"✅ SUCCESS: Imported {len(data_to_insert)} real-world sensor logs across 10 machines.")

    except FileNotFoundError:
        print(f"\n❌ ERROR: Could not find '{CSV_PATH}'.")
        print("   -> Did you download the AI4I CSV and rename it to 'real_sensors.csv'?")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    import_csv()