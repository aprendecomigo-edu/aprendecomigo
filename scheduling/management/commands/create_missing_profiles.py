from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Student, Teacher

User = get_user_model()


class Command(BaseCommand):
    help = "Create Student and Teacher profiles for existing users who lack them"

    def handle(self, **options):
        # Process student profiles
        self.stdout.write(self.style.SUCCESS("Processing student profiles..."))
        student_users = User.objects.filter(user_type="student")
        student_created = 0
        student_skipped = 0
        student_error = 0

        for user in student_users:
            try:
                # Check if student profile already exists
                Student.objects.get(user=user)
                student_skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Student profile already exists for: {user.email}"
                    )
                )
            except Student.DoesNotExist:
                try:
                    # Create student profile with default values
                    Student.objects.create(
                        user=user,
                        school_year="(Pending)",
                        birth_date=timezone.now().date(),  # Today as placeholder
                        address="(Pending)",
                    )
                    student_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created student profile for: {user.email}")
                    )
                except Exception as e:
                    student_error += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error creating student profile for {user.email}: {e}"
                        )
                    )

        # Process teacher profiles
        self.stdout.write(self.style.SUCCESS("\nProcessing teacher profiles..."))
        teacher_users = User.objects.filter(user_type="teacher")
        teacher_created = 0
        teacher_skipped = 0
        teacher_error = 0

        for user in teacher_users:
            try:
                # Check if teacher profile already exists
                Teacher.objects.get(user=user)
                teacher_skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Teacher profile already exists for: {user.email}"
                    )
                )
            except Teacher.DoesNotExist:
                try:
                    # Create teacher profile with default values
                    Teacher.objects.create(
                        user=user,
                        bio="",
                        specialty="",
                        education="",
                        availability="",
                        address="",
                    )
                    teacher_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created teacher profile for: {user.email}")
                    )
                except Exception as e:
                    teacher_error += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error creating teacher profile for {user.email}: {e}"
                        )
                    )

        # Print summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nComplete! "
                f"Students: Created {student_created}, skipped {student_skipped}, "
                f"errors {student_error} | "
                f"Teachers: Created {teacher_created}, skipped {teacher_skipped}, "
                f"errors {teacher_error}"
            )
        )
