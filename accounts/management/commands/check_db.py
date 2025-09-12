"""
Management command to check database status and list tables with row counts.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Check database status and list all tables with row counts'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write(self.style.WARNING('=== Database Status Check ===\n'))
        
        # Show database connection info
        self.stdout.write(f'Database engine: {connection.vendor}')
        self.stdout.write(f'Database name: {connection.settings_dict["NAME"]}')
        if connection.vendor == 'postgresql':
            self.stdout.write(f'Database host: {connection.settings_dict.get("HOST", "localhost")}')
        
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                # PostgreSQL: Get all tables with row counts
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_live_tup as row_count
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                tables = cursor.fetchall()
                
                self.stdout.write(f'\nFound {len(tables)} tables:\n')
                
                total_rows = 0
                for schema, table, count in tables:
                    self.stdout.write(f'  📊 {table}: {count} rows')
                    total_rows += count
                
                self.stdout.write(f'\nTotal rows across all tables: {total_rows}')
                
            elif connection.vendor == 'sqlite':
                # SQLite: Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = cursor.fetchall()
                
                self.stdout.write(f'\nFound {len(tables)} tables:\n')
                
                total_rows = 0
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    count = cursor.fetchone()[0]
                    self.stdout.write(f'  📊 {table_name}: {count} rows')
                    total_rows += count
                
                self.stdout.write(f'\nTotal rows across all tables: {total_rows}')
        
        # Check for users specifically
        try:
            user_count = User.objects.count()
            self.stdout.write(f'\n👤 Total users in database: {user_count}')
            
            if user_count > 0:
                # Show first few users
                self.stdout.write('\nFirst 5 users:')
                for user in User.objects.all()[:5]:
                    self.stdout.write(f'  - {user.email} (ID: {user.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError checking users: {e}'))
        
        # Check migration status
        self.stdout.write('\n=== Migration Status ===')
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 5")
        recent_migrations = cursor.fetchall()
        
        if recent_migrations:
            self.stdout.write('Recent migrations:')
            for app, name in recent_migrations:
                self.stdout.write(f'  ✓ {app}: {name}')
        else:
            self.stdout.write('No migrations found in database!')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database check complete!'))