"""
Guardian management views for Django web interface.

This module provides comprehensive guardian management functionality including:
- Listing and managing all guardians for a student
- Adding new guardians with proper permissions
- Editing existing guardian permissions
- Removing guardians (with safeguards)
- Setting primary guardian status

All views use HTMX for dynamic updates without page refresh and include
proper permission checks and validation.
"""

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST

from .forms import AddGuardianForm, EditGuardianPermissionsForm
from .models.profiles import GuardianStudentRelationship
from .models.schools import School, SchoolRole

logger = logging.getLogger(__name__)
User = get_user_model()


def _can_manage_guardians(user, student, school):
    """
    Check if the user can manage guardians for a student.
    Only admins and primary guardians can manage other guardians.
    """
    # Check if user is school admin
    is_admin = user.school_memberships.filter(
        school=school, role__in=[SchoolRole.SCHOOL_OWNER, SchoolRole.SCHOOL_ADMIN], is_active=True
    ).exists()

    if is_admin:
        return True

    # Primary guardians can manage
    primary_relationship = GuardianStudentRelationship.objects.filter(
        guardian=user, student=student, school=school, is_primary=True, is_active=True
    ).first()

    return primary_relationship is not None


@login_required
@require_http_methods(["GET"])
def manage_student_guardians(request: HttpRequest, school_id: int, student_id: int) -> HttpResponse:
    """
    Main view for managing all guardians for a student.
    Shows list of guardians with options to add, edit, remove, and set primary.
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to manage guardians for this student."))

    # Get all active guardian relationships for this student
    guardian_relationships = (
        GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True)
        .select_related("guardian")
        .order_by("-is_primary", "created_at")
    )

    # Check if current user is primary guardian
    is_primary_guardian = GuardianStudentRelationship.objects.filter(
        guardian=request.user, student=student, school=school, is_primary=True, is_active=True
    ).exists()

    context = {
        "school": school,
        "student": student,
        "guardian_relationships": guardian_relationships,
        "is_primary_guardian": is_primary_guardian,
        "can_manage": True,  # Already checked above
        "add_guardian_form": AddGuardianForm(student=student, school=school),
    }

    return render(request, "accounts/manage_guardians.html", context)


@login_required
@require_POST
def add_guardian(request: HttpRequest, school_id: int, student_id: int) -> HttpResponse:
    """
    Add a new guardian to a student.
    Uses HTMX for dynamic form submission and updates.
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to manage guardians for this student."))

    form = AddGuardianForm(student=student, school=school, data=request.POST)

    if form.is_valid():
        try:
            with transaction.atomic():
                relationship = form.save(created_by=request.user)

                messages.success(
                    request,
                    _("Guardian {guardian_name} has been successfully added.").format(
                        guardian_name=relationship.guardian.name
                    ),
                )

                # If this is an HTMX request, return the updated guardian list
                if request.headers.get("HX-Request"):
                    guardian_relationships = (
                        GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True)
                        .select_related("guardian")
                        .order_by("-is_primary", "created_at")
                    )

                    return render(
                        request,
                        "accounts/partials/guardian_list.html",
                        {
                            "guardian_relationships": guardian_relationships,
                            "school": school,
                            "student": student,
                            "can_manage": True,
                        },
                    )

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error adding guardian: {e}", exc_info=True)
            messages.error(request, _("An error occurred while adding the guardian."))

    else:
        # Return form with errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    # If HTMX request, return the form with errors
    if request.headers.get("HX-Request"):
        return render(
            request,
            "accounts/partials/add_guardian_form.html",
            {
                "form": form,
                "school": school,
                "student": student,
            },
        )

    # Fallback to full page reload
    return manage_student_guardians(request, school_id, student_id)


