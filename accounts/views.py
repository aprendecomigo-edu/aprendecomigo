from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from .forms import StudentOnboardingForm
from .models import Student

User = get_user_model()


@login_required
def dashboard_view(request):
    """Render the dashboard for authenticated users."""
    # Check if user needs onboarding based on user type
    if request.user.user_type == "student":
        try:
            # Check if student profile exists
            student = request.user.student_profile # TODO do we need this?
        except Student.DoesNotExist:
            # Redirect to student onboarding
            messages.info(request, _("Please complete your student profile"))
            return redirect("student_onboarding")

    # Check if the user has connected their Google account
    has_google = SocialAccount.objects.filter(
        user=request.user, provider="google"
    ).exists()

    # Get user account information
    user_info = {
        "username": request.user.username,
        "email": request.user.email,
        "name": request.user.name,
        "date_joined": request.user.date_joined,
        "is_admin": request.user.is_staff or request.user.is_superuser,
        "has_google": has_google,
        "user_type": request.user.user_type,
    }

    context = {
        "user_info": user_info,
    }

    # If Google connected, check token status
    if has_google:
        try:
            # Just check if token exists, we don't need the actual token
            SocialToken.objects.get(
                account__user=request.user, account__provider="google"
            )
            context["google_connected"] = True
        except SocialToken.DoesNotExist:
            context["google_connected"] = False

    # Simply determine which dashboard template to use based on user type
    user_is_admin = (
        request.user.is_admin or request.user.is_staff or request.user.is_superuser
    )

    # Add stats placeholder for each dashboard type
    stats = {}

    # Select template based on user type
    if user_is_admin:
        template_name = "admin_dashboard.html"
        # Example statistics for admin dashboard
        stats = {
            "students": User.objects.filter(user_type="student").count(),
            "teachers": User.objects.filter(user_type="teacher").count(),
            "classes": 0,  # Placeholder for class count
        }
    elif request.user.user_type == "teacher":
        template_name = "teacher_dashboard.html"
        # Example statistics for teacher dashboard
        stats = {
            "students": 0,  # Placeholder for student count
            "classes": 0,  # Placeholder for class count
            "hours": 0,  # Placeholder for hours count
        }
        # Add teacher-specific context data
        context["teacher_classes"] = []  # Placeholder for teacher classes
        context["upcoming_classes"] = []  # Placeholder for upcoming classes
    elif request.user.user_type == "student":
        template_name = "student_dashboard.html"
        # Example statistics for student dashboard
        stats = {
            "classes": 0,  # Placeholder for class count
            "hours": 0,  # Placeholder for hours count
            "assignments": 0,  # Placeholder for assignments count
        }
        # Add student-specific context data
        context["learning_progress"] = []  # Placeholder for learning progress
        context["recent_assignments"] = []  # Placeholder for recent assignments
        context["upcoming_classes"] = []  # Placeholder for upcoming classes
        context["calendar_iframe"] = (
            request.user.student_profile.calendar_iframe
        )  # Placeholder for upcoming classes
    else:
        # Fallback to generic dashboard
        template_name = "dashboard.html"

    context["stats"] = stats

    return render(request, template_name, context)


@login_required
def student_onboarding_view(request):
    """Onboarding view for students to complete their profile"""
    # Check if student profile already exists
    try:
        student = request.user.student_profile
        # If profile exists, redirect to dashboard
        messages.info(request, _("Your profile is already complete."))
        return redirect("dashboard")
    except Student.DoesNotExist:
        # Profile doesn't exist, continue with onboarding
        pass

    if request.method == "POST":
        form = StudentOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            # Create new student profile
            student = form.save(commit=False)
            student.user = request.user
            student.save()
            messages.success(request, _("Your profile has been saved successfully!"))
            return redirect("dashboard")
    else:
        # Pre-fill form with user data if available
        initial_data = {
            "name": request.user.name,
            "phone_number": request.user.phone_number,
        }
        form = StudentOnboardingForm(initial=initial_data)

    return render(
        request, "account/student_onboarding.html", {"form": form, "user": request.user}
    )