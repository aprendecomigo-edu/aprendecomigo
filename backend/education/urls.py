from django.urls import path

from . import views

app_name = "education"

urlpatterns = [
    # Teacher Dashboard and Management
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/courses/", views.teacher_courses, name="teacher_courses"),
    path("teacher/courses/create/", views.create_course, name="create_course"),
    path("teacher/courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("teacher/courses/<int:course_id>/schedule/", views.lesson_schedule, name="lesson_schedule"),
    path("teacher/courses/<int:course_id>/assignments/", views.assignment_management, name="assignment_management"),
    path("teacher/courses/<int:course_id>/analytics/", views.course_analytics, name="course_analytics"),
    # Student Portal and Enrollment
    path("student/portal/", views.student_portal, name="student_portal"),
    path("student/enroll/<int:course_id>/", views.enroll_in_course, name="enroll_in_course"),
    # Payment Views
    path(
        "payments/create-enrollment/<int:course_id>/", views.create_enrollment_payment, name="create_enrollment_payment"
    ),
    path("payments/confirm-enrollment/", views.confirm_enrollment_payment, name="confirm_enrollment_payment"),
    path("payments/history/", views.payment_history, name="payment_history"),
    path("payments/success/", views.payment_success, name="payment_success"),
    path("payments/cancel/", views.payment_cancel, name="payment_cancel"),
    # Reporting Views
    path("reports/", views.education_reports, name="education_reports"),
    path("reports/student/<int:student_id>/", views.student_progress_report, name="student_progress_report"),
    path("reports/course/<int:course_id>/", views.course_performance_report, name="course_performance_report"),
]
