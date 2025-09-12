"""
Management command to completely reset the database.
This will DROP all tables and recreate them with fresh migrations.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Completely reset the database by dropping all tables and running fresh migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt (for automated deployments)',
        )

    def handle(self, *args, **options):
        # Check if we're in Railway environment or have --force flag
        if not options['force'] and not os.environ.get('RAILWAY_ENVIRONMENT'):
            confirm = input(
                "\n⚠️  WARNING: This will DELETE ALL DATA in the database!\n"
                "Type 'yes' to continue: "
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        self.stdout.write(self.style.WARNING('Starting database reset...'))
        
        with connection.cursor() as cursor:
            # Get the database backend
            db_vendor = connection.vendor
            
            if db_vendor == 'postgresql':
                # PostgreSQL specific: Drop all tables in public schema
                self.stdout.write('Dropping all PostgreSQL tables...')
                
                # Get all table names
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = cursor.fetchall()
                
                self.stdout.write(f'Found {len(tables)} tables to drop.')
                
                # Disable foreign key checks for PostgreSQL
                cursor.execute("SET session_replication_role = 'replica';")
                
                # Drop all tables
                for table in tables:
                    table_name = table[0]
                    self.stdout.write(f'  Dropping table: {table_name}')
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                
                # Re-enable foreign key checks
                cursor.execute("SET session_replication_role = 'origin';")
                
            elif db_vendor == 'sqlite':
                # SQLite specific: Get all tables
                self.stdout.write('Dropping all SQLite tables...')
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()
                
                self.stdout.write(f'Found {len(tables)} tables to drop.')
                
                # Drop all tables
                for table in tables:
                    table_name = table[0]
                    self.stdout.write(f'  Dropping table: {table_name}')
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            
            else:
                self.stdout.write(self.style.ERROR(f'Unsupported database backend: {db_vendor}'))
                return
        
        self.stdout.write(self.style.SUCCESS('All tables dropped successfully!'))
        
        # Run migrations
        self.stdout.write('\nRunning fresh migrations...')
        call_command('migrate', '--run-syncdb', verbosity=2)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database reset complete!'))