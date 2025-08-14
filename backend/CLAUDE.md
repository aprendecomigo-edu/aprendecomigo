# Project-Specific Claude Instructions

## Aprende Comigo Platform Backend

<ch:project-context>
- **Project type**: Django-based educational platform backend (multi-tenant SaaS)
- **Main technologies**: 
  - Python/Django with Django REST Framework
  - PostgreSQL database
  - JWT authentication (passwordless) with Knox
  - Enterprise-grade logging system
- **Key patterns to follow**: 
  - Modular Django app architecture
  - DRY principles and separation of concerns
  - Django ORM optimization (select_related, prefetch_related)
  - Timezone-aware datetime handling (UTC storage)
  - Multi-tenancy support (users with multiple roles across schools)
</ch:project-context>

<ch:project-commands>
### Check full project structure
Run `ch ctx summarize`

### Django apps structure
Run `ch ctx focus <app_name>/ 1`

**Django Commands (Replaces Makefile):**
Usage: `ch django <command>` or `ch dj <command>`

Server Management:
  runserver      Start development server 
  stop           Stop all Django servers
  health         Check server health 
  logs           View server logs 

Testing:
  test                    Run tests
  test --parallel         Run tests in parallel
  test --coverage         Run tests with coverage 
  test --fast             Run tests with --keepdb

Code Quality:
  lint                    Run linting
  lint --fix              Run linting with auto-fi
  format                  Format code with ruff/black
  typecheck               Type checking with mypy

Dependencies:
  install                 Install dependencies
  deps                    Show dependencies
  outdated                Check outdated packages

General:
  manage [command]        Run any manage.py command

**Python Helpers:**
Usage: `ch py <command>`

Commands:
  deps        Show dependencies
  test        Run tests
  lint        Run linter
  format      Check code formatting
  venv        Virtual environment info
  outdated    Check for outdated packages
  audit       Security vulnerability scan
  run         Run Python script
  repl        Start interactive shell
</ch:project-commands>

<ch:project-notes>
## Important Architecture Notes
Project location: /Users/anapmc/Code/aprendecomigo/backend

### Cross-App Dependencies Best Practices
- Use lazy references ("app.Model" strings or settings.AUTH_USER_MODEL)
- Use app-registry (apps.get_model()) for runtime wiring
- Declare migration dependencies explicitly when needed
- Consider interface layers for heavily coupled apps
- Run @.claude/commands/x-app-django-review.md for a health check

### DateTime & Timezone Handling
- Always use `timezone.now()` (never `datetime.now()`)
- Store all datetimes in UTC
- Use `from zoneinfo import ZoneInfo` for explicit timezones
- Convert to local time only for display, not storage/logic

### Security & Performance
- Follow Django security best practices (CSRF, XSS, SQL injection protection)
- Implement proper query optimization (select_related, prefetch_related)
- Use database indexes effectively
- Implement pagination for large datasets
- Proper error handling with custom exceptions

### Logging System Features
- Hierarchical logger structure by business area
- Environment-specific configurations (dev/prod/test/ci)
- Automatic PII redaction for privacy
- Use @agent-django-logging-expert for any logging tasks and questions.

### Testing Standards
- Use Django's TestCase
- Use existing fixtures and factories or implement new when needed
- Check existing mocked services for 3rd parties (like Stripe) and use them
- Mock external dependencies for 3rd parties when none already exist
- Use @agent-drf-test-engineer when testing API/Client DRF functionality
- Use @agent-py-unit-test-engineer when testing logic, services or any other functionality.

### Code Quality Requirements
- PEP 8 compliance
- Type hints for better IDE support
- Clear documentation for complex logic
- Descriptive variable and function names
- Proper logging for debugging

### Multi-Tenancy Considerations
- Users can have multiple roles across different schools
- Proper data isolation between schools
- Role-based access control implementation
- School-specific configurations and settings
</ch:project-notes>

## Helper Scripts Available

You have access to efficient helper scripts that streamline common development tasks:

**🚀 Quick Start:**
```bash
chp  # Provides comprehensive project analysis
```

**🔍 Common Tasks (more efficient than manual commands):**
- `chs find-code "pattern"` - Fast code search (better than grep)
- `ch m read-many file1 file2` - Batch file reading (saves tokens)
- `ch ctx for-task "description"` - Generate focused context for specific tasks

These helpers bundle multiple operations into single commands, providing:
- Structured output optimized for analysis
- Automatic error handling
- Token-efficient responses
- Consistent patterns across tech stacks

Run `ch help` to see all available commands and categories.