from datetime import timedelta
import secrets

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

from .models import (
    CustomUser,
    School,
    SchoolInvitation,
    SchoolInvitationLink,
    SchoolMembership,
    SchoolRole,
    TeacherProfile,
)

User = get_user_model()


def create_school_owner(
    email: str, name: str, phone_number: str, primary_contact: str, school_data: dict, is_tutor: bool = False
) -> tuple[CustomUser, School]:
    # Use CustomUser.objects.create_user for type safety
    # Create the user
    user = CustomUser.objects.create_user(
        email=email,
        password=None,
        name=name,
        phone_number=phone_number,
        primary_contact=primary_contact,
    )

    school = School.objects.create(
        name=school_data.get("name"),
        description=school_data.get("description", ""),
        address=school_data.get("address", ""),
        contact_email=school_data.get("contact_email", email),
        phone_number=school_data.get("phone_number", phone_number),
        website=school_data.get("website", ""),
    )

    # Create school owner membership
    SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True)

    # For individual tutors, also create teacher role and profile
    if is_tutor:
        # Create teacher membership
        SchoolMembership.objects.create(user=user, school=school, role=SchoolRole.TEACHER, is_active=True)

        # Create teacher profile
        TeacherProfile.objects.create(
            user=user,
            bio="",  # Empty bio initially
            specialty="",  # Empty specialty initially
            # Other fields will use their default values
        )

    return user, school


def list_users_by_request_permissions(user) -> QuerySet:
    """
    Get list of Users based on request permissions
    """
    # System admins can see all users
    if user.is_staff or user.is_superuser:
        return User.objects.all()

    # School owners and admins can see all users in their schools
    admin_school_ids = list_school_ids_owned_or_managed(user)
    if len(admin_school_ids) > 0:
        school_user_ids = SchoolMembership.objects.filter(school_id__in=admin_school_ids, is_active=True).values_list(
            "user_id", flat=True
        )
        return User.objects.filter(id__in=school_user_ids)

    # Teachers can see themselves + students they teach (via ClassSession)
    if SchoolMembership.objects.filter(user=user, role=SchoolRole.TEACHER, is_active=True).exists() and hasattr(
        user, "teacher_profile"
    ):
        # Get students from class sessions this teacher taught
        from finances.models import ClassSession

        taught_student_ids = ClassSession.objects.filter(teacher=user.teacher_profile).values_list(
            "students", flat=True
        )

        # Include the teacher themselves + students they teach
        return User.objects.filter(models.Q(id=user.id) | models.Q(id__in=taught_student_ids)).distinct()

    # All other users (including students) can only see themselves
    return User.objects.filter(id=user.id)


def list_school_ids_owned_or_managed(user) -> list[int]:
    """
    Get list of schools ids based on request permissions
    """
    # Handle anonymous users
    if not user or not user.is_authenticated:
        return []

    admin_school_ids = SchoolMembership.objects.filter(
        user=user,
        role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
        is_active=True,
    ).values_list("school_id", flat=True)

    return list(admin_school_ids)


def user_exists(email: str) -> bool:
    """
    Check if a user exists in the database
    """
    return User.objects.filter(email=email).exists()


def get_user_by_email(email: str) -> CustomUser:
    """
    Get a user by email
    """
    return CustomUser.objects.get(email=email)


