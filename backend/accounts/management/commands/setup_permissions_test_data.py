import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import (
    CustomUser,
    EducationalSystem,
    School,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Set up test data for permissions testing with complex multi-role scenarios"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean existing test data before creating new data",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating it",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.clean = options["clean"]

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be created"))

        if self.clean:
            self.clean_test_data()

        self.create_test_data()

        if not self.dry_run:
            self.stdout.write(self.style.SUCCESS("Test data setup completed successfully!"))
        else:
            self.stdout.write(self.style.WARNING("DRY RUN completed - no actual data created"))

    def clean_test_data(self):
        """Clean existing test data"""
        self.stdout.write("Cleaning existing test data...")

        if not self.dry_run:
            # Delete test schools (this will cascade to memberships)
            test_schools = School.objects.filter(
                name__in=["Test School", "Test School 2", "Test School 3"]
            )
            for school in test_schools:
                self.stdout.write(f"  Deleting school: {school.name}")
                school.delete()

            # Delete test users
            test_users = CustomUser.objects.filter(
                email__in=[
                    "test.manager@example.com",
                    "school2.admin@example.com",
                    "school3.owner@example.com",
                    "additional.teacher@example.com",
                    "additional.student@example.com",
                    "student2@testschool.com",
                    "teacher2@testschool.com",
                ]
            )
            for user in test_users:
                self.stdout.write(f"  Deleting user: {user.email}")
                user.delete()

    @transaction.atomic
    def create_test_data(self):
        """Create comprehensive test data for permissions testing"""
        self.stdout.write("Creating test data...")

        # Get or create educational system
        educational_system = self.get_or_create_educational_system()

        # Create schools
        schools = self.create_schools()

        # Create main test user with multiple roles
        main_user = self.create_main_test_user()

        # Create supporting users
        supporting_users = self.create_supporting_users()

        # Assign roles and create memberships
        self.create_school_memberships(main_user, supporting_users, schools)

        # Create profiles for users who need them
        self.create_user_profiles(main_user, supporting_users, educational_system)

        # Display summary
        self.display_summary(main_user, supporting_users, schools)

    def get_or_create_educational_system(self):
        """Get or create Portugal educational system for testing"""
        if not self.dry_run:
            system, created = EducationalSystem.objects.get_or_create(
                code="pt",
                defaults={
                    "name": "Portugal",
                    "description": "Portuguese educational system for testing",
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write("  Created Portugal educational system")
            return system
        else:
            self.stdout.write("  Would get/create Portugal educational system")
            return None

    def create_schools(self):
        """Create the three test schools"""
        schools_data = [
            {
                "name": "Test School",
                "description": "Primary test school where main user is school owner",
                "contact_email": "contact@testschool.com",
                "address": "123 Test Street, Porto, Portugal",
                "phone_number": "+351 123 456 789",
            },
            {
                "name": "Test School 2",
                "description": "Secondary test school where main user is teacher",
                "contact_email": "contact@testschool2.com",
                "address": "456 Education Ave, Lisbon, Portugal",
                "phone_number": "+351 987 654 321",
            },
            {
                "name": "Test School 3",
                "description": "Third test school where main user is student",
                "contact_email": "contact@testschool3.com",
                "address": "789 Learning Blvd, Braga, Portugal",
                "phone_number": "+351 555 123 456",
            },
        ]

        schools = {}
        for school_data in schools_data:
            self.stdout.write(f"  Creating school: {school_data['name']}")
            if not self.dry_run:
                school = School.objects.create(**school_data)
                schools[school_data["name"]] = school
            else:
                schools[school_data["name"]] = None

        return schools

    def create_main_test_user(self):
        """Create the main test user who will have multiple roles"""
        user_data = {
            "email": "test.manager@example.com",
            "name": "Multi Role Test Manager",
            "phone_number": "+351 123 000 001",
            "email_verified": True,
            "phone_verified": True,
            "primary_contact": "email",
        }

        self.stdout.write(f"  Creating main test user: {user_data['email']}")
        if not self.dry_run:
            user = CustomUser.objects.create_user(**user_data)
            return user
        else:
            return None

    def create_supporting_users(self):
        """Create supporting users for each school"""
        users_data = [
            {
                "email": "school2.admin@example.com",
                "name": "School 2 Administrator",
                "phone_number": "+351 123 000 002",
                "role": "School 2 Owner",
            },
            {
                "email": "school3.owner@example.com",
                "name": "School 3 Owner",
                "phone_number": "+351 123 000 003",
                "role": "School 3 Owner",
            },
            {
                "email": "additional.teacher@example.com",
                "name": "Additional Teacher",
                "phone_number": "+351 123 000 004",
                "role": "Teacher at Test School",
            },
            {
                "email": "additional.student@example.com",
                "name": "Additional Student",
                "phone_number": "+351 123 000 005",
                "role": "Student at Test School",
            },
            {
                "email": "student2@testschool.com",
                "name": "Second Test Student",
                "phone_number": "+351 123 000 006",
                "role": "Student at Test School 2",
            },
            {
                "email": "teacher2@testschool.com",
                "name": "Second Test Teacher",
                "phone_number": "+351 123 000 007",
                "role": "Teacher at Test School 3",
            },
        ]

        users = {}
        for user_data in users_data:
            email = user_data["email"]
            role = user_data.pop("role")  # Remove role from user_data
            user_data.update(
                {"email_verified": True, "phone_verified": True, "primary_contact": "email"}
            )

            self.stdout.write(f"  Creating user: {email} ({role})")
            if not self.dry_run:
                user = CustomUser.objects.create_user(**user_data)
                users[email] = user
            else:
                users[email] = None

        return users

    def create_school_memberships(self, main_user, supporting_users, schools):
        """Create school memberships for all users"""

        # Main user memberships (the complex multi-role scenario)
        main_memberships = [
            ("Test School", SchoolRole.SCHOOL_OWNER, "Primary school ownership"),
            ("Test School 2", SchoolRole.TEACHER, "Teaching role at secondary school"),
            ("Test School 3", SchoolRole.STUDENT, "Learning role at third school"),
        ]

        self.stdout.write("  Creating memberships for main user:")
        for school_name, role, description in main_memberships:
            self.stdout.write(f"    {school_name}: {role} ({description})")
            if not self.dry_run:
                SchoolMembership.objects.create(
                    user=main_user, school=schools[school_name], role=role, is_active=True
                )

        # Supporting user memberships
        supporting_memberships = [
            ("school2.admin@example.com", "Test School 2", SchoolRole.SCHOOL_OWNER),
            ("school3.owner@example.com", "Test School 3", SchoolRole.SCHOOL_OWNER),
            ("additional.teacher@example.com", "Test School", SchoolRole.TEACHER),
            ("additional.student@example.com", "Test School", SchoolRole.STUDENT),
            ("student2@testschool.com", "Test School 2", SchoolRole.STUDENT),
            ("teacher2@testschool.com", "Test School 3", SchoolRole.TEACHER),
        ]

        self.stdout.write("  Creating memberships for supporting users:")
        for email, school_name, role in supporting_memberships:
            self.stdout.write(f"    {email}: {school_name} as {role}")
            if not self.dry_run:
                SchoolMembership.objects.create(
                    user=supporting_users[email],
                    school=schools[school_name],
                    role=role,
                    is_active=True,
                )

    def create_user_profiles(self, main_user, supporting_users, educational_system):
        """Create teacher and student profiles where needed"""

        if self.dry_run:
            self.stdout.write("  Would create teacher and student profiles")
            return

        # Create teacher profiles
        teacher_users = [
            (
                main_user,
                "Multi-role user with extensive experience in education management and teaching",
            ),
            (
                supporting_users["additional.teacher@example.com"],
                "Experienced mathematics teacher specializing in secondary education",
            ),
            (
                supporting_users["teacher2@testschool.com"],
                "Language arts teacher with focus on Portuguese literature",
            ),
        ]

        self.stdout.write("  Creating teacher profiles:")
        for user, bio in teacher_users:
            if user:
                self.stdout.write(f"    Teacher profile for: {user.email}")
                TeacherProfile.objects.create(
                    user=user,
                    bio=bio,
                    specialty="General Education",
                    education="Bachelor's in Education",
                    hourly_rate=25.00,
                    availability="Weekdays 9AM-6PM",
                    address="Teaching address, Portugal",
                    phone_number=user.phone_number,
                )

        # Create student profiles
        student_users = [
            (
                main_user,
                "12",
                date(1990, 5, 15),
            ),  # 12th grade, older student (continuing education)
            (supporting_users["additional.student@example.com"], "10", date(2008, 3, 22)),
            (supporting_users["student2@testschool.com"], "11", date(2007, 8, 10)),
        ]

        self.stdout.write("  Creating student profiles:")
        for user, school_year, birth_date in student_users:
            if user and educational_system:
                self.stdout.write(f"    Student profile for: {user.email}")
                StudentProfile.objects.create(
                    user=user,
                    educational_system=educational_system,
                    school_year=school_year,
                    birth_date=birth_date,
                    address=f"Student address for {user.name}, Portugal",
                    cc_number=f"CC{user.id:08d}" if user.id else "CC00000000",
                )

    def display_summary(self, main_user, supporting_users, schools):
        """Display a summary of created test data"""
        self.stdout.write(self.style.SUCCESS("\n=== TEST DATA SUMMARY ==="))

        # Schools summary
        self.stdout.write(self.style.HTTP_INFO("\nSchools Created:"))
        for name, school in schools.items():
            if school or self.dry_run:
                self.stdout.write(f"  • {name}")

        # Main user summary
        self.stdout.write(self.style.HTTP_INFO("\nMain Test User: test.manager@example.com"))
        self.stdout.write("  Roles across schools:")
        self.stdout.write("  • Test School: school_owner (can manage everything)")
        self.stdout.write("  • Test School 2: teacher (can teach, limited admin)")
        self.stdout.write("  • Test School 3: student (learning access only)")

        # Supporting users summary
        self.stdout.write(self.style.HTTP_INFO("\nSupporting Users:"))
        self.stdout.write("  • school2.admin@example.com (owner of Test School 2)")
        self.stdout.write("  • school3.owner@example.com (owner of Test School 3)")
        self.stdout.write("  • additional.teacher@example.com (teacher at Test School)")
        self.stdout.write("  • additional.student@example.com (student at Test School)")
        self.stdout.write("  • student2@testschool.com (student at Test School 2)")
        self.stdout.write("  • teacher2@testschool.com (teacher at Test School 3)")

        # Testing scenarios
        self.stdout.write(self.style.HTTP_INFO("\nKey Testing Scenarios:"))
        self.stdout.write("  1. Multi-role permissions (same user, different schools)")
        self.stdout.write("  2. Cross-school access control")
        self.stdout.write("  3. Role-based dashboard content")
        self.stdout.write("  4. School management boundaries")
        self.stdout.write("  5. Teacher/Student profile access")

        if not self.dry_run:
            self.stdout.write(self.style.WARNING("\nTo test, log in as test.manager@example.com"))
            self.stdout.write("You should see different views/permissions based on school context")
