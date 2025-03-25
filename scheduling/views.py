from django.shortcuts import render
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CalendarFilterForm
from .models import Subject
from django.contrib.auth import get_user_model

User = get_user_model()


class CalendarView(LoginRequiredMixin, TemplateView):
    """View to display embedded Google Calendar."""
    template_name = 'scheduling/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add calendar settings to context
        # In a real implementation, you'd use actual API keys and calendar IDs
        context.update({
            'calendar_id': 'primary',  # This would be configurable or user-specific
            'page_title': 'Calendar',
        })
        
        return context


class AdminCalendarView(LoginRequiredMixin, FormView):
    """Admin view for calendar management with filtering options."""
    template_name = 'scheduling/admin_calendar.html'
    form_class = CalendarFilterForm
    success_url = '.'  # Redirect to the same page
    
    def get_initial(self):
        initial = super().get_initial()
        # Set default values
        initial['date_range'] = 'week'
        initial['calendar_id'] = 'primary'
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add any additional form kwargs here if needed
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Process form data if available
        form = context.get('form')
        if form and form.is_valid():
            calendar_id = form.cleaned_data.get('calendar_id', 'primary')
        else:
            calendar_id = 'primary'
        
        # Add calendar context
        context.update({
            'calendar_id': calendar_id,
            'page_title': 'Admin Calendar',
            'can_add_events': True,  # Flag to show/hide direct links to Google Calendar
            
            # Add example data for the template (would be dynamic in production)
            'teachers': User.objects.filter(is_admin=False),
            'subjects': Subject.objects.all(),
        })
        
        return context
    
    def form_valid(self, form):
        # Process the form data
        # Since we're using client-side filtering with JavaScript,
        # we don't need server-side processing
        return super().form_valid(form)
