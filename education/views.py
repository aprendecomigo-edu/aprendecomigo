from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.models import StudentProfile, TeacherProfile

from .models import Assignment, AssignmentSubmission, Course, Enrollment, Lesson, Payment, Subject
from .services import EducationPaymentService


@login_required
def teacher_dashboard(request):
    """Main teacher dashboard with metrics and analytics."""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, "You must be a teacher to access this dashboard.")
        return redirect("accounts:profile")

    # Get teacher's courses and metrics
    courses = Course.objects.filter(teacher=teacher).select_related("subject")
    active_courses = courses.filter(status="active")

    # Calculate metrics
    total_students = Enrollment.objects.filter(course__teacher=teacher, is_active=True).count()

    total_revenue = Payment.objects.filter(teacher=teacher, status="completed").aggregate(Sum("teacher_amount"))[
        "teacher_amount__sum"
    ] or Decimal("0.00")

    pending_assignments = AssignmentSubmission.objects.filter(
        assignment__course__teacher=teacher, graded_at__isnull=True, is_draft=False
    ).count()

    upcoming_lessons = Lesson.objects.filter(
        course__teacher=teacher, status="scheduled", scheduled_date__gte=timezone.now()
    ).order_by("scheduled_date")[:5]

    recent_enrollments = (
        Enrollment.objects.filter(course__teacher=teacher)
        .select_related("student__user", "course")
        .order_by("-enrollment_date")[:5]
    )

    context = {
        "teacher": teacher,
        "total_courses": courses.count(),
        "active_courses": active_courses.count(),
        "total_students": total_students,
        "total_revenue": total_revenue,
        "pending_assignments": pending_assignments,
        "upcoming_lessons": upcoming_lessons,
        "recent_enrollments": recent_enrollments,
        "courses": active_courses[:3],  # Show first 3 active courses
    }

    return render(request, "education/teacher/dashboard.html", context)


@login_required
def teacher_courses(request):
    """Teacher's course management interface."""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    # Filter and search courses
    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("search", "")

    courses = Course.objects.filter(teacher=teacher).select_related("subject")

    if status_filter:
        courses = courses.filter(status=status_filter)

    if search_query:
        courses = courses.filter(Q(title__icontains=search_query) | Q(subject__name__icontains=search_query))

    courses = courses.order_by("-created_at")

    # Pagination
    paginator = Paginator(courses, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "teacher": teacher,
        "page_obj": page_obj,
        "status_filter": status_filter,
        "search_query": search_query,
        "status_choices": Course.STATUS_CHOICES,
    }

    return render(request, "education/teacher/courses.html", context)


@login_required
def course_detail(request, course_id):
    """Detailed course view with enrollments and lessons."""
    course = get_object_or_404(Course, id=course_id)

    # Check if user is the teacher of this course
    try:
        teacher = request.user.teacher_profile
        if course.teacher != teacher:
            return HttpResponseForbidden("You can only view your own courses")
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    # Get course data
    enrollments = (
        Enrollment.objects.filter(course=course, is_active=True)
        .select_related("student__user")
        .order_by("-enrollment_date")
    )

    lessons = Lesson.objects.filter(course=course).order_by("scheduled_date")

    assignments = Assignment.objects.filter(course=course, is_active=True).order_by("due_date")

    # Calculate course metrics
    avg_progress = enrollments.aggregate(Avg("progress_percentage"))["progress_percentage__avg"] or 0

    completed_lessons = lessons.filter(status="completed").count()
    total_lessons = lessons.count()

    total_revenue = Payment.objects.filter(teacher=teacher, enrollment__course=course, status="completed").aggregate(
        Sum("teacher_amount")
    )["teacher_amount__sum"] or Decimal("0.00")

    context = {
        "course": course,
        "enrollments": enrollments,
        "lessons": lessons[:10],  # Show recent 10 lessons
        "assignments": assignments,
        "avg_progress": round(avg_progress, 1),
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "total_revenue": total_revenue,
        "enrolled_count": enrollments.count(),
    }

    return render(request, "education/teacher/course_detail.html", context)


