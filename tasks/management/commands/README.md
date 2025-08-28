# School Admin Test Data Management Commands

This directory contains Django management commands for creating and managing realistic test data for the school admin dashboard in the Aprende Comigo platform.

## Available Commands

### 1. create_school_admin_test_data

Creates comprehensive, realistic test data for testing the school admin dashboard functionality.

**Usage:**
```bash
# Create test data with default admin email
python manage.py create_school_admin_test_data

# Create test data with custom admin email
python manage.py create_school_admin_test_data --school-admin-email admin@myschool.pt

# Clear existing data and create fresh test data
python manage.py create_school_admin_test_data --clear-existing
```

**What it creates:**
- School admin user with proper permissions
- Portuguese school context (Escola Aprende Comigo Lisboa)
- 4 realistic teacher profiles with Portuguese names and subjects
- 6 student accounts with Portuguese names
- 9 contextually appropriate admin tasks (urgent feedback responses, teacher reviews, etc.)
- 30+ realistic class schedules spread over 2 weeks with proper Portuguese subjects

**Tasks created include:**
- "Rever candidaturas de novos professores" (Review teacher applications)
- "Enviar newsletter mensal aos pais" (Send monthly parent newsletter)
- "Organizar reunião de professores" (Organize teacher meeting)
- "Responder a feedback dos pais" (Respond to parent feedback) - marked as urgent
- And more...

**Class subjects include:**
- Matemática, Física (João Silva)
- Português, Literatura (Maria Santos)
- História, Geografia (Carlos Mendes)
- Inglês, Francês (Ana Rodrigues)

### 2. verify_test_data

Displays and verifies the created test data for review and debugging.

**Usage:**
```bash
# Verify test data for default admin
python manage.py verify_test_data

# Verify test data for specific admin
python manage.py verify_test_data --school-admin-email admin@myschool.pt
```

**Output includes:**
- School information
- Complete list of admin tasks with priorities and due dates
- Upcoming class schedules
- School members summary (teachers and students)
- Statistics overview

## Test Data Context

All test data is created with Portuguese context appropriate for the Aprende Comigo platform:

- **School**: Escola Aprende Comigo Lisboa
- **Location**: Lisboa, Portugal
- **Language**: Portuguese names, subjects, and task descriptions
- **Academic Context**: Portuguese educational system (8º ano, 9º ano, etc.)
- **Realistic Timing**: Tasks with realistic due dates, classes scheduled during appropriate hours

## Environment Setup

Run these commands with proper Django environment:

```bash
# From project root
source .venv/bin/activate
cd backend
DJANGO_SETTINGS_MODULE=aprendecomigo.settings.development python manage.py [command]
```

## Notes

- Test data is safe to create multiple times (uses get_or_create patterns)
- Use `--clear-existing` flag to reset data for fresh testing
- All created users have verified emails and completed onboarding
- Teachers have complete profiles with realistic hourly rates and specializations
- Class schedules include various statuses (scheduled, confirmed, completed)