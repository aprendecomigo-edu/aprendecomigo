"""
Management command to verify and display the created test data.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser, SchoolMembership, SchoolRole
from scheduler.models import ClassSchedule
from tasks.models import Task


class Command(BaseCommand):
    help = "Verify and display created test data for school admin dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-admin-email",
            type=str,
            default="admin.escola@aprendecomigo.com",
            help="Email for the school admin user",
        )

    def handle(self, *args, **options):
        admin_email = options["school_admin_email"]

        try:
            # Get admin user
            admin_user = CustomUser.objects.get(email=admin_email)

            # Get admin's school
            admin_membership = SchoolMembership.objects.filter(
                user=admin_user, role__in=[SchoolRole.SCHOOL_ADMIN, SchoolRole.SCHOOL_OWNER], is_active=True
            ).first()

            if not admin_membership:
                self.stdout.write(self.style.ERROR(f"No admin school found for {admin_email}"))
                return

            school = admin_membership.school

            # Display school info
            self.stdout.write(self.style.SUCCESS("\n=== SCHOOL INFORMATION ==="))
            self.stdout.write(f"School: {school.name}")
            self.stdout.write(f"Admin: {admin_user.name} ({admin_user.email})")

            # Display tasks
            tasks = Task.objects.filter(user=admin_user).order_by("-priority", "due_date")
            self.stdout.write(self.style.SUCCESS(f"\n=== ADMIN TASKS ({tasks.count()}) ==="))
            for task in tasks:
                urgent_flag = " 🚨" if task.is_urgent else ""
                days_until = task.days_until_due
                due_info = f" (in {days_until} days)" if days_until is not None else ""
                self.stdout.write(f"[{task.priority.upper()}] {task.title}{urgent_flag}{due_info}")
                self.stdout.write(f"  Status: {task.status} | Type: {task.task_type}")
                if task.description:
                    self.stdout.write(f"  Description: {task.description[:80]}...")
                self.stdout.write("")

            # Display upcoming classes
            upcoming_classes = ClassSchedule.objects.filter(
                school=school, scheduled_date__gte=timezone.now().date()
            ).order_by("scheduled_date", "start_time")[:10]

            self.stdout.write(self.style.SUCCESS("\n=== UPCOMING CLASSES (next 10) ==="))
            for schedule in upcoming_classes:
                self.stdout.write(f"{schedule.scheduled_date} {schedule.start_time} - {schedule.title}")
                self.stdout.write(f"  Teacher: {schedule.teacher.user.name} | Student: {schedule.student.name}")
                self.stdout.write(f"  Status: {schedule.status} | Duration: {schedule.duration_minutes}min")
                self.stdout.write("")

            # Display school members summary
            teachers = SchoolMembership.objects.filter(school=school, role=SchoolRole.TEACHER, is_active=True)
            students = SchoolMembership.objects.filter(school=school, role=SchoolRole.STUDENT, is_active=True)

            self.stdout.write(self.style.SUCCESS("\n=== SCHOOL MEMBERS SUMMARY ==="))
            self.stdout.write(f"Teachers: {teachers.count()}")
            for teacher_membership in teachers:
                self.stdout.write(f"  - {teacher_membership.user.name} ({teacher_membership.user.email})")

            self.stdout.write(f"\nStudents: {students.count()}")
            for student_membership in students:
                self.stdout.write(f"  - {student_membership.user.name} ({student_membership.user.email})")

            # Display statistics
            total_classes = ClassSchedule.objects.filter(school=school).count()
            completed_classes = ClassSchedule.objects.filter(school=school, status="completed").count()
            pending_tasks = Task.objects.filter(user=admin_user, status="pending").count()

            self.stdout.write(self.style.SUCCESS("\n=== STATISTICS ==="))
            self.stdout.write(f"Total classes: {total_classes}")
            self.stdout.write(f"Completed classes: {completed_classes}")
            self.stdout.write(f"Pending admin tasks: {pending_tasks}")

        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {admin_email} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error verifying data: {e!s}"))
