"""
Context helper functions for accounts app.

This module provides utility functions to generate context data for templates,
particularly for form choices and options that need to be centrally managed.
"""

from .models.enums import UnifiedSchoolYear


def get_school_year_choices():
    """
    Get school year choices for template dropdowns.

    Returns:
        list: List of tuples (value, label) for school year options
    """
    return UnifiedSchoolYear.choices
