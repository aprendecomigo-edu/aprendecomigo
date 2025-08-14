"""
Management command to create a teacher test user for testing teacher dashboard routing.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole


class Command(BaseCommand):
    help = "Create a teacher test user for testing teacher dashboard functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, default="teacher.test@aprendecomigo.com", help="Email for the teacher test user"
        )
        parser.add_argument("--name", type=str, default="Teacher Test User", help="Name for the teacher test user")
        parser.add_argument(
            "--school-name",
            type=str,
            default="Test School for Teachers",
            help="Name of the school to create for the teacher",
        )

    def handle(self, *args, **options):
        email = options["email"]
        name = options["name"]
        school_name = options["school_name"]

        try:
            with transaction.atomic():
                # Check if user already exists
                if CustomUser.objects.filter(email=email).exists():
                    user = CustomUser.objects.get(email=email)
                    self.stdout.write(
                        self.style.WARNING(f"User with email {email} already exists. Using existing user.")
                    )
                else:
                    # Create the teacher user
                    user = CustomUser.objects.create_user(
                        email=email,
                        name=name,
                        email_verified=True,
                        first_login_completed=True,
                        onboarding_completed=True,
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created user: {user.email}"))

                # Check if school exists
                school, created = School.objects.get_or_create(
                    name=school_name,
                    defaults={
                        "description": "Test school for teacher dashboard testing",
                        "address": "Test Address",
                        "contact_email": "contact@testschool.com",
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created school: {school.name}"))
                else:
                    self.stdout.write(
                        self.style.WARNING(f"School {school.name} already exists. Using existing school.")
                    )

                # Create or update teacher membership
                membership, created = SchoolMembership.objects.get_or_create(
                    user=user,
                    school=school,
                    defaults={"role": SchoolRole.TEACHER, "is_active": True, "joined_at": timezone.now()},
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created teacher membership for {user.email} at {school.name}")
                    )
                else:
                    # Update existing membership to be teacher
                    membership.role = SchoolRole.TEACHER
                    membership.is_active = True
                    membership.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated membership for {user.email} to TEACHER role"))

                # Verify the setup
                self.stdout.write(self.style.SUCCESS("\n--- Teacher Test User Created Successfully ---"))
                self.stdout.write(f"Email: {user.email}")
                self.stdout.write(f"Name: {user.name}")
                self.stdout.write(f"School: {school.name}")
                self.stdout.write(f"Role: {membership.role}")
                self.stdout.write(f"Active: {membership.is_active}")

                # Verify what the dashboard_info endpoint would return
                user_type = None
                is_admin = False

                # Check teacher role
                if SchoolMembership.objects.filter(user=user, role=SchoolRole.TEACHER, is_active=True).exists():
                    user_type = "teacher"

                self.stdout.write("\n--- Expected API Response ---")
                self.stdout.write(f"user_type: {user_type}")
                self.stdout.write(f"is_admin: {is_admin}")
                self.stdout.write("Expected routing: /(teacher)/dashboard")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating teacher test user: {e!s}"))
            raise e
