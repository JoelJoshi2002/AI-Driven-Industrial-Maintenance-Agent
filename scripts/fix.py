import sys
import os
from sqlalchemy import text

# 1. Add the parent directory (root folder) to Python's path
# This allows us to import 'database.connection'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Now the import will work
from database.connection import engine

def add_missing_column():
    print("🔧 Attempting to add 'location' column to 'machines' table...")
    try:
        with engine.connect() as conn:
            # Use raw SQL to add the column safely
            conn.execute(text("ALTER TABLE machines ADD COLUMN location VARCHAR(255) NULL;"))
            conn.commit()
        print("✅ SUCCESS: Column 'location' added successfully!")
    except Exception as e:
        # If the column already exists, this catches the error
        print(f"⚠️  Note: {e}")

if __name__ == "__main__":
    add_missing_column()