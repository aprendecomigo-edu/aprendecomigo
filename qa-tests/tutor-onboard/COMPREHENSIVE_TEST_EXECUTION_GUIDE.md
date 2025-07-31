# Individual Tutor Onboarding QA Test Execution Guide

## Overview
This guide provides comprehensive instructions for executing QA test cases to validate the individual tutor onboarding flow implementation (GitHub Issue #44). All acceptance criteria are systematically tested through 10 detailed test cases.

## Prerequisites

### Environment Setup
1. **Project Location**: `/Users/anapmc/Code/aprendecomigo`
2. **Development Servers**: Both backend and frontend must be running
3. **Access URL**: Frontend accessible at `http://localhost:8081`
4. **Backend API**: Available at `http://localhost:8000/api/`

### Starting the Test Environment
```bash
cd /Users/anapmc/Code/aprendecomigo
make dev
```

Verify servers are running:
```bash
make logs
```

Expected output:
- Backend: Django development server running on port 8000
- Frontend: Metro/Expo server running on port 8081

## Test Case Execution Order

### Phase 1: Core Functionality Tests (TOB-001 to TOB-003)
Execute these tests first to validate basic functionality:

1. **TOB-001**: Educational System Selection
2. **TOB-002**: Course Catalog Browser  
3. **TOB-003**: Multi-Select Course Functionality

### Phase 2: Advanced Feature Tests (TOB-004 to TOB-007)
Execute these tests to validate advanced features:

4. **TOB-004**: Grade Level Specification
5. **TOB-005**: Course-Specific Rate Configuration
6. **TOB-006**: Search and Filter Functionality
7. **TOB-007**: Visual Course Selection Feedback

### Phase 3: Integration and End-to-End Tests (TOB-008 to TOB-010)
Execute these tests to validate complete system integration:

8. **TOB-008**: Backend API Integration
9. **TOB-009**: Complete Onboarding Flow
10. **TOB-010**: Mobile Responsiveness

## Test Execution Instructions

### Accessing the Individual Tutor Onboarding Flow

1. **Navigate to Frontend**: Open browser to `http://localhost:8081`
2. **Find Onboarding Entry Point**: Look for individual tutor onboarding options
   - May be accessible via `/onboarding/teacher-profile` route
   - May be available through user type selection or dashboard
3. **Start Fresh Session**: Use new browser session or incognito mode for clean testing

### Test Data Requirements

- **Educational Systems**: Portugal, Brazil, Custom should be available
- **Course Data**: Comprehensive course catalog with multiple education levels
- **User Account**: Fresh account for testing (recommended)

## Detailed Test Execution

### TOB-001: Educational System Selection
**Acceptance Criteria Validation**:
- ✅ Educational system selection (Portugal, Brazil, Custom) with clear descriptions

**Execution Steps**:
1. Navigate to educational system selection step
2. Verify all three systems (Portugal, Brazil, Custom) are displayed
3. Verify each system has clear, informative descriptions
4. Test selection functionality and visual feedback
5. Verify progression to next step works

**Pass Criteria**: All educational systems displayed with clear descriptions, selection works correctly

### TOB-002: Course Catalog Browser
**Acceptance Criteria Validation**:
- ✅ Course browsing interface organized by education level and subject area

**Execution Steps**:
1. Select educational system and proceed to course catalog
2. Verify courses are organized by education level
3. Verify subject area categorization is clear
4. Test navigation between education levels
5. Verify course information completeness

**Pass Criteria**: Course catalog clearly organized by education level and subject area

### TOB-003: Multi-Select Course Functionality
**Acceptance Criteria Validation**:
- ✅ Multi-select functionality for choosing multiple courses to teach

**Execution Steps**:
1. Test selecting single course with visual feedback
2. Test selecting multiple courses simultaneously
3. Test deselecting individual courses
4. Test cross-level and cross-subject selection
5. Verify selection persistence and progression

**Pass Criteria**: Multi-select works correctly with proper visual feedback

### TOB-004: Grade Level Specification
**Acceptance Criteria Validation**:
- ✅ Grade level specification for each selected course (elementary, middle, high school)

**Execution Steps**:
1. Proceed to grade level specification step
2. Verify grade level options (Elementary, Middle, High School, University, etc.)
3. Test setting grade levels for each selected course
4. Test multiple grade levels per course
5. Verify validation and progression

**Pass Criteria**: Grade level specification works for all selected courses

### TOB-005: Course-Specific Rate Configuration
**Acceptance Criteria Validation**:
- ✅ Course-specific rate configuration allowing different prices per subject

**Execution Steps**:
1. Navigate to rate configuration step
2. Verify individual course rate settings
3. Test setting different rates for different courses
4. Test rate validation and formatting
5. Verify rate persistence and calculations

**Pass Criteria**: Different rates can be set for each course with proper validation

### TOB-006: Search and Filter Functionality
**Acceptance Criteria Validation**:
- ✅ Search and filter functionality for finding specific courses quickly

**Execution Steps**:
1. Test course search by name, code, and subject area  
2. Test education level filters
3. Test subject area filters
4. Test difficulty level filters
5. Test combined search + filters functionality

**Pass Criteria**: Search and filters effectively help find specific courses

### TOB-007: Visual Course Selection Feedback
**Acceptance Criteria Validation**:
- ✅ Visual confirmation of selected courses with easy removal options

**Execution Steps**:
1. Test visual feedback for course selection
2. Test selected course summary/display
3. Test individual course removal methods
4. Test batch/clear all removal
5. Verify visual consistency and accessibility

**Pass Criteria**: Clear visual feedback with intuitive removal options

### TOB-008: Backend API Integration
**Acceptance Criteria Validation**:
- ✅ Integration with existing Course and TeacherCourse backend models

**Execution Steps**:
1. Monitor network requests during onboarding
2. Verify API calls for educational systems, courses, selections
3. Check database records after completion
4. Test error handling and data validation
5. Verify authentication and security

**Pass Criteria**: Proper API integration with correct data persistence

### TOB-009: Complete Onboarding Flow
**Acceptance Criteria Validation**:
- ✅ All acceptance criteria working together in complete flow

**Execution Steps**:
1. Execute complete end-to-end onboarding process
2. Verify all data persists between steps
3. Test integration with teacher profile system
4. Verify final configuration accuracy
5. Confirm post-onboarding state

**Pass Criteria**: Complete flow works seamlessly from start to finish

### TOB-010: Mobile Responsiveness
**Acceptance Criteria Validation**:
- ✅ Cross-platform compatibility requirement

**Execution Steps**:
1. Test desktop resolution (1920x1080)
2. Test laptop resolution (1366x768)
3. Test tablet landscape and portrait
4. Test mobile landscape and portrait
5. Test cross-browser compatibility

**Pass Criteria**: Fully functional across all tested screen sizes and browsers

## Recording Test Results

### For Each Test Case
1. **Create Run Directory**: `qa-tests/tutor-onboard/tob-XXX/run-YYYYMMDD-HHMMSS/`
2. **Document Results**: Create `results.md` with detailed findings
3. **Capture Screenshots**: Save screenshots for key validation points
4. **Update Runs CSV**: Add entry to `runs.csv` with overall result

### Results Format
```csv
run_id,timestamp,overall_result,steps_passed,steps_failed,browser,environment,notes
run-20250731-143000,2025-07-31T14:30:00Z,PASS,10,0,Chrome,macOS development,All acceptance criteria validated
```

## Acceptance Criteria Validation Matrix

| Test Case | Acceptance Criterion | Status | Notes |
|-----------|---------------------|---------|-------|
| TOB-001 | Educational system selection (Portugal, Brazil, Custom) with clear descriptions | ⏳ Pending | |
| TOB-002 | Course browsing interface organized by education level and subject area | ⏳ Pending | |
| TOB-003 | Multi-select functionality for choosing multiple courses to teach | ⏳ Pending | |
| TOB-004 | Grade level specification for each selected course (elementary, middle, high school) | ⏳ Pending | |
| TOB-005 | Course-specific rate configuration allowing different prices per subject | ⏳ Pending | |
| TOB-006 | Search and filter functionality for finding specific courses quickly | ⏳ Pending | |
| TOB-007 | Visual confirmation of selected courses with easy removal options | ⏳ Pending | |
| TOB-008 | Integration with existing Course and TeacherCourse backend models | ⏳ Pending | |
| TOB-009 | Complete individual tutor onboarding flow from start to finish | ⏳ Pending | |
| TOB-010 | Cross-platform compatibility and mobile responsiveness | ⏳ Pending | |

## Success Criteria

### Overall PASS Requirements
- All 10 test cases must PASS
- All acceptance criteria from GitHub issue #44 validated
- No critical bugs or functionality issues discovered
- Mobile responsiveness confirmed across major screen sizes

### Overall FAIL Conditions
- Any test case fails
- Any acceptance criterion not properly implemented
- Critical bugs that prevent onboarding completion
- Poor mobile/responsive design that impacts usability

## Troubleshooting

### Common Issues
1. **Servers Not Starting**: Check `make logs` for error details
2. **Frontend Not Loading**: Verify port 8081 is accessible
3. **Backend API Errors**: Check backend logs and database connection
4. **Course Data Missing**: Verify Django migrations have run
5. **User Authentication Issues**: Check Django user management

### Debug Commands
```bash
# Check server status
make logs

# Restart servers
make stop
make dev

# Check Django migrations
cd backend
python manage.py showmigrations

# Access Django shell for debugging
python manage.py shell
```

## Next Steps After Testing

1. **Update Results**: Update `latest_runs.csv` with test results
2. **Create Summary Report**: Generate comprehensive findings report
3. **Log Issues**: Document any bugs or issues discovered
4. **Validate Fixes**: Re-run failed tests after fixes are implemented

## Contact and Support

- **QA Framework**: Located in `/qa-tests/` directory
- **Test Cases**: Individual test cases in `/qa-tests/tutor-onboard/tob-XXX/`
- **Server Logs**: Use `make logs` for real-time debugging
- **Documentation**: Each test case has detailed `test-case.txt` file