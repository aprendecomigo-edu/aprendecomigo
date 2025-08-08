---
allowed-tools: Bash(*), read_file, edit_file, grep_search, codebase_search, run_terminal_cmd, list_dir, file_search
description: Execute a specific QA test case and automatically fix any failures detected
---

# Run and Fix QA Test: $ARGUMENTS

Execute the specified QA test case and automatically attempt to fix any failures according to project guidelines and functional requirements.

## CRITICAL: Binary Result System
- **PASS**: Only if ALL steps execute perfectly with zero issues
- **FAIL**: If ANY step has even the slightest issue, deviation, or unexpected behavior

## Auto-Fix Protocol
**When FAIL occurs**: Immediately analyze the failure and implement appropriate fixes based on:
- Project requirements and architecture patterns
- UX guidelines and user experience standards  
- Code consistency with existing implementations
- Error handling and user feedback patterns
1. **Environment Setup**: Ensure virtual environment is activated and services are ready
2. **Service Management**: Start dev servers based on makefile or others
3. **Test Execution**: Follow the test-case.txt instructions step by step
  4. **Results Capture**: Generate timestamped run directory with screenshots and logs
  5. **IMMEDIATE Fix Implementation**: On ANY failure (FAIL), immediately:
     - Analyze root cause using codebase search
     - Implement fixes following project patterns and UX guidelines
     - Re-test to verify fix effectiveness
  6. **Results Documentation**: Update CSV files and create detailed results.md with test and fix details
  7. **Cleanup**: Stop services and clean up temporary files

## QA Test Organization Structure

The QA tests are organized as follows:
```
qa-tests/
├── auth/                           # Authentication tests category
│   ├── latest_runs.csv             # Master list of latest runs for each auth test. Same nr of rows as nr of tests in auth
│   ├── auth-001/                   # Individual test case folder
│   │   ├── test-case.txt          # Test instructions (static)
│   │   ├── runs.csv               # ALL historical runs for this test
│   │   └── run-YYYYMMDD-HHMMSS/   # Timestamped run results
│   │       ├── server.log         # Django server logs
│   │       ├── results.md         # Detailed results
│   │       └── screenshots/       # Test screenshots
│   └── auth-002/                   # Additional auth tests
└── navigation/                     # Future test categories
    ├── latest_runs.csv
    └── nav-001/
```

## Test Discovery and Execution Process

### Step 1: Environment Setup
Before running any tests, ensure the environment is properly configured:


**Project root**: make sure you are or navigate to project root, probably $pwd
**Verify virtual environment exists** and activate it. example source .venv/bin/activate




# Set environment variables if needed

### Step 2: Service Management
Each test requires backend and frontend services to be running:
```make dev```

(Optional) If necessary, kill existing services make stop
```

### Step 3: Test Discovery
Discover the test case by scanning the qa-tests directory:
**Test to Execute**: `$ARGUMENTS`

**Test Instructions**: qa-tests/$ARGUMENTS/test-case.txt

**Previous Runs**: !`[ -f "qa-tests/$ARGUMENTS/runs.csv" ] && tail -3 qa-tests/$ARGUMENTS/runs.csv || echo "No previous runs found"`

### Step 4: Test Execution Protocol
For each discovered test case:

#### A. Parse Test Instructions
```bash
# Read test-case.txt file
# Extract test ID, name, and purpose
# Parse step-by-step instructions
# Identify expected screenshots
```


#### B. Execute Test Steps
For each test case, follow these execution patterns:

**General Test Execution Steps:**
- Use Playwright browser automation
- Navigate to URLs specified in test case
-  Fill forms with test data
- Click buttons as instructed
- Capture screenshots at designated points
- Extract verification codes from server logs
- Verify expected outcomes

#### D. Result Tracking
Track the outcome of each step:


 For each test step:
   - Execute the step
   - Check expected outcome   
   - Log detailed results

### Step 5: Results Documentation

#### A. Create results.md
```markdown
# Test Results - [TEST_ID] - Run [TIMESTAMP]

## Test Execution Summary
- Test ID: [TEST_ID]
- Run ID: run-[TIMESTAMP]
- Timestamp: [ISO_TIMESTAMP]
- Environment: macOS development
- Browser: Playwright Chrome
- Overall Result: [PASS/FAIL] 
  - **FAIL**: ANY deviation, error, UI issue, or unexpected behavior
  - **PASS**: Perfect execution with zero issues

## Step-by-Step Results
[For each step: PASS/FAIL status, details, screenshots]

## Issues Identified & Fixes Applied
[For each FAIL: Root cause analysis + specific code/UI fixes implemented]

## Fix Implementation Details
- Code changes made to resolve issues
- UX improvements applied
- Consistency updates with project patterns
- Error handling enhancements added

### Step 6: CSV Updates

#### A. Update runs.csv (Individual Test)
```csv
run_id,timestamp,overall_result,steps_passed,steps_failed,browser,environment,notes
run-[TIMESTAMP],[ISO_TIMESTAMP],[RESULT],[PASSED],[FAILED],Playwright Chrome,macOS development,[NOTES]
```

#### B. Update latest_runs.csv (Category Level)
Add test or replace existing older run
```csv
test_id,test_name,description,last_run,overall_status,total_runs,pass_count,fail_count
[TEST_ID],[TEST_NAME],[DESCRIPTION],[TIMESTAMP],[RESULT],[TOTAL],[PASS_COUNT],[FAIL_COUNT]
```

### Step 7: Cleanup
Kill background processes
Clean up temporary files


## Expected Behaviors and Error Handling

### Successful Test Execution
- All services start successfully
- Test steps execute in order with PASS/FAIL determination
- Screenshots captured at designated points
- Server logs contain expected entries
- **CRITICAL**: Any failures (FAIL) are immediately diagnosed and fixed
- Fixes are re-tested to ensure effectiveness
- CSV tracking files are updated with fix details
- Detailed results report documents all fixes applied

### Error Recovery
- Always clean up processes on exit
- Preserve partial results even on failure
- Log errors to help debug issues
- Continue with next test if one fails

## Summary Report Format

After test complete, generate a summary:

```
=== QA Test Run Summary ===
Date: [TIMESTAMP]
Environment: macOS development
Browser: Playwright Chrome

Tests Executed: [TOTAL]
Passed: [PASS_COUNT]
Failed: [FAIL_COUNT]

=== Test Results ===
[TEST_ID] - [RESULT] - [NOTES]

=== Failed Tests ===
[List of failed tests with reasons]

=== Recommendations ===
[Action items based on failures]
```

## Usage Instructions

1. **Prerequisites:**
   - Project must be set up with virtual environment
   - Dependencies installed
   - Database migrated with test users

2. **Reviewing Results:**
   - Check individual test results in run directories
   - Review CSV files for historical trends
   - Read results.md files for detailed analysis

3. **Troubleshooting:**
   - Check server logs in run directories
   - Verify services are accessible
   - Ensure test data exists in database

   Execute this test systematically with **strict PASS/FAIL evaluation** - immediately implement fixes for any failures using project patterns and UX guidelines, then re-test to ensure perfect execution.