from django.urls import path
from . import views

# NOTE: This file only contains custom password reset URLs.
# Standard authentication URLs (login, logout, etc.) are included from
# django.contrib.auth.urls in the project's main urls.py file.
# See: path('', include('django.contrib.auth.urls'))

urlpatterns = [
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
] 