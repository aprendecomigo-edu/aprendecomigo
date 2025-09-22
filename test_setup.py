import datetime

from django.contrib.auth import get_user_model

from accounts.models.profiles import StudentProfile
from accounts.models.schools import School, SchoolMembership

User = get_user_model()
user = User.objects.get(email="admin@test.com")
school = School.objects.get(id=1)  # Use existing "Test Practice" school
membership, created = SchoolMembership.objects.get_or_create(
    user=user, school=school, defaults={"role": "ADMIN", "is_active": True}
)
user.active_school = school
user.save()

# Create multiple students with same name for testing
for i in range(3):
    # Create a user for the student
    student_user, _ = User.objects.get_or_create(email=f"diana{i}@test.com", defaults={"name": f"Diana {chr(65 + i)}"})
    s, _ = StudentProfile.objects.get_or_create(
        user=student_user,
        school=school,
        defaults={"birth_date": datetime.date(2010, 1, 1), "educational_system": "PRIMARY", "school_year": "3"},
    )
    # Create school membership for student
    SchoolMembership.objects.get_or_create(
        user=student_user, school=school, defaults={"role": "STUDENT", "is_active": True}
    )
    print(f"Student: {student_user.name}")

# Create another student
other_user, _ = User.objects.get_or_create(email="other@test.com", defaults={"name": "Other Student"})
other, _ = StudentProfile.objects.get_or_create(
    user=other_user,
    school=school,
    defaults={"birth_date": datetime.date(2010, 1, 1), "educational_system": "PRIMARY", "school_year": "3"},
)
SchoolMembership.objects.get_or_create(user=other_user, school=school, defaults={"role": "STUDENT", "is_active": True})
print(f"School: {school.name}, Membership: {membership.role}")
print(f"Total students: {StudentProfile.objects.filter(school=school).count()}")
