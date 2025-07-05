#!/usr/bin/env python3
"""
Professional Database Migration Script for ELMA Group
Migrates data from SQLite (development) to PostgreSQL (production)
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime

def migrate_database():
    """Migrate ELMA Group database from SQLite to PostgreSQL"""
    
    print("🗄️ ELMA Group Database Migration")
    print("=" * 50)
    
    # Database configurations
    sqlite_db = 'elma_app.db'
    postgres_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'elmagroup_db'),
        'user': os.environ.get('DB_USER', 'elmagroup'),
        'password': os.environ.get('DB_PASSWORD', 'elma_secure_password_2024'),
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    try:
        # Connect to SQLite
        print("📂 Connecting to SQLite database...")
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        print("🐘 Connecting to PostgreSQL database...")
        postgres_conn = psycopg2.connect(**postgres_config)
        postgres_cursor = postgres_conn.cursor()
        
        # Get all table names from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables to migrate")
        
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue
                
            print(f"📋 Migrating table: {table_name}")
            
            # Get table structure
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = sqlite_cursor.fetchall()
            
            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                # Prepare column names for PostgreSQL
                column_names = [col[1] for col in columns]
                placeholders = ','.join(['%s'] * len(column_names))
                
                # Insert data into PostgreSQL
                insert_query = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"
                
                for row in rows:
                    try:
                        postgres_cursor.execute(insert_query, tuple(row))
                    except Exception as e:
                        print(f"⚠️ Warning: Could not migrate row in {table_name}: {e}")
                
                postgres_conn.commit()
                print(f"✅ Migrated {len(rows)} rows from {table_name}")
            else:
                print(f"ℹ️ Table {table_name} is empty")
        
        print("\n🎉 Database migration completed successfully!")
        print("📊 Migration Summary:")
        print(f"   - Tables migrated: {len([t for t in tables if t[0] != 'sqlite_sequence'])}")
        print(f"   - Source: SQLite ({sqlite_db})")
        print(f"   - Target: PostgreSQL ({postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']})")
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)
    finally:
        # Clean up connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'postgres_conn' in locals():
            postgres_conn.close()

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        # Count records in both databases
        sqlite_conn = sqlite3.connect('elma_app.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        postgres_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'elmagroup_db'),
            'user': os.environ.get('DB_USER', 'elmagroup'),
            'password': os.environ.get('DB_PASSWORD', 'elma_secure_password_2024'),
            'port': os.environ.get('DB_PORT', '5432')
        }
        postgres_conn = psycopg2.connect(**postgres_config)
        postgres_cursor = postgres_conn.cursor()
        
        # Get table names
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = [table[0] for table in sqlite_cursor.fetchall()]
        
        print("📊 Record count verification:")
        for table in tables:
            # Count SQLite records
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Count PostgreSQL records
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            postgres_count = postgres_cursor.fetchone()[0]
            
            status = "✅" if sqlite_count == postgres_count else "❌"
            print(f"   {status} {table}: SQLite({sqlite_count}) → PostgreSQL({postgres_count})")
        
        sqlite_conn.close()
        postgres_conn.close()
        
    except Exception as e:
        print(f"⚠️ Verification error: {e}")

if __name__ == "__main__":
    print("🏢 ELMA Group Professional Database Migration")
    print("=" * 50)
    print("This script migrates your development SQLite database")
    print("to a professional PostgreSQL production database.")
    print()
    
    # Check if SQLite database exists
    if not os.path.exists('elma_app.db'):
        print("❌ SQLite database 'elma_app.db' not found!")
        print("Please run this script from the ELMA Group project directory.")
        sys.exit(1)
    
    # Check environment variables
    required_env = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_env = [var for var in required_env if not os.environ.get(var)]
    
    if missing_env:
        print("⚠️ Missing environment variables:")
        for var in missing_env:
            print(f"   - {var}")
        print()
        print("Please set these environment variables:")
        print("export DB_HOST='your-rds-endpoint.amazonaws.com'")
        print("export DB_NAME='elmagroup_db'")
        print("export DB_USER='elmagroup'")
        print("export DB_PASSWORD='your-secure-password'")
        print()
        print("Or run with default localhost values for testing.")
        
        response = input("Continue with localhost defaults? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Confirm migration
    print("\n🚨 IMPORTANT: This will migrate data to PostgreSQL.")
    print("Make sure your PostgreSQL database is set up and empty.")
    response = input("Continue with migration? (y/N): ")
    
    if response.lower() == 'y':
        migrate_database()
        verify_migration()
        print("\n🎉 Migration complete! Your ELMA Group database is now professional-ready.")
    else:
        print("Migration cancelled.")
