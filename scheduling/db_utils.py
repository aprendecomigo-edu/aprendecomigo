from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from accounts.models import Student, Teacher

from .models import ClassSession, ClassType

User = get_user_model()


def get_google_token(admin_email):
    """
    Get token from a user's django-allauth social account

    Args:
        admin_email: Email of admin user whose Google credentials to use

    Returns:
        token, refresh_token
    """
    if not admin_email:
        raise ValueError("Admin email is required for authentication")

    try:
        # Find the admin's social account
        social_account = SocialAccount.objects.get(
            user__email=admin_email, provider="google"
        )
        # Get their Google token
        social_token = SocialToken.objects.get(account=social_account)
        return (
            social_token.token,
            social_token.token_secret,
        )

    except (ObjectDoesNotExist, KeyError) as e:
        raise ValueError(f"Could not get Google credentials for {admin_email}: {e}")


def get_or_create_class_type(class_type_code):
    """Get or create a ClassType object based on the class type code."""
    try:
        class_type = ClassType.objects.get(name=class_type_code)
    except ClassType.DoesNotExist:
        print(
            f"WARNING: Class type code '{class_type_code}' not found in database. "
            f"Creating with default values."
        )
        class_type = ClassType.objects.create(
            name=class_type_code,
            hourly_rate=0,  # Default rate that should be updated by admin
        )
    return class_type


def get_or_create_teacher(teacher_name):
    """Get or create a Teacher user based on the teacher name."""
    teacher_username = teacher_name.replace(" ", "").lower()
    teacher_first_name = (
        teacher_name.split()[0] if " " in teacher_name else teacher_name
    )
    teacher_last_name = teacher_name.split()[-1] if " " in teacher_name else ""

    # Try different ways to find the teacher
    try:
        # Try by username first
        teacher = User.objects.get(username=teacher_username)
    except User.DoesNotExist:
        try:
            # Try by first and last name
            teacher = User.objects.filter(
                first_name=teacher_first_name, last_name=teacher_last_name
            ).first()

            if not teacher:
                raise User.DoesNotExist
        except User.DoesNotExist:
            # Create a placeholder teacher
            placeholder_email = f"{teacher_username}@placeholder.aprendecomigo.com"
            teacher = User.objects.create(
                username=teacher_username,
                email=placeholder_email,
                name=teacher_name,  # Set the name field (required)
                first_name=teacher_first_name,
                last_name=teacher_last_name,
                user_type="teacher",  # Set user type to teacher
            )

            # Create a basic Teacher profile for the placeholder user
            try:
                # Use empty values for optional fields
                Teacher.objects.create(
                    user=teacher,
                    bio="",
                    specialty="",
                    education="",
                    availability="",
                    address="",
                )
                print(f"Created placeholder teacher profile for: {teacher.email}")
            except Exception as e:
                print(f"Failed to create teacher profile: {e}")

            print(
                f"Created placeholder teacher: {teacher.email} (needs profile completion)"
            )

    return teacher


def get_or_create_student(student_name):
    """Get or create a Student user based on the student name."""
    student_username = student_name.replace(" ", "").lower()
    student_first_name = (
        student_name.split()[0] if " " in student_name else student_name
    )
    student_last_name = student_name.split()[-1] if " " in student_name else ""

    # Try different ways to find the student
    try:
        # Try by username first
        student = User.objects.get(username=student_username)
    except User.DoesNotExist:
        try:
            # Try by first and last name
            student = User.objects.filter(
                first_name=student_first_name, last_name=student_last_name
            ).first()

            if not student:
                raise User.DoesNotExist
        except User.DoesNotExist:
            # Create a placeholder student
            placeholder_email = f"{student_username}@placeholder.aprendecomigo.com"
            student = User.objects.create(
                username=student_username,
                email=placeholder_email,
                name=student_name,  # Set the name field (required)
                first_name=student_first_name,
                last_name=student_last_name,
                user_type="student",  # Set user type to student
            )

            # Create a basic Student profile for the placeholder user
            try:
                # Use default values for required fields
                Student.objects.create(
                    user=student,
                    school_year="(Pending)",
                    birth_date=timezone.now().date(),  # Today as placeholder
                    address="(Pending)",
                )
                print(f"Created placeholder student profile for: {student.email}")
            except Exception as e:
                print(f"Failed to create student profile: {e}")

            print(
                f"Created placeholder student: {student.email} (needs profile completion)"
            )

    return student


def create_or_update_class_session(event_data, teacher, class_type, student):
    """Create or update a ClassSession record based on event data."""
    session, created_new = ClassSession.objects.update_or_create(
        google_calendar_id=event_data["google_calendar_id"],
        defaults={
            "title": event_data["title"],
            "teacher": teacher,
            "class_type": class_type,
            "start_time": event_data["start_time"],
            "end_time": event_data["end_time"],
            "attended": event_data["attended"],
        },
    )

    # Add student to the session
    session.students.add(student)

    return session, created_new