@login_required
def create_course(request):
    """Course creation form."""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    if request.method == "POST":
        # Basic form processing - in a real app you'd use Django forms
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        subject_id = request.POST.get("subject")
        course_type = request.POST.get("course_type", "individual")
        price_per_hour = request.POST.get("price_per_hour")
        total_hours = request.POST.get("total_hours", 10)
        max_students = request.POST.get("max_students", 1)
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # Basic validation
        errors = []
        if not title:
            errors.append("Title is required")
        if not description:
            errors.append("Description is required")
        if not subject_id:
            errors.append("Subject is required")
        if not price_per_hour:
            errors.append("Price per hour is required")
        if not start_date:
            errors.append("Start date is required")
        if not end_date:
            errors.append("End date is required")

        if not errors:
            try:
                subject = get_object_or_404(Subject, id=subject_id)

                course = Course.objects.create(
                    title=title,
                    description=description,
                    subject=subject,
                    teacher=teacher,
                    course_type=course_type,
                    price_per_hour=Decimal(price_per_hour),
                    total_hours=int(total_hours),
                    max_students=int(max_students),
                    start_date=start_date,
                    end_date=end_date,
                    status="draft",
                )

                messages.success(request, f"Course '{course.title}' created successfully!")
                return redirect("education:course_detail", course_id=course.id)

            except Exception as e:
                errors.append(f"Error creating course: {e!s}")

        # If there are errors, show them
        for error in errors:
            messages.error(request, error)

    # Get subjects for the form
    subjects = Subject.objects.filter(is_active=True).order_by("name")

    context = {
        "teacher": teacher,
        "subjects": subjects,
        "course_types": Course.COURSE_TYPE_CHOICES,
    }

    return render(request, "education/teacher/create_course.html", context)


@login_required
def student_portal(request):
    """Student course browsing and enrollment interface."""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student access required")
        return redirect("accounts:profile")

    # Filter courses
    subject_filter = request.GET.get("subject", "")
    course_type_filter = request.GET.get("course_type", "")
    search_query = request.GET.get("search", "")

    # Get available courses (published and not full)
    courses = Course.objects.filter(status="published").select_related("teacher__user", "subject")

    if subject_filter:
        courses = courses.filter(subject_id=subject_filter)

    if course_type_filter:
        courses = courses.filter(course_type=course_type_filter)

    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(teacher__user__first_name__icontains=search_query)
            | Q(teacher__user__last_name__icontains=search_query)
        )

    # Exclude courses student is already enrolled in
    enrolled_course_ids = Enrollment.objects.filter(student=student, is_active=True).values_list("course_id", flat=True)

    courses = courses.exclude(id__in=enrolled_course_ids)

    # Add enrollment status and availability
    for course in courses:
        course.is_full = course.is_full
        course.can_enroll = not course.is_full

    courses = courses.order_by("-created_at")

    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get student's current enrollments
    my_enrollments = Enrollment.objects.filter(student=student, is_active=True).select_related(
        "course", "course__teacher__user"
    )[:3]

    # Get filter options
    subjects = Subject.objects.filter(is_active=True).order_by("name")

    context = {
        "student": student,
        "page_obj": page_obj,
        "my_enrollments": my_enrollments,
        "subjects": subjects,
        "course_types": Course.COURSE_TYPE_CHOICES,
        "subject_filter": subject_filter,
        "course_type_filter": course_type_filter,
        "search_query": search_query,
    }

    return render(request, "education/student/portal.html", context)


