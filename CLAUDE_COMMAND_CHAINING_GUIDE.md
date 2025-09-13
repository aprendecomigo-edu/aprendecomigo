# Claude Code Command Chaining Guide

This guide explains how to chain multiple Claude commands for sequential execution and data passing.

## 1. Sequential Commands with Output Passing (Dependent)

For when you want output of one command to be input of the next:

```bash
# Example 1: Save output then use it
claude -p "Generate a list of 5 Python best practices" > output1.txt
claude -p "$(cat output1.txt) - Now create unit tests for these practices"

# Example 2: Using pipe directly
echo "Analyze this data: temperature readings 23,25,27,22" | claude -p "create a summary report"

# Example 3: Chain with file processing
claude -p "Create a JSON structure for user data" > user_schema.json
claude -p "Based on this schema: $(cat user_schema.json), create a Django model"
```

## 2. Independent Sequential Commands (One After Another)

For when commands should run in sequence but independently:

```bash
# Using && operator (runs next only if previous succeeds)
claude -p "Generate test data for user model" > test_data.txt && \
claude -p "Create unit tests for authentication" > auth_tests.py && \
claude -p "Review the codebase for security issues" > security_review.txt

# Using ; operator (runs regardless of previous command result)
claude -p "Document the API endpoints"; \
claude -p "Create migration files"; \
claude -p "Update requirements.txt"

# In a bash script for complex workflows
#!/bin/bash
claude -p "Analyze current database schema" > schema_analysis.txt
claude -p "Suggest performance optimizations" > optimizations.txt
claude -p "Create implementation plan" > implementation_plan.txt
```

## Advanced Chaining Patterns

```bash
# Multi-step data processing
claude -p "Extract user requirements from this: $(cat requirements.md)" > parsed_requirements.txt
claude -p "Create Django models based on: $(cat parsed_requirements.txt)" > models.py
claude -p "Generate corresponding API serializers for: $(cat models.py)" > serializers.py

# Using session continuation for context
claude -c "Start building a payment system"
claude -c "Add validation for credit card data"
claude -c "Implement fraud detection"
```

## Complete Development Workflow Example

```bash
# Complete development workflow
claude -p "Analyze the current finances app structure" > analysis.txt && \
claude -p "Based on this analysis: $(cat analysis.txt), suggest improvements" > improvements.txt && \
claude -p "Implement the top 3 suggestions from: $(cat improvements.txt)" && \
claude -p "Create comprehensive tests for the changes made"
```

## Key Points

- **Dependent chains**: Use `$(cat file.txt)` or pipes `|` to pass output as input
- **Independent chains**: Use `&&` (conditional) or `;` (unconditional) for sequential execution
- **Always use `-p` flag**: When chaining with `&&` or `;`, use `claude -p "query"` format
- **Session continuation**: Use `claude -c` to maintain context across related commands

## Operators Summary

- `&&` - Run next command only if previous succeeds
- `;` - Run next command regardless of previous result
- `|` - Pipe output directly to next command
- `$(cat file.txt)` - Include file contents in command
- `>` - Redirect output to file
- `claude -c` - Continue previous conversation
- `claude -p` - Execute prompt/query
