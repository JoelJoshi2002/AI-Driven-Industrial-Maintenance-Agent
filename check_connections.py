import mysql.connector
import chromadb
import sys

def check_sql():
    print("1. Testing SQL Connection (MariaDB)...", end=" ")
    try:
        conn = mysql.connector.connect(
            host="localhost", 
            user="user", 
            password="industrial_secret_password",
            database="industrial_db",
            port=3306
        )
        if conn.is_connected():
            print("✅ SUCCESS!")
            conn.close()
            return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def check_vector():
    print("2. Testing Vector Connection (ChromaDB)...", end=" ")
    try:
        # The new client connection method
        chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        
        # New "Health Check": Try to get the version or list collections
        version = chroma_client.get_version()
        print(f"✅ SUCCESS! (v{version})")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    print("--- INFRASTRUCTURE DIAGNOSTIC ---")
    sql = check_sql()
    vec = check_vector()
    
    if sql and vec:
        print("\n🎉 GREAT SUCCESS! Your Data Center is live.")
    else:
        print("\n⚠️  ISSUES FOUND. Is Docker running?")