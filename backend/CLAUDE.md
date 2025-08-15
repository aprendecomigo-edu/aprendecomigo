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

## Django Commands (ch dj or ch django)

**IMPORTANT: Always use these commands instead of direct tools. They handle virtual environment activation, settings, and provide better error handling.**

### Server Management
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj runserver` | `python manage.py runserver` | Start development server (auto-kills existing) |
| `ch dj runserver --prod` | `daphne -b 0.0.0.0 -p 8000 ...` | Start with Daphne (production-like) |
| `ch dj stop` | `lsof -ti:8000 \| xargs kill -9` | Stop all Django servers |
| `ch dj health` | `curl http://localhost:8000/api/` | Check server health status |
| `ch dj logs` | `tail -f logs/server-*.log` | View server logs |

### Testing
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj test` | `python manage.py test --noinput` | Run all tests |
| `ch dj test --parallel` | `python manage.py test --parallel` | Run tests in parallel |
| `ch dj test --coverage` | `coverage run && coverage report` | Run tests with coverage report |
| `ch dj test --fast` | `python manage.py test --keepdb` | Run tests keeping test database |

### Code Quality (ALWAYS USE THESE)
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj lint` | `ruff check .` | Check for linting issues |
| `ch dj lint fix` | `ruff check . --fix` | Auto-fix safe issues (USE THIS FIRST) |
| `ch dj lint fix-unsafe` | `ruff check . --fix --unsafe-fixes` | Fix including unsafe (AVOID) |
| `ch dj lint diff` | `ruff check . --diff` | Preview what would be fixed |
| `ch dj lint stats` | `ruff check . --statistics` | Show linting statistics |
| `ch dj lint explain E501` | `ruff rule E501` | Explain specific error codes |
| `ch dj format` | `ruff format .` | Format code automatically |
| `ch dj typecheck` | `mypy .` | Run type checking |

### Database Management
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj migrate` | `python manage.py migrate` | Run database migrations |
| `ch dj makemigrations` | `python manage.py makemigrations` | Create new migrations |
| `ch dj showmigrations` | `python manage.py showmigrations` | Show migration status |
| `ch dj shell` | `python manage.py shell` | Django interactive shell |
| `ch dj dbshell` | `python manage.py dbshell` | Database SQL shell |

### Dependencies & Security
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj deps` | `pip list`, `cat requirements/*.txt` | Show all dependencies (smart detection) |
| `ch dj install` | `pip install -r requirements/dev.txt` | Install dev dependencies (default) |
| `ch dj install prod` | `pip install -r requirements/prod.txt` | Install production dependencies |
| `ch dj install all` | `pip install -r requirements/*.txt` | Install all requirement files |
| `ch dj outdated` | `pip list --outdated` | Check for outdated packages |
| `ch dj audit` | `pip-audit` or `safety check` | Security vulnerability scan |

### Admin
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj createsuperuser` | `python manage.py createsuperuser` | Create Django superuser |
| `ch dj collectstatic` | `python manage.py collectstatic --noinput` | Collect static files |

### General
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj manage <cmd>` | `python manage.py <cmd>` | Run any manage.py command |

## Why Use ch dj Commands?

1. **Auto-activates virtual environment** - No need to remember to activate
2. **Sets correct Django settings** - Automatically configures DJANGO_SETTINGS_MODULE
3. **Better error handling** - Provides colored output and clear error messages
4. **Smart detection** - Automatically detects requirements structure (file vs directory)
5. **Consistent interface** - Same commands work across different project setups
6. **All-in-one solution** - No need for separate Python helpers, Django commands handle everything
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
- Use ch commands for linting and code quality

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