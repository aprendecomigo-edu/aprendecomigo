from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, Http404
from django.urls import reverse
from functools import wraps

from datetime import datetime
from dateutil.relativedelta import relativedelta

from accounts.models import CustomUser
from .models import PaymentPlan, StudentPayment, TeacherCompensation
from .services import StudentPaymentService, TeacherCompensationService, FinancialUtilities


def is_staff_or_admin(user):
    """Check if user is staff or admin"""
    return user.is_staff or user.is_superuser or user.is_admin


def admin_required(view_func):
    """Custom decorator for admin-only views that shows 404 for non-admin logged-in users"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if is_staff_or_admin(request.user):
            return view_func(request, *args, **kwargs)
        # Return 404 for non-admin authenticated users
        raise Http404(_("Page not found"))
    return _wrapped_view


# Admin Dashboard
@admin_required
def admin_dashboard(request):
    """Financial admin dashboard"""
    # Get summary data for display
    today = timezone.now().date()
    start_date = today.replace(day=1)
    next_month = today.replace(day=1) + relativedelta(months=1)
    end_date = next_month - relativedelta(days=1)
    
    # Get recent payments
    recent_payments = StudentPayment.objects.all().order_by('-payment_date')[:5]
    
    # Get recent compensations
    recent_compensations = TeacherCompensation.objects.all().order_by('-period_end')[:5]
    
    return render(request, 'financials/admin_dashboard.html', {
        'recent_payments': recent_payments,
        'recent_compensations': recent_compensations,
    })


# Payment Plan Views
@admin_required
def payment_plan_list(request):
    """List all payment plans"""
    payment_plans = PaymentPlan.objects.all()
    return render(request, 'financials/payment_plan_list.html', {
        'payment_plans': payment_plans,
    })


@admin_required
def payment_plan_detail(request, pk):
    """Show details of a payment plan"""
    payment_plan = get_object_or_404(PaymentPlan, pk=pk)
    student_payments = payment_plan.student_payments.all()
    
    # Validate payment plan configuration
    validation_errors = FinancialUtilities.validate_payment_plan(payment_plan)
    
    return render(request, 'financials/payment_plan_detail.html', {
        'payment_plan': payment_plan,
        'student_payments': student_payments,
        'validation_errors': validation_errors,
    })


# Student Payment Views
@login_required
def student_payment_list(request):
    """List student payments based on user role"""
    if is_staff_or_admin(request.user):
        # Admin can see all payments
        payments = StudentPayment.objects.all().order_by('-payment_date')
    elif request.user.user_type == 'student':
        # Students can only see their own payments
        payments = StudentPayment.objects.filter(student=request.user).order_by('-payment_date')
    else:
        # Other users can't see payments - show a 404 instead of 403
        raise Http404(_("Page not found"))
    
    return render(request, 'financials/student_payment_list.html', {
        'payments': payments,
    })


@login_required
def student_payment_detail(request, pk):
    """Show details of a student payment"""
    payment = get_object_or_404(StudentPayment, pk=pk)
    
    # Check permissions
    if not (is_staff_or_admin(request.user) or payment.student == request.user):
        # Show 404 instead of 403
        raise Http404(_("Page not found"))
    
    return render(request, 'financials/student_payment_detail.html', {
        'payment': payment,
        'is_expired': payment.is_expired,
        'remaining_hours': payment.remaining_hours,
    })


@login_required
def student_payments(request, student_id):
    """Show all payments for a specific student"""
    student = get_object_or_404(CustomUser, pk=student_id, user_type='student')
    
    # Check permissions
    if not (is_staff_or_admin(request.user) or student == request.user):
        # Show 404 instead of 403
        raise Http404(_("Page not found"))
    
    payments = StudentPayment.objects.filter(student=student).order_by('-payment_date')
    
    # Get active payment plans
    active_plans = StudentPaymentService.get_active_payment_plans(student)
    
    return render(request, 'financials/student_payments.html', {
        'student': student,
        'payments': payments,
        'active_plans': active_plans,
    })


# Teacher Compensation Views
@login_required
def teacher_compensation_list(request):
    """List teacher compensations based on user role"""
    if is_staff_or_admin(request.user):
        # Admin can see all compensations
        compensations = TeacherCompensation.objects.all().order_by('-period_end')
    elif request.user.user_type == 'teacher':
        # Teachers can only see their own compensations
        compensations = TeacherCompensation.objects.filter(teacher=request.user).order_by('-period_end')
    else:
        # Other users can't see compensations - show a 404 instead of 403
        raise Http404(_("Page not found"))
    
    return render(request, 'financials/teacher_compensation_list.html', {
        'compensations': compensations,
    })


@login_required
def teacher_compensation_detail(request, pk):
    """Show details of a teacher compensation"""
    compensation = get_object_or_404(TeacherCompensation, pk=pk)
    
    # Check permissions
    if not (is_staff_or_admin(request.user) or compensation.teacher == request.user):
        # Show 404 instead of 403
        raise Http404(_("Page not found"))
    
    return render(request, 'financials/teacher_compensation_detail.html', {
        'compensation': compensation,
        'is_fully_paid': compensation.is_fully_paid,
        'balance_due': compensation.amount_owed - compensation.amount_paid,
    })


@login_required
def teacher_compensations(request, teacher_id):
    """Show all compensations for a specific teacher"""
    teacher = get_object_or_404(CustomUser, pk=teacher_id, user_type='teacher')
    
    # Check permissions
    if not (is_staff_or_admin(request.user) or teacher == request.user):
        # Show 404 instead of 403
        raise Http404(_("Page not found"))
    
    compensations = TeacherCompensation.objects.filter(teacher=teacher).order_by('-period_end')
    
    # Get statistics for the teacher
    total_owed = sum(comp.amount_owed for comp in compensations)
    total_paid = sum(comp.amount_paid for comp in compensations)
    balance_due = total_owed - total_paid
    
    return render(request, 'financials/teacher_compensations.html', {
        'teacher': teacher,
        'compensations': compensations,
        'total_owed': total_owed,
        'total_paid': total_paid,
        'balance_due': balance_due,
    })


# Report Views
@admin_required
def payment_report(request):
    """Generate a student payment report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    student_id = request.GET.get('student_id')
    
    # Set default date range to current month if not provided
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        next_month = today.replace(day=1) + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    student = None
    if student_id:
        student = get_object_or_404(CustomUser, pk=student_id, user_type='student')
    
    report = StudentPaymentService.generate_payment_report(student, start_date, end_date)
    
    # Get list of students for the filter
    students = CustomUser.objects.filter(user_type='student')
    
    return render(request, 'financials/payment_report.html', {
        'report': report,
        'students': students,
        'selected_student': student,
        'start_date': start_date,
        'end_date': end_date,
    })


@admin_required
def compensation_report(request):
    """Generate a teacher compensation report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    teacher_id = request.GET.get('teacher_id')
    
    # Set default date range to current month if not provided
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        next_month = today.replace(day=1) + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    teacher = None
    if teacher_id:
        teacher = get_object_or_404(CustomUser, pk=teacher_id, user_type='teacher')
    
    report = TeacherCompensationService.generate_compensation_report(teacher, start_date, end_date)
    
    # Get list of teachers for the filter
    teachers = CustomUser.objects.filter(user_type='teacher')
    
    return render(request, 'financials/compensation_report.html', {
        'report': report,
        'teachers': teachers,
        'selected_teacher': teacher,
        'start_date': start_date,
        'end_date': end_date,
    })


@admin_required
def financial_summary(request):
    """Generate a financial summary report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Set default date range to current month if not provided
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        next_month = today.replace(day=1) + relativedelta(months=1)
        end_date = next_month - relativedelta(days=1)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    summary = FinancialUtilities.generate_financial_summary(start_date, end_date)
    
    return render(request, 'financials/financial_summary.html', {
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    })
