from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from .forms import StudentOnboardingForm
from .models import Student

User = get_user_model()


@login_required
def dashboard_view(request):
    """Render the dashboard for authenticated users."""
    # Handle user type updates from login form
    if request.method == "POST" and 'user_type' in request.POST:
        user_type = request.POST.get('user_type')
        if user_type in ['student', 'teacher']:
            request.user.user_type = user_type
            request.user.save()
            
            # Redirect to appropriate onboarding if needed
            if user_type == 'student' and not hasattr(request.user, 'student_profile'):
                return redirect('student_onboarding')
            # Future: redirect to teacher onboarding if needed
    
    # Check if user needs onboarding based on user type
    if request.user.user_type == 'student':
        try:
            # Check if student profile exists
            student = request.user.student_profile
        except Student.DoesNotExist:
            # Redirect to student onboarding
            messages.info(request, _("Please complete your student profile"))
            return redirect('student_onboarding')
    
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

    return render(request, "dashboard.html", context)


@login_required
def student_onboarding_view(request):
    """Onboarding view for students to complete their profile"""
    # Check if student profile already exists
    try:
        student = request.user.student_profile
        # If profile exists, redirect to dashboard
        messages.info(request, _("Your profile is already complete."))
        return redirect('dashboard')
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
            return redirect('dashboard')
    else:
        # Pre-fill form with user data if available
        initial_data = {
            'name': request.user.name,
            'phone_number': request.user.phone_number,
        }
        form = StudentOnboardingForm(initial=initial_data)
    
    return render(request, "account/student_onboarding.html", {
        "form": form,
        "user": request.user
    })


def user_type_selection_view(request):
    """View to let users select their account type (student or teacher)"""
    if request.method == "POST":
        user_type = request.POST.get("user_type")
        
        if user_type in ['student', 'teacher']:
            # Update user type
            request.user.user_type = user_type
            request.user.save()
            
            # Redirect to appropriate onboarding
            if user_type == 'student':
                return redirect('student_onboarding')
            elif user_type == 'teacher':
                return redirect('dashboard')  # Replace with teacher onboarding when implemented
    
    return render(request, "accounts/select_user_type.html")
