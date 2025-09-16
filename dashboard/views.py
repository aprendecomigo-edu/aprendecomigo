"""
Dashboard views with clean URLs outside of accounts app
"""

from datetime import timedelta
import json
import logging
from uuid import uuid4

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views import View
from django.views.decorators.csrf import csrf_protect

from accounts.models import CustomUser, InvitationStatus, School, SchoolMembership, TeacherInvitation
from accounts.models.enums import SchoolRole
from accounts.models.profiles import StudentProfile, TeacherProfile
from finances.models import PurchaseTransaction
from scheduler.models import ClassSchedule
from tasks.models import Task

logger = logging.getLogger("accounts.auth")


@method_decorator(csrf_protect, name="dispatch")
class DashboardView(LoginRequiredMixin, View):
    """Main dashboard view that renders appropriate template based on user role"""

    def get(self, request):
        """Render appropriate dashboard template based on user role"""

        # Get user's active school membership to determine role
        active_membership = SchoolMembership.objects.filter(user=request.user, is_active=True).first()

        if active_membership:
            role = active_membership.role
            # Check school role first (higher priority than individual profiles)
            if role in [SchoolRole.SCHOOL_OWNER.value, SchoolRole.SCHOOL_ADMIN.value]:
                return self._render_admin_dashboard(request)
            elif role == SchoolRole.TEACHER.value:
                return self._render_teacher_dashboard(request)
            elif role == SchoolRole.STUDENT.value:
                return self._render_student_dashboard(request)
            elif role == SchoolRole.GUARDIAN.value:
                return self._render_guardian_dashboard(request)

        # TODO: No Fallbacks something is wrong if there's no active membership
        logger.error(f"User {request.user.id} has no active school membership.")
        return JsonResponse({"error": "No active school membership found."}, status=403)

    def _render_admin_dashboard(self, request):
        """Render admin dashboard directly at /dashboard/ - moved from AdminDashboardView"""

        # Get the logged-in user (authentication handled by main get() method)
        user = request.user

        # Get statistics
        total_teachers = TeacherProfile.objects.count()
        total_students = StudentProfile.objects.count()

        # Get active sessions (scheduled in the next 7 days)
        today = timezone.now()
        week_from_now = today + timedelta(days=7)
        active_sessions = ClassSchedule.objects.filter(
            scheduled_date__gte=today.date(),
            scheduled_date__lte=week_from_now.date(),
            status__in=["scheduled", "confirmed"],
        ).count()

        # Get revenue this month from actual financial data

        current_month = today.month
        current_year = today.year

        try:
            revenue_this_month = (
                PurchaseTransaction.objects.filter(
                    created_at__year=current_year, created_at__month=current_month, status="completed"
                ).aggregate(total=models.Sum("amount_charged"))["total"]
                or 0
            )
            revenue_this_month = int(revenue_this_month / 100)  # Convert cents to euros
        except Exception:
            revenue_this_month = 0  # Default to 0 if no payment data

        # Get tasks from task management system
        try:
            user_tasks = Task.objects.filter(user=user).order_by("-created_at")[:10]
            tasks = []
            for task in user_tasks:
                tasks.append(
                    {
                        "id": task.pk,
                        "title": task.title,
                        "priority": task.priority.lower() if task.priority else "medium",
                        "status": "completed" if task.status == "completed" else "pending",
                        "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
                    }
                )
        except Exception:
            # Fallback to empty tasks if Task model doesn't exist or has issues
            tasks = []

        # Get upcoming events (classes) - simplified for now
        events = []
        schedules = (
            ClassSchedule.objects.select_related("teacher__user", "student")
            .filter(scheduled_date__gte=today.date(), scheduled_date__lte=week_from_now.date())
            .order_by("scheduled_date", "start_time")[:10]
        )

        for schedule in schedules:
            # Get real teacher name
            teacher_name = "Professor"
            if schedule.teacher and schedule.teacher.user:
                teacher_name = schedule.teacher.user.name
                if not teacher_name:
                    teacher_name = schedule.teacher.user.email.split("@")[0]

            # Get real student name
            student_name = "Aluno"
            if schedule.student:
                student_name = schedule.student.name
                if not student_name:
                    student_name = schedule.student.email.split("@")[0] if schedule.student.email else "Aluno"

            # Use the actual title from the schedule, or create a descriptive one
            if schedule.title and schedule.title.strip():
                title = schedule.title
            else:
                # Create a descriptive title based on available data
                class_type_display = schedule.get_class_type_display() if schedule.class_type else "Aula"
                title = f"{class_type_display} - {teacher_name}"

            events.append(
                {
                    "id": schedule.pk,
                    "title": title,
                    "scheduled_date": schedule.scheduled_date.strftime("%Y-%m-%d"),
                    "start_time": schedule.start_time.strftime("%H:%M") if schedule.start_time else "09:00",
                    "end_time": schedule.end_time.strftime("%H:%M") if schedule.end_time else "10:00",
                    "duration_minutes": 60,
                    "teacher_name": teacher_name,
                    "student_name": student_name,
                    "status": schedule.status or "scheduled",
                }
            )

        context = {
            "title": "Admin Dashboard - Aprende Comigo",
            "user": user,
            "active_section": "dashboard",
            "total_teachers": total_teachers,
            "total_students": total_students,
            "active_sessions": active_sessions,
            "revenue_this_month": revenue_this_month,
            "tasks": json.dumps(tasks),  # JSON encode for JavaScript
            "events": events,
            "now": timezone.now(),
        }

        return render(request, "dashboard/admin_dashboard.html", context)

    def _render_teacher_dashboard(self, request):
        """Render teacher dashboard with teaching tools and data"""
        return render(
            request,
            "dashboard/teacher_dashboard.html",
            {"title": "Teacher Dashboard - Aprende Comigo", "user": request.user, "active_section": "dashboard"},
        )

    def _render_student_dashboard(self, request):
        """Render student dashboard with learning tools"""
        return render(
            request,
            "dashboard/student_dashboard.html",
            {"title": "Student Portal - Aprende Comigo", "user": request.user, "active_section": "dashboard"},
        )

    def _render_guardian_dashboard(self, request):
        """Render guardian dashboard with student progress monitoring"""
        return render(
            request,
            "dashboard/guardian_dashboard.html",
            {"title": "Guardian Portal - Aprende Comigo", "user": request.user, "active_section": "dashboard"},
        )


