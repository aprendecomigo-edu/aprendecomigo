"""
ProfileCompletionService - Business logic for teacher profile completion scoring.

This service implements the business requirements for calculating profile completion
percentages and identifying missing fields to improve profile quality.

Business Logic:
- Basic info (name, bio, education): 40% weight
- Teaching details (subjects, rates, availability): 40% weight
- Professional info (experience, languages, calendar): 20% weight
- Critical fields: bio, at least one subject, hourly rate
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProfileCompletionService:
    """Service for calculating teacher profile completion and providing recommendations."""

    # Weight distribution for completion calculation
    BASIC_INFO_WEIGHT = 0.4  # 40%
    TEACHING_DETAILS_WEIGHT = 0.4  # 40%
    PROFESSIONAL_INFO_WEIGHT = 0.2  # 20%

    # Critical fields that significantly impact completion
    CRITICAL_FIELDS = [
        "bio",
        "hourly_rate",
        "teaching_subjects",  # At least one subject/course required
    ]

    # Optional fields that improve profile quality
    OPTIONAL_FIELDS = [
        "specialty",
        "education",
        "availability",
        "address",
        "phone_number",
        "calendar_iframe",
        "education_background",
        "rate_structure",
        "weekly_availability",
    ]

    # Quality thresholds
    BIO_MIN_LENGTH = 50
    BIO_GOOD_LENGTH = 150
    PROFILE_COMPLETE_THRESHOLD = 80.0

    @classmethod
    def calculate_completion(cls, teacher_profile) -> dict[str, Any]:
        """
        Calculate comprehensive profile completion score and recommendations.

        Args:
            teacher_profile: TeacherProfile instance

        Returns:
            Dict containing:
            - completion_percentage: Overall completion score (0-100)
            - missing_critical: List of missing critical fields
            - missing_optional: List of missing optional fields
            - recommendations: List of improvement suggestions
            - is_complete: Boolean indicating if profile meets completion threshold
            - scores_breakdown: Detailed scoring by category
        """
        try:
            # Calculate scores for each category
            basic_score = cls._calculate_basic_info_score(teacher_profile)
            teaching_score = cls._calculate_teaching_details_score(teacher_profile)
            professional_score = cls._calculate_professional_info_score(teacher_profile)

            # Calculate weighted total
            completion_percentage = cls.calculate_weighted_score(basic_score, teaching_score, professional_score)

            # Identify missing fields
            missing_critical, missing_optional = cls.identify_missing_fields(teacher_profile)

            # Generate recommendations
            recommendations = cls.get_profile_recommendations(teacher_profile)

            # Determine if profile is complete
            is_complete = completion_percentage >= cls.PROFILE_COMPLETE_THRESHOLD and len(missing_critical) == 0

            return {
                "completion_percentage": round(completion_percentage, 1),
                "missing_critical": missing_critical,
                "missing_optional": missing_optional,
                "recommendations": recommendations,
                "is_complete": is_complete,
                "scores_breakdown": {
                    "basic_info": round(basic_score, 1),
                    "teaching_details": round(teaching_score, 1),
                    "professional_info": round(professional_score, 1),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating profile completion for {teacher_profile.id}: {e}")
            # Return minimal valid response on error
            return {
                "completion_percentage": 0.0,
                "missing_critical": cls.CRITICAL_FIELDS.copy(),
                "missing_optional": cls.OPTIONAL_FIELDS.copy(),
                "recommendations": [{"text": "Please complete your profile information", "priority": "high"}],
                "is_complete": False,
                "scores_breakdown": {
                    "basic_info": 0.0,
                    "teaching_details": 0.0,
                    "professional_info": 0.0,
                },
            }

    @classmethod
    def _calculate_basic_info_score(cls, teacher_profile) -> float:
        """Calculate score for basic information (40% weight)."""
        score = 0.0
        max_score = 100.0

        # Name (from user) - 20%
        if teacher_profile.user and teacher_profile.user.name:
            score += 20.0

        # Bio quality - 40%
        bio_score = cls._assess_bio_quality(teacher_profile.bio)
        score += bio_score * 0.4

        # Education - 40%
        if teacher_profile.education and len(teacher_profile.education.strip()) > 10:
            score += 40.0

        return min(score, max_score)

    @classmethod
    def _calculate_teaching_details_score(cls, teacher_profile) -> float:
        """Calculate score for teaching details (40% weight)."""
        score = 0.0
        max_score = 100.0

        # Hourly rate - 30%
        if teacher_profile.hourly_rate and teacher_profile.hourly_rate > 0:
            score += 30.0

        # Teaching subjects/courses - 40%
        courses_count = teacher_profile.teacher_courses.filter(is_active=True).count()
        if courses_count > 0:
            # Scale up to 40% based on number of courses (max at 3+ courses)
            course_score = min(courses_count * 15, 40)
            score += course_score

        # Specialty - 15%
        if teacher_profile.specialty and len(teacher_profile.specialty.strip()) > 5:
            score += 15.0

        # Availability - 15%
        if teacher_profile.availability and len(teacher_profile.availability.strip()) > 10:
            score += 15.0

        return min(score, max_score)

    @classmethod
    def _calculate_professional_info_score(cls, teacher_profile) -> float:
        """Calculate score for professional information (20% weight)."""
        score = 0.0
        max_score = 100.0

        # Contact information - 30%
        contact_score = 0.0
        if teacher_profile.phone_number and len(teacher_profile.phone_number.strip()) > 5:
            contact_score += 15.0
        if teacher_profile.address and len(teacher_profile.address.strip()) > 10:
            contact_score += 15.0
        score += contact_score

        # Calendar integration - 30%
        if teacher_profile.calendar_iframe and len(teacher_profile.calendar_iframe.strip()) > 10:
            score += 30.0

        # Advanced fields (new structured data) - 40%
        advanced_score = 0.0

        # Check for education_background
        if hasattr(teacher_profile, "education_background") and teacher_profile.education_background:
            advanced_score += 10.0

        # Check for teaching_subjects
        if hasattr(teacher_profile, "teaching_subjects") and teacher_profile.teaching_subjects:
            advanced_score += 10.0

        # Check for rate_structure
        if hasattr(teacher_profile, "rate_structure") and teacher_profile.rate_structure:
            advanced_score += 10.0

        # Check for weekly_availability
        if hasattr(teacher_profile, "weekly_availability") and teacher_profile.weekly_availability:
            advanced_score += 10.0

        score += advanced_score

        return min(score, max_score)

    @classmethod
    def _assess_bio_quality(cls, bio: str) -> float:
        """Assess the quality of a biography text (0-100)."""
        if not bio or not bio.strip():
            return 0.0

        bio = bio.strip()
        length = len(bio)

        # Length scoring
        if length < cls.BIO_MIN_LENGTH:
            length_score = (length / cls.BIO_MIN_LENGTH) * 60  # Max 60% for short bios
        elif length < cls.BIO_GOOD_LENGTH:
            length_score = 60 + ((length - cls.BIO_MIN_LENGTH) / (cls.BIO_GOOD_LENGTH - cls.BIO_MIN_LENGTH)) * 30
        else:
            length_score = 90  # Good length gets 90%

        # Content quality indicators
        quality_score = 10  # Base score for having content

        # Check for professional keywords
        professional_keywords = [
            "experience",
            "teach",
            "education",
            "student",
            "year",
            "qualified",
            "degree",
            "master",
            "bachelor",
            "phd",
            "certified",
            "training",
        ]

        bio_lower = bio.lower()
        keyword_count = sum(1 for keyword in professional_keywords if keyword in bio_lower)
        quality_score += min(keyword_count * 2, 10)  # Up to 10% for keywords

        return min(length_score + quality_score, 100.0)

    @classmethod
    def identify_missing_fields(cls, teacher_profile) -> tuple[list[str], list[str]]:
        """
        Identify missing critical and optional fields.

        Returns:
            Tuple of (missing_critical, missing_optional) field lists
        """
        missing_critical = []
        missing_optional = []

        # Check critical fields
        if not teacher_profile.bio or len(teacher_profile.bio.strip()) < cls.BIO_MIN_LENGTH:
            missing_critical.append("bio")

        if not teacher_profile.hourly_rate or teacher_profile.hourly_rate <= 0:
            missing_critical.append("hourly_rate")

        # Check for at least one teaching subject/course
        if teacher_profile.teacher_courses.filter(is_active=True).count() == 0:
            missing_critical.append("teaching_subjects")

        # Check optional fields
        optional_field_mapping = {
            "specialty": teacher_profile.specialty,
            "education": teacher_profile.education,
            "availability": teacher_profile.availability,
            "address": teacher_profile.address,
            "phone_number": teacher_profile.phone_number,
            "calendar_iframe": teacher_profile.calendar_iframe,
        }

        for field_name, field_value in optional_field_mapping.items():
            if not field_value or len(str(field_value).strip()) == 0:
                missing_optional.append(field_name)

        # Check new structured fields
        for field_name in ["education_background", "rate_structure", "weekly_availability"]:
            if not hasattr(teacher_profile, field_name) or not getattr(teacher_profile, field_name, None):
                missing_optional.append(field_name)

        return missing_critical, missing_optional

    @classmethod
    def get_profile_recommendations(cls, teacher_profile) -> list[dict[str, str]]:
        """
        Generate specific recommendations for profile improvement.

        Returns:
            List of recommendation dictionaries with 'text' and 'priority' keys
        """
        recommendations = []
        missing_critical, missing_optional = cls.identify_missing_fields(teacher_profile)

        # Critical field recommendations
        if "bio" in missing_critical:
            recommendations.append(
                {
                    "text": f"Add a professional biography (at least {cls.BIO_MIN_LENGTH} characters) describing your teaching experience and qualifications.",
                    "priority": "high",
                }
            )

        if "hourly_rate" in missing_critical:
            recommendations.append(
                {"text": "Set your hourly rate to help students understand your pricing.", "priority": "high"}
            )

        if "teaching_subjects" in missing_critical:
            recommendations.append(
                {
                    "text": "Add at least one subject or course that you teach to help students find you.",
                    "priority": "high",
                }
            )

        # Optional field recommendations (prioritized)
        priority_optional = ["availability", "education", "calendar_iframe"]
        for field in priority_optional:
            if field in missing_optional:
                if field == "availability":
                    recommendations.append(
                        {"text": "Add your availability schedule to help students book classes.", "priority": "medium"}
                    )
                elif field == "education":
                    recommendations.append(
                        {"text": "Add your educational background to build student confidence.", "priority": "medium"}
                    )
                elif field == "calendar_iframe":
                    recommendations.append(
                        {"text": "Integrate your calendar to streamline scheduling.", "priority": "medium"}
                    )

        # Contact information
        if "phone_number" in missing_optional:
            recommendations.append({"text": "Add your phone number for easier communication.", "priority": "low"})

        if "address" in missing_optional:
            recommendations.append({"text": "Add your address if you offer in-person classes.", "priority": "low"})

        # Advanced features
        if "rate_structure" in missing_optional:
            recommendations.append(
                {
                    "text": "Set up detailed rate structure for different class types (individual, group, trial).",
                    "priority": "low",
                }
            )

        return recommendations

    @classmethod
    def calculate_weighted_score(cls, basic_score: float, teaching_score: float, professional_score: float) -> float:
        """Calculate weighted total score from category scores."""
        total = (
            basic_score * cls.BASIC_INFO_WEIGHT
            + teaching_score * cls.TEACHING_DETAILS_WEIGHT
            + professional_score * cls.PROFESSIONAL_INFO_WEIGHT
        )
        return round(total, 1)

    @classmethod
    def calculate_bulk_completion(cls, teacher_profiles) -> list[dict[str, Any]]:
        """
        Calculate completion for multiple teacher profiles efficiently.

        Args:
            teacher_profiles: QuerySet or list of TeacherProfile instances

        Returns:
            List of completion data dictionaries
        """
        results = []

        for profile in teacher_profiles:
            try:
                completion_data = cls.calculate_completion(profile)
                results.append(
                    {
                        "teacher_id": profile.id,
                        "user_id": profile.user.id,
                        "name": profile.user.name if profile.user else "Unknown",
                        "email": profile.user.email if profile.user else "Unknown",
                        "completion_percentage": completion_data["completion_percentage"],
                        "is_complete": completion_data["is_complete"],
                        "missing_critical_count": len(completion_data["missing_critical"]),
                        "recommendations_count": len(completion_data["recommendations"]),
                    }
                )
            except Exception as e:
                logger.error(f"Error calculating bulk completion for profile {profile.id}: {e}")
                results.append(
                    {
                        "teacher_id": profile.id,
                        "user_id": profile.user.id if profile.user else None,
                        "name": "Error",
                        "email": "Error",
                        "completion_percentage": 0.0,
                        "is_complete": False,
                        "missing_critical_count": len(cls.CRITICAL_FIELDS),
                        "recommendations_count": 0,
                    }
                )

        return results

    @classmethod
    def get_school_completion_analytics(cls, school_id: int) -> dict[str, Any]:
        """
        Generate school-wide profile completion analytics.

        Args:
            school_id: ID of the school to analyze

        Returns:
            Dictionary with school completion statistics
        """
        from accounts.models import SchoolMembership, SchoolRole

        try:
            # Get all teacher profiles for the school
            teacher_memberships = SchoolMembership.objects.filter(
                school_id=school_id, role=SchoolRole.TEACHER, is_active=True
            ).select_related("user__teacher_profile")

            teacher_profiles = []
            for membership in teacher_memberships:
                if hasattr(membership.user, "teacher_profile"):
                    teacher_profiles.append(membership.user.teacher_profile)

            if not teacher_profiles:
                return {
                    "total_teachers": 0,
                    "average_completion": 0.0,
                    "complete_profiles": 0,
                    "incomplete_profiles": 0,
                    "completion_distribution": {
                        "0-25%": 0,
                        "26-50%": 0,
                        "51-75%": 0,
                        "76-100%": 0,
                    },
                    "common_missing_fields": [],
                }

            # Calculate completion for all profiles
            bulk_results = cls.calculate_bulk_completion(teacher_profiles)

            # Calculate analytics
            total_teachers = len(bulk_results)
            completion_scores = [r["completion_percentage"] for r in bulk_results]
            average_completion = sum(completion_scores) / total_teachers if total_teachers > 0 else 0.0

            complete_profiles = sum(1 for r in bulk_results if r["is_complete"])
            incomplete_profiles = total_teachers - complete_profiles

            # Distribution
            distribution = {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0}
            for score in completion_scores:
                if score <= 25:
                    distribution["0-25%"] += 1
                elif score <= 50:
                    distribution["26-50%"] += 1
                elif score <= 75:
                    distribution["51-75%"] += 1
                else:
                    distribution["76-100%"] += 1

            # Find common missing fields
            all_missing_critical = []
            for profile in teacher_profiles:
                missing_critical, _ = cls.identify_missing_fields(profile)
                all_missing_critical.extend(missing_critical)

            # Count frequency of missing fields
            missing_field_counts = {}
            for field in all_missing_critical:
                missing_field_counts[field] = missing_field_counts.get(field, 0) + 1

            # Get top 5 most common missing fields
            common_missing_fields = sorted(missing_field_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "total_teachers": total_teachers,
                "average_completion": round(average_completion, 1),
                "complete_profiles": complete_profiles,
                "incomplete_profiles": incomplete_profiles,
                "completion_distribution": distribution,
                "common_missing_fields": [
                    {"field": field, "count": count, "percentage": round((count / total_teachers) * 100, 1)}
                    for field, count in common_missing_fields
                ],
            }

        except Exception as e:
            logger.error(f"Error calculating school completion analytics for school {school_id}: {e}")
            return {
                "total_teachers": 0,
                "average_completion": 0.0,
                "complete_profiles": 0,
                "incomplete_profiles": 0,
                "completion_distribution": {"0-25%": 0, "26-50%": 0, "51-75%": 0, "76-100%": 0},
                "common_missing_fields": [],
            }
