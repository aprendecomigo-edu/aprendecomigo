from django.urls import path
from . import views

app_name = 'financials'

urlpatterns = [
    # Admin Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Payment plans
    path('payment-plans/', views.payment_plan_list, name='payment_plan_list'),
    path('payment-plans/<int:pk>/', views.payment_plan_detail, name='payment_plan_detail'),
    
    # Student payments
    path('student-payments/', views.student_payment_list, name='student_payment_list'),
    path('student-payments/<int:pk>/', views.student_payment_detail, name='student_payment_detail'),
    path('student/<int:student_id>/payments/', views.student_payments, name='student_payments'),
    
    # Teacher compensations
    path('teacher-compensations/', views.teacher_compensation_list, name='teacher_compensation_list'),
    path('teacher-compensations/<int:pk>/', views.teacher_compensation_detail, name='teacher_compensation_detail'),
    path('teacher/<int:teacher_id>/compensations/', views.teacher_compensations, name='teacher_compensations'),
    
    # Reports
    path('reports/payments/', views.payment_report, name='payment_report'),
    path('reports/compensations/', views.compensation_report, name='compensation_report'),
    path('reports/financial-summary/', views.financial_summary, name='financial_summary'),
] 