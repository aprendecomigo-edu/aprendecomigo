#!/usr/bin/env python
"""
Simple script to check authentication classes for views.
"""

import os

import django

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

# Print authentication classes
print("\nAuthentication Classes:")
print("-" * 50)

views = [
    UserViewSet,
    TeacherViewSet,
    StudentViewSet,
    RequestEmailCodeView,
    VerifyEmailCodeView,
ß]

for view in views:
    auth_classes = getattr(view, "authentication_classes", None)
    print(f"{view.__name__}: {auth_classes}")

# Check inheritance
print("\nInheritance:")
print("-" * 50)

for view in views:
    if view.__name__ in ["RequestEmailCodeView", "VerifyEmailCodeView"]:
        # These are authentication views, so they don't need Knox auth
        expected = "django.rest_framework.views.APIView"
    elif view.__name__.endswith("ViewSet"):
        expected = "KnoxAuthenticatedViewSet"
    else:
        expected = "KnoxAuthenticatedAPIView"

    actual = view.__bases__[0].__name__
    is_correct = actual == expected or (
        expected == "django.rest_framework.views.APIView" and actual == "APIView"
    )

    print(f"{view.__name__}: {actual} {'✓' if is_correct else '✗'}")

print("\nDone.")
