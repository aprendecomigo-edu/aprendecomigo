from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
import secrets
from datetime import timedelta
from django.utils import timezone

from .models import CustomUser, School, SchoolMembership, SchoolRole, SchoolInvitation

User = get_user_model()


def create_school_owner(
    email: str, name: str, phone_number: str, primary_contact: str, school_data: dict
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

    # Create school membership
    SchoolMembership.objects.create(
        user=user, school=school, role=SchoolRole.SCHOOL_OWNER, is_active=True
    )
    return user, school


def list_users_by_request_permissions(user) -> QuerySet:
    """
    Get list of Users based on request permissions
    """
    # System admins can see all users
    if user.is_staff or user.is_superuser:
        return User.objects.all()

    # School owners and admins can see users in their schools
    # Get all schools where this user is an owner or admin
    admin_school_ids = list_school_ids_owned_or_managed(user)

    if len(admin_school_ids) > 0:
        # Get all users in these schools
        school_user_ids = SchoolMembership.objects.filter(
            school_id__in=admin_school_ids, is_active=True
        ).values_list("user_id", flat=True)

        return User.objects.filter(id__in=school_user_ids)

    # Other users can only see themselves
    return User.objects.filter(id=user.id)


def list_school_ids_owned_or_managed(user) -> list[int]:
    """
    Get list of schools ids based on request permissions
    """
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
    school_id: int, 
    email: str, 
    invited_by: CustomUser, 
    role: str = SchoolRole.TEACHER
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