@login_required
@require_http_methods(["POST"])
def enroll_in_course(request, course_id):
    """Handle student enrollment in a course."""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({"error": "Student access required"}, status=403)

    course = get_object_or_404(Course, id=course_id, status="published")

    # Check if already enrolled
    if Enrollment.objects.filter(student=student, course=course, is_active=True).exists():
        return JsonResponse({"error": "Already enrolled in this course"}, status=400)

    # Check if course is full
    if course.is_full:
        return JsonResponse({"error": "Course is full"}, status=400)

    try:
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            start_date=course.start_date,
            status="pending",  # Pending payment
        )

        messages.success(request, f"Successfully enrolled in '{course.title}'!")

        return JsonResponse({"success": True, "message": "Enrollment successful", "enrollment_id": enrollment.id})

    except Exception as e:
        return JsonResponse({"error": f"Enrollment failed: {e!s}"}, status=500)


@login_required
def lesson_schedule(request, course_id):
    """Lesson scheduling interface for teachers."""
    course = get_object_or_404(Course, id=course_id)

    # Check if user is the teacher
    try:
        teacher = request.user.teacher_profile
        if course.teacher != teacher:
            return HttpResponseForbidden("You can only manage your own courses")
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_lesson":
            title = request.POST.get("title", "").strip()
            scheduled_date = request.POST.get("scheduled_date")
            duration = request.POST.get("duration", 60)
            description = request.POST.get("description", "")

            if title and scheduled_date:
                try:
                    lesson = Lesson.objects.create(
                        course=course,
                        title=title,
                        description=description,
                        scheduled_date=scheduled_date,
                        duration_minutes=int(duration),
                        status="scheduled",
                    )
                    messages.success(request, f"Lesson '{lesson.title}' scheduled successfully!")
                except Exception as e:
                    messages.error(request, f"Error scheduling lesson: {e!s}")
            else:
                messages.error(request, "Title and scheduled date are required")

    # Get lessons for this course
    lessons = Lesson.objects.filter(course=course).order_by("scheduled_date")

    # Get enrolled students for attendance tracking
    enrolled_students = Enrollment.objects.filter(course=course, is_active=True).select_related("student__user")

    context = {
        "course": course,
        "lessons": lessons,
        "enrolled_students": enrolled_students,
    }

    return render(request, "education/teacher/lesson_schedule.html", context)


@login_required
def assignment_management(request, course_id):
    """Assignment management for teachers."""
    course = get_object_or_404(Course, id=course_id)

    # Check if user is the teacher
    try:
        teacher = request.user.teacher_profile
        if course.teacher != teacher:
            return HttpResponseForbidden("You can only manage your own courses")
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_assignment":
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "").strip()
            assignment_type = request.POST.get("assignment_type", "homework")
            due_date = request.POST.get("due_date")
            max_points = request.POST.get("max_points", 100)

            if title and description and due_date:
                try:
                    assignment = Assignment.objects.create(
                        course=course,
                        title=title,
                        description=description,
                        assignment_type=assignment_type,
                        due_date=due_date,
                        max_points=int(max_points),
                    )
                    messages.success(request, f"Assignment '{assignment.title}' created successfully!")
                except Exception as e:
                    messages.error(request, f"Error creating assignment: {e!s}")
            else:
                messages.error(request, "Title, description, and due date are required")

    # Get assignments for this course
    assignments = Assignment.objects.filter(course=course, is_active=True).order_by("-created_at")

    # Add submission counts
    for assignment in assignments:
        assignment.submission_count = assignment.submissions.count()
        assignment.pending_grading = assignment.submissions.filter(graded_at__isnull=True, is_draft=False).count()

    context = {
        "course": course,
        "assignments": assignments,
        "assignment_types": Assignment.TYPE_CHOICES,
    }

    return render(request, "education/teacher/assignment_management.html", context)


