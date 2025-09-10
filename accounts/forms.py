"""
Forms for teacher invitation and onboarding process.

This module contains forms used during the teacher invitation acceptance
and onboarding workflow.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import TeacherProfile

User = get_user_model()


class TeacherRegistrationForm(forms.Form):
    """
    Form for teacher registration during invitation acceptance.
    
    Used when a teacher accepts an invitation and needs to create their account.
    Includes basic information required for account creation and initial profile.
    """
    
    name = forms.CharField(
        label=_("Nome completo"),
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduza o seu nome completo'
        })
    )
    
    phone_number = forms.CharField(
        label=_("Número de telemóvel"),
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+351912345678',
            'type': 'tel'
        }),
        help_text=_("Formato: +351912345678 (usado para verificação OTP)")
    )
    
    # Optional fields that can be filled during initial registration
    bio = forms.CharField(
        label=_("Biografia profissional"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva brevemente a sua experiência e especialidade...'
        }),
        required=False,
        help_text=_("Opcional: Pode preencher mais tarde no seu perfil")
    )
    
    specialty = forms.CharField(
        label=_("Especialidade"),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Matemática, Português, Inglês...'
        }),
        required=False,
        help_text=_("Opcional: Principal área de ensino")
    )
    
    # Multiple choice for subjects (will be stored as JSON)
    teaching_subjects = forms.CharField(
        label=_("Disciplinas que leciona"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Matemática, Física, Química (separadas por vírgulas)'
        }),
        required=False,
        help_text=_("Opcional: Separe múltiplas disciplinas com vírgulas")
    )
    
    def clean_phone_number(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Basic validation for Portuguese phone numbers
            import re
            pattern = r'^\+351\d{9}$|^\d{9}$'
            if not re.match(pattern, phone.replace(' ', '')):
                raise forms.ValidationError(
                    _("Formato inválido. Use +351912345678 ou 912345678")
                )
            # Ensure it starts with +351
            if not phone.startswith('+351'):
                phone = '+351' + phone.replace(' ', '')
        return phone
    
    def clean_teaching_subjects(self):
        """Convert comma-separated subjects to list."""
        subjects_str = self.cleaned_data.get('teaching_subjects', '')
        if subjects_str:
            # Split by comma and clean up
            subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
            return subjects
        return []
    
    def save(self, email, school):
        """
        Create user account and initial teacher profile.
        
        Args:
            email: Teacher's email address from invitation
            school: School they're joining
            
        Returns:
            Created User instance
        """
        # Create user
        user = User.objects.create_user(
            email=email,
            name=self.cleaned_data['name'],
            phone_number=self.cleaned_data['phone_number']
        )
        
        # Create teacher profile if optional fields were provided
        if any([
            self.cleaned_data.get('bio'),
            self.cleaned_data.get('specialty'),
            self.cleaned_data.get('teaching_subjects')
        ]):
            TeacherProfile.objects.create(
                user=user,
                bio=self.cleaned_data.get('bio', ''),
                specialty=self.cleaned_data.get('specialty', ''),
                teaching_subjects=self.cleaned_data.get('teaching_subjects', [])
            )
        
        return user