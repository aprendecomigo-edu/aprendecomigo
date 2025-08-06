#!/usr/bin/env python

import os
import sys
import django
from datetime import date, time, datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.development')
django.setup()

from accounts.models import CustomUser, School, SchoolMembership, TeacherProfile, SchoolRole, SchoolSettings, EducationalSystem
from scheduler.models import TeacherAvailability, TeacherUnavailability

# Create test data similar to the test
edu_system, _ = EducationalSystem.objects.get_or_create(
    code="custom", defaults={"name": "Test System", "description": "Test educational system"}
)
school, _ = School.objects.get_or_create(name="Test School", defaults={"description": "Test Description"})
school_settings, _ = SchoolSettings.objects.get_or_create(
    school=school, defaults={"timezone": "America/New_York", "educational_system": edu_system}
)

teacher_user, _ = CustomUser.objects.get_or_create(
    email="teacher@test.com", 
    defaults={"name": "Test Teacher", "password": "testpass123"}
)
teacher_profile, _ = TeacherProfile.objects.get_or_create(
    user=teacher_user, defaults={"bio": "Test bio"}
)

# Create test date and availability
test_date = date.today() + timedelta(days=1)
day_of_week = test_date.strftime("%A").lower()

print(f"Test date: {test_date}")
print(f"Day of week: {day_of_week}")

# Clean up existing data
TeacherAvailability.objects.filter(teacher=teacher_profile).delete()
TeacherUnavailability.objects.filter(teacher=teacher_profile).delete()

# Create availability 9-17
availability = TeacherAvailability.objects.create(
    teacher=teacher_profile,
    school=school,
    day_of_week=day_of_week,
    start_time=time(9, 0),
    end_time=time(17, 0),
    is_active=True
)

# Create unavailability 14-16
unavailability = TeacherUnavailability.objects.create(
    teacher=teacher_profile,
    school=school,
    date=test_date,
    start_time=time(14, 0),
    end_time=time(16, 0),
    is_all_day=False,
    reason='Doctor appointment'
)

print(f"Created availability: {availability.start_time} - {availability.end_time}")
print(f"Created unavailability: {unavailability.start_time} - {unavailability.end_time}")

# Now test the slot generation logic
from scheduler.views import ClassScheduleViewSet

view = ClassScheduleViewSet()
conflicts = view._get_conflicting_periods(teacher_profile, test_date, [school])

print(f"Found {len(conflicts)} conflicts:")
for conflict in conflicts:
    print(f"  {conflict['start_time']} - {conflict['end_time']} (timezone: {conflict['timezone']})")

# Test slot generation
import pytz
school_timezone = pytz.timezone(school_settings.timezone)

print(f"\nSchool timezone: {school_timezone}")
print(f"Current timezone offset for {test_date}: {school_timezone.localize(datetime.combine(test_date, time(12, 0))).strftime('%z')}")

# Let's check the timezone conversion manually
availability_start = school_timezone.localize(
    datetime.combine(test_date, availability.start_time)
)
availability_end = school_timezone.localize(
    datetime.combine(test_date, availability.end_time)
)

print(f"Availability in local time: {availability.start_time} - {availability.end_time}")
print(f"Availability in timezone-aware: {availability_start} - {availability_end}")
print(f"Availability in UTC: {availability_start.astimezone(pytz.UTC)} - {availability_end.astimezone(pytz.UTC)}")

# Let's also check the conflict conversion
conflict = conflicts[0]
conflict_tz = pytz.timezone(conflict['timezone'])
conflict_start = conflict_tz.localize(
    datetime.combine(test_date, conflict['start_time'])
).astimezone(school_timezone)
conflict_end = conflict_tz.localize(
    datetime.combine(test_date, conflict['end_time'])
).astimezone(school_timezone)

print(f"Conflict in local time: {conflict['start_time']} - {conflict['end_time']}")
print(f"Conflict normalized: {conflict_start} - {conflict_end}")
print(f"Conflict in UTC: {conflict_start.astimezone(pytz.UTC)} - {conflict_end.astimezone(pytz.UTC)}")

slots = view._generate_time_slots(availability, conflicts, 60, school_timezone, test_date)

print(f"\nGenerated {len(slots)} slots:")
for slot in slots:
    print(f"  {slot['start']} - {slot['end']}")
    
# Let's convert the problematic slot back to local time to check
problem_slot_start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
problem_slot_end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
local_start = problem_slot_start.astimezone(school_timezone)
local_end = problem_slot_end.astimezone(school_timezone)
print(f"\nFirst slot in local time: {local_start.time()} - {local_end.time()}")

# Check if 15:00-16:00 slot overlaps with 14:00-16:00 unavailability
print("\nTesting overlap logic:")
slot_start = datetime.combine(test_date, time(15, 0))
slot_end = datetime.combine(test_date, time(16, 0))
unavail_start = datetime.combine(test_date, time(14, 0))
unavail_end = datetime.combine(test_date, time(16, 0))

print(f"Slot: {slot_start.time()} - {slot_end.time()}")
print(f"Unavail: {unavail_start.time()} - {unavail_end.time()}")

overlap_condition1 = slot_start < unavail_end
overlap_condition2 = slot_end > unavail_start
both_true = overlap_condition1 and overlap_condition2

print(f"slot_start < unavail_end: {slot_start.time()} < {unavail_end.time()} = {overlap_condition1}")
print(f"slot_end > unavail_start: {slot_end.time()} > {unavail_start.time()} = {overlap_condition2}")
print(f"Both conditions true (should overlap): {both_true}")