@login_required
def course_analytics(request, course_id):
    """Course analytics and reporting for teachers."""
    course = get_object_or_404(Course, id=course_id)

    # Check if user is the teacher
    try:
        teacher = request.user.teacher_profile
        if course.teacher != teacher:
            return HttpResponseForbidden("You can only view analytics for your own courses")
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    # Get analytics data
    enrollments = Enrollment.objects.filter(course=course, is_active=True).select_related("student__user")

    # Progress analytics
    progress_stats = {
        "avg_progress": enrollments.aggregate(Avg("progress_percentage"))["progress_percentage__avg"] or 0,
        "completion_rate": enrollments.filter(status="completed").count(),
        "active_students": enrollments.filter(status="active").count(),
        "dropped_students": enrollments.filter(status="dropped").count(),
    }

    # Assignment analytics
    assignments = Assignment.objects.filter(course=course, is_active=True)
    assignment_stats = []

    for assignment in assignments:
        submissions = assignment.submissions.filter(is_draft=False)
        graded_submissions = submissions.filter(graded_at__isnull=False)

        assignment_stats.append(
            {
                "assignment": assignment,
                "total_submissions": submissions.count(),
                "graded_submissions": graded_submissions.count(),
                "avg_grade": graded_submissions.aggregate(Avg("grade_percentage"))["grade_percentage__avg"] or 0,
                "late_submissions": submissions.filter(is_late=True).count(),
            }
        )

    # Revenue analytics
    payments = Payment.objects.filter(enrollment__course=course, status="completed")

    revenue_stats = {
        "total_revenue": payments.aggregate(Sum("teacher_amount"))["teacher_amount__sum"] or Decimal("0.00"),
        "platform_fees": payments.aggregate(Sum("platform_fee"))["platform_fee__sum"] or Decimal("0.00"),
        "payment_count": payments.count(),
    }

    context = {
        "course": course,
        "enrollments": enrollments,
        "progress_stats": progress_stats,
        "assignment_stats": assignment_stats,
        "revenue_stats": revenue_stats,
    }

    return render(request, "education/teacher/course_analytics.html", context)


# Payment Views


@login_required
@require_http_methods(["POST"])
def create_enrollment_payment(request, course_id):
    """Create payment intent for course enrollment."""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({"error": "Student access required"}, status=403)

    payment_service = EducationPaymentService()
    result = payment_service.create_enrollment_payment(student_user=request.user, course_id=course_id)

    if result["success"]:
        return JsonResponse(
            {
                "success": True,
                "client_secret": result["client_secret"],
                "payment_intent_id": result["payment_intent_id"],
            }
        )
    else:
        return JsonResponse({"success": False, "error": result.get("error", "Payment creation failed")}, status=400)


@login_required
@require_http_methods(["POST"])
def confirm_enrollment_payment(request):
    """Confirm successful enrollment payment."""
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return JsonResponse({"error": "Student access required"}, status=403)

    data = json.loads(request.body)
    payment_intent_id = data.get("payment_intent_id")
    course_id = data.get("course_id")

    if not payment_intent_id or not course_id:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    payment_service = EducationPaymentService()
    result = payment_service.process_successful_enrollment_payment(
        payment_intent_id=payment_intent_id, student_user=request.user, course_id=int(course_id)
    )

    if result["success"]:
        messages.success(request, f"Successfully enrolled in {result['course_title']}!")
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=400)


