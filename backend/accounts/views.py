from common.permissions import (
    IsOwnerOrSchoolAdmin,
    IsSchoolOwnerOrAdmin,
    IsStudentInAnySchool,
    IsTeacherInAnySchool,
)
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.utils import timezone
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    EmailVerificationCode,
    School,
    SchoolInvitation,
    SchoolMembership,
    SchoolRole,
    StudentProfile,
    TeacherProfile
)
from .serializers import (
    BiometricVerifySerializer,
    CreateUserSerializer,
    EmailRequestSerializer,
    EmailVerifySerializer,
    InvitationAcceptSerializer,
    InvitationRequestSerializer,
    SchoolInvitationSerializer,
    SchoolMembershipSerializer,
    SchoolSerializer,
    SchoolWithMembersSerializer,
    StudentSerializer,
    TeacherSerializer,
    UserSerializer,
    UserWithRolesSerializer,
)
from common.throttles import EmailCodeRequestThrottle, EmailBasedThrottle, IPBasedThrottle, IPSignupThrottle
User = get_user_model()


# Base class for authenticated views
class KnoxAuthenticatedAPIView(APIView):
    """
    Base class for views that require Knox token authentication.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


# Base class for authenticated viewsets
class KnoxAuthenticatedViewSet(viewsets.ModelViewSet):
    """
    Base class for viewsets that require Knox token authentication.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class UserViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for users.
    """

    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        # System admins can see all users
        if user.is_staff or user.is_superuser:
            return User.objects.all()

        # School owners and admins can see users in their schools
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists():
            # Get all schools where this user is an owner or admin
            admin_school_ids = SchoolMembership.objects.filter(
                user=user,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True
            ).values_list('school_id', flat=True)

            # Get all users in these schools
            school_user_ids = SchoolMembership.objects.filter(
                school_id__in=admin_school_ids,
                is_active=True
            ).values_list('user_id', flat=True)

            return User.objects.filter(id__in=school_user_ids)

        # Other users can only see themselves
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.action == "create":
            # Only school owners/admins and system admins can create users
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        elif self.action == "signup":
            # Anyone can sign up
            permission_classes = [AllowAny]
        elif self.action == "list":
            # Any authenticated user can list, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only owner or school admin can modify user records
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        elif self.action in ["retrieve", "school_profile", "dashboard_info"]:
            # Any authenticated user can retrieve, but queryset is filtered appropriately
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def dashboard_info(self, request):
        """
        Get dashboard information for the current user
        """
        user = request.user

        # This method should only be called for authenticated users
        # If this is reached with AnonymousUser, it's a misconfiguration
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Basic user info
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "date_joined": user.date_joined,
        }

        # Get user's roles in schools
        memberships = SchoolMembership.objects.filter(
            user=user,
            is_active=True
        )

        user_info["roles"] = [{
            "school": {
                "id": m.school.id,
                "name": m.school.name
            },
            "role": m.role,
            "role_display": m.get_role_display()
        } for m in memberships]

        # Stats based on primary role
        stats = {}

        # If user is a school owner or admin in any school
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists():
            # Get schools where user is admin
            admin_school_ids = SchoolMembership.objects.filter(
                user=user,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True
            ).values_list('school_id', flat=True)

            # Admin stats
            stats = {
                "schools_count": len(admin_school_ids),
                "student_count": SchoolMembership.objects.filter(
                    school_id__in=admin_school_ids,
                    role=SchoolRole.STUDENT,
                    is_active=True
                ).count(),
                "teacher_count": SchoolMembership.objects.filter(
                    school_id__in=admin_school_ids,
                    role=SchoolRole.TEACHER,
                    is_active=True
                ).count(),
            }

        # If user is a teacher in any school
        elif SchoolMembership.objects.filter(
            user=user,
            role=SchoolRole.TEACHER,
            is_active=True
        ).exists():
            # Teacher stats
            stats = {
                "today_classes": 0,  # Would need to calculate from scheduling models
                "week_classes": 0,
                "student_count": 0,
                "monthly_earnings": 0,
            }

            # Check if teacher needs profile
            needs_onboarding = not hasattr(user, "teacher_profile") or user.teacher_profile is None
            user_info["needs_onboarding"] = needs_onboarding

            # Include calendar if available
            if hasattr(user, "teacher_profile") and user.teacher_profile:
                user_info["calendar_iframe"] = user.teacher_profile.calendar_iframe

        # If user is a student in any school
        elif SchoolMembership.objects.filter(
            user=user,
            role=SchoolRole.STUDENT,
            is_active=True
        ).exists():
            # Student stats
            stats = {
                "upcoming_classes": 0,
                "completed_classes": 0,
                "balance": "$0",
            }

            # Check if student needs onboarding
            needs_onboarding = not hasattr(user, "student_profile") or user.student_profile is None
            user_info["needs_onboarding"] = needs_onboarding

            # Include calendar if available
            if hasattr(user, "student_profile") and user.student_profile:
                user_info["calendar_iframe"] = user.student_profile.calendar_iframe

        return Response({"user_info": user_info, "stats": stats})

    @action(detail=False, methods=["get"])
    def school_profile(self, request):
        """
        Get school profile information for a specific school
        """
        school_id = request.query_params.get('school_id')

        if not school_id:
            return Response(
                {"error": "School ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            return Response(
                {"error": "School not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has access to this school
        if not (
            request.user.is_superuser
            or request.user.is_staff
            or SchoolMembership.objects.filter(
                user=request.user,
                school=school,
                is_active=True
            ).exists()
        ):
            return Response(
                {"error": "You don't have access to this school"},
                status=status.HTTP_403_FORBIDDEN
            )

        # School statistics
        stats = {
            "students": SchoolMembership.objects.filter(
                school=school,
                role=SchoolRole.STUDENT,
                is_active=True
            ).count(),
            "teachers": SchoolMembership.objects.filter(
                school=school,
                role=SchoolRole.TEACHER,
                is_active=True
            ).count(),
            "classes": 0,  # Would need to calculate from scheduling models
            "class_types": 0,
        }

        # School information
        school_info = {
            "id": school.id,
            "name": school.name,
            "description": school.description,
            "address": school.address,
            "contact_email": school.contact_email,
            "phone_number": school.phone_number,
            "website": school.website,
            "created_at": school.created_at,
        }

        return Response({"stats": stats, "school_info": school_info})

    @action(detail=False, methods=["post"])
    def verify_contact(self, request):
        """
        Verify a contact method (email or phone) using a verification code
        """
        contact_type = request.data.get('contact_type')
        code = request.data.get('code')

        if not contact_type or contact_type not in ['email', 'phone']:
            return Response(
                {"error": "Invalid contact type. Must be 'email' or 'phone'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not code:
            return Response(
                {"error": "Verification code is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        contact_value = getattr(user, "email" if contact_type == "email" else "phone_number")

        # Check for verification code
        try:
            if contact_type == 'email':
                verification = EmailVerificationCode.objects.filter(
                    email=contact_value, is_used=False
                ).latest("created_at")
            else:
                # For phone verification, we would need a similar model for phone codes
                # This example assumes we're using the same model for simplicity
                verification = EmailVerificationCode.objects.filter(
                    email=contact_value, is_used=False
                ).latest("created_at")
        except EmailVerificationCode.DoesNotExist:
            return Response(
                {"error": f"No verification code found for this {contact_type}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the code
        if not verification.is_valid(code):
            return Response(
                {"error": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark verification as used
        verification.use()

        # Update user's verification status
        setattr(user, f"{contact_type}_verified", True)
        user.save()

        return Response({
            "message": f"Your {contact_type} has been verified successfully.",
            "user": UserSerializer(user).data
        })

    @action(detail=False, methods=["post"])
    def set_primary_contact(self, request):
        """
        Update the user's primary contact method
        """
        primary_contact = request.data.get('primary_contact')

        if not primary_contact or primary_contact not in ['email', 'phone']:
            return Response(
                {"error": "Invalid contact type. Must be 'email' or 'phone'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Ensure the selected contact is verified
        if primary_contact == 'email' and not user.email_verified:
            return Response(
                {"error": "Email must be verified before setting it as primary contact."},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif primary_contact == 'phone' and not user.phone_verified:
            return Response(
                {"error": "Phone number must be verified before setting it as primary contact."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update primary contact
        user.primary_contact = primary_contact
        user.save()

        return Response({
            "message": f"Your primary contact has been updated to {primary_contact}.",
            "user": UserSerializer(user).data
        })

    @action(detail=False, methods=["post"], throttle_classes=[EmailCodeRequestThrottle, IPSignupThrottle])
    def signup(self, request):
        """
        Sign up as a new user without requiring authentication.

        This handles the first step of the onboarding process where a user
        fills out the form with their information and selects a primary contact.
        """
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')
        name = validated_data.get('name')
        primary_contact = validated_data.get('primary_contact')
        school_data = validated_data.get('school', {})

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the user (without password initially)
        user = User.objects.create_user(
            email=email,
            password=None,  # Will be set after verification
            name=name,
            phone_number=phone_number,
            primary_contact=primary_contact
        )

        # Create school if school data provided
        if school_data:
            school = School.objects.create(
                name=school_data.get('name'),
                description=school_data.get('description', ''),
                address=school_data.get('address', ''),
                contact_email=school_data.get('contact_email', email),
                phone_number=school_data.get('phone_number', phone_number),
                website=school_data.get('website', '')
            )

            # Create school membership
            SchoolMembership.objects.create(
                user=user,
                school=school,
                role=SchoolRole.SCHOOL_OWNER,
                is_active=True
            )
        else:
            # Create default school
            school = School.objects.create(
                name=f"{user.name}'s School",
                description="Default school created on sign up",
                contact_email=user.email,
                phone_number=user.phone_number
            )

            # Create school membership
            SchoolMembership.objects.create(
                user=user,
                school=school,
                role=SchoolRole.SCHOOL_OWNER,
                is_active=True
            )

        # Generate verification code for primary contact
        if primary_contact == 'email':
            verification = EmailVerificationCode.generate_code(email)
            contact_value = email
        else:
            # For phone verification, in a real system we'd use a different
            # mechanism like SMS, but for this example we'll use email
            verification = EmailVerificationCode.generate_code(phone_number)
            contact_value = phone_number

        code = verification.get_current_code()

        # Send verification code (email for this example)
        try:
            contact_type_display = "email" if primary_contact == "email" else "phone number"
            send_mail(
                subject="Aprende Comigo - Verification Code",
                message=f"Your verification code is: {code}\n\nThis code will expire in 2 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],  # Always send to email for this example
                fail_silently=False,
            )
        except Exception as e:
            # Rollback user creation if email fails
            user.delete()
            return Response(
                {"error": f"Failed to send verification code: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "message": f"User created successfully. Verification code sent to your {contact_type_display}.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "primary_contact": user.primary_contact
            },
            "school": {
                "id": school.id,
                "name": school.name
            }
        }, status=status.HTTP_201_CREATED)


class SchoolViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for schools.
    """

    serializer_class = SchoolSerializer

    def get_queryset(self):
        user = self.request.user
        # System admins can see all schools
        if user.is_staff or user.is_superuser:
            return School.objects.all()

        # Users can see schools they're members of
        school_ids = SchoolMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('school_id', flat=True)

        return School.objects.filter(id__in=school_ids)

    def get_permissions(self):
        if self.action == "create":
            # Any authenticated user can create a school (becoming its owner)
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Only school owner/admin can modify school
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # For list, retrieve, etc.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Create the school
        school = serializer.save()

        # Create a membership for the creator as school owner
        SchoolMembership.objects.create(
            user=self.request.user,
            school=school,
            role=SchoolRole.SCHOOL_OWNER,
            is_active=True
        )

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """
        Get detailed information about the school including its members
        """
        school = self.get_object()
        serializer = SchoolWithMembersSerializer(school)
        return Response(serializer.data)


class SchoolMembershipViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for school memberships.
    """

    serializer_class = SchoolMembershipSerializer

    def get_queryset(self):
        user = self.request.user
        # System admins can see all memberships
        if user.is_staff or user.is_superuser:
            return SchoolMembership.objects.all()

        # School owners and admins can see memberships in their schools
        admin_school_ids = SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).values_list('school_id', flat=True)

        if admin_school_ids:
            return SchoolMembership.objects.filter(school_id__in=admin_school_ids)

        # Other users can only see their own memberships
        return SchoolMembership.objects.filter(user=user)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school owner/admin can manage memberships
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        else:
            # For list, retrieve, etc.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class SchoolInvitationViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for school invitations.
    """

    serializer_class = SchoolInvitationSerializer

    def get_queryset(self):
        user = self.request.user
        # System admins can see all invitations
        if user.is_staff or user.is_superuser:
            return SchoolInvitation.objects.all()

        # School owners and admins can see invitations for their schools
        admin_school_ids = SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).values_list('school_id', flat=True)

        return SchoolInvitation.objects.filter(
            school_id__in=admin_school_ids,
            invited_by=user
        )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            # Only school owner/admin can manage invitations
            permission_classes = [IsAuthenticated, IsSchoolOwnerOrAdmin]
        elif self.action == "accept":
            # Anyone can accept an invitation with the correct token
            permission_classes = [AllowAny]
        else:
            # For list, retrieve, etc.
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Set the invited_by field to the current user
        # Set expiration date (e.g., 7 days from now)
        expires_at = timezone.now() + timezone.timedelta(days=7)

        # Generate a unique token
        import uuid
        token = uuid.uuid4().hex

        serializer.save(
            invited_by=self.request.user,
            expires_at=expires_at,
            token=token
        )

    @action(detail=False, methods=["post"])
    def accept(self, request):
        """
        Accept an invitation and create a school membership
        """
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']

        try:
            invitation = SchoolInvitation.objects.get(token=token)
        except SchoolInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation token"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if invitation is valid
        if not invitation.is_valid():
            return Response(
                {"error": "Invitation has expired or already been used"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = invitation.email

        # If user is authenticated and their email matches the invitation
        if request.user.is_authenticated and request.user.email == email:
            user = request.user
        else:
            # Look for existing user with this email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create a new user if this is a new email
                user = User.objects.create_user(
                    email=email,
                    name=email.split('@')[0],  # Default name from email
                    password=None  # Will need to set password via reset
                )

        # Create the membership
        SchoolMembership.objects.create(
            user=user,
            school=invitation.school,
            role=invitation.role,
            is_active=True
        )

        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.save()

        # If the user is new or not authenticated, generate an auth token
        if not request.user.is_authenticated:
            # Create token for the user
            token_instance, token = AuthToken.objects.create(user)

            return Response({
                "message": "Invitation accepted successfully",
                "token": token,
                "user": UserWithRolesSerializer(user).data
            })

        return Response({
            "message": "Invitation accepted successfully"
        })

    @action(detail=False, methods=["post"])
    def invite(self, request):
        """
        Invite a user to join a school with a specific role
        """
        serializer = InvitationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        school_id = serializer.validated_data['school_id']
        message = serializer.validated_data.get('message', '')

        # Check if the school exists
        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            return Response(
                {"error": "School not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user has permission to invite to this school
        has_permission = SchoolMembership.objects.filter(
            user=request.user,
            school=school,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists()

        if not has_permission and not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "You don't have permission to invite users to this school"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create the invitation
        expires_at = timezone.now() + timezone.timedelta(days=7)
        token = uuid.uuid4().hex

        invitation = SchoolInvitation.objects.create(
            school=school,
            email=email,
            invited_by=request.user,
            role=role,
            token=token,
            expires_at=expires_at
        )

        # Send invitation email
        try:
            invite_url = f"{settings.FRONTEND_URL}/invitation/accept/{token}"
            send_mail(
                subject=f"Invitation to join {school.name}",
                message=f"""
                You have been invited to join {school.name} as a {invitation.get_role_display()}.

                {message}

                Please click the link below to accept the invitation:
                {invite_url}

                This invitation will expire on {expires_at.strftime('%Y-%m-%d')}.
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            # Delete the invitation if email fails
            invitation.delete()
            return Response(
                {"error": f"Failed to send invitation email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "message": f"Invitation sent to {email}",
            "invitation": SchoolInvitationSerializer(invitation).data
        })


class TeacherViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for teacher profiles.
    """

    serializer_class = TeacherSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return TeacherProfile.objects.all()

        # School owners and admins can see teachers in their schools
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists():
            # Get the schools where user is an admin
            admin_school_ids = SchoolMembership.objects.filter(
                user=user,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True
            ).values_list('school_id', flat=True)

            # Get all teacher users in these schools
            teacher_user_ids = SchoolMembership.objects.filter(
                school_id__in=admin_school_ids,
                role=SchoolRole.TEACHER,
                is_active=True
            ).values_list('user_id', flat=True)

            return TeacherProfile.objects.filter(user_id__in=teacher_user_ids)

        # Teachers can see their own profile
        if hasattr(user, "teacher_profile"):
            return TeacherProfile.objects.filter(user=user)

        return TeacherProfile.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated, IsTeacherInAnySchool]
        return [permission() for permission in permission_classes]


class StudentViewSet(KnoxAuthenticatedViewSet):
    """
    API endpoint for student profiles.
    """

    serializer_class = StudentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return StudentProfile.objects.all()

        # School owners and admins can see students in their schools
        if SchoolMembership.objects.filter(
            user=user,
            role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
            is_active=True
        ).exists():
            # Get the schools where user is an admin
            admin_school_ids = SchoolMembership.objects.filter(
                user=user,
                role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN],
                is_active=True
            ).values_list('school_id', flat=True)

            # Get all student users in these schools
            student_user_ids = SchoolMembership.objects.filter(
                school_id__in=admin_school_ids,
                role=SchoolRole.STUDENT,
                is_active=True
            ).values_list('user_id', flat=True)

            return StudentProfile.objects.filter(user_id__in=student_user_ids)

        # Teachers can see students in schools where they teach
        if SchoolMembership.objects.filter(
            user=user,
            role=SchoolRole.TEACHER,
            is_active=True
        ).exists():
            # Get the schools where user is a teacher
            teacher_school_ids = SchoolMembership.objects.filter(
                user=user,
                role=SchoolRole.TEACHER,
                is_active=True
            ).values_list('school_id', flat=True)

            # Get all student users in these schools
            student_user_ids = SchoolMembership.objects.filter(
                school_id__in=teacher_school_ids,
                role=SchoolRole.STUDENT,
                is_active=True
            ).values_list('user_id', flat=True)

            return StudentProfile.objects.filter(user_id__in=student_user_ids)

        # Students can see their own profile
        if hasattr(user, "student_profile"):
            return StudentProfile.objects.filter(user=user)

        return StudentProfile.objects.none()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "onboarding"]:
            permission_classes = [IsAuthenticated, IsOwnerOrSchoolAdmin]
        else:
            permission_classes = [IsAuthenticated, IsStudentInAnySchool]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"])
    def onboarding(self, request):
        """
        Handle student onboarding to complete their profile
        """
        user = request.user

        # Check if student profile already exists
        try:
            student = StudentProfile.objects.get(user=user)
            return Response(
                {"message": "Your profile is already complete."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StudentProfile.DoesNotExist:
            # Create new profile
            serializer = StudentSerializer(data=request.data)
            if serializer.is_valid():
                # Set the user and save
                serializer.save(user=user)
                return Response(
                    {"message": "Student profile created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class RequestEmailCodeView(APIView):
    """
    API endpoint for requesting a TOTP verification code.
    Rate limited to prevent abuse.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailCodeRequestThrottle]

    def post(self, request):
        serializer = EmailRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        verification = EmailVerificationCode.generate_code(email)

        # Get the current TOTP code
        code = verification.get_current_code()

        # Send email with verification code
        try:
            send_mail(
                subject="Aprende Comigo - Verification Code",
                message=f"Your verification code is: {code}\n\nThis code will expire in 2 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": f"Verification code sent to {email}."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailCodeView(APIView):
    """
    API endpoint for verifying a TOTP code and authenticating the user.
    Uses Knox tokens for authentication.
    Rate limited by both email and IP to prevent brute force attacks.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailBasedThrottle, IPBasedThrottle]  # Apply both throttles

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        # Try to get the latest verification code for this email
        try:
            verification = EmailVerificationCode.objects.filter(
                email=email, is_used=False
            ).latest("created_at")
        except EmailVerificationCode.DoesNotExist:
            return Response(
                {"error": "No verification code found for this email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the code
        if not verification.is_valid(code):
            # Record the failed attempt
            locked_out = verification.record_failed_attempt()
            if locked_out:
                return Response(
                    {
                        "error": "Too many failed attempts. Please request a new verification code."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Invalid or expired verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": email.split("@")[0],  # Default name from email
            },
        )

        # Mark verification as used
        verification.use()

        # Set the appropriate verification flag based on primary_contact
        if user.primary_contact == "email":
            user.email_verified = True
        elif user.primary_contact == "phone":
            user.phone_verified = True
        user.save()

        # Create a session token for the user
        token_instance, token = AuthToken.objects.create(user)

        # If using Django sessions, also login the user
        if hasattr(request, "_request") and hasattr(request._request, "session"):
            login(request._request, user)

        # Return the token and user info
        response_data = {
            "token": token,
            "user": UserSerializer(user).data,
        }

        # If this is a new user, create a school and set as owner
        if created:
            # Create a default school for this user
            school = School.objects.create(
                name=f"{user.name}'s School",
                description="Default school created on sign up",
                contact_email=user.email
            )

            # Create a school membership for this user as owner
            SchoolMembership.objects.create(
                user=user,
                school=school,
                role=SchoolRole.SCHOOL_OWNER,
                is_active=True
            )

            response_data["is_new_user"] = True
            response_data["school"] = {
                "id": school.id,
                "name": school.name
            }

        return Response(response_data, status=status.HTTP_200_OK)

class BiometricVerifyView(APIView):
    """
    API endpoint for biometric authentication.
    Accepts an email address and issues an authentication token without requiring a verification code.
    Rate limited to prevent abuse.
    """

    authentication_classes: list = []  # No authentication required
    permission_classes = [AllowAny]
    throttle_classes = [EmailBasedThrottle, IPBasedThrottle]  # Apply both throttles

    def post(self, request):
        serializer = BiometricVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "No user found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create a session token for the user
        token_instance, token = AuthToken.objects.create(user)

        # If using Django sessions, also login the user
        if hasattr(request, "_request") and hasattr(request._request, "session"):
            login(request._request, user)

        # Return the token and user info
        return Response(
            {
                "token": token,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


    """API endpoint for user profile operations."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
