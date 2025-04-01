from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

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
        template_name = "dashboard/admin.html"
        # Import here to avoid circular import
        from scheduling.models import ClassSession, ClassType
        # Statistics for admin dashboard
        stats = {
            "students": User.objects.filter(user_type="student").count(),
            "teachers": User.objects.filter(user_type="teacher").count(),
            "classes": ClassSession.objects.count(),
            "class_types": ClassType.objects.count(),
        }
    elif request.user.user_type == "teacher":
        template_name = "dashboard/teacher.html"
        # Example statistics for teacher dashboard
        stats = {
            "today_classes": 0,  # Placeholder for today's classes
            "week_classes": 0,   # Placeholder for weekly classes
            "student_count": 0,  # Placeholder for student count
            "monthly_earnings": 0,  # Placeholder for monthly earnings
        }
        # Add teacher-specific context data
        context["teacher_classes"] = []  # Placeholder for teacher classes
        context["upcoming_classes"] = []  # Placeholder for upcoming classes
    elif request.user.user_type == "student":
        template_name = "dashboard/student.html"
        # Example statistics for student dashboard
        stats = {
            "upcoming_classes": 0,  # Placeholder for upcoming classes
            "completed_classes": 0,  # Placeholder for completed classes
            "balance": "$0",  # Placeholder for balance
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
        template_name = "dashboard/index.html"

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

@login_required
def profile_view(request):
    """Render the user profile page"""
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
        "user_type": request.user.user_type,
        "has_google": has_google,
    }

    # Check Google token status
    google_connected = False
    if has_google:
        try:
            SocialToken.objects.get(
                account__user=request.user, account__provider="google"
            )
            google_connected = True
        except SocialToken.DoesNotExist:
            google_connected = False

    return render(request, "profile/base.html", {
        "user_info": user_info,
        "google_connected": google_connected
    })

@login_required
def profile_edit(request):
    """Render the profile edit form"""
    user_info = {
        "name": request.user.name,
        "email": request.user.email,
        "bio": getattr(request.user, 'bio', ''),
    }
    
    # If this is an HTMX request, return just the form
    if request.headers.get('HX-Request') == 'true':
        return render(request, "profile/edit.html", {
            "user_info": user_info
        })
    else:
        # If not an HTMX request, return the full page
        return render(request, "profile/base.html", {
            "user_info": user_info,
            "show_edit_form": True
        })

@login_required
def profile_update(request):
    """Handle profile updates"""
    if request.method == 'POST':
        # Update user profile
        request.user.name = request.POST.get('name', request.user.name)
        request.user.email = request.POST.get('email', request.user.email)
        
        # Update bio if the field exists in the model
        if hasattr(request.user, 'bio'):
            request.user.bio = request.POST.get('bio', '')
        
        request.user.save()
        
        messages.success(request, _("Your profile has been updated successfully!"))
        
        # If this is an HTMX request, return updated profile info
        if request.headers.get('HX-Request') == 'true':
            return redirect('profile')
        else:
            return redirect('profile')
    
    # If not a POST request, redirect to profile page
    return redirect('profile')