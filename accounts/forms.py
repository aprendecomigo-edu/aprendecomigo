from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm

from .models import CustomUser


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
        fields = ("email", "name", "phone_number")


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
    )
