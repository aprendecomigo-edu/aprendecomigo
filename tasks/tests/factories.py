"""
Test data factories for the tasks app.

This module provides factory classes using factory_boy to create
test data for Task and related models. These factories help create
consistent, maintainable test data with minimal setup.

Usage examples:
    # Simple task creation
    task = TaskFactory()

    # System task
    system_task = SystemTaskFactory(
        user=user,
        system_code=Task.EMAIL_VERIFICATION
    )

    # User with system tasks
    user = UserWithSystemTasksFactory()

    # Multiple tasks
    tasks = TaskFactory.create_batch(5, user=user)
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
import factory
from factory.django import DjangoModelFactory

from accounts.models import EducationalSystem, StudentProfile
from tasks.models import Task, TaskComment

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating CustomUser instances."""

    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    username = factory.LazyAttribute(lambda obj: obj.email.split("@")[0])
    phone_number = factory.Faker("phone_number")

    # Verification fields (default unverified)
    email_verified = False
    phone_verified = False

    # Profile fields
    first_login_completed = False
    onboarding_completed = False


class VerifiedUserFactory(UserFactory):
    """Factory for creating fully verified users."""

    email_verified = True
    phone_verified = True


class TaskFactory(DjangoModelFactory):
    """Factory for creating Task instances."""

    class Meta:
        model = Task

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=200)
    user = factory.SubFactory(UserFactory)

    status = "pending"
    priority = "medium"
    task_type = "personal"

    is_urgent = False
    is_system_generated = False
    system_code = None

    # Dates
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    completed_at = None


class CompletedTaskFactory(TaskFactory):
    """Factory for creating completed tasks."""

    status = "completed"
    completed_at = factory.LazyFunction(timezone.now)


class OverdueTaskFactory(TaskFactory):
    """Factory for creating overdue tasks."""

    status = "pending"
    due_date = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))


class UrgentTaskFactory(TaskFactory):
    """Factory for creating urgent tasks."""

    priority = "high"
    is_urgent = True


class SystemTaskFactory(TaskFactory):
    """Factory for creating system-generated tasks."""

    task_type = "system"
    is_system_generated = True
    system_code = Task.EMAIL_VERIFICATION
    priority = "high"

    title = factory.LazyAttribute(lambda obj: f"System Task: {obj.system_code}")
    description = factory.LazyAttribute(lambda obj: f"System generated task for {obj.system_code}")


class EmailVerificationTaskFactory(SystemTaskFactory):
    """Factory for creating email verification tasks."""

    system_code = Task.EMAIL_VERIFICATION
    title = "Verify your email address"
    description = "Click the verification link sent to your email"


class PhoneVerificationTaskFactory(SystemTaskFactory):
    """Factory for creating phone verification tasks."""

    system_code = Task.PHONE_VERIFICATION
    title = "Verify your phone number"
    description = "Enter the SMS code to verify your phone"


class FirstStudentTaskFactory(SystemTaskFactory):
    """Factory for creating first student tasks."""

    system_code = Task.FIRST_STUDENT_ADDED
    title = "Add your first student"
    description = "Add a student to start using the platform"
    priority = "medium"


class OnboardingTaskFactory(TaskFactory):
    """Factory for creating onboarding tasks."""

    task_type = "onboarding"
    is_system_generated = True
    priority = "high"

    title = factory.Iterator(
        ["Complete Your Profile", "Explore the Dashboard", "Set Up Your School", "Invite Your First Teacher"]
    )

    description = factory.LazyAttribute(lambda obj: f"Onboarding step: {obj.title}")


class AssignmentTaskFactory(TaskFactory):
    """Factory for creating assignment tasks."""

    task_type = "assignment"
    priority = "high"

    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("paragraph", nb_sentences=3)

    # Assignment tasks often have specific due dates
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=14))


class TaskCommentFactory(DjangoModelFactory):
    """Factory for creating TaskComment instances."""

    class Meta:
        model = TaskComment

    task = factory.SubFactory(TaskFactory)
    user = factory.SelfAttribute("task.user")  # Default to task owner
    comment = factory.Faker("paragraph", nb_sentences=2)


class EducationalSystemFactory(DjangoModelFactory):
    """Factory for creating EducationalSystem instances."""

    class Meta:
        model = EducationalSystem
        django_get_or_create = ("code",)

    name = factory.Iterator(["Portuguese System", "British System", "International Baccalaureate", "American System"])
    code = factory.Iterator(["pt", "uk", "ib", "us"])
    description = factory.LazyAttribute(lambda obj: f"{obj.name} educational curriculum")


class StudentProfileFactory(DjangoModelFactory):
    """Factory for creating StudentProfile instances."""

    class Meta:
        model = StudentProfile

    user = factory.SubFactory(UserFactory)
    educational_system = factory.SubFactory(EducationalSystemFactory)

    birth_date = factory.Faker("date_of_birth", minimum_age=5, maximum_age=18)
    school_year = factory.Iterator(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])

    address = factory.Faker("address")


