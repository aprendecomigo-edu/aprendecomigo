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
| `ch dj runserver --prod` | `uvicorn aprendecomigo.asgi:application --reload` | Start with Uvicorn (production-like with WebSocket) |
| `ch dj stop` | `lsof -ti:8000 \| xargs kill -9` | Stop all Django servers |
| `ch dj health` | `curl http://localhost:8000/api/` | Check server health status |
| `ch dj logs` | `tail -f logs/server-*.log` | View server logs |

### Testing
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj test` | `python manage.py test --noinput` | Run all tests |
| `ch dj test accounts` | `python manage.py test accounts --noinput` | Run tests for specific app |
| `ch dj test --parallel` | `python manage.py test --parallel` | Run tests in parallel |
| `ch dj test --coverage accounts` | `coverage run manage.py test accounts` | Run tests with coverage for specific app |
| `ch dj test --fast` | `python manage.py test --keepdb` | Run tests keeping test database |

### Code Quality (ALWAYS USE THESE)
| Command | Replaces | Description |
|---------|----------|-------------|
| `ch dj lint` | `ruff check .` | Check entire project for linting issues |
| `ch dj lint accounts/` | `ruff check accounts/` | Check specific app/folder |
| `ch dj lint fix models.py` | `ruff check models.py --fix` | Auto-fix specific file |
| `ch dj lint fix` | `ruff check . --fix` | Auto-fix safe issues (USE THIS FIRST) |
| `ch dj lint fix-unsafe` | `ruff check . --fix --unsafe-fixes` | Fix including unsafe (AVOID) |
| `ch dj lint diff accounts/` | `ruff check accounts/ --diff` | Preview fixes for specific folder |
| `ch dj lint stats` | `ruff check . --statistics` | Show linting statistics |
| `ch dj lint explain E501` | `ruff rule E501` | Explain specific error codes |
| `ch dj format` | `ruff format .` | Format entire project |
| `ch dj format accounts/models.py` | `ruff format accounts/models.py` | Format specific file |
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
| `ch dj install <package>` | `pip install <package>` + manual requirements update | Install ANY package & auto-update requirements |
| `ch dj uninstall <package>` | `pip uninstall <package>` + manual cleanup | Uninstall ANY package & clean requirements |
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

### ESSENTIAL WORKFLOW - Start every project with these:
chp                          # ALWAYS run first - comprehensive project overview
ch ctx for-task "desc"       # Generate focused context for specific tasks
ch nlp tokens file.txt       # Check token count BEFORE adding to context

### SEARCH & DISCOVERY (clear token savings):
chs find-code "pattern"      # More efficient than grep, structured output
ch s search-imports module   # Find where modules are imported
ch cr imported-by module     # Find who imports this module/file
ch cr dependency-tree dir    # Visualize dependency structure
ch cq console-logs           # Find debug statements quickly
ch cq secrets-scan           # Security scan for exposed secrets

### FILE OPERATIONS (use with specific files only):
ch m read-many f1 f2 f3      # Batch read SPECIFIC files in ONE call
ch m list-structure dir      # See what's in a directory first
ch nlp tokens file1 file2    # Check sizes before batch reading

### CONTEXT MANAGEMENT (critical for token efficiency):
ch ctx for-task "migration"  # Get only relevant context
ch ctx summarize             # Create project summary
ch ctx focus src/ 2          # Focus on specific directory (depth 2)
ch ctx mdout                 # Extract all markdown outlines


### Common Usage Examples

```bash
# Testing specific apps
ch dj test                 # Run all tests
ch dj test --coverage accounts      # Test with coverage for accounts
ch dj test --fast accounts          # Fast test with keepdb for accounts

# Linting specific files/folders
ch dj lint fix            # Auto-fix issues in the whole project
ch dj lint accounts/models.py       # Lint specific file
ch dj lint diff accounts/models.py  # Preview fixes for specific file

# Formatting specific targets
ch dj format              # Format project
ch dj format accounts/              # Format entire app
ch dj format accounts/models.py     # Format specific file

# Server management
ch dj runserver                     # Development server

# Package management (ALWAYS USE THESE INSTEAD OF pip install)
ch dj install requests              # Install package and optionally add to requirements
ch dj install "requests>=2.28.0"    # Install specific version
ch dj install django-debug-toolbar  # Installs and prompts to add to requirements
ch dj uninstall requests            # Uninstall and clean from requirements
ch dj install                       # Install all dev dependencies from requirements/
ch dj install prod                  # Install production dependencies
ch dj install all                   # Install all requirement files
```

- `chs find-code "pattern"` - Fast code search (better than grep)
- `ch m read-many file1 file2` - Batch file reading (saves tokens)
- `ch ctx for-task "description"` - Generate focused context for specific tasks

```
Run `ch help` to see all available commands and categories.

## Why use `ch` and `chs` commands?

1. **Auto-activates virtual environment** - No need to remember to activate
2. **Sets correct Django settings** - Automatically configures DJANGO_SETTINGS_MODULE
3. **Better error handling** - Provides colored output and clear error messages
4. **Smart detection** - Automatically detects requirements structure (file vs directory)
5. **Consistent interface** - Same commands work across different project setups
6. **Efficient execution** - No need for separate Python helpers, Django commands handle everything
7. **Granular control** - Target specific apps, files, or folders for testing, linting, and formatting
</ch:project-commands>

<ch:project-notes>
## Important Architecture Notes
Project location: /Users/anapmc/Code/aprendecomigo

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