# Scheduling Rules & Conflict Management Unit Tests - GitHub Issue #152

This document describes the comprehensive unit test suite created for the NEW scheduling rules and conflict management business logic components.

## Overview

Three comprehensive test files have been created to validate the business logic layer for advanced scheduling rules and conflict management. These tests follow Test-Driven Development (TDD) principles and **will fail initially** since the business logic services are not yet implemented.

## Test Files Created

### 1. `test_scheduling_rules_business_logic.py` (29 tests)
**Main orchestrator services for scheduling rules validation**

**Services Tested:**
- `SchedulingRulesService` - Main orchestrator for all scheduling rules
- `ConflictDetectionService` - Enhanced conflict detection utilities  
- `AvailabilityCalculationService` - Available slots with buffer/notice rules
- `SchedulingConfigurationService` - Configuration management

**Key Test Scenarios:**
- Minimum notice period validation (2 hours default, configurable per teacher/class-type)
- Buffer time calculation (15 minutes default, varies by class type)  
- Conflict detection (student double-booking, teacher buffer violations)
- Booking limits enforcement (daily/weekly limits per teacher/student)
- Configuration hierarchy (school defaults → teacher overrides → class-type specific)

### 2. `test_conflict_detection_utilities.py` (19 tests)
**Pure utility functions for conflict detection**

**Utilities Tested:**
- `detect_time_overlap()` - Time overlap calculation with boundary conditions
- `handle_day_boundary_cases()` - Classes spanning midnight
- `detect_student_conflicts()` - Student double-booking detection
- `detect_teacher_conflicts()` - Teacher conflicts with buffer times
- `calculate_buffer_impact()` - Buffer time impact calculations
- `find_available_gaps()` - Finding gaps between classes
- `validate_time_boundaries()` - Time validation utilities

**Key Test Scenarios:**
- Exact time boundary handling (adjacent vs overlapping classes)
- Day boundary cases (midnight-crossing classes)
- Buffer time calculations with multiple existing classes
- Cross-school conflict detection
- Edge cases (1-minute gaps, exact overlaps, etc.)

### 3. `test_available_slots_with_scheduling_rules.py` (19 tests)
**Available slots calculation with enhanced scheduling rules**

**Services Tested:**
- `apply_buffer_time_to_slots()` - Exclude slots violating buffer time
- `filter_slots_by_minimum_notice()` - Remove slots within notice period
- `apply_booking_limits_to_availability()` - Limit slots based on booking limits
- `merge_availability_with_rules()` - Combine all scheduling rules
- `AvailabilityCalculationEngine` - Full workflow orchestrator

**Key Test Scenarios:**
- Buffer time application with various existing class configurations
- Minimum notice filtering with timezone considerations
- Booking limit enforcement at daily and weekly levels
- Complex scenarios with multiple overlapping rules
- Performance testing with large numbers of slots

## Test Design Principles

All tests follow these key principles:

### ✅ **Fast and Isolated**
- No database operations (all mocked)
- No network dependencies
- No real filesystem operations
- Each test runs in milliseconds

### ✅ **Focused Business Logic**
- Tests individual methods in isolation
- One behavior per test method
- Clear arrange-act-assert structure
- Descriptive test names explaining expected behavior

### ✅ **Comprehensive Coverage**
- Happy path scenarios
- Edge cases and boundary conditions
- Error conditions and validation
- Configuration hierarchy testing
- Complex interaction scenarios

### ✅ **Deterministic**
- No real time dependencies (all mocked)
- No random behavior
- Same inputs always produce same results
- Timezone-aware testing with controlled datetime mocking

## Expected Business Logic Components

Based on the tests, these business logic services need to be implemented:

