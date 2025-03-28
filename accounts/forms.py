from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, Student


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "name", "phone_number", "user_type")


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )


class StudentOnboardingForm(forms.ModelForm):
    """
    Form for student onboarding after registration
    """

    # User fields can be updated as part of onboarding
    name = forms.CharField(
        label=_("Full Name"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        label=_("Phone Number"),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Student
        fields = ("school_year", "birth_date", "address", "cc_number", "cc_photo")
        widgets = {
            "school_year": forms.Select(
                attrs={"class": "form-control"},
                choices=[
                    ("", _("Choose")),
                    ("1", "1º Ano"),
                    ("2", "2º Ano"),
                    ("3", "3º Ano"),
                    ("4", "4º Ano"),
                    ("5", "5º Ano"),
                    ("6", "6º Ano"),
                    ("7", "7º Ano"),
                    ("8", "8º Ano"),
                    ("9", "9º Ano"),
                    ("10", "10º Ano"),
                    ("11", "11º Ano"),
                    ("12", "12º Ano"),
                    ("college", _("College/University")),
                    ("adult", _("Adult Education")),
                ],
            ),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cc_number": forms.TextInput(attrs={"class": "form-control"}),
            "cc_photo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields required except cc_photo
        for field_name, field in self.fields.items():
            if field_name not in ["cc_photo"]:
                field.required = True

    def save(self, commit=True):
        student = super().save(commit=False)

        # Update user fields if available
        if hasattr(student, "user") and student.user:
            user = student.user
            if "name" in self.cleaned_data:
                user.name = self.cleaned_data["name"]
            if "phone_number" in self.cleaned_data:
                user.phone_number = self.cleaned_data["phone_number"]

            # Set user type to student
            user.user_type = "student"
            user.save()

        if commit:
            student.save()
        return student


class StudentCreationForm(forms.ModelForm):
    """
    Form for creating a student with user account in the admin
    """

    email = forms.EmailField(label="Email", required=False)
    name = forms.CharField(label="Full Name", max_length=150, required=False)
    phone_number = forms.CharField(label="Phone Number", max_length=20, required=False)
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = Student
        fields = (
            "school_year",
            "birth_date",
            "address",
            "cc_number",
            "cc_photo",
            "calendar_iframe",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we have an instance, we're editing an existing student
        if self.instance and self.instance.pk:
            # Pre-fill the user fields
            self.fields["email"].initial = self.instance.user.email
            self.fields["name"].initial = self.instance.user.name
            self.fields["phone_number"].initial = self.instance.user.phone_number

            # Make passwords not required in edit mode
            self.fields["password1"].required = False
            self.fields["password2"].required = False
        else:
            # Make user fields required in create mode
            self.fields["email"].required = True
            self.fields["name"].required = True
            self.fields["password1"].required = True
            self.fields["password2"].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        # Only check passwords if provided
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match")
        return password2

    @transaction.atomic
    def save(self, commit=True):
        # Check if we're editing an existing student
        if self.instance and self.instance.pk:
            # Update existing user
            user = self.instance.user
            if "email" in self.cleaned_data:
                user.email = self.cleaned_data["email"]
            if "name" in self.cleaned_data:
                user.name = self.cleaned_data["name"]
            if "phone_number" in self.cleaned_data:
                user.phone_number = self.cleaned_data.get("phone_number", "")

            # Only update password if provided
            password = self.cleaned_data.get("password1")
            if password:
                user.set_password(password)

            user.save()

            # Update student
            student = super().save(commit=commit)
            return student
        else:
            # Create new user and student
            user = CustomUser(
                email=self.cleaned_data["email"],
                name=self.cleaned_data["name"],
                phone_number=self.cleaned_data.get("phone_number", ""),
                user_type="student",
            )
            user.set_password(self.cleaned_data["password1"])
            user.save()

            # Create student profile
            student = super().save(commit=False)
            student.user = user
            if commit:
                student.save()
            return student