@login_required
@require_http_methods(["GET", "POST"])
def update_guardian_permissions(
    request: HttpRequest, school_id: int, student_id: int, relationship_id: int
) -> HttpResponse:
    """
    Update permissions for an existing guardian.
    GET: Show edit form
    POST: Process form submission
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)
    relationship = get_object_or_404(
        GuardianStudentRelationship, id=relationship_id, student=student, school=school, is_active=True
    )

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to manage guardians for this student."))

    if request.method == "POST":
        form = EditGuardianPermissionsForm(relationship=relationship, data=request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_relationship = form.save()

                    messages.success(
                        request,
                        _("Guardian permissions for {guardian_name} have been updated.").format(
                            guardian_name=updated_relationship.guardian.name
                        ),
                    )

                    # If HTMX request, return updated guardian card
                    if request.headers.get("HX-Request"):
                        return render(
                            request,
                            "accounts/partials/guardian_card.html",
                            {
                                "relationship": updated_relationship,
                                "school": school,
                                "student": student,
                                "can_manage": True,
                            },
                        )

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error updating guardian permissions: {e}", exc_info=True)
                messages.error(request, _("An error occurred while updating guardian permissions."))
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:  # GET request
        form = EditGuardianPermissionsForm(relationship=relationship)

    # Return edit form
    if request.headers.get("HX-Request"):
        return render(
            request,
            "accounts/partials/edit_guardian_form.html",
            {
                "form": form,
                "relationship": relationship,
                "school": school,
                "student": student,
            },
        )

    # Fallback to full page
    return manage_student_guardians(request, school_id, student_id)


@login_required
@require_POST
def remove_guardian(request: HttpRequest, school_id: int, student_id: int, relationship_id: int) -> HttpResponse:
    """
    Remove a guardian from a student (deactivate the relationship).
    Includes safeguards to prevent removing the last guardian.
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)
    relationship = get_object_or_404(
        GuardianStudentRelationship, id=relationship_id, student=student, school=school, is_active=True
    )

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to manage guardians for this student."))

    # Check if this is the last active guardian
    active_guardians_count = GuardianStudentRelationship.objects.filter(
        student=student, school=school, is_active=True
    ).count()

    if active_guardians_count <= 1:
        messages.error(request, _("Cannot remove the last guardian. A student must have at least one active guardian."))
    else:
        try:
            with transaction.atomic():
                # If removing primary guardian, set another as primary
                if relationship.is_primary:
                    other_relationship = (
                        GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True)
                        .exclude(id=relationship.id)
                        .first()
                    )

                    if other_relationship:
                        other_relationship.is_primary = True
                        other_relationship.can_manage_finances = True  # Primary must have financial permissions
                        other_relationship.save()

                # Deactivate the relationship
                relationship.is_active = False
                relationship.save()

                messages.success(
                    request,
                    _("Guardian {guardian_name} has been removed.").format(guardian_name=relationship.guardian.name),
                )

        except Exception as e:
            logger.error(f"Error removing guardian: {e}", exc_info=True)
            messages.error(request, _("An error occurred while removing the guardian."))

    # If HTMX request, return updated guardian list
    if request.headers.get("HX-Request"):
        guardian_relationships = (
            GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True)
            .select_related("guardian")
            .order_by("-is_primary", "created_at")
        )

        return render(
            request,
            "accounts/partials/guardian_list.html",
            {
                "guardian_relationships": guardian_relationships,
                "school": school,
                "student": student,
                "can_manage": True,
            },
        )

    # Fallback to full page reload
    return manage_student_guardians(request, school_id, student_id)


@login_required
@require_POST
def set_primary_guardian(request: HttpRequest, school_id: int, student_id: int, relationship_id: int) -> HttpResponse:
    """
    Set a guardian as the primary guardian for a student.
    Automatically grants financial permissions to the new primary guardian.
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)
    relationship = get_object_or_404(
        GuardianStudentRelationship, id=relationship_id, student=student, school=school, is_active=True
    )

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to manage guardians for this student."))

    if relationship.is_primary:
        messages.info(request, _("This guardian is already the primary guardian."))
    else:
        try:
            with transaction.atomic():
                # Remove primary status from all other guardians
                GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True).update(
                    is_primary=False
                )

                # Set this guardian as primary and grant financial permissions
                relationship.is_primary = True
                relationship.can_manage_finances = True
                relationship.save()

                messages.success(
                    request,
                    _("{guardian_name} is now the primary guardian.").format(guardian_name=relationship.guardian.name),
                )

        except Exception as e:
            logger.error(f"Error setting primary guardian: {e}", exc_info=True)
            messages.error(request, _("An error occurred while setting the primary guardian."))

    # If HTMX request, return updated guardian list
    if request.headers.get("HX-Request"):
        guardian_relationships = (
            GuardianStudentRelationship.objects.filter(student=student, school=school, is_active=True)
            .select_related("guardian")
            .order_by("-is_primary", "created_at")
        )

        return render(
            request,
            "accounts/partials/guardian_list.html",
            {
                "guardian_relationships": guardian_relationships,
                "school": school,
                "student": student,
                "can_manage": True,
            },
        )

    # Fallback to full page reload
    return manage_student_guardians(request, school_id, student_id)


@login_required
@require_http_methods(["GET"])
def get_guardian_details(request: HttpRequest, school_id: int, student_id: int, relationship_id: int) -> JsonResponse:
    """
    Get detailed information about a guardian relationship.
    Used for AJAX requests and modals.
    """
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(User, id=student_id)
    relationship = get_object_or_404(
        GuardianStudentRelationship, id=relationship_id, student=student, school=school, is_active=True
    )

    # Permission check
    if not _can_manage_guardians(request.user, student, school):
        raise PermissionDenied(_("You don't have permission to view guardian details."))

    data = {
        "id": relationship.id,
        "guardian": {
            "id": relationship.guardian.id,
            "name": relationship.guardian.name,
            "email": relationship.guardian.email,
            "phone": getattr(relationship.guardian, "phone", ""),
        },
        "relationship_type": relationship.relationship_type,
        "is_primary": relationship.is_primary,
        "permissions": {
            "can_manage_finances": relationship.can_manage_finances,
            "can_book_classes": relationship.can_book_classes,
            "can_view_records": relationship.can_view_records,
            "can_edit_profile": relationship.can_edit_profile,
            "can_receive_notifications": relationship.can_receive_notifications,
        },
        "created_at": relationship.created_at.isoformat(),
        "updated_at": relationship.updated_at.isoformat(),
    }

    return JsonResponse(data)
