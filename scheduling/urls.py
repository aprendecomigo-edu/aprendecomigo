from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('google-calendar-status/', views.google_calendar_status, name='google_calendar_status'),
    path('connect-google/', views.connect_google_calendar, name='connect_google_calendar'),
] 