-- PostgreSQL Database Reset Script
-- This will drop ALL tables in the public schema and reset the database

-- First, let's see what we're working with
\echo '=== Current Database Status ==='
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

\echo '=== Total tables and rows ==='
SELECT 
    COUNT(*) as total_tables,
    SUM(n_live_tup) as total_rows
FROM pg_stat_user_tables 
WHERE schemaname = 'public';

-- Disable foreign key checks to allow dropping tables with dependencies
SET session_replication_role = 'replica';

-- Drop all tables in public schema
\echo '=== Dropping all tables ==='
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', r.tablename;
    END LOOP;
END $$;

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- Verify all tables are gone
\echo '=== Verification: Remaining tables ==='
SELECT COUNT(*) as remaining_tables
FROM pg_tables 
WHERE schemaname = 'public';

-- Show any remaining tables (should be empty)
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public';

\echo '=== Database reset complete! ==='
\echo 'All tables have been dropped. Run Django migrations to recreate schema.'