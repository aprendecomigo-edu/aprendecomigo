"""
Wizard Orchestration Service for Teacher Profile Creation.

GitHub Issue #95: Backend wizard orchestration API for guided profile creation.

This service provides:
- Step-by-step wizard orchestration
- Profile completion tracking
- School policy integration
- Wizard metadata generation
"""

import logging
from typing import Any

from accounts.models import School, SchoolSettings, TeacherProfile
from accounts.services.profile_completion import ProfileCompletionService

logger = logging.getLogger(__name__)


class WizardOrchestrationService:
    """
    Service for orchestrating the teacher profile creation wizard.

    Provides step-by-step guidance, validation, and progress tracking
    for comprehensive teacher profile creation during invitation acceptance.
    """

    # Define wizard steps with metadata
    WIZARD_STEPS = [
        {
            "step_number": 0,
            "title": "Personal Information",
            "description": "Basic personal details and contact information",
            "fields": ["first_name", "last_name", "email", "phone_number", "profile_photo"],
            "is_required": True,
            "estimated_time_minutes": 3,
        },
        {
            "step_number": 1,
            "title": "Professional Background",
            "description": "Your education and professional experience",
            "fields": [
                "professional_bio",
                "professional_title",
                "years_experience",
                "education_background",
                "teaching_experience",
                "credentials_documents",
            ],
            "is_required": True,
            "estimated_time_minutes": 8,
        },
        {
            "step_number": 2,
            "title": "Teaching Subjects",
            "description": "Subjects you teach and your expertise levels",
            "fields": ["teaching_subjects", "grade_level_preferences", "specialty"],
            "is_required": True,
            "estimated_time_minutes": 5,
        },
        {
            "step_number": 3,
            "title": "Rates & Pricing",
            "description": "Set your hourly rates and pricing structure",
            "fields": ["hourly_rate", "rate_structure"],
            "is_required": True,
            "estimated_time_minutes": 4,
        },
        {
            "step_number": 4,
            "title": "Availability",
            "description": "When are you available to teach?",
            "fields": ["availability", "weekly_availability", "availability_schedule"],
            "is_required": False,
            "estimated_time_minutes": 6,
        },
        {
            "step_number": 5,
            "title": "Additional Information",
            "description": "Optional details to complete your profile",
            "fields": ["address", "calendar_iframe"],
            "is_required": False,
            "estimated_time_minutes": 3,
        },
    ]

    @classmethod
    def generate_wizard_metadata(cls, teacher_profile: TeacherProfile, school: School) -> dict[str, Any]:
        """
        Generate complete wizard metadata for guided profile creation.

        Args:
            teacher_profile: The teacher's profile instance
            school: The school context for policies

        Returns:
            Dict containing wizard metadata including steps, completion status, and school policies
        """
        try:
            # Get completion status
            completion_status = cls._get_completion_status(teacher_profile)

            # Get school policies
            school_policies = cls._get_school_policies(school)

            # Determine current step based on completion
            current_step = cls._determine_current_step(completion_status)

            # Generate step metadata
            steps = cls._generate_step_metadata(school_policies)

            return {
                "steps": steps,
                "current_step": current_step,
                "completion_status": completion_status,
                "school_policies": school_policies,
            }

        except Exception as e:
            logger.error(f"Failed to generate wizard metadata for teacher {teacher_profile.id}: {e}")
            # Return minimal fallback metadata
            return cls._get_fallback_metadata()

    @classmethod
    def _get_completion_status(cls, teacher_profile: TeacherProfile) -> dict[str, Any]:
        """Get detailed completion status for the teacher profile."""
        try:
            completion_data = ProfileCompletionService.calculate_completion(teacher_profile)

            return {
                "completion_percentage": float(completion_data["completion_percentage"]),
                "missing_critical": completion_data.get("missing_critical", []),
                "missing_optional": completion_data.get("missing_optional", []),
                "is_complete": completion_data.get("is_complete", False),
                "scores_breakdown": completion_data.get("scores_breakdown", {}),
                "recommendations": completion_data.get("recommendations", []),
            }

        except Exception as e:
            logger.error(f"Failed to get completion status for teacher {teacher_profile.id}: {e}")
            return {
                "completion_percentage": 0.0,
                "missing_critical": [],
                "missing_optional": [],
                "is_complete": False,
                "scores_breakdown": {"basic_info": 0.0, "teaching_details": 0.0, "professional_info": 0.0},
                "recommendations": [],
            }

    @classmethod
    def _get_school_policies(cls, school: School) -> dict[str, Any]:
        """Get school-specific policies relevant to the wizard."""
        try:
            # Get or create school settings
            settings, created = SchoolSettings.objects.get_or_create(
                school=school,
                defaults={
                    "currency_code": "EUR",
                    "working_hours_start": "08:00",
                    "working_hours_end": "18:00",
                    "timezone": "UTC",
                    "trial_cost_absorption": "school",
                },
            )

            # Generate rate constraints based on currency and region
            rate_constraints = cls._generate_rate_constraints(settings.currency_code)

            return {
                "currency_code": settings.currency_code,
                "rate_constraints": rate_constraints,
                "working_hours": {"start": str(settings.working_hours_start), "end": str(settings.working_hours_end)},
                "timezone": settings.timezone,
                "trial_cost_absorption": settings.trial_cost_absorption,
            }

        except Exception as e:
            logger.error(f"Failed to get school policies for school {school.id}: {e}")
            return cls._get_default_school_policies()

    @classmethod
    def _generate_rate_constraints(cls, currency_code: str) -> dict[str, Any]:
        """Generate rate constraints based on currency and market data."""
        # Default rate ranges by currency (these could be moved to database/config)
        currency_constraints = {
            "EUR": {"min_rate": 10.0, "max_rate": 100.0, "suggested_range": [15.0, 50.0], "currency_symbol": "€"},
            "USD": {"min_rate": 12.0, "max_rate": 120.0, "suggested_range": [18.0, 60.0], "currency_symbol": "$"},
            "BRL": {"min_rate": 50.0, "max_rate": 500.0, "suggested_range": [80.0, 250.0], "currency_symbol": "R$"},
            "GBP": {"min_rate": 8.0, "max_rate": 80.0, "suggested_range": [12.0, 40.0], "currency_symbol": "£"},
        }

        constraints = currency_constraints.get(currency_code, currency_constraints["EUR"])
        constraints["currency"] = currency_code

        return constraints

    @classmethod
    def _determine_current_step(cls, completion_status: dict[str, Any]) -> int:
        """Determine the current step based on completion status."""
        # If profile is complete, return the last step
        if completion_status.get("is_complete", False):
            return len(cls.WIZARD_STEPS) - 1

        # Otherwise, find the first step with missing required fields
        missing_critical = completion_status.get("missing_critical", [])

        # Map missing fields to steps (simplified logic)
        if any(field in missing_critical for field in ["name", "email", "phone_number"]):
            return 0  # Personal Information
        elif any(field in missing_critical for field in ["bio", "education", "experience"]):
            return 1  # Professional Background
        elif any(field in missing_critical for field in ["teaching_subjects", "specialty"]):
            return 2  # Teaching Subjects
        elif any(field in missing_critical for field in ["hourly_rate", "rate_structure"]):
            return 3  # Rates & Pricing
        else:
            return 4  # Availability (optional steps)

    @classmethod
    def _generate_step_metadata(cls, school_policies: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate step metadata with school-specific information."""
        steps = []

        for step_template in cls.WIZARD_STEPS:
            step = step_template.copy()

            # Add school-specific context to step descriptions
            if step["step_number"] == 3:  # Rates & Pricing step
                currency = school_policies.get("currency_code", "EUR")
                currency_symbol = school_policies.get("rate_constraints", {}).get("currency_symbol", "€")
                step["description"] = f"Set your hourly rates in {currency} ({currency_symbol})"

            steps.append(step)

        return steps

    @classmethod
    def _get_default_school_policies(cls) -> dict[str, Any]:
        """Get default school policies as fallback."""
        return {
            "currency_code": "EUR",
            "rate_constraints": cls._generate_rate_constraints("EUR"),
            "working_hours": {"start": "08:00", "end": "18:00"},
            "timezone": "UTC",
            "trial_cost_absorption": "school",
        }

    @classmethod
    def _get_fallback_metadata(cls) -> dict[str, Any]:
        """Get minimal fallback metadata in case of errors."""
        return {
            "steps": cls.WIZARD_STEPS,
            "current_step": 0,
            "completion_status": {
                "completion_percentage": 0.0,
                "missing_critical": [],
                "missing_optional": [],
                "is_complete": False,
                "scores_breakdown": {},
                "recommendations": [],
            },
            "school_policies": cls._get_default_school_policies(),
        }

    @classmethod
    def validate_step_data(cls, step: int, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data for a specific wizard step.

        Args:
            step: Step number (0-based)
            data: Data to validate

        Returns:
            Dict with validation results including is_valid, validated_data, and errors
        """
        try:
            from accounts.serializers import ProfileWizardDataSerializer

            # Use the comprehensive ProfileWizardDataSerializer for validation
            serializer = ProfileWizardDataSerializer(data=data)

            if serializer.is_valid():
                return {"is_valid": True, "validated_data": serializer.validated_data, "errors": {}}
            else:
                return {"is_valid": False, "validated_data": {}, "errors": serializer.errors}

        except Exception as e:
            logger.error(f"Failed to validate step {step} data: {e}")
            return {
                "is_valid": False,
                "validated_data": {},
                "errors": {"general": ["Validation failed due to server error"]},
            }
