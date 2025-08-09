# Custom Security Scan Instructions for Aprende Comigo

## Platform-Specific Security Checks

### Authentication & Authorization
- Verify JWT token validation in all API endpoints
- Check for proper role-based access control (School Owner, Teacher, Student, Parent)
- Ensure passwordless email verification is properly implemented
- Validate multi-school role management

### Payment Security
- Check for secure handling of payment information
- Verify Stripe API keys are not exposed
- Ensure payment processing follows PCI compliance
- Validate parent approval workflows for student payments

### Data Privacy (LGPD/GDPR Compliance)
- Check for proper PII handling for students (minors)
- Verify data encryption for sensitive information
- Ensure proper data retention policies
- Validate consent management for parents/guardians

### API Security
- Check for rate limiting on all endpoints
- Verify input validation and sanitization
- Look for SQL injection vulnerabilities
- Check for proper CORS configuration
- Validate WebSocket authentication

### Django-Specific Checks
- Verify CSRF protection is enabled
- Check for secure session management
- Validate proper use of Django ORM to prevent SQL injection
- Ensure DEBUG is False in production settings
- Check for exposed Django admin panel

### React Native/Expo Checks
- Verify secure storage of authentication tokens
- Check for hardcoded API endpoints or secrets
- Validate certificate pinning for API calls
- Ensure proper handling of deep links

### School Data Isolation
- Verify multi-tenant data isolation
- Check that users can only access their school's data
- Validate proper scoping of database queries
- Ensure no cross-school data leakage

### Real-time Communication Security
- Verify WebSocket authentication
- Check for proper message validation
- Ensure classroom sessions are properly isolated
- Validate video streaming security

### File Upload Security
- Check file type validation
- Verify file size limits
- Ensure malware scanning for uploads
- Validate proper file storage permissions

### Dependency Security
- Check for known vulnerabilities in npm packages
- Verify Python package security
- Ensure all dependencies are up to date
- Check for supply chain attacks

## Priority Vulnerabilities

Mark as CRITICAL if found:
1. Authentication bypass
2. Payment data exposure
3. Student PII leakage
4. Cross-school data access
5. SQL injection in payment or user management
6. Exposed API keys or secrets
7. Admin panel vulnerabilities

Mark as HIGH if found:
1. Session hijacking possibilities
2. XSS in user-generated content
3. CSRF vulnerabilities
4. Insecure direct object references
5. Missing rate limiting on critical endpoints
6. Weak password reset mechanisms
7. Improper error handling exposing system info

## False Positive Filters

Ignore these common false positives:
- Test files with mock API keys (containing "test" or "mock")
- Development environment configurations
- Example code in documentation
- Frontend hardcoded text that doesn't contain sensitive data
- Console.log statements in development mode checks

## Compliance Requirements

Ensure compliance with:
- LGPD (Brazilian Data Protection Law)
- COPPA (for US users under 13)
- Educational data protection regulations
- Payment processing standards (PCI DSS)