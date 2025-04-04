from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import ClassSession, ClassType

User = get_user_model()


def is_admin(user):
    """Check if the user is an admin"""
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def manage_class_types(request):
    """View for managing class types"""
    if request.method == "POST":
        name = request.POST.get("name")
        hourly_rate = request.POST.get("hourly_rate")

        # Simple validation
        if not name or not hourly_rate:
            messages.error(
                request, "Both Class Type Code and Hourly Rate are required."
            )
            return redirect("manage_class_types")

        try:
            # Check if class type already exists
            if ClassType.objects.filter(name=name).exists():
                messages.error(request, f"Class Type '{name}' already exists.")
                return redirect("manage_class_types")

            # Create new class type
            ClassType.objects.create(name=name, hourly_rate=hourly_rate)
            messages.success(request, f"Class Type '{name}' created successfully.")
            return redirect("manage_class_types")
        except Exception as e:
            messages.error(request, f"Error creating class type: {str(e)}")

    class_types = ClassType.objects.all().order_by("name")
    return render(
        request, "scheduling/manage_class_types.html", {"class_types": class_types}
    )


@login_required
@user_passes_test(is_admin)
def edit_class_type(request, class_type_id):
    """View for editing a class type"""
    class_type = get_object_or_404(ClassType, id=class_type_id)

    if request.method == "POST":
        name = request.POST.get("name")
        hourly_rate = request.POST.get("hourly_rate")

        # Simple validation
        if not name or not hourly_rate:
            messages.error(
                request, "Both Class Type Code and Hourly Rate are required."
            )
            return redirect("edit_class_type", class_type_id=class_type_id)

        try:
            # Check if another class type with the same name exists (excluding current)
            if ClassType.objects.filter(name=name).exclude(id=class_type_id).exists():
                messages.error(
                    request, f"Another class type with code '{name}' already exists."
                )
                return redirect("edit_class_type", class_type_id=class_type_id)

            # Update class type
            class_type.name = name
            class_type.hourly_rate = hourly_rate
            class_type.save()

            messages.success(request, f"Class Type '{name}' updated successfully.")
            return redirect("manage_class_types")
        except Exception as e:
            messages.error(request, f"Error updating class type: {str(e)}")

    return render(
        request, "scheduling/edit_class_type.html", {"class_type": class_type}
    )


@login_required
@user_passes_test(is_admin)
def delete_class_type(request, class_type_id):
    """View for deleting a class type"""
    class_type = get_object_or_404(ClassType, id=class_type_id)

    # Check if class type is in use
    if class_type.sessions.exists():
        messages.error(
            request,
            f"Cannot delete class type '{class_type.name}' because it is used by "
            f"{class_type.sessions.count()} sessions.",
        )
        return redirect("manage_class_types")

    try:
        class_type_name = class_type.name
        class_type.delete()
        messages.success(
            request, f"Class Type '{class_type_name}' deleted successfully."
        )
    except Exception as e:
        messages.error(request, f"Error deleting class type: {str(e)}")

    return redirect("manage_class_types")


@login_required
@user_passes_test(is_admin)
def view_sessions(request):
    """View for viewing and filtering class sessions"""
    # Get filter parameters
    teacher_id = request.GET.get("teacher")
    student_id = request.GET.get("student")
    class_type_id = request.GET.get("class_type")
    attended = request.GET.get("attended")
    date_range = request.GET.get("date_range", "all")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Base query with select_related to reduce database queries
    sessions = (
        ClassSession.objects.select_related("teacher", "class_type")
        .all()
        .order_by("-start_time")
    )

    # Apply filters
    if teacher_id:
        sessions = sessions.filter(teacher_id=teacher_id)

    if student_id:
        sessions = sessions.filter(students__id=student_id)

    if class_type_id:
        sessions = sessions.filter(class_type_id=class_type_id)

    if attended is not None and attended != "":
        sessions = sessions.filter(attended=(attended == "1"))

    # Apply date range filters
    today = timezone.now().date()
    if date_range == "today":
        sessions = sessions.filter(start_time__date=today)
    elif date_range == "week":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        sessions = sessions.filter(start_time__date__range=[start_of_week, end_of_week])
    elif date_range == "month":
        sessions = sessions.filter(
            start_time__year=today.year, start_time__month=today.month
        )
    elif date_range == "custom" and start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            sessions = sessions.filter(start_time__date__range=[start, end])
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")

    # Prepare data for template
    teachers = User.objects.filter(user_type="teacher").order_by("name")
    students = User.objects.filter(user_type="student").order_by("name")
    class_types = ClassType.objects.all().order_by("name")

    # Pagination - smaller page size for better performance
    paginator = Paginator(sessions, 8)  # Show 8 sessions per page for faster loading
    page_number = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, EmptyPage, PageNotAnInteger):
        if sessions.exists():
            page_obj = paginator.page(1)
        else:
            # Handle empty queryset case
            page_obj = Paginator([], 8).page(1)

    context = {
        "sessions": page_obj,
        "teachers": teachers,
        "students": students,
        "class_types": class_types,
        "selected_teacher": int(teacher_id) if teacher_id else None,
        "selected_student": int(student_id) if student_id else None,
        "selected_class_type": int(class_type_id) if class_type_id else None,
        "selected_attended": attended,
        "date_range": date_range,
        "start_date": start_date,
        "end_date": end_date,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
    }

    # If it's an HTMX request, return just the partial template
    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/sessions_table.html", context)

    # Otherwise return the full template
    return render(request, "scheduling/view_sessions.html", context)


