#!/bin/bash

# Script to set up Git hooks for the project

echo "Setting up Git hooks..."

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy pre-commit hook
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✓ Pre-commit hook installed successfully!"
echo ""
echo "The pre-commit hook will automatically:"
echo "  • Check Python files for syntax errors and undefined names"
echo "  • Run flake8 linting on backend code"
echo "  • Prevent commits with critical errors that would fail CI/CD"
echo ""
echo "To bypass the hook (not recommended), use: git commit --no-verify"