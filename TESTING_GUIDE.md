# Testing Guide - Aprende Comigo Platform

This guide outlines the testing strategies and best practices for the Aprende Comigo Django backend, optimized for different development and deployment scenarios.

## 🚀 Testing Strategy Overview

Our testing configuration follows Django best practices with optimizations for speed and reliability:

- **Database**: SQLite `:memory:` for fastest execution
- **Password Hashing**: MD5 hasher for faster authentication tests
- **Caching**: In-memory backends to eliminate I/O overhead
- **Logging**: Minimal output to reduce noise and improve performance
- **Throttling**: Disabled during tests to prevent artificial delays

## 📋 Available Testing Commands

### Local Development Testing
```bash
make django-tests-dev
```
**Configuration**: `aprendecomigo.settings.testing`
**Execution Time**: ~12 seconds for 925 tests

### Parallel Testing
```bash
make django-tests-parallel
```
**Configuration**: `aprendecomigo.settings.testing` + `--parallel`
**Execution Time**: ~4-6 seconds (on multi-core systems)

### Standard Testing
```bash
make django-tests
```
**Configuration**: `aprendecomigo.settings.testing`
**Use**: CI/CD pipelines, consistent environments

### Coverage Analysis
```bash
make django-tests-coverage
```
**Configuration**: `aprendecomigo.settings.testing` + coverage reporting
**Execution Time**: ~20 seconds (includes coverage overhead)

## 🎯 When to Use Each Strategy

### **Daily Development Workflow**
**Command**: `make django-tests-dev`

**When to use:**
- ✅ During active development cycles
- ✅ Quick feedback on code changes
- ✅ Running specific test files or methods
- ✅ Test-Driven Development (TDD) workflow

**Characteristics:**
- Fastest execution time
- Optimized for rapid iteration
- Minimal logging output

### **Pre-Commit Validation**
**Command**: `make django-tests-parallel`

**When to use:**
- ✅ Before pushing code to remote repository
- ✅ Full test suite validation on powerful development machines (8+ cores)
- ✅ Creating pull requests
- ❌ Avoid on resource-constrained CI environments

**Characteristics:**
- Ultra-fast execution on multi-core systems
- Each parallel worker gets isolated `:memory:` database
- Perfect for comprehensive local validation

### **CI/CD Pipeline Testing**
**Command**: `make django-tests`

**When to use:**
- ✅ GitHub Actions / GitLab CI pipelines
- ✅ Docker containers with limited resources
- ✅ Production deployment gates
- ✅ Staging environment validation

**Characteristics:**
- Consistent performance across different environments
- Single-threaded for predictable resource usage
- Reliable for automated deployments

### **Code Quality Analysis**
**Command**: `make django-tests-coverage`

**When to use:**
- ✅ Weekly code quality reviews
- ✅ Before major releases
- ✅ Identifying untested code paths
- ✅ Technical debt assessment
- ❌ Not recommended for daily development (slower due to coverage overhead)

**Characteristics:**
- Provides detailed test coverage metrics
- Helps identify gaps in test suite
- Generates coverage reports

## 📊 Performance Comparison

| Strategy | Execution Time | CPU Usage | Use Case | Environment |
|----------|----------------|-----------|----------|-------------|
| `django-tests-dev` | **12s** | Low | Daily development | Local |
| `django-tests-parallel` | **4-6s** | High | Pre-commit validation | Local (multi-core) |
| `django-tests` | **12s** | Low | CI/CD pipelines | Automated |
| `django-tests-coverage` | **20s** | Medium | Quality analysis | Local/Automated |

## 🔧 Configuration Details

### Testing Settings (`aprendecomigo.settings.testing`)

**Database Configuration:**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # In-memory for maximum speed
    }
}
```

**Performance Optimizations:**
```python
# Faster password hashing for auth tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory backends
SESSION_ENGINE = "django.contrib.sessions.backends.db"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disabled throttling
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "purchase_initiation": "10000/minute",
        "auth_code_request": "10000/minute",
        # ... other high limits
    },
}
```

**Logging Configuration:**
- **Console Level**: WARNING (reduce test noise)
- **Memory Handlers**: Capture important events for test verification
- **Null Handlers**: Discard verbose logs (DB queries, requests)

### Development Settings (`aprendecomigo.settings.development`)

**Test Database Override:**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "NAME": ":memory:",  # Use in-memory for dev tests too
        },
    }
}
```

## 🏗️ Integration Testing (Advanced)

For scenarios requiring persistent data or complex database constraints:

```python
# Custom settings for integration tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "integration_test.db",  # File-based for persistence
    }
}
```

**When to use:**
- End-to-end workflow testing
- Multi-transaction scenarios
- Database constraint validation
- Staging environment with realistic data

## 📝 Test Writing Guidelines

### Test Structure
- Use `django.test.TestCase` for database-related tests
- Organize tests into logical modules (`test_models.py`, `test_views.py`, etc.)
- Ensure tests are independent and can run in any order

### Performance Tips
- Avoid unnecessary database queries in test setup
- Use `setUpTestData()` for shared test data
- Mock external services (Stripe, email providers)
- Keep test data minimal and focused

### Naming Conventions
```python
class TestUserAuthentication(TestCase):
    def test_valid_email_creates_verification_code(self):
        # Test implementation
        pass
    
    def test_invalid_email_returns_error(self):
        # Test implementation
        pass
```

## 🚨 Troubleshooting

### Common Issues

**Slow Test Execution:**
- Verify you're using `:memory:` database
- Check for unnecessary database queries
- Ensure throttling is disabled

**Test Database Conflicts:**
- Tests should be isolated and not depend on external state
- Use `TransactionTestCase` only when necessary
- Clear caches between tests if needed

**Memory Issues (Parallel Testing):**
- Reduce parallel worker count: `--parallel 4`
- Monitor system resources during test execution
- Consider using `django-tests-dev` instead

### Debug Mode
For detailed test debugging, temporarily modify logging level:
```python
# In testing.py
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['your_app']['level'] = 'DEBUG'
```

## 📈 Test Metrics

**Current Test Suite:**
- **Total Tests**: 925
- **Execution Time**: ~12 seconds (optimized)
- **Coverage Target**: >80%

**Quality Gates:**
- All tests must pass before deployment
- No critical security test failures
- Performance tests within acceptable thresholds

---

**Last Updated**: August 2025  
**Django Version**: 5.1+  
**Python Version**: 3.13+

For questions about testing strategies, consult this guide or reach out to the development team.