"""
Forms for guardian management functionality.

This module provides forms for managing multiple guardians per student,
including adding new guardians and editing their permissions.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models.profiles import GuardianStudentRelationship

User = get_user_model()


class AddGuardianForm(forms.Form):
    """
    Form for adding a new guardian to a student.
    Handles both creating new users and adding existing users as guardians.
    """

    # Guardian user selection/creation
    email = forms.EmailField(
        label=_("Guardian Email"),
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "guardian@example.com",
            }
        ),
        help_text=_("Email address of the guardian. If they don't have an account, one will be created."),
    )

    name = forms.CharField(
        label=_("Full Name"),
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "Guardian full name",
            }
        ),
        help_text=_("Full name of the guardian"),
    )

    phone = forms.CharField(
        label=_("Phone Number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "+351 900 000 000",
            }
        ),
        help_text=_("Guardian's phone number (optional)"),
    )

    # Relationship details
    relationship_type = forms.CharField(
        label=_("Relationship"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "e.g., Mother, Father, Legal Guardian",
            }
        ),
        help_text=_("Relationship to the student (optional)"),
    )

    is_primary = forms.BooleanField(
        label=_("Set as Primary Guardian"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Primary guardian handles billing and is the main contact"),
    )

    # Permissions
    can_manage_finances = forms.BooleanField(
        label=_("Can Manage Finances"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can manage student's financial accounts and payments"),
    )

    can_book_classes = forms.BooleanField(
        label=_("Can Book Classes"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can book and cancel classes for the student"),
    )

    can_view_records = forms.BooleanField(
        label=_("Can View Records"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can view student's academic records and progress"),
    )

    can_edit_profile = forms.BooleanField(
        label=_("Can Edit Profile"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can edit student's profile information"),
    )

    can_receive_notifications = forms.BooleanField(
        label=_("Can Receive Notifications"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Receives notifications about the student"),
    )

    def __init__(self, student, school, *args, **kwargs):
        self.student = student
        self.school = school
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """Validate email and check for existing relationships."""
        email = self.cleaned_data["email"].lower()

        # Check if a guardian with this email already exists for this student
        try:
            guardian_user = User.objects.get(email=email)
            existing_relationship = GuardianStudentRelationship.objects.filter(
                guardian=guardian_user, student=self.student, school=self.school, is_active=True
            ).first()

            if existing_relationship:
                raise ValidationError(_("This guardian is already associated with this student."))
        except User.DoesNotExist:
            # This is fine, we'll create a new user
            pass

        return email

    def clean_is_primary(self):
        """Validate primary guardian status."""
        is_primary = self.cleaned_data.get("is_primary", False)

        # If setting as primary, automatically grant financial permissions
        if is_primary:
            self.cleaned_data["can_manage_finances"] = True

        return is_primary

    def save(self, created_by=None):
        """
        Create or get the guardian user and establish the relationship.
        Returns the created GuardianStudentRelationship instance.
        """
        email = self.cleaned_data["email"]
        name = self.cleaned_data["name"]
        phone = self.cleaned_data.get("phone", "")

        with transaction.atomic():
            # Create or get guardian user
            guardian_user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "phone_number": phone,
                    "is_active": True,
                },
            )

            # Update name and phone if user exists but info is different
            if not created:
                if guardian_user.name != name:
                    guardian_user.name = name
                if phone and guardian_user.phone_number != phone:
                    guardian_user.phone_number = phone
                guardian_user.save()

            # If setting as primary, remove primary status from other guardians
            if self.cleaned_data.get("is_primary", False):
                GuardianStudentRelationship.objects.filter(
                    student=self.student, school=self.school, is_active=True
                ).update(is_primary=False)

            # Create the guardian relationship
            relationship = GuardianStudentRelationship.objects.create(
                guardian=guardian_user,
                student=self.student,
                school=self.school,
                is_primary=self.cleaned_data.get("is_primary", False),
                can_manage_finances=self.cleaned_data.get("can_manage_finances", False),
                can_book_classes=self.cleaned_data.get("can_book_classes", True),
                can_view_records=self.cleaned_data.get("can_view_records", True),
                can_edit_profile=self.cleaned_data.get("can_edit_profile", True),
                can_receive_notifications=self.cleaned_data.get("can_receive_notifications", True),
                relationship_type=self.cleaned_data.get("relationship_type", ""),
                created_by=created_by,
            )

            return relationship


class EditGuardianPermissionsForm(forms.Form):
    """
    Form for editing an existing guardian's permissions and details.
    """

    # Relationship details
    relationship_type = forms.CharField(
        label=_("Relationship"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
                "placeholder": "e.g., Mother, Father, Legal Guardian",
            }
        ),
        help_text=_("Relationship to the student"),
    )

    is_primary = forms.BooleanField(
        label=_("Primary Guardian"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Primary guardian handles billing and is the main contact"),
    )

    # Permissions
    can_manage_finances = forms.BooleanField(
        label=_("Can Manage Finances"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can manage student's financial accounts and payments"),
    )

    can_book_classes = forms.BooleanField(
        label=_("Can Book Classes"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can book and cancel classes for the student"),
    )

    can_view_records = forms.BooleanField(
        label=_("Can View Records"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can view student's academic records and progress"),
    )

    can_edit_profile = forms.BooleanField(
        label=_("Can Edit Profile"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Can edit student's profile information"),
    )

    can_receive_notifications = forms.BooleanField(
        label=_("Can Receive Notifications"),
        required=False,
        widget=forms.CheckboxInput(
            attrs={"class": "h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"}
        ),
        help_text=_("Receives notifications about the student"),
    )

    def __init__(self, relationship, *args, **kwargs):
        self.relationship = relationship
        super().__init__(*args, **kwargs)

        # Pre-populate form with current values
        self.fields["relationship_type"].initial = relationship.relationship_type
        self.fields["is_primary"].initial = relationship.is_primary
        self.fields["can_manage_finances"].initial = relationship.can_manage_finances
        self.fields["can_book_classes"].initial = relationship.can_book_classes
        self.fields["can_view_records"].initial = relationship.can_view_records
        self.fields["can_edit_profile"].initial = relationship.can_edit_profile
        self.fields["can_receive_notifications"].initial = relationship.can_receive_notifications

    def clean_is_primary(self):
        """Validate primary guardian status."""
        is_primary = self.cleaned_data.get("is_primary", False)

        # If setting as primary, automatically grant financial permissions
        if is_primary:
            self.cleaned_data["can_manage_finances"] = True

        return is_primary

    def clean(self):
        """Additional validation to ensure business rules."""
        cleaned_data = super().clean()
        is_primary = cleaned_data.get("is_primary", False)

        # Primary guardians must have financial permissions
        if is_primary and not cleaned_data.get("can_manage_finances", False):
            cleaned_data["can_manage_finances"] = True

        return cleaned_data

    def save(self):
        """
        Update the guardian relationship with new permissions and details.
        Returns the updated GuardianStudentRelationship instance.
        """
        with transaction.atomic():
            # If setting as primary, remove primary status from other guardians
            if self.cleaned_data.get("is_primary", False) and not self.relationship.is_primary:
                GuardianStudentRelationship.objects.filter(
                    student=self.relationship.student, school=self.relationship.school, is_active=True
                ).exclude(id=self.relationship.id).update(is_primary=False)

            # Update the relationship
            self.relationship.relationship_type = self.cleaned_data.get("relationship_type", "")
            self.relationship.is_primary = self.cleaned_data.get("is_primary", False)
            self.relationship.can_manage_finances = self.cleaned_data.get("can_manage_finances", False)
            self.relationship.can_book_classes = self.cleaned_data.get("can_book_classes", False)
            self.relationship.can_view_records = self.cleaned_data.get("can_view_records", False)
            self.relationship.can_edit_profile = self.cleaned_data.get("can_edit_profile", False)
            self.relationship.can_receive_notifications = self.cleaned_data.get("can_receive_notifications", False)

            self.relationship.save()

            return self.relationship
