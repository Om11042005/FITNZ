import mysql.connector

# Database Configuration
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Apple@2310'  # Your MySQL password
}

def reset_database():
    """Completely reset the database - WARNING: DELETES ALL DATA!"""
    try:
        # Connect to MySQL Server
        print("🔌 Connecting to MySQL server...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 1. Drop the existing database
        print("🗑️  Deleting existing 'fitnz' database...")
        cursor.execute("DROP DATABASE IF EXISTS fitnz")
        
        # 2. Create a fresh database
        print("🆕 Creating fresh 'fitnz' database...")
        cursor.execute("CREATE DATABASE fitnz")
        
        print("✅ Database reset completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run: python main.py")
        print("2. Use these default login credentials:")
        print("   - Developer: username 'dev', password 'dev123'")
        print("   - Manager: username 'manager', password 'man123'") 
        print("   - Employee: username 'emp', password 'emp123'")
        print("   - Customer: username 'alice', password 'alice123'")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MySQL server is running")
        print("2. Check your MySQL password in both reset_db.py and database.py")
        print("3. Verify you have the correct host and user credentials")
        print("4. Ensure you have privileges to create/drop databases")

if __name__ == "__main__":
    print("🚀 FIT NZ Database Reset Utility")
    print("⚠️  WARNING: This will delete ALL existing data!")
    print("-" * 50)
    
    confirm = input("Type 'RESET' to confirm database reset: ")
    if confirm == "RESET":
        reset_database()
    else:
        print("❌ Reset cancelled.")
