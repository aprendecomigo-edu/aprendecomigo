"""
Context processors for accounts app.
Provides global template context variables for authenticated users.
"""

from .models.schools import School, SchoolMembership


def user_context(request):
    """
    Add user and school context to all templates.
    
    Provides:
    - user_first_name: User's first name
    - school_name: Current school name
    - user_role: User's role in current school
    """
    context = {}
    
    if request.user.is_authenticated:
        # Get user info
        context['user_first_name'] = request.user.first_name
        
        # Get current school
        current_school = get_current_school(request)
        
        if current_school:
            context['school_name'] = current_school.name
            # Get user role for this school
            context['user_role'] = get_user_role_for_school(request.user, current_school)
        else:
            context['school_name'] = 'No School Selected'
            context['user_role'] = 'guest'
    
    return context


def get_current_school(request):
    """
    Determine current school from request.
    
    Priority:
    1. Session-stored school ID
    2. User's primary/default school
    3. First school the user belongs to
    """
    # Option 1: From session (user switched schools)
    school_id = request.session.get('current_school_id')
    if school_id:
        try:
            return School.objects.get(id=school_id, memberships__user=request.user, memberships__is_active=True)
        except School.DoesNotExist:
            # Clean up invalid session data
            request.session.pop('current_school_id', None)
    
    # Option 2: From user's profile (if you have a default school field)
    # if hasattr(request.user, 'profile') and request.user.profile.default_school:
    #     return request.user.profile.default_school
    
    # Option 3: First school the user belongs to
    first_school = School.objects.filter(memberships__user=request.user, memberships__is_active=True).first()
    if first_school:
        # Store in session for consistency
        request.session['current_school_id'] = first_school.id
        return first_school
    
    return None


def get_user_role_for_school(user, school):
    """
    Get user's role in specific school.
    
    Returns the user's role (admin, teacher, student, etc.) for the given school.
    """
    membership = SchoolMembership.objects.get(user=user, school=school, is_active=True)
    return membership.role.lower()