### Core Services (to be created in `scheduling_rules_services.py`)
```python
class SchedulingRulesService:
    def validate_minimum_notice(self, booking_datetime, school, teacher=None, class_type=None)
    def calculate_buffer_time(self, class_type, teacher=None, school=None)  
    def check_conflicts(self, teacher, student, school, date, start_time, end_time)
    def validate_booking_limits(self, teacher, student, school, date, class_type)
    def get_rule_configuration(self, school, teacher=None, class_type=None)

class ConflictDetectionService:
    def detect_student_conflicts(self, student, school, date, start_time, end_time)
    def detect_teacher_conflicts(self, teacher, school, date, start_time, end_time, buffer_minutes=0)

class AvailabilityCalculationService:
    def apply_buffer_time_to_slots(self, slots, existing_classes, buffer_minutes)
    def filter_slots_by_minimum_notice(self, slots, minimum_hours)
    def apply_booking_limits_to_availability(self, slots, teacher, school, date, current_bookings)

class SchedulingConfigurationService:
    def get_minimum_notice_hours(self, school, teacher=None, class_type=None)
    def get_buffer_time_minutes(self, school, teacher=None, class_type=None)  
    def get_booking_limits(self, school, teacher=None, student=None)
    def update_teacher_rules(self, teacher, school, rules)
```

### Utility Functions (to be created in `conflict_detection_utilities.py`)
```python
def detect_time_overlap(start1, end1, start2, end2, return_details=False)
def handle_day_boundary_cases(date, start_time, end_time)
def calculate_buffer_impact(target_start_time, target_end_time, existing_classes, buffer_minutes)
def find_available_gaps(day_start_time, day_end_time, existing_classes, buffer_minutes, required_duration_minutes)
def validate_time_boundaries(start_time, end_time, allow_midnight_crossing=False)
```

### Available Slots Services (to be created in `available_slots_services.py`)
```python
def apply_buffer_time_to_slots(slots, existing_classes, buffer_minutes, include_excluded_metadata=False)
def filter_slots_by_minimum_notice(slots, minimum_hours, include_excluded_metadata=False)
def apply_booking_limits_to_availability(slots, teacher, school, date, **limits)
def merge_availability_with_rules(base_slots, existing_classes, rules_config, teacher, school, student, date)

class AvailabilityCalculationEngine:
    def calculate_available_slots(self, request_params)

class SlotFilteringService:
    def apply_all_filters(self, slots, filters)
```

## Configuration Requirements

The tests expect these configuration capabilities:

### Default Settings
- **Minimum notice**: 2 hours  
- **Buffer time**: 15 minutes
- **Daily booking limit**: 8 classes
- **Weekly booking limit**: 40 classes

### Configuration Hierarchy
1. **School defaults** - Base configuration for all users
2. **Teacher overrides** - Teacher-specific rules (e.g., 4-hour notice, 30-minute buffer)
3. **Class-type specific** - Rules that vary by class type (individual vs group vs trial)

### Class-Type Variations
- **Individual classes**: Standard buffer time (15 min)
- **Group classes**: Longer buffer time (20 min), different notice requirements
- **Trial classes**: Shorter buffer time (10 min), flexible notice requirements

## Running the Tests

```bash
# Run all scheduling rules tests
source .venv/bin/activate
python manage.py test scheduler.test_scheduling_rules_business_logic --settings=aprendecomigo.settings.testing

# Run conflict detection utility tests  
python manage.py test scheduler.test_conflict_detection_utilities --settings=aprendecomigo.settings.testing

# Run available slots calculation tests
python manage.py test scheduler.test_available_slots_with_scheduling_rules --settings=aprendecomigo.settings.testing

# Run all scheduler tests
python manage.py test scheduler --settings=aprendecomigo.settings.testing
```

## Current Status

**✅ Tests Created**: 67 comprehensive unit tests covering all business logic scenarios
**❌ Implementation**: Business logic services not yet implemented (tests will fail with ImportError/Mock failures)
**✅ Test Quality**: All tests follow best practices and will validate correct implementation

## Next Steps

1. **Implement Core Services**: Create the business logic services in the appropriate files
2. **Add Configuration Models**: Create database models for storing scheduling rules configuration  
3. **Integration**: Connect the business logic to the existing DRF API endpoints
4. **Validation**: Run tests to ensure all business logic works correctly
5. **Performance Optimization**: Ensure services perform well with large numbers of classes/slots

## Integration with Existing Code

These new services will integrate with:
- **Existing `BookingOrchestratorService`** - Will use new `SchedulingRulesService` for validation
- **Existing `AvailableSlotsService`** - Will be enhanced with new buffer time and notice filtering
- **DRF API endpoints** - Will call the new business logic for validation and slot calculation
- **Configuration system** - New models for storing school/teacher/class-type specific rules

The tests ensure that all new business logic will work correctly when integrated with the existing codebase while maintaining the current API contracts.