#!/usr/bin/env python3
"""
PostgreSQL Connection Test for ELMA Group
Test database connectivity before deploying to production
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError

def test_database_connection():
    """Test PostgreSQL database connection"""
    
    print("🗄️ ELMA Group PostgreSQL Connection Test")
    print("=" * 50)
    
    # Database configuration from environment variables
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'elmagroup_db'),
        'user': os.environ.get('DB_USER', 'elmagroup'),
        'password': os.environ.get('DB_PASSWORD', 'ElmaGroup2024!Secure'),
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    print(f"🔗 Testing connection to:")
    print(f"   Host: {db_config['host']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    print(f"   Port: {db_config['port']}")
    print()
    
    try:
        # Attempt connection
        print("📡 Connecting to PostgreSQL...")
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        # Test basic functionality
        print("✅ Connection successful!")
        
        # Get PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"📊 PostgreSQL Version: {version.split()[0]} {version.split()[1]}")
        
        # Test database permissions
        cursor.execute("SELECT current_database(), current_user, session_user;")
        db_info = cursor.fetchone()
        print(f"🗄️ Current Database: {db_info[0]}")
        print(f"👤 Current User: {db_info[1]}")
        print(f"🔐 Session User: {db_info[2]}")
        
        # Test table creation permissions
        print("\n🔧 Testing table creation permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_message VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO connection_test (test_message) 
            VALUES ('ELMA Group connection test successful!');
        """)
        
        # Read test data
        cursor.execute("SELECT * FROM connection_test ORDER BY created_at DESC LIMIT 1;")
        test_record = cursor.fetchone()
        print(f"✅ Test record created: ID={test_record[0]}, Message='{test_record[1]}'")
        
        # Clean up test table
        cursor.execute("DROP TABLE IF EXISTS connection_test;")
        connection.commit()
        print("🧹 Test table cleaned up")
        
        # Test SSL connection (for production)
        cursor.execute("SHOW ssl;")
        ssl_status = cursor.fetchone()[0]
        print(f"🔒 SSL Status: {ssl_status}")
        
        connection.close()
        print("\n🎉 All database tests passed!")
        print("🚀 Your PostgreSQL database is ready for ELMA Group!")
        
        return True
        
    except OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify host, port, database name")
        print("3. Confirm username and password")
        print("4. Check firewall/security group settings")
        print("5. Ensure SSL requirements are met")
        return False
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def print_connection_examples():
    """Print connection string examples for different hosting options"""
    
    print("\n📋 PostgreSQL Connection Examples:")
    print("=" * 50)
    
    print("\n🏆 AWS RDS PostgreSQL:")
    print("export DB_HOST='elmagroup-production.xxx.us-east-1.rds.amazonaws.com'")
    print("export DB_NAME='elmagroup_db'")
    print("export DB_USER='elmagroup'")
    print("export DB_PASSWORD='your-secure-password'")
    print("export DB_PORT='5432'")
    
    print("\n🥈 DigitalOcean Managed PostgreSQL:")
    print("export DB_HOST='elmagroup-db-do-user-xxx.db.ondigitalocean.com'")
    print("export DB_NAME='elmagroup_db'")
    print("export DB_USER='elmagroup'")
    print("export DB_PASSWORD='your-auto-generated-password'")
    print("export DB_PORT='25060'")
    
    print("\n🥉 Self-Managed PostgreSQL on EC2:")
    print("export DB_HOST='your-ec2-ip-address'")
    print("export DB_NAME='elmagroup_db'")
    print("export DB_USER='elmagroup'")
    print("export DB_PASSWORD='your-chosen-password'")
    print("export DB_PORT='5432'")

if __name__ == "__main__":
    print("🏢 ELMA Group PostgreSQL Database Connection Test")
    print("=" * 60)
    print("This script tests your PostgreSQL database connection")
    print("and verifies it's ready for production deployment.")
    print()
    
    # Check if environment variables are set
    required_env = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_env = [var for var in required_env if not os.environ.get(var)]
    
    if missing_env:
        print("⚠️ Missing environment variables:")
        for var in missing_env:
            print(f"   - {var}")
        print()
        print_connection_examples()
        print()
        print("Set these variables and run the test again.")
        
        response = input("\nContinue with localhost defaults for testing? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run the connection test
    success = test_database_connection()
    
    if success:
        print("\n✅ Database is ready for ELMA Group production deployment!")
        sys.exit(0)
    else:
        print("\n❌ Database connection failed. Please fix the issues and try again.")
        sys.exit(1)
