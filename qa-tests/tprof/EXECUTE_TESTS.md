# Teacher Profile Wizard - Test Execution Guide

## Quick Start Instructions

### Step 1: Environment Setup (Required)

```bash
# Navigate to project directory
cd /Users/anapmc/Code/aprendecomigo

# Check if virtual environment exists
ls -la .venv

# If .venv doesn't exist, create it:
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Start development servers
make dev

# Verify servers are running (in separate terminal)
make health
```

**Expected Output:**
- Frontend: http://localhost:8081 ✓
- Backend: http://localhost:8000/api/ ✓

### Step 2: Execute Critical Tests (Priority Order)

#### 🔴 CRITICAL - Execute First

**1. TPROF-001: Complete Wizard Flow**
```bash
# Navigate to browser: http://localhost:8081/onboarding/teacher-profile

# Expected: 7-step wizard loads properly
# Test Duration: ~15 minutes
# Result: PASS/FAIL + screenshot evidence
```

**2. TPROF-002: Form Validation**
```bash
# Test all validation rules systematically
# Focus on required fields and data formats
# Test Duration: ~20 minutes
# Result: PASS/FAIL + validation behavior notes
```

**3. TPROF-003: Auto-Save & Persistence**
```bash
# Test auto-save every 30 seconds
# Test browser refresh recovery
# Test Duration: ~10 minutes
# Result: PASS/FAIL + data persistence verification
```

#### 🟡 IMPORTANT - Execute After Critical Tests Pass

**4. TPROF-004: Mobile Responsiveness**
```bash
# Use browser dev tools to simulate devices:
# - iPhone SE (375x667)
# - iPad (768x1024)
# - Desktop (1920x1080)
# Test Duration: ~15 minutes
```

**5. TPROF-005: Edge Cases**
```bash
# Test with extreme values and special characters
# Test file upload edge cases
# Test Duration: ~25 minutes
```

**6. TPROF-006: Navigation Flow**
```bash
# Test step navigation and flow control
# Test browser back/forward buttons
# Test Duration: ~15 minutes
```

## Test Execution Commands

### Manual Execution (Recommended First)

```bash
# Create run directory with timestamp
RUN_ID="run-$(date +%Y%m%d-%H%M%S)"
mkdir -p qa-tests/tprof/tprof-001/$RUN_ID/screenshots

# Start test execution
echo "Starting TPROF-001 execution at $(date)" | tee qa-tests/tprof/tprof-001/$RUN_ID/execution.log

# Take screenshots during test
# Save results to results.md in run directory
```

### Automated Execution (After Manual Success)

```bash
# Install Playwright for automation (if needed)
npm install -g playwright

# Example automation script (create as needed)
cd qa-tests/tprof
node execute-automated-tests.js  # Create this script for automation
```

## Test Data Requirements

### Required Test Accounts
- Email: `teacher.test@aprendecomigo.com`
- Role: Individual tutor (school_owner + teacher)
- State: Email verified, no existing profile

### Test Assets Needed
- Profile photo: Any valid image file (JPG/PNG)
- Sample text for biography testing
- Rate data for different currency testing

### Environment Variables
```bash
export DJANGO_ENV=development
export EXPO_PUBLIC_ENV=development
```

## Recording Results

### For Each Test Execution:

1. **Create Run Directory**
   ```bash
   RUN_ID="run-$(date +%Y%m%d-%H%M%S)"
   mkdir -p qa-tests/tprof/[test-id]/$RUN_ID/screenshots
   ```

2. **Document Results**
   - Take screenshots at each major step
   - Record overall PASS/FAIL result
   - Note any issues or unexpected behavior
   - Time the execution

3. **Update Tracking Files**
   ```bash
   # Update individual test runs.csv
   echo "$RUN_ID,$(date -u +%Y-%m-%dT%H:%M:%SZ),PASS,7,0,Chrome,macOS,All steps completed successfully" >> qa-tests/tprof/tprof-001/runs.csv
   
   # Update category latest_runs.csv
   # Replace existing entry or add new one
   ```

## Expected Results Summary

### TPROF-001: Complete Wizard Flow
- **PASS Criteria:** All 7 steps complete, profile saved, redirect to dashboard
- **Time:** ~15 minutes
- **Screenshots:** At least 10 (one per major step)

### TPROF-002: Form Validation
- **PASS Criteria:** All validation rules work, clear error messages
- **Time:** ~20 minutes
- **Focus:** Required fields, data formats, business rules

### TPROF-003: Auto-Save & Persistence
- **PASS Criteria:** Auto-save works, data survives interruptions
- **Time:** ~10 minutes
- **Focus:** 30-second intervals, browser refresh recovery

### TPROF-004: Mobile Responsiveness
- **PASS Criteria:** Works perfectly on all tested device sizes
- **Time:** ~15 minutes
- **Focus:** Touch interactions, virtual keyboard, layouts

### TPROF-005: Edge Cases
- **PASS Criteria:** Handles all extreme inputs gracefully
- **Time:** ~25 minutes
- **Focus:** Boundary values, special characters, file uploads

### TPROF-006: Navigation Flow
- **PASS Criteria:** All navigation works correctly
- **Time:** ~15 minutes
- **Focus:** Step transitions, progress tracking, URL handling

## Troubleshooting

### Common Issues

**1. Servers Won't Start**
```bash
# Check for port conflicts
lsof -i :8000 -i :8081

# Kill conflicting processes
make stop

# Check dependencies
make check-deps

# Try starting individual servers
make backend  # In one terminal
make frontend # In another terminal
```

**2. Wizard Won't Load**
```bash
# Check backend API is responding
curl http://localhost:8000/api/

# Check frontend is serving
curl http://localhost:8081

# Check for JavaScript errors in browser console
# Check network tab for failed API calls
```

**3. Authentication Issues**
```bash
# Verify user account exists and is verified
# Check authentication tokens in browser dev tools
# Verify API endpoints are returning correct responses
```

### Debug Commands

```bash
# View server logs
make logs

# Check server health
make health

# Monitor network requests in browser dev tools
# Check console for JavaScript errors
# Verify API responses in network tab
```

## Success Metrics

### Minimum Acceptable Results
- **TPROF-001:** PASS (CRITICAL)
- **TPROF-002:** PASS (CRITICAL)  
- **TPROF-003:** PASS (CRITICAL)
- **TPROF-004:** PASS or minor issues only
- **TPROF-005:** PASS or minor issues only
- **TPROF-006:** PASS or minor issues only

### Performance Requirements
- Wizard initial load: < 3 seconds
- Step transitions: < 500ms
- Auto-save completion: < 2 seconds
- Form interactions: < 100ms response time

### Quality Standards
- No JavaScript console errors
- No broken UI elements
- All text readable without horizontal scrolling
- Touch targets minimum 44px on mobile
- Consistent visual design across steps

## Immediate Next Steps

1. **Setup Environment** (30 minutes)
   - Verify Python virtual environment
   - Start development servers
   - Confirm wizard URL accessible

2. **Execute TPROF-001** (15 minutes)
   - Complete full wizard flow
   - Document with screenshots
   - Record PASS/FAIL result

3. **If TPROF-001 PASSES:** Continue with TPROF-002 and TPROF-003
4. **If TPROF-001 FAILS:** Document issues and implement fixes before continuing

## Contact & Support

- **Test Files Location:** `/Users/anapmc/Code/aprendecomigo/qa-tests/tprof/`
- **GitHub Issue:** #43 (Teacher Profile Creation Wizard)
- **Priority:** HIGH - Critical for tutor onboarding

---
**Guide Updated:** 2025-07-31  
**Next Review:** After test execution begins