@login_required
@user_passes_test(is_admin)
def edit_session(request, session_id):
    """View for editing a class session"""
    session = get_object_or_404(ClassSession, id=session_id)

    if request.method == "POST":
        # Get form data
        teacher_id = request.POST.get("teacher")
        student_ids = request.POST.getlist("students")
        class_type_id = request.POST.get("class_type")
        start_date = request.POST.get("start_date")
        start_time = request.POST.get("start_time")
        end_date = request.POST.get("end_date")
        end_time = request.POST.get("end_time")
        attended = request.POST.get("attended") == "on"

        try:
            # Update session
            session.teacher_id = teacher_id
            session.class_type_id = class_type_id

            # Parse datetime
            start_datetime = f"{start_date} {start_time}"
            end_datetime = f"{end_date} {end_time}"
            session.start_time = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
            session.end_time = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")

            session.attended = attended
            session.save()

            # Update students (clear and re-add)
            session.students.clear()
            for student_id in student_ids:
                session.students.add(student_id)

            # Update title based on students
            students_str = ", ".join(
                [student.name for student in session.students.all()]
            )
            title = students_str
            if not attended:
                title += " - FALTOU"
            session.title = title
            session.save()

            messages.success(request, "Class session updated successfully.")
            return redirect("view_sessions")
        except Exception as e:
            messages.error(request, f"Error updating session: {str(e)}")

    # Prepare data for template
    teachers = User.objects.filter(user_type="teacher").order_by("name")
    students = User.objects.filter(user_type="student").order_by("name")
    class_types = ClassType.objects.all().order_by("name")

    context = {
        "session": session,
        "teachers": teachers,
        "students": students,
        "class_types": class_types,
    }

    return render(request, "scheduling/edit_session.html", context)


@login_required
@user_passes_test(is_admin)
def calendar_sync(request):
    """View for syncing with Google Calendar"""
    if request.method == "POST":
        admin_email = request.POST.get("admin_email")
        days = request.POST.get("days")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        calendar_id = request.POST.get("calendar_id", settings.GOOGLE_CALENDAR_ID)

        # Validate inputs
        if not admin_email:
            messages.error(request, "Admin email is required.")
            return redirect("calendar_sync")

        try:
            # Import here to avoid circular imports
            from .google_calendar import sync_calendar_events

            if start_date and end_date:
                # Use date range
                created, updated, total = sync_calendar_events(
                    calendar_id=calendar_id,
                    admin_email=admin_email,
                    start_date=start_date,
                    end_date=end_date,
                )
                messages.success(
                    request,
                    f"Successfully synced {total} events ({created} created, {updated} updated) "
                    f"from {start_date} to {end_date}.",
                )
            else:
                # Use days
                days = int(days) if days else 30
                created, updated, total = sync_calendar_events(
                    calendar_id=calendar_id, days=days, admin_email=admin_email
                )
                messages.success(
                    request,
                    f"Successfully synced {total} events ({created} created, {updated} updated) "
                    f"for the next {days} days.",
                )

            return redirect("view_sessions")
        except Exception as e:
            messages.error(request, f"Error syncing calendar: {str(e)}")

    # Get admin users for the dropdown
    admin_users = User.objects.filter(is_admin=True).order_by("name")

    context = {
        "admin_users": admin_users,
        "default_calendar_id": getattr(settings, "GOOGLE_CALENDAR_ID", ""),
    }

    return render(request, "scheduling/calendar_sync.html", context)


@login_required
def filter_sessions(request):
    """API endpoint to filter sessions"""
    # Get filter parameters from request
    teacher_id = request.GET.get("teacher")
    student_id = request.GET.get("student")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Start with optimized query using select_related
    sessions = (
        ClassSession.objects.select_related("teacher", "class_type")
        .all()
        .order_by("-start_time")
    )

    # Apply filters
    if teacher_id:
        sessions = sessions.filter(teacher_id=teacher_id)
    if student_id:
        sessions = sessions.filter(students__id=student_id)
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            sessions = sessions.filter(start_time__date__gte=start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            sessions = sessions.filter(start_time__date__lte=end)
        except ValueError:
            pass

    # Pagination - smaller page size for better performance
    paginator = Paginator(sessions, 8)  # Show 8 sessions per page for faster loading
    page_number = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page_number)
    except (ValueError, EmptyPage, PageNotAnInteger):
        if sessions.exists():
            page_obj = paginator.page(1)
        else:
            # Handle empty queryset case
            page_obj = Paginator([], 8).page(1)

    return render(
        request,
        "partials/sessions_table.html",
        {
            "sessions": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
        },
    )


@login_required
def upcoming_classes(request):
    """HTMX endpoint to get upcoming classes for a student"""
    if request.user.user_type != "student":
        return HttpResponse("Unauthorized", status=403)

    # Get upcoming classes for the student
    upcoming = ClassSession.objects.filter(
        students=request.user, start_time__gt=timezone.now()
    ).order_by("start_time")[
        :5
    ]  # Limit to 5 upcoming classes

    return render(
        request, "partials/upcoming_classes.html", {"upcoming_classes": upcoming}
    )


@login_required
def today_schedule(request):
    """HTMX endpoint to get today's schedule for a teacher"""
    if request.user.user_type != "teacher":
        return HttpResponse("Unauthorized", status=403)

    # Get today's classes for the teacher
    today = timezone.now().date()
    schedule = ClassSession.objects.filter(
        teacher=request.user, start_time__date=today
    ).order_by("start_time")

    return render(request, "partials/teacher_schedule.html", {"schedule": schedule})