@login_required
def payment_history(request):
    """Display payment history for students or earnings for teachers."""
    if hasattr(request.user, "studentprofile"):
        # Student payment history
        payment_service = EducationPaymentService()
        result = payment_service.get_student_payment_history(request.user)

        context = {
            "user_type": "student",
            "student": request.user.student_profile,
            "payments": result.get("payments", []) if result["success"] else [],
            "total_spent": result.get("total_spent", "0.00") if result["success"] else "0.00",
            "payment_count": result.get("payment_count", 0) if result["success"] else 0,
        }

        return render(request, "education/payment_history.html", context)

    elif hasattr(request.user, "teacherprofile"):
        # Teacher earnings
        payment_service = EducationPaymentService()
        result = payment_service.get_teacher_earnings(request.user)

        # Get recent payments
        recent_payments = (
            Payment.objects.filter(teacher=request.user.teacher_profile, status="completed")
            .select_related("student__user", "enrollment__course")
            .order_by("-created_at")[:10]
        )

        context = {
            "user_type": "teacher",
            "teacher": request.user.teacher_profile,
            "total_earnings": result.get("total_earnings", "0.00") if result["success"] else "0.00",
            "total_platform_fees": result.get("total_platform_fees", "0.00") if result["success"] else "0.00",
            "payment_count": result.get("payment_count", 0) if result["success"] else 0,
            "earnings_by_type": result.get("earnings_by_type", {}) if result["success"] else {},
            "recent_payments": recent_payments,
        }

        return render(request, "education/payment_history.html", context)

    else:
        messages.error(request, "No profile found. Please complete your profile setup.")
        return redirect("accounts:profile")


@login_required
def payment_success(request):
    """Payment success page."""
    payment_intent_id = request.GET.get("payment_intent")
    course_id = request.GET.get("course_id")

    context = {
        "payment_intent_id": payment_intent_id,
        "course_id": course_id,
    }

    # Get course details if available
    if course_id:
        try:
            course = Course.objects.get(id=course_id)
            context["course"] = course
        except Course.DoesNotExist:
            pass

    return render(request, "education/payment_success.html", context)


@login_required
def payment_cancel(request):
    """Payment cancelled page."""
    course_id = request.GET.get("course_id")

    context = {
        "course_id": course_id,
    }

    # Get course details if available
    if course_id:
        try:
            course = Course.objects.get(id=course_id)
            context["course"] = course
        except Course.DoesNotExist:
            pass

    return render(request, "education/payment_cancel.html", context)


# Reporting Views