class UserWithSystemTasksFactory(UserFactory):
    """Factory that creates a user with all system tasks."""

    @factory.post_generation
    def system_tasks(obj, create, extracted, **kwargs):
        """Create system tasks after user creation."""
        if not create:
            return

        # Create all system verification tasks
        EmailVerificationTaskFactory(user=obj)
        PhoneVerificationTaskFactory(user=obj)
        FirstStudentTaskFactory(user=obj)


class UserWithCompletedTasksFactory(UserFactory):
    """Factory that creates a user with completed system tasks."""

    email_verified = True
    phone_verified = True

    @factory.post_generation
    def completed_system_tasks(obj, create, extracted, **kwargs):
        """Create completed system tasks after user creation."""
        if not create:
            return

        # Create completed system tasks
        EmailVerificationTaskFactory(user=obj, status="completed", completed_at=timezone.now())
        PhoneVerificationTaskFactory(user=obj, status="completed", completed_at=timezone.now())
        FirstStudentTaskFactory(user=obj, status="completed", completed_at=timezone.now())


class TaskWithCommentsFactory(TaskFactory):
    """Factory that creates a task with comments."""

    @factory.post_generation
    def comments(obj, create, extracted, **kwargs):
        """Create comments after task creation."""
        if not create:
            return

        # Create 2-5 comments by default
        comment_count = extracted or factory.Faker("random_int", min=2, max=5).evaluate(None, None, {})
        TaskCommentFactory.create_batch(comment_count, task=obj)


# Factory traits for common combinations
class TaskTraits:
    """Common traits that can be applied to task factories."""

    @staticmethod
    def with_due_tomorrow():
        """Task due tomorrow."""
        return {"due_date": timezone.now() + timedelta(days=1)}

    @staticmethod
    def with_due_yesterday():
        """Overdue task."""
        return {"due_date": timezone.now() - timedelta(days=1), "status": "pending"}

    @staticmethod
    def high_priority():
        """High priority task."""
        return {"priority": "high", "is_urgent": True}

    @staticmethod
    def low_priority():
        """Low priority task."""
        return {"priority": "low", "is_urgent": False}


# Convenience methods for common test scenarios
def create_user_with_mixed_tasks(task_count=5):
    """Create a user with a mix of different task types and statuses."""
    user = UserFactory()

    # Create system tasks
    EmailVerificationTaskFactory(user=user)
    PhoneVerificationTaskFactory(user=user, status="completed", completed_at=timezone.now())
    FirstStudentTaskFactory(user=user)

    # Create user tasks with various statuses
    TaskFactory.create_batch(
        task_count,
        user=user,
        status=factory.Iterator(["pending", "in_progress", "completed"]),
        priority=factory.Iterator(["low", "medium", "high"]),
        task_type=factory.Iterator(["personal", "assignment"]),
    )

    return user


def create_verification_scenario():
    """Create a complete verification test scenario."""
    # Unverified user
    unverified_user = UserFactory(email_verified=False, phone_verified=False)
    UserWithSystemTasksFactory(email=unverified_user.email, email_verified=False, phone_verified=False)

    # Email-only verified user
    email_verified_user = UserFactory(email_verified=True, phone_verified=False)
    EmailVerificationTaskFactory(user=email_verified_user, status="completed", completed_at=timezone.now())
    PhoneVerificationTaskFactory(user=email_verified_user)
    FirstStudentTaskFactory(user=email_verified_user)

    # Fully verified user
    fully_verified_user = UserWithCompletedTasksFactory()

    return {"unverified": unverified_user, "email_only": email_verified_user, "fully_verified": fully_verified_user}


def create_educational_scenario():
    """Create educational system with students for testing."""
    # Create educational system
    educational_system = EducationalSystemFactory()

    # Create students
    students = []
    for i in range(3):
        student_user = UserFactory(email=f"student{i}@example.com")
        student_profile = StudentProfileFactory(user=student_user, educational_system=educational_system)
        students.append(student_profile)

    return {"educational_system": educational_system, "students": students}


# Export commonly used factories for easy imports
__all__ = [
    "AssignmentTaskFactory",
    "CompletedTaskFactory",
    "EducationalSystemFactory",
    "EmailVerificationTaskFactory",
    "FirstStudentTaskFactory",
    "OnboardingTaskFactory",
    "OverdueTaskFactory",
    "PhoneVerificationTaskFactory",
    "StudentProfileFactory",
    "SystemTaskFactory",
    "TaskCommentFactory",
    "TaskFactory",
    "TaskTraits",
    "TaskWithCommentsFactory",
    "UrgentTaskFactory",
    "UserFactory",
    "UserWithCompletedTasksFactory",
    "UserWithSystemTasksFactory",
    "VerifiedUserFactory",
    "create_educational_scenario",
    "create_user_with_mixed_tasks",
    "create_verification_scenario",
]