class TeachersView(View):
    """Teachers management page"""

    def get(self, request):
        """Render teachers management page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')

        return render(
            request,
            "dashboard/teachers.html",
            {"title": "Teachers - Aprende Comigo", "user": request.user, "active_section": "teachers"},
        )


class StudentsView(View):
    """Students management page"""

    def get(self, request):
        """Render students management page"""
        # TODO: Remove authentication bypass in production
        # if not request.user.is_authenticated:
        #     return redirect('accounts:signin')

        return render(
            request,
            "dashboard/students.html",
            {"title": "Students - Aprende Comigo", "user": request.user, "active_section": "students"},
        )


class InvitationsView(LoginRequiredMixin, View):
    """Invitations management page"""

    def get(self, request):
        """Render invitations page with server-side data"""

        # Get user's schools - using same logic as PeopleView
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Check if this is a partial request for invitations list
        if request.GET.get("load_invitations"):
            return self._render_invitations_list(request)

        # Fetch invitations server-side
        invitations_queryset = (
            TeacherInvitation.objects.filter(school__in=user_schools)
            .select_related("school", "invited_by")
            .order_by("-created_at")
        )

        invitations = []
        for invitation in invitations_queryset:
            invitations.append(
                {
                    "id": invitation.pk,
                    "email": invitation.email,
                    "role": invitation.get_role_display(),
                    "status": invitation.get_status_display(),
                    "created_at": invitation.created_at,
                    "school_name": invitation.school.name if invitation.school else "",
                    "invited_by": invitation.invited_by.get_full_name() if invitation.invited_by else "",
                    "custom_message": invitation.custom_message or "",
                    "is_active": invitation.status in ["pending", "sent", "delivered", "viewed"]
                    and not invitation.is_accepted
                    and invitation.expires_at > timezone.now(),
                }
            )

        return render(
            request,
            "dashboard/invitations.html",
            {
                "title": "Invitations - Aprende Comigo",
                "user": request.user,
                "active_section": "invitations",
                "invitations": invitations,
                "user_schools": user_schools,
            },
        )

    def post(self, request):
        """Handle invitation form submissions"""
        action = request.POST.get("action")

        if action == "send_invitation":
            return self._handle_send_invitation(request)
        elif action == "resend_invitation":
            return self._handle_resend_invitation(request)
        elif action == "cancel_invitation":
            return self._handle_cancel_invitation(request)
        elif action == "load_invitations":
            return self._render_invitations_list(request)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

    def _handle_send_invitation(self, request):
        """Handle sending a new teacher invitation"""

        try:
            email = request.POST.get("email")
            role = request.POST.get("role", "teacher")
            custom_message = request.POST.get("custom_message", "")

            if not email:
                return render(request, "shared/partials/error_message.html", {"error": "Email is required"})

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)

            if not user_schools.exists():
                return render(
                    request, "shared/partials/error_message.html", {"error": "No schools found for this user"}
                )

            # Use the first school for now (TODO: allow school selection)
            school = user_schools.first()

            # Check for existing active invitation
            existing = TeacherInvitation.objects.filter(
                email=email,
                school=school,
                is_accepted=False,
                expires_at__gt=timezone.now(),
                status__in=[
                    InvitationStatus.PENDING,
                    InvitationStatus.SENT,
                    InvitationStatus.DELIVERED,
                    InvitationStatus.VIEWED,
                ],
            ).first()

            if existing:
                return render(
                    request,
                    "shared/partials/error_message.html",
                    {"error": "An active invitation already exists for this email and school"},
                )

            # Create new invitation
            invitation = TeacherInvitation.objects.create(
                school=school,
                email=email,
                invited_by=request.user,
                role=role,
                custom_message=custom_message,
                batch_id=uuid4(),
                status=InvitationStatus.PENDING,
            )

            # TODO: Send email invitation using messaging service
            invitation.mark_email_sent()

            # Return success message and update the invitations list
            response = render(
                request,
                "shared/partials/success_message.html",
                {"message": f"Invitation sent successfully to {email}!"},
            )
            response["HX-Trigger"] = "refreshInvitations"
            return response

        except Exception as e:
            return render(request, "shared/partials/error_message.html", {"error": f"Failed to send invitation: {e!s}"})

    def _handle_resend_invitation(self, request):
        """Handle resending an existing invitation"""
        try:
            invitation_id = request.POST.get("invitation_id")
            if not invitation_id:
                return render(request, "shared/partials/error_message.html", {"error": "Invitation ID is required"})

            invitation = TeacherInvitation.objects.get(pk=invitation_id)

            # TODO: Resend email using messaging service
            invitation.mark_email_sent()

            response = render(
                request,
                "shared/partials/success_message.html",
                {"message": f"Invitation resent to {invitation.email}!"},
            )
            response["HX-Trigger"] = "refreshInvitations"
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, "shared/partials/error_message.html", {"error": "Invitation not found"})
        except Exception as e:
            return render(
                request, "shared/partials/error_message.html", {"error": f"Failed to resend invitation: {e!s}"}
            )

    def _handle_cancel_invitation(self, request):
        """Handle canceling an existing invitation"""
        try:
            invitation_id = request.POST.get("invitation_id")
            if not invitation_id:
                return render(request, "shared/partials/error_message.html", {"error": "Invitation ID is required"})

            invitation = TeacherInvitation.objects.get(pk=invitation_id)
            invitation.cancel()

            response = render(
                request,
                "shared/partials/success_message.html",
                {"message": f"Invitation to {invitation.email} has been cancelled!"},
            )
            response["HX-Trigger"] = "refreshInvitations"
            return response

        except TeacherInvitation.DoesNotExist:
            return render(request, "shared/partials/error_message.html", {"error": "Invitation not found"})
        except Exception as e:
            return render(
                request, "shared/partials/error_message.html", {"error": f"Failed to cancel invitation: {e!s}"}
            )

    def _render_invitations_list(self, request):
        """Render invitations list partial for HTMX updates"""

        # Get user's schools - using same logic as main view
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Fetch invitations
        invitations_queryset = (
            TeacherInvitation.objects.filter(school__in=user_schools)
            .select_related("school", "invited_by")
            .order_by("-created_at")
        )

        invitations = []
        for invitation in invitations_queryset:
            invitations.append(
                {
                    "id": invitation.pk,
                    "email": invitation.email,
                    "role": invitation.get_role_display(),
                    "status": invitation.get_status_display(),
                    "created_at": invitation.created_at,
                    "school_name": invitation.school.name if invitation.school else "",
                    "invited_by": invitation.invited_by.get_full_name() if invitation.invited_by else "",
                    "custom_message": invitation.custom_message or "",
                    "is_active": invitation.status in ["pending", "sent", "delivered", "viewed"]
                    and not invitation.is_accepted
                    and invitation.expires_at > timezone.now(),
                }
            )

        return render(
            request,
            "dashboard/partials/invitations_list.html",
            {
                "invitations": invitations,
            },
        )


@method_decorator(csrf_protect, name="dispatch")
class PeopleView(LoginRequiredMixin, View):
    """Unified people management page with tabs for teachers, students, staff"""

    def get(self, request):
        """Render people management page with initial data server-side"""

        # Get user's schools - using same logic as API views
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Get teachers data with profiles
        teacher_memberships = SchoolMembership.objects.filter(
            school__in=user_schools, role=SchoolRole.TEACHER.value
        ).select_related("user", "school")

        teachers = []
        for membership in teacher_memberships:
            user = membership.user
            try:
                profile = user.teacher_profile
                bio = profile.bio
                specialty = profile.specialty
                hourly_rate = float(profile.hourly_rate) if profile.hourly_rate else None
            except TeacherProfile.DoesNotExist:
                bio = ""
                specialty = ""
                hourly_rate = None

            teachers.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "full_name": user.get_full_name(),
                    "bio": bio,
                    "specialty": specialty,
                    "hourly_rate": hourly_rate,
                    "school": {"id": membership.school.id, "name": membership.school.name},
                    "status": "active" if user.is_active else "inactive",
                }
            )

        # Get students data with profiles
        student_memberships = SchoolMembership.objects.filter(
            school__in=user_schools, role=SchoolRole.STUDENT.value
        ).select_related("user", "school")

        students = []
        for membership in student_memberships:
            user = membership.user
            try:
                profile = user.student_profile
                school_year = profile.school_year
            except (StudentProfile.DoesNotExist, AttributeError):
                school_year = ""

            students.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "full_name": user.get_full_name(),
                    "school_year": school_year,
                    "school": {"id": membership.school.id, "name": membership.school.name},
                    "status": "active" if user.is_active else "inactive",
                }
            )

        # Add Guardian-Only students (no user accounts)
        guardian_only_profiles = StudentProfile.objects.filter(
            user=None,  # Guardian-Only students have no user account
            account_type="GUARDIAN_ONLY",
        ).select_related("guardian")

        for profile in guardian_only_profiles:
            # Use the first school from user_schools for display (admin can manage across schools)
            school = user_schools.first() if user_schools.exists() else None
            guardian_user = profile.guardian.user if profile.guardian else None

            students.append(
                {
                    "id": f"guardian_only_{profile.id}",  # Unique ID for guardian-only students
                    "email": guardian_user.email if guardian_user else "",
                    "name": profile.name,  # Use the name field from StudentProfile
                    "full_name": profile.name,
                    "school_year": profile.school_year,
                    "school": {"id": school.id, "name": school.name} if school else {"id": 0, "name": "Unknown"},
                    "status": "active",  # Guardian-Only students are always "active"
                }
            )

        # Calculate stats
        teacher_stats = {
            "active": len([t for t in teachers if t["status"] == "active"]),
            "pending": 0,  # We'll implement this based on invitations later
            "inactive": len([t for t in teachers if t["status"] == "inactive"]),
            "total": len(teachers),
        }

        student_stats = {"total": len(students)}

        return render(
            request,
            "dashboard/people.html",
            {
                "title": "People - Aprende Comigo",
                "user": request.user,
                "active_section": "people",
                "teachers": teachers,
                "students": students,
                "teacher_stats": teacher_stats,
                "student_stats": student_stats,
            },
        )

    def post(self, request):
        """Handle form submissions for adding teachers/students"""
        action = request.POST.get("action")

        if action == "add_teacher":
            return self._handle_add_teacher(request)
        elif action == "add_student":
            return self._handle_add_student(request)
        elif action == "invite_teacher":
            return self._handle_invite_teacher(request)
        elif action == "search_students":
            return self._handle_search_students(request)
        elif action == "get_student_detail":
            return self._handle_get_student_detail(request)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

    def _handle_add_teacher(self, request):
        """Handle adding a new teacher"""

        try:
            email = request.POST.get("email")
            bio = request.POST.get("bio", "")
            specialty = request.POST.get("specialty", "")

            if not email:
                return render(request, "shared/partials/error_message.html", {"error": "Email is required"})

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Create new user if doesn't exist - use email prefix as default name
                default_name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
                user = CustomUser.objects.create_user(
                    email=email,
                    name=default_name,  # Use the name field that exists on CustomUser
                )

            # Create or update teacher profile
            teacher_profile, created = TeacherProfile.objects.get_or_create(
                user=user, defaults={"bio": bio, "specialty": specialty}
            )
            if not created:
                teacher_profile.bio = bio
                teacher_profile.specialty = specialty
                teacher_profile.save()

            # Add to user's schools as teacher
            for school in user_schools:
                SchoolMembership.objects.get_or_create(user=user, school=school, defaults={"role": SchoolRole.TEACHER})

            # Return updated teachers partial
            return self._render_teachers_partial(request)

        except Exception as e:
            return render(request, "shared/partials/error_message.html", {"error": f"Failed to add teacher: {e!s}"})

    def _validate_email_format(self, email):
        """Validate email format and return sanitized email or raise ValidationError"""
        if not email:
            return ""

        # Strip whitespace first
        email = email.strip()

        # Check for basic format requirements
        if " " in email:
            raise ValidationError(f"Email cannot contain spaces: {email}")

        if "@" not in email:
            raise ValidationError(f"Email must contain @: {email}")

        if email.startswith("@") or email.endswith("@"):
            raise ValidationError(f"Invalid email format: {email}")

        # Reject emails with non-ASCII characters (internationalized domains)
        # This matches the test expectation for stricter validation
        try:
            email.encode("ascii")
        except UnicodeEncodeError:
            raise ValidationError(f"Email must contain only ASCII characters: {email}")

        # Use Django's built-in validator
        try:
            validate_email(email)
            return escape(email)
        except ValidationError:
            raise ValidationError(f"Invalid email format: {email}")

    def _handle_add_student(self, request):
        """Handle adding a new student with the three account type scenarios"""

        from django.db import transaction

        from accounts.models.educational import EducationalSystem
        from accounts.models.profiles import GuardianProfile
        from accounts.permissions import PermissionService

        try:
            account_type = request.POST.get("account_type", "separate")
            logger.info(f"Processing student registration with account_type: {account_type}")

            # Log all form data for debugging
            form_data = dict(request.POST.items())
            # Remove CSRF token from logs for security
            form_data.pop("csrfmiddlewaretoken", None)
            logger.debug(f"Form data received: {form_data}")

            # Get user's schools
            def get_user_schools(user):
                if user.is_staff or user.is_superuser:
                    return School.objects.all()
                school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
                return School.objects.filter(id__in=school_ids)

            user_schools = get_user_schools(request.user)

            # Get default educational system (Portugal)
            educational_system = EducationalSystem.objects.filter(code="pt").first()
            if not educational_system:
                educational_system = EducationalSystem.objects.first()

            with transaction.atomic():
                if account_type == "guardian_only":
                    # Handle guardian-only scenario (young student without login)
                    # Sanitize all text inputs to prevent XSS
                    student_name = escape(request.POST.get("student_name", "").strip())
                    student_birth_date = request.POST.get("birth_date")
                    student_school_year = escape(request.POST.get("guardian_only_student_school_year", "").strip())
                    student_notes = escape(request.POST.get("guardian_only_student_notes", "").strip())

                    guardian_name = escape(request.POST.get("guardian_name", "").strip())
                    guardian_email_raw = request.POST.get("guardian_email", "").strip()
                    guardian_phone = escape(request.POST.get("guardian_only_guardian_phone", "").strip())
                    guardian_tax_nr = escape(request.POST.get("guardian_only_guardian_tax_nr", "").strip())
                    guardian_address = escape(request.POST.get("guardian_only_guardian_address", "").strip())
                    guardian_invoice = request.POST.get("guardian_only_guardian_invoice") == "on"
                    guardian_email_notifications = (
                        request.POST.get("guardian_only_guardian_email_notifications") == "on"
                    )
                    guardian_sms_notifications = request.POST.get("guardian_only_guardian_sms_notifications") == "on"

                    # Validate and sanitize email
                    try:
                        guardian_email = self._validate_email_format(guardian_email_raw)
                    except ValidationError as e:
                        logger.error(f"Guardian email validation failed: {e}")
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": str(e)},
                        )

                    # Validate required fields for guardian-only account
                    if not all([student_name, student_birth_date, guardian_name, guardian_email]):
                        missing_fields = []
                        if not student_name:
                            missing_fields.append("student name")
                        if not student_birth_date:
                            missing_fields.append("student birth date")
                        if not guardian_name:
                            missing_fields.append("guardian name")
                        if not guardian_email:
                            missing_fields.append("guardian email")

                        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                        logger.error(
                            f"Guardian-only validation failed: {error_msg}. Received data: student_name={student_name}, student_birth_date={student_birth_date}, guardian_name={guardian_name}, guardian_email={guardian_email}"
                        )
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": error_msg},
                        )

                    # Create or get guardian user
                    try:
                        guardian_user = CustomUser.objects.get(email=guardian_email)
                    except CustomUser.DoesNotExist:
                        guardian_user = CustomUser.objects.create_user(
                            email=guardian_email, name=guardian_name, phone_number=guardian_phone
                        )

                    # Create guardian profile
                    guardian_profile, _ = GuardianProfile.objects.get_or_create(
                        user=guardian_user,
                        defaults={
                            "address": guardian_address,
                            "tax_nr": guardian_tax_nr,
                            "invoice": guardian_invoice,
                            "email_notifications_enabled": guardian_email_notifications,
                            "sms_notifications_enabled": guardian_sms_notifications,
                        },
                    )

                    # Create student profile WITHOUT a user account (guardian-only)
                    student_profile = StudentProfile.objects.create(
                        user=None,  # No user account for guardian-only students
                        name=student_name,  # Store student name directly
                        account_type="GUARDIAN_ONLY",
                        educational_system=educational_system,
                        school_year=student_school_year,
                        birth_date=student_birth_date,
                        guardian=guardian_profile,
                        notes=student_notes,
                    )

                    # Setup permissions for guardian to manage this student
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add guardian to schools (student placeholder account doesn't need school membership)
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                        )

                elif account_type == "separate":
                    # Handle separate guardian scenario (STUDENT_GUARDIAN)
                    # Sanitize all text inputs to prevent XSS
                    student_name = escape(request.POST.get("student_name", "").strip())
                    student_email_raw = request.POST.get("student_email", "").strip()
                    student_birth_date = request.POST.get("birth_date")
                    student_school_year = escape(request.POST.get("student_school_year", "").strip())
                    student_notes = escape(request.POST.get("student_notes", "").strip())

                    guardian_name = escape(request.POST.get("guardian_name", "").strip())
                    guardian_email_raw = request.POST.get("guardian_email", "").strip()
                    guardian_phone = escape(request.POST.get("guardian_phone", "").strip())
                    guardian_tax_nr = escape(request.POST.get("guardian_tax_nr", "").strip())
                    guardian_address = escape(request.POST.get("guardian_address", "").strip())
                    guardian_invoice = request.POST.get("guardian_invoice") == "on"
                    guardian_email_notifications = request.POST.get("guardian_email_notifications") == "on"
                    guardian_sms_notifications = request.POST.get("guardian_sms_notifications") == "on"

                    # Validate and sanitize emails
                    try:
                        student_email = self._validate_email_format(student_email_raw)
                        guardian_email = self._validate_email_format(guardian_email_raw)
                    except ValidationError as e:
                        logger.error(f"Email validation failed: {e}")
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": str(e)},
                        )

                    # Validate required fields for student+guardian account
                    if not all([student_name, student_email, student_birth_date, guardian_name, guardian_email]):
                        missing_fields = []
                        if not student_name:
                            missing_fields.append("student name")
                        if not student_email:
                            missing_fields.append("student email")
                        if not student_birth_date:
                            missing_fields.append("student birth date")
                        if not guardian_name:
                            missing_fields.append("guardian name")
                        if not guardian_email:
                            missing_fields.append("guardian email")

                        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                        logger.error(
                            f"Student+Guardian validation failed: {error_msg}. Received data: student_name={student_name}, student_email={student_email}, student_birth_date={student_birth_date}, guardian_name={guardian_name}, guardian_email={guardian_email}"
                        )
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": error_msg},
                        )

                    # Create or get student user
                    try:
                        student_user = CustomUser.objects.get(email=student_email)
                    except CustomUser.DoesNotExist:
                        student_user = CustomUser.objects.create_user(email=student_email, name=student_name)

                    # Create or get guardian user
                    try:
                        guardian_user = CustomUser.objects.get(email=guardian_email)
                    except CustomUser.DoesNotExist:
                        guardian_user = CustomUser.objects.create_user(
                            email=guardian_email, name=guardian_name, phone_number=guardian_phone
                        )

                    # Create guardian profile
                    guardian_profile, _ = GuardianProfile.objects.get_or_create(
                        user=guardian_user,
                        defaults={
                            "address": guardian_address,
                            "tax_nr": guardian_tax_nr,
                            "invoice": guardian_invoice,
                            "email_notifications_enabled": guardian_email_notifications,
                            "sms_notifications_enabled": guardian_sms_notifications,
                        },
                    )

                    # Create student profile with STUDENT_GUARDIAN account type
                    student_profile, created = StudentProfile.objects.get_or_create(
                        user=student_user,
                        defaults={
                            "name": student_name,
                            "account_type": "STUDENT_GUARDIAN",
                            "educational_system": educational_system,
                            "school_year": student_school_year,
                            "birth_date": student_birth_date,
                            "guardian": guardian_profile,
                            "notes": student_notes,
                        },
                    )

                    if not created:
                        student_profile.name = student_name
                        student_profile.account_type = "STUDENT_GUARDIAN"
                        student_profile.school_year = student_school_year
                        student_profile.birth_date = student_birth_date
                        student_profile.guardian = guardian_profile
                        student_profile.notes = student_notes
                        student_profile.save()

                    # Setup permissions for student-guardian relationship
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add both users to schools
                    for school in user_schools:
                        # Add student
                        SchoolMembership.objects.get_or_create(
                            user=student_user, school=school, defaults={"role": SchoolRole.STUDENT.value}
                        )
                        # Add guardian
                        SchoolMembership.objects.get_or_create(
                            user=guardian_user, school=school, defaults={"role": SchoolRole.GUARDIAN}
                        )

                elif account_type == "self":
                    # Handle self-guardian scenario (adult student)
                    # Sanitize all text inputs to prevent XSS
                    name = escape(request.POST.get("student_name", "").strip())
                    email_raw = request.POST.get("student_email", "").strip()
                    phone = escape(request.POST.get("self_phone", "").strip())
                    birth_date = request.POST.get("birth_date")
                    school_year = escape(request.POST.get("self_school_year", "").strip())
                    tax_nr = escape(request.POST.get("self_tax_nr", "").strip())
                    address = escape(request.POST.get("self_address", "").strip())
                    notes = escape(request.POST.get("self_notes", "").strip())
                    invoice = request.POST.get("self_invoice") == "on"
                    email_notifications = request.POST.get("self_email_notifications") == "on"
                    sms_notifications = request.POST.get("self_sms_notifications") == "on"

                    # Validate and sanitize email
                    try:
                        email = self._validate_email_format(email_raw)
                    except ValidationError as e:
                        logger.error(f"Student email validation failed: {e}")
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": str(e)},
                        )

                    # Validate required fields for adult student account
                    if not all([name, email, birth_date]):
                        missing_fields = []
                        if not name:
                            missing_fields.append("student name")
                        if not email:
                            missing_fields.append("student email")
                        if not birth_date:
                            missing_fields.append("student birth date")

                        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                        logger.error(
                            f"Adult student validation failed: {error_msg}. Received data: name={name}, email={email}, birth_date={birth_date}"
                        )
                        return render(
                            request,
                            "shared/partials/error_message.html",
                            {"error": error_msg},
                        )

                    # Create or get user
                    try:
                        user = CustomUser.objects.get(email=email)
                    except CustomUser.DoesNotExist:
                        user = CustomUser.objects.create_user(email=email, name=name, phone_number=phone)

                    # For adult students, no need for guardian profile
                    # Create student profile with ADULT_STUDENT account type
                    student_profile, created = StudentProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            "name": name,
                            "account_type": "ADULT_STUDENT",
                            "educational_system": educational_system,
                            "school_year": school_year,
                            "birth_date": birth_date,
                            "guardian": None,  # No guardian for adult students
                            "notes": notes,
                            "address": address,
                            "tax_nr": tax_nr,
                            "invoice": invoice,
                            "email_notifications_enabled": email_notifications,
                            "sms_notifications_enabled": sms_notifications,
                        },
                    )

                    if not created:
                        student_profile.name = name
                        student_profile.account_type = "ADULT_STUDENT"
                        student_profile.school_year = school_year
                        student_profile.birth_date = birth_date
                        student_profile.guardian = None
                        student_profile.notes = notes
                        student_profile.address = address
                        student_profile.tax_nr = tax_nr
                        student_profile.invoice = invoice
                        student_profile.email_notifications_enabled = email_notifications
                        student_profile.sms_notifications_enabled = sms_notifications
                        student_profile.save()

                    # Setup permissions for adult student (full access)
                    PermissionService.setup_permissions_for_student(student_profile)

                    # Add user to schools as student only (they handle their own account)
                    for school in user_schools:
                        SchoolMembership.objects.get_or_create(
                            user=user, school=school, defaults={"role": SchoolRole.STUDENT.value}
                        )
                else:
                    logger.error(f"Invalid account type received: {account_type}")
                    return render(
                        request,
                        "shared/partials/error_message.html",
                        {
                            "error": f'Invalid account type: {account_type}. Must be "separate", "guardian_only", or "self"'
                        },
                    )

            logger.info(f"Successfully created student with account_type: {account_type}")

            # Return success response with HTMX trigger to refresh the student list
            response = render(
                request,
                "shared/partials/success_message.html",
                {"message": "Student added successfully!"},
            )
            # Only set HTMX trigger for HTMX requests
            if request.headers.get("HX-Request"):
                response["HX-Trigger"] = "refreshStudents"
            return response

        except Exception as e:
            logger.exception("Error adding student")
            return render(request, "shared/partials/error_message.html", {"error": f"Failed to add student: {e!s}"})

    def _handle_invite_teacher(self, request):
        """Handle teacher invitation"""
        # TODO: Implement teacher invitation logic
        return render(
            request, "shared/partials/success_message.html", {"message": "Teacher invitation functionality coming soon"}
        )

    def _handle_search_students(self, request):
        """Handle student search requests"""
        search_query = request.POST.get("search", "").strip()
        return self._render_students_partial(request, search_query=search_query)

    def _handle_get_student_detail(self, request):
        """Handle student detail requests"""

        try:
            student_id = request.POST.get("student_id")
            if not student_id:
                return render(request, "shared/partials/error_message.html", {"error": "Student ID is required"})

            # Get student with all related data
            student = CustomUser.objects.select_related(
                "student_profile", "student_profile__guardian", "student_profile__educational_system"
            ).get(id=student_id)

            # Get school membership
            membership = (
                SchoolMembership.objects.filter(user=student, role=SchoolRole.STUDENT.value)
                .select_related("school")
                .first()
            )

            # Prepare student detail data
            student_detail = {
                "id": student.id,
                "email": student.email,
                "name": student.name,
                "full_name": student.get_full_name(),
                "phone_number": student.phone_number or "",
                "is_active": student.is_active,
                "date_joined": student.date_joined,
                "last_login": student.last_login,
                "school": {"name": membership.school.name, "id": membership.school.id} if membership else None,
            }

            # Add student profile data if exists
            if hasattr(student, "student_profile"):
                profile = student.student_profile
                student_detail.update(
                    {
                        "school_year": profile.school_year or "",
                        "birth_date": profile.birth_date,
                        "account_type": profile.account_type or "",
                        "notes": profile.notes or "",
                        "educational_system": profile.educational_system.name if profile.educational_system else "",
                    }
                )

                # Add guardian data if exists
                if profile.guardian:
                    guardian = profile.guardian
                    student_detail["guardian"] = {
                        "id": guardian.id,
                        "name": guardian.user.get_full_name() if guardian.user else "",
                        "email": guardian.user.email if guardian.user else "",
                        "phone_number": guardian.user.phone_number if guardian.user else "",
                        "tax_number": guardian.tax_nr or "",
                        "address": guardian.address or "",
                        "invoice": guardian.invoice,
                        "email_notifications_enabled": guardian.email_notifications_enabled,
                        "sms_notifications_enabled": guardian.sms_notifications_enabled,
                    }

            return render(request, "dashboard/partials/student_detail_modal_content.html", {"student": student_detail})

        except CustomUser.DoesNotExist:
            return render(request, "shared/partials/error_message.html", {"error": "Student not found"})
        except Exception as e:
            return render(
                request, "shared/partials/error_message.html", {"error": f"Error fetching student details: {e!s}"}
            )

    def _render_teachers_partial(self, request):
        """Render teachers list partial for HTMX updates"""
        from accounts.models import School, SchoolMembership
        from accounts.models.enums import SchoolRole
        from accounts.models.profiles import TeacherProfile

        # Get user's schools
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Get teachers data with profiles
        teacher_memberships = SchoolMembership.objects.filter(
            school__in=user_schools, role=SchoolRole.TEACHER.value
        ).select_related("user", "school")

        teachers = []
        for membership in teacher_memberships:
            user = membership.user
            try:
                profile = user.teacher_profile
                bio = profile.bio
                specialty = profile.specialty
                hourly_rate = float(profile.hourly_rate) if profile.hourly_rate else None
            except TeacherProfile.DoesNotExist:
                bio = ""
                specialty = ""
                hourly_rate = None

            teachers.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "full_name": user.get_full_name(),
                    "bio": bio,
                    "specialty": specialty,
                    "hourly_rate": hourly_rate,
                    "school": {"id": membership.school.id, "name": membership.school.name},
                    "status": "active" if user.is_active else "inactive",
                }
            )

        # Calculate stats
        teacher_stats = {
            "active": len([t for t in teachers if t["status"] == "active"]),
            "pending": 0,  # We'll implement this based on invitations later
            "inactive": len([t for t in teachers if t["status"] == "inactive"]),
            "total": len(teachers),
        }

        return render(
            request,
            "dashboard/partials/teachers_list.html",
            {
                "teachers": teachers,
                "teacher_stats": teacher_stats,
            },
        )

    def _render_students_partial(self, request, search_query=None):
        """Render students list partial for HTMX updates"""
        from django.db.models import Q

        from accounts.models import School, SchoolMembership
        from accounts.models.enums import SchoolRole
        from accounts.models.profiles import StudentProfile

        # Get user's schools
        def get_user_schools(user):
            if user.is_staff or user.is_superuser:
                return School.objects.all()
            school_ids = SchoolMembership.objects.filter(user=user).values_list("school_id", flat=True)
            return School.objects.filter(id__in=school_ids)

        user_schools = get_user_schools(request.user)

        # Get students data with profiles
        student_memberships = SchoolMembership.objects.filter(
            school__in=user_schools, role=SchoolRole.STUDENT.value
        ).select_related("user", "school")

        # Apply search filter if provided
        if search_query:
            # Search across student and guardian fields
            student_memberships = student_memberships.filter(
                Q(user__name__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(user__student_profile__school_year__icontains=search_query)
            )

        students = []
        for membership in student_memberships:
            user = membership.user
            try:
                profile = user.student_profile
                school_year = profile.school_year
                account_type = profile.account_type
                created_at = profile.created_at  # Use StudentProfile.created_at

                # Get guardian info if exists
                guardian_info = None
                if profile.guardian:
                    guardian_profile = profile.guardian
                    guardian_info = {
                        "name": guardian_profile.user.get_full_name() if guardian_profile.user else "",
                        "email": guardian_profile.user.email if guardian_profile.user else "",
                        "phone": guardian_profile.user.phone_number if guardian_profile.user else "",
                    }
            except (StudentProfile.DoesNotExist, AttributeError):
                school_year = ""
                account_type = ""
                guardian_info = None
                created_at = user.date_joined  # Fallback to user creation date if no profile

            # Include guardian info in search
            student_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "full_name": user.get_full_name(),
                "school_year": school_year,
                "account_type": account_type,
                "guardian": guardian_info,
                "school": {"id": membership.school.id, "name": membership.school.name},
                "status": "active" if user.is_active else "inactive",
                "date_joined": created_at,
            }

            # Add student to results if no search or if search matches
            if not search_query:
                students.append(student_data)
            else:
                # Check if search matches any student field
                student_matches = any(
                    search_query.lower() in str(value).lower() for value in [user.name, user.email, school_year]
                )

                # Check if search matches guardian fields
                guardian_matches = False
                if guardian_info:
                    guardian_matches = any(
                        search_query.lower() in str(value).lower()
                        for value in [guardian_info.get("name", ""), guardian_info.get("email", "")]
                    )

                if student_matches or guardian_matches:
                    students.append(student_data)

        # Sort students by newest first (by created_at date)
        students.sort(key=lambda x: x["date_joined"], reverse=True)

        student_stats = {"total": len(students)}

        return render(
            request,
            "dashboard/partials/students_list.html",
            {
                "students": students,
                "student_stats": student_stats,
            },
        )


class TeachersPartialView(View):
    """Render just the teachers partial for HTMX requests"""

    def get(self, request):
        """Return teachers partial"""
        people_view = PeopleView()
        return people_view._render_teachers_partial(request)


class StudentsPartialView(View):
    """Render just the students partial for HTMX requests"""

    def get(self, request):
        """Return students partial"""
        people_view = PeopleView()
        return people_view._render_students_partial(request)
