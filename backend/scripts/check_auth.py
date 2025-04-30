#!/usr/bin/env python
"""
Simple script to check authentication classes for views.
"""

import os
import sys

import django
from django.views import View
from rest_framework.viewsets import ViewSet

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings")
django.setup()

# Import views
from accounts.views import (
    RequestEmailCodeView,
    StudentViewSet,
    TeacherViewSet,
    UserViewSet,
    VerifyEmailCodeView,
)


def check_auth_classes(views: list[type[View | ViewSet]]) -> bool:
    """Check authentication classes for each view."""
    all_correct = True

    for view in views:
        auth_classes = getattr(view, "authentication_classes", None)
        if auth_classes is None:
            sys.stderr.write(f"Warning: {view.__name__} has no authentication_classes\n")
            all_correct = False
            continue

        # Check inheritance
        actual = [base.__name__ for base in view.__bases__]
        is_correct = any(
            base.__name__ in ["KnoxAuthenticatedAPIView", "KnoxAuthenticatedViewSet"]
            for base in view.__bases__
        )

        if not is_correct:
            sys.stderr.write(
                f"Warning: {view.__name__} does not inherit from Knox authenticated classes\n"
            )
            all_correct = False

    return all_correct


def main() -> None:
    """Main function."""
    views = [
        RequestEmailCodeView,
        StudentViewSet,
        TeacherViewSet,
        UserViewSet,
        VerifyEmailCodeView,
    ]

    success = check_auth_classes(views)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
