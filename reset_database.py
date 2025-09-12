#!/usr/bin/env python
"""
Reset Database Script for Railway PostgreSQL
This script will DROP all tables and recreate them with fresh migrations
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings')
django.setup()

from django.db import connection

def reset_database():
    """Drop all tables and recreate database schema"""
    
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables to drop...")
        
        # Disable foreign key checks
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        
        # Drop all tables
        for table in tables:
            table_name = table[0]
            print(f"Dropping table: {table_name}")
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        
        print("All tables dropped successfully!")
        
        # Now run migrations
        from django.core.management import call_command
        print("\nRunning fresh migrations...")
        call_command('migrate', '--run-syncdb')
        
        print("\nDatabase reset complete!")

if __name__ == "__main__":
    # For Railway deployment, auto-confirm if RAILWAY_ENVIRONMENT is set
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("Running in Railway environment - auto-confirming database reset")
        reset_database()
    elif input("WARNING: This will DELETE ALL DATA in the database. Type 'yes' to continue: ") == 'yes':
        reset_database()
    else:
        print("Aborted.")