@login_required
def education_reports(request):
    """Comprehensive education reporting dashboard."""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, "Teacher access required for reports.")
        return redirect("accounts:profile")

    # Get date range from request (default to last 30 days)
    from datetime import datetime, timedelta

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if request.GET.get("start_date"):
        start_date = datetime.strptime(request.GET.get("start_date"), "%Y-%m-%d").date()
    if request.GET.get("end_date"):
        end_date = datetime.strptime(request.GET.get("end_date"), "%Y-%m-%d").date()

    # Course Performance Report
    courses = (
        Course.objects.filter(teacher=teacher)
        .annotate(
            enrollment_count=Count("enrollments", filter=Q(enrollments__is_active=True)),
            completion_rate=Avg("enrollments__progress_percentage"),
            revenue=Sum("enrollments__payments__teacher_amount", filter=Q(enrollments__payments__status="completed")),
            lesson_count=Count("lessons"),
            completed_lessons=Count("lessons", filter=Q(lessons__status="completed")),
        )
        .order_by("-created_at")
    )

    # Student Progress Report
    student_progress = (
        Enrollment.objects.filter(course__teacher=teacher, is_active=True)
        .select_related("student__user", "course")
        .annotate(
            completed_assignments=Count(
                "student__submissions",
                filter=Q(
                    student__submissions__assignment__course__teacher=teacher,
                    student__submissions__graded_at__isnull=False,
                ),
            ),
            avg_grade=Avg(
                "student__submissions__grade_percentage",
                filter=Q(
                    student__submissions__assignment__course__teacher=teacher,
                    student__submissions__graded_at__isnull=False,
                ),
            ),
        )
        .order_by("-progress_percentage")
    )

    # Financial Summary
    financial_data = Payment.objects.filter(
        teacher=teacher, status="completed", created_at__date__range=[start_date, end_date]
    ).aggregate(
        total_revenue=Sum("teacher_amount"),
        platform_fees=Sum("platform_fee"),
        payment_count=Count("id"),
        avg_payment=Avg("teacher_amount"),
    )

    # Revenue by payment type
    revenue_by_type = (
        Payment.objects.filter(teacher=teacher, status="completed", created_at__date__range=[start_date, end_date])
        .values("payment_type")
        .annotate(total=Sum("teacher_amount"), count=Count("id"))
        .order_by("-total")
    )

    # Monthly trend (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_start = (end_date.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        month_data = Payment.objects.filter(
            teacher=teacher, status="completed", created_at__date__range=[month_start, next_month]
        ).aggregate(revenue=Sum("teacher_amount"), payments=Count("id"))

        monthly_revenue.append(
            {
                "month": month_start.strftime("%b %Y"),
                "revenue": month_data["revenue"] or Decimal("0.00"),
                "payments": month_data["payments"] or 0,
            }
        )

    monthly_revenue.reverse()

    # Assignment and grading statistics
    assignment_stats = Assignment.objects.filter(
        course__teacher=teacher, is_active=True, assigned_date__date__range=[start_date, end_date]
    ).aggregate(
        total_assignments=Count("id"),
        total_submissions=Count("submissions"),
        pending_grading=Count(
            "submissions", filter=Q(submissions__graded_at__isnull=True, submissions__is_draft=False)
        ),
        avg_submission_time=Avg("submissions__submitted_at"),
    )

    # Top performing students
    top_students = student_progress.filter(progress_percentage__gt=0).order_by("-progress_percentage")[:5]

    # Recent activity
    recent_enrollments = (
        Enrollment.objects.filter(course__teacher=teacher, enrollment_date__date__range=[start_date, end_date])
        .select_related("student__user", "course")
        .order_by("-enrollment_date")[:10]
    )

    recent_lessons = (
        Lesson.objects.filter(course__teacher=teacher, scheduled_date__date__range=[start_date, end_date])
        .select_related("course")
        .order_by("-scheduled_date")[:10]
    )

    context = {
        "teacher": teacher,
        "start_date": start_date,
        "end_date": end_date,
        "courses": courses,
        "student_progress": student_progress[:10],  # Top 10 students
        "financial_data": financial_data,
        "revenue_by_type": revenue_by_type,
        "monthly_revenue": monthly_revenue,
        "assignment_stats": assignment_stats,
        "top_students": top_students,
        "recent_enrollments": recent_enrollments,
        "recent_lessons": recent_lessons,
        # Summary metrics
        "total_courses": courses.count(),
        "total_students": student_progress.count(),
        "avg_completion_rate": courses.aggregate(avg=Avg("completion_rate"))["avg"] or 0,
        "total_revenue": financial_data["total_revenue"] or Decimal("0.00"),
    }

    return render(request, "education/reports/dashboard.html", context)


@login_required
def student_progress_report(request, student_id):
    """Detailed progress report for a specific student."""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    # Get student and verify teacher has access
    try:
        student_profile = StudentProfile.objects.get(id=student_id)
        # Verify teacher has courses with this student
        enrollment = Enrollment.objects.filter(student=student_profile, course__teacher=teacher, is_active=True).first()

        if not enrollment:
            return HttpResponseForbidden("You don't have access to this student's data")

    except StudentProfile.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect("education:education_reports")

    # Get all enrollments for this student in teacher's courses
    enrollments = (
        Enrollment.objects.filter(student=student_profile, course__teacher=teacher)
        .select_related("course", "course__subject")
        .order_by("-enrollment_date")
    )

    # Get assignment submissions
    submissions = (
        AssignmentSubmission.objects.filter(student=student_profile, assignment__course__teacher=teacher)
        .select_related("assignment", "assignment__course")
        .order_by("-submitted_at")
    )

    # Calculate performance metrics
    graded_submissions = submissions.filter(graded_at__isnull=False)
    avg_grade = graded_submissions.aggregate(avg=Avg("grade_percentage"))["avg"] or 0

    # Attendance data
    attended_lessons = Lesson.objects.filter(course__teacher=teacher, students_present=student_profile).count()

    total_lessons = Lesson.objects.filter(
        course__teacher=teacher, course__enrollments__student=student_profile, status="completed"
    ).count()

    attendance_rate = (attended_lessons / total_lessons * 100) if total_lessons > 0 else 0

    # Payment history
    payments = Payment.objects.filter(student=student_profile, teacher=teacher, status="completed").order_by(
        "-created_at"
    )

    context = {
        "teacher": teacher,
        "student": student_profile,
        "enrollments": enrollments,
        "submissions": submissions[:20],  # Latest 20 submissions
        "payments": payments[:10],  # Latest 10 payments
        "avg_grade": round(avg_grade, 1),
        "attendance_rate": round(attendance_rate, 1),
        "total_submissions": submissions.count(),
        "graded_submissions": graded_submissions.count(),
        "pending_submissions": submissions.filter(graded_at__isnull=True, is_draft=False).count(),
        "total_paid": payments.aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00"),
    }

    return render(request, "education/reports/student_detail.html", context)


