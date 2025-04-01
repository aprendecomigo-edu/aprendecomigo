from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs are handled by django-allauth
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('school-profile/', views.school_profile_view, name='school_profile'),
] 