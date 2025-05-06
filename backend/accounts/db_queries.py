from django.contrib.auth import get_user_model

from .models import School, SchoolMembership, SchoolRole

User = get_user_model()


def create_school_owner(email, name, phone_number, primary_contact, school_data):
    # Create the user (without password initially)
    user = User.objects.create_user(
        email,
        password=None,  # Will be set after verification
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


def list_users_by_request_permissions(user) -> list[User]:
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

    return admin_school_ids


def user_exists(email) -> bool:
    """
    Check if a user exists in the database
    """
    return User.objects.filter(email=email).exists()


def get_user_by_email(email) -> User:
    """
    Get a user by email
    """
    return User.objects.get(email=email)
