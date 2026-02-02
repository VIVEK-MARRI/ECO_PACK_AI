#!/usr/bin/env python3
"""
Test PostgreSQL database connection
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Get config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ecopackai'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'admin')
}

print("=" * 60)
print("PostgreSQL Connection Test")
print("=" * 60)
print(f"\nTesting connection with:")
print(f"  Host: {DB_CONFIG['host']}")
print(f"  Port: {DB_CONFIG['port']}")
print(f"  Database: {DB_CONFIG['database']}")
print(f"  User: {DB_CONFIG['user']}")
print(f"  Password: {'*' * len(DB_CONFIG['password'])}")

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("\n✓ SUCCESS: Connected to PostgreSQL!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ PostgreSQL Version: {version[0]}")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"\n✗ CONNECTION ERROR: {e}")
    print("\nPossible causes:")
    print("  1. PostgreSQL service is not running")
    print("  2. Wrong host/port")
    print("  3. Database doesn't exist")
    print("  4. User/password is incorrect")
    
except psycopg2.Error as e:
    print(f"\n✗ DATABASE ERROR: {e}")

except Exception as e:
    print(f"\n✗ ERROR: {e}")

print("\n" + "=" * 60)
