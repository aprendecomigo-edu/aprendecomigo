# Automated Security Review Setup

## Overview
This repository uses Claude Code's automated security review to scan all pull requests targeting the `main` branch for potential security vulnerabilities.

## How It Works

### 1. Automatic PR Scanning
- Triggers on all PRs to `main` branch
- Runs Claude's security analysis on changed code
- Comments directly on the PR with findings
- Creates GitHub issues for critical vulnerabilities

### 2. Security Issue Creation
When critical or high-severity vulnerabilities are found:
- Automatically creates a GitHub issue with `[SECURITY]` prefix
- Tags with `security` and `priority-critical` labels
- Assigns to PR author
- Links issue back to the PR

### 3. PR Labels
Each reviewed PR receives one of these labels:
- `security-review-passed` - No critical findings
- `security-review-failed` - Critical/high findings detected

## Setup Requirements

### 1. GitHub Secrets
Add the following secret to your repository:
- `CLAUDE_API_KEY` - Your Claude API key from Anthropic

To add the secret:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CLAUDE_API_KEY`
4. Value: Your API key

### 2. Repository Permissions
Ensure GitHub Actions has these permissions:
- Read access to code
- Write access to pull requests
- Write access to issues

## Custom Security Rules

The scan uses platform-specific rules defined in `.github/security-scan-instructions.md`, including:

### EdTech-Specific Checks
- Multi-school data isolation
- Student PII protection (LGPD/COPPA compliance)
- Payment processing security
- Parent approval workflows
- Role-based access control

### Technology Stack Checks
- Django security best practices
- React Native/Expo security
- JWT token validation
- WebSocket authentication
- API rate limiting

## Security Severity Levels

### Critical (Immediate Action Required)
- Authentication bypass
- Payment data exposure
- Student PII leakage
- Cross-school data access
- Exposed API keys

### High (Fix Before Merge)
- Session hijacking risks
- XSS vulnerabilities
- CSRF vulnerabilities
- Missing rate limiting
- Weak authentication

### Medium/Low (Fix Soon)
- Code quality issues
- Best practice violations
- Performance concerns

## Manual Security Review

For local security reviews before pushing:
```bash
# In Claude Code terminal
/security-review
```

## Workflow Files

- `.github/workflows/security-review.yml` - Main workflow
- `.github/security-scan-instructions.md` - Custom rules
- `.github/ISSUE_TEMPLATE/security_vulnerability.yml` - Issue template

## Monitoring

### PR Comments
Claude will comment directly on PRs with:
- Vulnerability descriptions
- Affected code locations
- Recommended fixes
- Severity levels

### GitHub Issues
Critical findings create issues with:
- Full vulnerability details
- PR reference
- Assignment to PR author
- Tracking labels

### Workflow Summary
Check Actions tab for:
- Security scan results
- Processing time
- Error logs

## Best Practices

1. **Review All Findings**: Even if automated, manually verify findings
2. **Fix Before Merge**: Don't merge PRs with security-review-failed label
3. **Update Rules**: Periodically update security-scan-instructions.md
4. **Monitor Patterns**: Track recurring security issues
5. **Team Training**: Use findings for security awareness

## Troubleshooting

### Scan Not Running
- Check if PR targets `main` branch
- Verify `CLAUDE_API_KEY` secret is set
- Check Actions permissions

### False Positives
- Update `.github/security-scan-instructions.md`
- Add patterns to false positive filters
- Use inline comments to suppress specific warnings

### Scan Timeout
- Default timeout is 30 minutes
- For large PRs, consider splitting changes
- Adjust `claudecode-timeout` in workflow

## Support

- **Security Issues**: security@aprendecomigo.com
- **Workflow Issues**: Create a GitHub issue
- **Claude Code Docs**: https://docs.anthropic.com/claude-code

## Compliance

This setup helps maintain compliance with:
- LGPD (Brazilian Data Protection)
- COPPA (Children's Privacy)
- PCI DSS (Payment Security)
- Educational Data Protection