@login_required
def course_performance_report(request, course_id):
    """Detailed performance report for a specific course."""
    course = get_object_or_404(Course, id=course_id)

    try:
        teacher = request.user.teacher_profile
        if course.teacher != teacher:
            return HttpResponseForbidden("You can only view reports for your own courses")
    except TeacherProfile.DoesNotExist:
        return HttpResponseForbidden("Teacher access required")

    # Enrollment analytics
    enrollments = Enrollment.objects.filter(course=course, is_active=True).select_related("student__user")

    enrollment_by_status = enrollments.values("status").annotate(count=Count("id")).order_by("status")

    # Assignment performance
    assignments = (
        Assignment.objects.filter(course=course, is_active=True)
        .annotate(
            submission_count=Count("submissions", filter=Q(submissions__is_draft=False)),
            avg_grade=Avg("submissions__grade_percentage", filter=Q(submissions__graded_at__isnull=False)),
            completion_rate=Count("submissions", filter=Q(submissions__is_draft=False)) * 100.0 / enrollments.count(),
        )
        .order_by("due_date")
    )

    # Lesson analytics
    lessons = Lesson.objects.filter(course=course).order_by("scheduled_date")
    lesson_attendance = []

    for lesson in lessons:
        attendance_count = lesson.students_present.count()
        lesson_attendance.append(
            {
                "lesson": lesson,
                "attendance_count": attendance_count,
                "attendance_rate": (attendance_count / enrollments.count() * 100) if enrollments.count() > 0 else 0,
            }
        )

    # Financial performance
    payments = Payment.objects.filter(enrollment__course=course, status="completed")

    financial_summary = payments.aggregate(
        total_revenue=Sum("teacher_amount"), platform_fees=Sum("platform_fee"), payment_count=Count("id")
    )

    # Progress distribution
    progress_distribution = {
        "0-25%": enrollments.filter(progress_percentage__lt=25).count(),
        "25-50%": enrollments.filter(progress_percentage__gte=25, progress_percentage__lt=50).count(),
        "50-75%": enrollments.filter(progress_percentage__gte=50, progress_percentage__lt=75).count(),
        "75-100%": enrollments.filter(progress_percentage__gte=75).count(),
    }

    context = {
        "course": course,
        "enrollments": enrollments,
        "enrollment_by_status": enrollment_by_status,
        "assignments": assignments,
        "lesson_attendance": lesson_attendance,
        "financial_summary": financial_summary,
        "progress_distribution": progress_distribution,
        "avg_progress": enrollments.aggregate(Avg("progress_percentage"))["progress_percentage__avg"] or 0,
        "completion_rate": enrollments.filter(status="completed").count(),
        "dropout_rate": enrollments.filter(status="dropped").count(),
    }

    return render(request, "education/reports/course_detail.html", context)