def create_user_school_and_membership(user: CustomUser, school_name: str) -> School:
    """
    Create a school and membership for a new user during signup.

    Creates a personal school for the user and assigns them as SCHOOL_OWNER.
    Must be called within a transaction - will raise exceptions if creation fails.

    Args:
        user: The newly created user who needs a school
        school_name: The name for the school (from signup form)

    Returns:
        School: The created school instance

    Raises:
        Exception: If school or membership creation fails (by design for transaction rollback)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Create a school for the user (no try/catch - let exceptions bubble up)
    school = School.objects.create(
        name=school_name,
        description=f"Personal tutoring school for {user.first_name or user.email}",
        contact_email=user.email,
    )

    # Create school membership as owner (no try/catch - let exceptions bubble up)
    SchoolMembership.objects.create(
        user=user,
        school=school,
        role=SchoolRole.SCHOOL_OWNER,
        is_active=True,
    )

    logger.info(f"Created school '{school_name}' and owner membership for user: {user.email}")
    return school


def can_user_manage_school(user: CustomUser, school_id: int) -> bool:
    """
    Check if a user can manage a specific school (is owner or admin).
    """
    return SchoolMembership.objects.filter(
        user=user,
        school_id=school_id,
        role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
        is_active=True,
    ).exists()


def create_school_invitation(
    school_id: int, email: str, invited_by: CustomUser, role: str = SchoolRole.TEACHER
) -> SchoolInvitation:
    """
    Create a school invitation with a secure token.
    """
    # Generate a secure token
    token = secrets.token_urlsafe(32)

    # Set expiration to 7 days from now
    expires_at = timezone.now() + timedelta(days=7)

    invitation = SchoolInvitation.objects.create(
        school_id=school_id,
        email=email,
        invited_by=invited_by,
        role=role,
        token=token,
        expires_at=expires_at,
    )

    return invitation


def get_schools_user_can_manage(user: CustomUser) -> QuerySet:
    """
    Get schools that the user can manage (is owner or admin).
    """
    school_ids = list_school_ids_owned_or_managed(user)
    return School.objects.filter(id__in=school_ids)


def get_or_create_school_invitation_link(
    school_id: int, role: str, created_by: CustomUser, expires_days: int = 365
) -> "SchoolInvitationLink":
    """
    Get or create a generic invitation link for a school.
    Returns existing valid link or creates a new one.
    """
    # Try to get existing valid link
    try:
        invitation_link = SchoolInvitationLink.objects.get(school_id=school_id, role=role, is_active=True)

        # Check if it's still valid (not expired)
        if invitation_link.is_valid():
            return invitation_link
        else:
            # Deactivate expired link
            invitation_link.is_active = False
            invitation_link.save()
    except SchoolInvitationLink.DoesNotExist:
        pass

    # Create new invitation link
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(days=expires_days)

    invitation_link = SchoolInvitationLink.objects.create(
        school_id=school_id,
        role=role,
        token=token,
        created_by=created_by,
        expires_at=expires_at,
        is_active=True,
    )

    return invitation_link


def join_school_via_invitation_link(
    token: str, user: CustomUser, teacher_data: dict | None = None
) -> tuple["TeacherProfile", "SchoolMembership"]:
    """
    Join a school using a generic invitation link.
    Creates teacher profile and school membership.
    """
    from django.db import transaction

    from .models import (
        Course,
        SchoolInvitationLink,
        SchoolMembership,
        TeacherCourse,
        TeacherProfile,
    )

    # Get the invitation link
    try:
        invitation_link = SchoolInvitationLink.objects.get(token=token)
    except SchoolInvitationLink.DoesNotExist:
        raise ValueError("Invalid invitation link")

    # Validate invitation link
    if not invitation_link.is_valid():
        raise ValueError("Invitation link has expired or is no longer valid")

    # Check if user is already a teacher at this school
    existing_membership = SchoolMembership.objects.filter(  # type: ignore[misc]
        user=user, school=invitation_link.school, role=invitation_link.role, is_active=True
    ).first()

    if existing_membership:
        raise ValueError("User is already a member of this school with this role")

    with transaction.atomic():
        # Create or get teacher profile
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={
                "bio": teacher_data.get("bio", "") if teacher_data else "",
                "specialty": teacher_data.get("specialty", "") if teacher_data else "",
            },
        )

        # Update teacher profile if data provided and profile already existed
        if not created and teacher_data:
            if teacher_data.get("bio"):
                teacher_profile.bio = teacher_data["bio"]
            if teacher_data.get("specialty"):
                teacher_profile.specialty = teacher_data["specialty"]
            teacher_profile.save()

        # Create school membership
        membership = SchoolMembership.objects.create(  # type: ignore[misc]
            user=user, school=invitation_link.school, role=invitation_link.role, is_active=True
        )

        # Associate courses if provided
        teacher_courses = []
        if teacher_data and teacher_data.get("course_ids"):
            course_ids = teacher_data["course_ids"]
            courses = Course.objects.filter(id__in=course_ids)

            for course in courses:
                teacher_course, _ = TeacherCourse.objects.get_or_create(
                    teacher=teacher_profile, course=course, defaults={"is_active": True}
                )
                teacher_courses.append(teacher_course)

        # Increment usage count
        invitation_link.increment_usage()

        return teacher_profile, membership
