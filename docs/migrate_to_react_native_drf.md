# Migrate to React Native and Django REST Framework

This document outlines a step-by-step plan to migrate the current Django template-based application to a modern architecture using React Native for the frontend (supporting web, iOS, and Android) and Django REST Framework for the backend API.

## Migration Overview

The migration will follow these high-level steps:
1. Transform the Django backend into a REST API
2. Create a React Native project with web support
3. Implement API consumers in React Native
4. Add mobile-specific features
5. Deploy to web, iOS, and Android platforms

## Phase 1: Prepare Django Backend for API Transition

### Step 1: Install and Configure DRF
1. Install necessary packages:
   ```bash
   pip install djangorestframework djangorestframework-simplejwt django-cors-headers
   ```

2. Update `settings.py`:
   ```python
   INSTALLED_APPS = [
       # existing apps
       'rest_framework',
       'rest_framework_simplejwt',
       'corsheaders',
   ]
   
   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       # existing middleware
   ]
   
   # DRF Settings
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'rest_framework_simplejwt.authentication.JWTAuthentication',
       ),
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
   }
   
   # JWT Settings
   SIMPLE_JWT = {
       'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
       'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
       # other JWT settings
   }
   
   # CORS Settings
   CORS_ALLOW_ALL_ORIGINS = False  # Set to True during development
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://localhost:19006",  # Expo web port
   ]
   ```

#### Execution Prompt for Step 1:
```
Transform the Django project into a REST API by installing and configuring Django REST Framework with JWT authentication:

1. First, examine the current project structure to understand the existing setup:
   - Identify the main Django settings file
   - Check the current INSTALLED_APPS and MIDDLEWARE configurations
   - Review any existing authentication mechanisms

2. Install required packages by running:
   ```bash
   pip install djangorestframework djangorestframework-simplejwt django-cors-headers
   ```

3. Update requirements.txt to include these new dependencies:
   ```bash
   pip freeze > requirements.txt
   ```

4. Modify the Django settings.py file to:
   - Add 'rest_framework', 'rest_framework_simplejwt', and 'corsheaders' to INSTALLED_APPS
   - Add 'corsheaders.middleware.CorsMiddleware' to MIDDLEWARE (before CommonMiddleware)
   - Import datetime.timedelta at the top of the file

5. Add the following DRF and JWT configurations to settings.py:
   ```python
   # DRF Settings
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
           'rest_framework_simplejwt.authentication.JWTAuthentication',
       ),
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
   }
   
   # JWT Settings
   SIMPLE_JWT = {
       'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
       'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
       'ROTATE_REFRESH_TOKENS': False,
       'BLACKLIST_AFTER_ROTATION': True,
       'UPDATE_LAST_LOGIN': False,
       'ALGORITHM': 'HS256',
       'SIGNING_KEY': SECRET_KEY,
       'VERIFYING_KEY': None,
       'AUDIENCE': None,
       'ISSUER': None,
       'AUTH_HEADER_TYPES': ('Bearer',),
       'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
       'USER_ID_FIELD': 'id',
       'USER_ID_CLAIM': 'user_id',
   }
   ```

6. Add CORS settings to settings.py:
   ```python
   # CORS Settings
   CORS_ALLOW_ALL_ORIGINS = True  # For development; set to False in production
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://localhost:19006",  # Expo web port
   ]
   ```

7. Run migrations to ensure database is up to date:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. Test the installation by running the development server:
   ```bash
   python manage.py runserver
   ```

9. Verify that DRF is properly installed by checking the Django admin interface and ensuring there are no errors in the console.

10. Update documentation
```

### Step 2: Create API Endpoints for Authentication
1. Create `api` app:
   ```bash
   python manage.py startapp api
   ```

2. Implement authentication endpoints:
   - JWT token obtain/refresh/verify
   - User registration
   - Password reset 

3. Configure URL routes in `api/urls.py`:
   ```python
   from django.urls import path, include
   from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
   
   urlpatterns = [
       path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
       path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
       # Add other authentication endpoints
   ]
   ```

#### Execution Prompt for Step 2:
```
Create API endpoints for authentication using Django REST Framework and JWT:

1. Create a new Django app for the API:
   ```bash
   python manage.py startapp api
   ```

2. Add the new 'api' app to INSTALLED_APPS in settings.py.

3. Create an authentication views file in the api app (api/auth_views.py):
   ```python
   from rest_framework import status, permissions
   from rest_framework.views import APIView
   from rest_framework.response import Response
   from rest_framework_simplejwt.views import TokenObtainPairView
   from django.contrib.auth import get_user_model
   from django.contrib.auth.tokens import default_token_generator
   from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
   from django.utils.encoding import force_bytes
   from django.core.mail import send_mail
   from .serializers import UserRegistrationSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer

   User = get_user_model()

   class CustomTokenObtainPairView(TokenObtainPairView):
       """
       Custom token view that returns user info along with tokens
       """
       def post(self, request, *args, **kwargs):
           response = super().post(request, *args, **kwargs)
           if response.status_code == 200:
               user = User.objects.get(email=request.data['email'])
               response.data['user_id'] = user.id
               response.data['email'] = user.email
               response.data['name'] = user.name
               response.data['is_admin'] = user.is_admin
               # Add any other user fields you need
           return response

   class RegisterView(APIView):
       permission_classes = [permissions.AllowAny]

       def post(self, request):
           serializer = UserRegistrationSerializer(data=request.data)
           if serializer.is_valid():
               user = serializer.save()
               return Response({
                   "message": "User registered successfully",
                   "user_id": user.id
               }, status=status.HTTP_201_CREATED)
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   class PasswordResetView(APIView):
       permission_classes = [permissions.AllowAny]

       def post(self, request):
           serializer = PasswordResetSerializer(data=request.data)
           if serializer.is_valid():
               email = serializer.validated_data['email']
               try:
                   user = User.objects.get(email=email)
                   uid = urlsafe_base64_encode(force_bytes(user.pk))
                   token = default_token_generator.make_token(user)
                   reset_link = f"https://yourfrontend.com/reset-password/{uid}/{token}/"
                   
                   # Send email
                   send_mail(
                       'Password Reset',
                       f'Click the link to reset your password: {reset_link}',
                       'noreply@example.com',
                       [user.email],
                       fail_silently=False,
                   )
                   return Response({"message": "Password reset link sent"}, status=status.HTTP_200_OK)
               except User.DoesNotExist:
                   # Return success even if user doesn't exist for security
                   return Response({"message": "Password reset link sent"}, status=status.HTTP_200_OK)
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   class PasswordResetConfirmView(APIView):
       permission_classes = [permissions.AllowAny]

       def post(self, request):
           serializer = PasswordResetConfirmSerializer(data=request.data)
           if serializer.is_valid():
               uid = serializer.validated_data['uid']
               token = serializer.validated_data['token']
               password = serializer.validated_data['new_password']
               
               try:
                   uid = urlsafe_base64_decode(uid).decode()
                   user = User.objects.get(pk=uid)
               except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                   return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)
               
               if default_token_generator.check_token(user, token):
                   user.set_password(password)
                   user.save()
                   return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
               else:
                   return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)
               
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   ```

4. Create serializers for authentication in api/serializers.py:
   ```python
   from rest_framework import serializers
   from django.contrib.auth import get_user_model
   
   User = get_user_model()
   
   class UserRegistrationSerializer(serializers.ModelSerializer):
       password = serializers.CharField(write_only=True)
       password_confirm = serializers.CharField(write_only=True)
   
       class Meta:
           model = User
           fields = ('email', 'name', 'password', 'password_confirm')
   
       def validate(self, data):
           if data['password'] != data['password_confirm']:
               raise serializers.ValidationError("Passwords don't match")
           return data
   
       def create(self, validated_data):
           validated_data.pop('password_confirm')
           user = User.objects.create_user(
               email=validated_data['email'],
               name=validated_data['name'],
               password=validated_data['password']
           )
           return user
           
   class PasswordResetSerializer(serializers.Serializer):
       email = serializers.EmailField()
   
   class PasswordResetConfirmSerializer(serializers.Serializer):
       uid = serializers.CharField()
       token = serializers.CharField()
       new_password = serializers.CharField(min_length=8)
       confirm_password = serializers.CharField(min_length=8)
   
       def validate(self, data):
           if data['new_password'] != data['confirm_password']:
               raise serializers.ValidationError("Passwords don't match")
           return data
   ```

5. Create api/urls.py for authentication endpoints:
   ```python
   from django.urls import path, include
   from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
   from .auth_views import CustomTokenObtainPairView, RegisterView, PasswordResetView, PasswordResetConfirmView

   urlpatterns = [
       # JWT Authentication
       path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
       path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
       path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
       
       # User Registration
       path('register/', RegisterView.as_view(), name='register'),
       
       # Password Reset
       path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
       path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
   ]
   ```

6. Include the API URLs in the project's main urls.py:
   ```python
   from django.urls import path, include

   urlpatterns = [
       # Existing URLs
       path('api/', include('api.urls')),
   ]
   ```

7. Test the authentication endpoints using a tool like curl, Postman, or httpie:
   - Test token generation with a POST to /api/token/
   - Test token refresh with a POST to /api/token/refresh/
   - Test user registration with a POST to /api/register/
   - Test password reset flow

8. Document the API endpoints and their required parameters for frontend developers to use.
```

### Step 3: Create API Serializers for Existing Models
1. Create serializers for all models:
   - User/Profile serializers
   - ClassSession serializers
   - Financial model serializers

2. Example serializer:
   ```python
   # api/serializers.py
   from rest_framework import serializers
   from accounts.models import User
   
   class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ('id', 'email', 'name', 'phone_number', 'is_admin')
           read_only_fields = ('id',)
   ```

#### Execution Prompt for Step 3:
```
Create serializers for existing models to expose them through the REST API:

1. Examine the existing models in the project:
   - Analyze the accounts app for User and Profile models
   - Analyze the scheduling app for calendar-related models
   - Analyze the financials app for payment and compensation models

2. Update the api/serializers.py file to include serializers for all models:

3. Create User and Profile serializers:
   ```python
   from rest_framework import serializers
   from accounts.models import User, TeacherProfile, StudentProfile, ParentProfile
   
   class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ('id', 'email', 'name', 'phone_number', 'is_admin', 'role')
           read_only_fields = ('id',)
   
   class TeacherProfileSerializer(serializers.ModelSerializer):
       user = UserSerializer(read_only=True)
       
       class Meta:
           model = TeacherProfile
           fields = ('id', 'user', 'specialties', 'hourly_rate', 'bio', 'qualifications')
           read_only_fields = ('id',)
   
   class StudentProfileSerializer(serializers.ModelSerializer):
       user = UserSerializer(read_only=True)
       
       class Meta:
           model = StudentProfile
           fields = ('id', 'user', 'grade_level', 'date_of_birth', 'notes')
           read_only_fields = ('id',)
   
   class ParentProfileSerializer(serializers.ModelSerializer):
       user = UserSerializer(read_only=True)
       children = StudentProfileSerializer(many=True, read_only=True)
       
       class Meta:
           model = ParentProfile
           fields = ('id', 'user', 'children')
           read_only_fields = ('id',)
   ```

4. Create Calendar serializers in a new file api/calendar_serializers.py:
   ```python
   from rest_framework import serializers
   from scheduling.models import Subject, ClassType, ClassSession
   from accounts.models import User
   
   class SubjectSerializer(serializers.ModelSerializer):
       class Meta:
           model = Subject
           fields = ('id', 'name', 'description', 'grade_level_range')
           read_only_fields = ('id',)
   
   class ClassTypeSerializer(serializers.ModelSerializer):
       class Meta:
           model = ClassType
           fields = ('id', 'name', 'group_class', 'default_duration', 'hourly_rate', 'description')
           read_only_fields = ('id',)
   
   class TeacherForSessionSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ('id', 'name', 'email')
           read_only_fields = fields
   
   class StudentForSessionSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ('id', 'name', 'email')
           read_only_fields = fields
   
   class ClassSessionSerializer(serializers.ModelSerializer):
       teacher = TeacherForSessionSerializer(read_only=True)
       students = StudentForSessionSerializer(many=True, read_only=True)
       subject = SubjectSerializer(read_only=True)
       class_type = ClassTypeSerializer(read_only=True)
       
       subject_id = serializers.PrimaryKeyRelatedField(
           write_only=True, 
           queryset=Subject.objects.all(),
           source='subject'
       )
       class_type_id = serializers.PrimaryKeyRelatedField(
           write_only=True, 
           queryset=ClassType.objects.all(),
           source='class_type'
       )
       teacher_id = serializers.PrimaryKeyRelatedField(
           write_only=True, 
           queryset=User.objects.filter(role='teacher'),
           source='teacher'
       )
       student_ids = serializers.PrimaryKeyRelatedField(
           write_only=True, 
           queryset=User.objects.filter(role='student'),
           source='students',
           many=True
       )
       
       class Meta:
           model = ClassSession
           fields = (
               'id', 'title', 'start_time', 'end_time', 'status', 
               'teacher', 'students', 'subject', 'class_type', 
               'google_calendar_id', 'price_override', 'attended',
               'teacher_id', 'student_ids', 'subject_id', 'class_type_id'
           )
           read_only_fields = ('id', 'google_calendar_id')
   ```

5. Create Financial serializers in a new file api/financial_serializers.py:
   ```python
   from rest_framework import serializers
   from financials.models import PaymentPlan, StudentPayment, TeacherCompensation
   from scheduling.models import ClassType, ClassSession
   from accounts.models import User
   from .calendar_serializers import ClassSessionSerializer
   
   class PaymentPlanSerializer(serializers.ModelSerializer):
       class_type = serializers.PrimaryKeyRelatedField(
           queryset=ClassType.objects.all(),
           required=False,
           allow_null=True
       )
       
       class Meta:
           model = PaymentPlan
           fields = (
               'id', 'name', 'description', 'plan_type', 
               'rate', 'hours_included', 'expiration_period', 'class_type'
           )
           read_only_fields = ('id',)
   
   class StudentPaymentSerializer(serializers.ModelSerializer):
       student = serializers.PrimaryKeyRelatedField(
           queryset=User.objects.filter(role='student')
       )
       payment_plan = serializers.PrimaryKeyRelatedField(
           queryset=PaymentPlan.objects.all()
       )
       
       class Meta:
           model = StudentPayment
           fields = (
               'id', 'student', 'payment_plan', 'amount_paid', 'payment_date',
               'period_start', 'period_end', 'hours_purchased', 'hours_used',
               'status', 'notes'
           )
           read_only_fields = ('id',)
   
   class TeacherCompensationSerializer(serializers.ModelSerializer):
       teacher = serializers.PrimaryKeyRelatedField(
           queryset=User.objects.filter(role='teacher')
       )
       class_sessions = serializers.PrimaryKeyRelatedField(
           queryset=ClassSession.objects.all(),
           many=True
       )
       class_sessions_detail = ClassSessionSerializer(
           source='class_sessions',
           many=True,
           read_only=True
       )
       
       class Meta:
           model = TeacherCompensation
           fields = (
               'id', 'teacher', 'period_start', 'period_end', 
               'class_sessions', 'class_sessions_detail', 'hours_taught', 
               'amount_owed', 'amount_paid', 'payment_date', 'status', 'notes'
           )
           read_only_fields = ('id', 'hours_taught', 'amount_owed')
   ```

6. Create serializers for homework management if applicable:
   ```python
   from rest_framework import serializers
   from homework.models import HomeworkAssignment, HomeworkSubmission
   
   class HomeworkAssignmentSerializer(serializers.ModelSerializer):
       # Implementation based on your models
       
       class Meta:
           model = HomeworkAssignment
           fields = ('id', 'title', 'description', 'due_date', 'teacher', 'students', 'file_attachments', 'date_created')
           read_only_fields = ('id', 'date_created')
   
   class HomeworkSubmissionSerializer(serializers.ModelSerializer):
       # Implementation based on your models
       
       class Meta:
           model = HomeworkSubmission
           fields = ('id', 'assignment', 'student', 'submission_date', 'file_attachments', 'feedback', 'notes')
           read_only_fields = ('id', 'submission_date')
   ```

7. Create nested serializers for combining related data where needed:
   ```python
   class StudentWithPaymentsSerializer(serializers.ModelSerializer):
       profile = StudentProfileSerializer(read_only=True)
       payments = StudentPaymentSerializer(many=True, read_only=True)
       
       class Meta:
           model = User
           fields = ('id', 'email', 'name', 'profile', 'payments')
           read_only_fields = fields
   
   class TeacherWithCompensationsSerializer(serializers.ModelSerializer):
       profile = TeacherProfileSerializer(read_only=True)
       compensations = TeacherCompensationSerializer(many=True, read_only=True)
       
       class Meta:
           model = User
           fields = ('id', 'email', 'name', 'profile', 'compensations')
           read_only_fields = fields
   ```

8. Test serializer functionality:
   - Create simple view functions to test serialization of objects
   - Ensure proper nested serialization works
   - Test serialization with related objects
```

### Step 4: Implement API Viewsets
1. Create viewsets for all models:
   ```python
   # api/viewsets.py
   from rest_framework import viewsets
   from accounts.models import User
   from .serializers import UserSerializer
   
   class UserViewSet(viewsets.ModelViewSet):
       queryset = User.objects.all()
       serializer_class = UserSerializer
       # Add permissions
   ```

2. Configure URL routes with routers:
   ```python
   # api/urls.py (continued from above)
   from rest_framework.routers import DefaultRouter
   from .viewsets import UserViewSet
   
   router = DefaultRouter()
   router.register(r'users', UserViewSet)
   # Register other viewsets
   
   urlpatterns = [
       # Authentication URLs from above
       path('', include(router.urls)),
   ]
   ```

### Step 5: Convert Business Logic to API Services
1. Move view logic to API-oriented services
2. Refactor financial calculations as API endpoints
3. Implement calendar synchronization endpoints

#### Execution Prompt for Step 5:
```
Convert business logic from Django views to API services:

1. Create service modules to contain business logic:
   - Create api/services/ directory
   - Create separate service files for each logical domain

2. Create a calendar service in api/services/calendar_service.py:
   ```python
   from django.conf import settings
   from google.oauth2.credentials import Credentials
   from googleapiclient.discovery import build
   from scheduling.models import Subject, ClassType, ClassSession
   from accounts.models import User
   import re
   from datetime import datetime, timedelta
   
   class CalendarService:
       """Service for Google Calendar integration"""
       
       @staticmethod
       def get_credentials(user):
           """Get Google API credentials for a user"""
           # Implementation based on your current auth system
           # This would use the stored refresh token to get valid credentials
           pass
       
       @staticmethod
       def sync_calendar_events(user, calendar_id=None, time_min=None, time_max=None):
           """
           Sync events from Google Calendar to ClassSession objects
           """
           # Get credentials
           credentials = CalendarService.get_credentials(user)
           if not credentials:
               return {"error": "No valid Google credentials found"}
               
           # Build the calendar service
           service = build('calendar', 'v3', credentials=credentials)
           
           # Set default parameters
           if not calendar_id:
               calendar_id = 'primary'
               
           if not time_min:
               time_min = datetime.utcnow().isoformat() + 'Z'
               
           if not time_max:
               # Default to 30 days in the future
               time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
           
           # Call the Calendar API
           events_result = service.events().list(
               calendarId=calendar_id,
               timeMin=time_min,
               timeMax=time_max,
               maxResults=100,
               singleEvents=True,
               orderBy='startTime'
           ).execute()
           
           events = events_result.get('items', [])
           
           results = {
               'created': 0,
               'updated': 0,
               'ignored': 0,
               'errors': []
           }
           
           for event in events:
               try:
                   # Parse event data according to your rules
                   # Example parsing logic:
                   title = event.get('summary', '')
                   
                   # Check for absence marker
                   attended = 'FALTOU' not in title
                   
                   # Extract student name from title
                   # This regex would depend on your naming convention
                   student_name_match = re.search(r'^([^:]+)', title)
                   if not student_name_match:
                       results['ignored'] += 1
                       continue
                       
                   student_name = student_name_match.group(1).strip()
                   
                   # Get teacher from location field
                   teacher_name = event.get('location', '').strip()
                   
                   # Get price code from description
                   description = event.get('description', '')
                   price_code_match = re.search(r'Price: (\w+)', description)
                   price_code = price_code_match.group(1) if price_code_match else None
                   
                   # Find the teacher user
                   try:
                       teacher = User.objects.get(name=teacher_name, role='teacher')
                   except User.DoesNotExist:
                       results['errors'].append(f"Teacher not found: {teacher_name}")
                       results['ignored'] += 1
                       continue
                   
                   # Find the student user
                   try:
                       student = User.objects.get(name=student_name, role='student')
                   except User.DoesNotExist:
                       results['errors'].append(f"Student not found: {student_name}")
                       results['ignored'] += 1
                       continue
                   
                   # Find class type based on price code
                   try:
                       class_type = ClassType.objects.get(name=price_code)
                   except ClassType.DoesNotExist:
                       results['errors'].append(f"Class type not found: {price_code}")
                       results['ignored'] += 1
                       continue
                   
                   # Get start and end times
                   start_time = event['start'].get('dateTime')
                   end_time = event['end'].get('dateTime')
                   
                   if not start_time or not end_time:
                       results['ignored'] += 1
                       continue
                   
                   # Create or update session
                   session, created = ClassSession.objects.update_or_create(
                       google_calendar_id=event['id'],
                       defaults={
                           'title': title,
                           'teacher': teacher,
                           'class_type': class_type,
                           'start_time': start_time,
                           'end_time': end_time,
                           'attended': attended,
                       }
                   )
                   
                   # Add the student to the session
                   session.students.add(student)
                   
                   if created:
                       results['created'] += 1
                   else:
                       results['updated'] += 1
                       
               except Exception as e:
                   results['errors'].append(str(e))
                   results['ignored'] += 1
           
           return results
   ```

3. Create a financial service in api/services/financial_service.py:
   ```python
   from django.db.models import Sum, F, ExpressionWrapper, fields
   from django.db.models.functions import Cast
   from financials.models import TeacherCompensation, StudentPayment
   from scheduling.models import ClassSession
   from datetime import timedelta
   
   class FinancialService:
       """Service for financial calculations"""
       
       @staticmethod
       def calculate_teacher_compensation(teacher, period_start, period_end):
           """
           Calculate teacher compensation for a given period
           """
           # Get all classes taught by the teacher in the period
           sessions = ClassSession.objects.filter(
               teacher=teacher,
               start_time__gte=period_start,
               end_time__lte=period_end,
               attended=True
           )
           
           # Calculate total hours
           total_hours = 0
           total_amount = 0
           
           for session in sessions:
               # Calculate duration in hours
               duration = (session.end_time - session.start_time).total_seconds() / 3600
               
               # Get hourly rate from class type
               hourly_rate = session.class_type.hourly_rate
               
               # Calculate amount for this session
               session_amount = duration * hourly_rate
               
               total_hours += duration
               total_amount += session_amount
           
           # Create or update compensation record
           compensation, created = TeacherCompensation.objects.update_or_create(
               teacher=teacher,
               period_start=period_start,
               period_end=period_end,
               defaults={
                   'hours_taught': total_hours,
                   'amount_owed': total_amount,
                   'status': 'pending'
               }
           )
           
           # Add class sessions
           compensation.class_sessions.set(sessions)
           
           return compensation
       
       @staticmethod
       def calculate_student_remaining_hours(student):
           """
           Calculate remaining hours for a student with package-based payment plans
           """
           # Get active package-based payments
           payments = StudentPayment.objects.filter(
               student=student,
               payment_plan__plan_type='package',
               status='completed'
           )
           
           results = []
           
           for payment in payments:
               # Get used hours from class sessions
               used_hours = ClassSession.objects.filter(
                   students=student,
                   attended=True,
                   class_type=payment.payment_plan.class_type,
                   start_time__gte=payment.payment_date,
               ).aggregate(
                   total_hours=Sum(
                       ExpressionWrapper(
                           F('end_time') - F('start_time'),
                           output_field=fields.DurationField()
                       )
                   )
               )['total_hours'] or timedelta()
               
               # Convert to hours
               used_hours_float = used_hours.total_seconds() / 3600
               
               # Update payment
               payment.hours_used = used_hours_float
               payment.save()
               
               # Calculate remaining hours
               remaining_hours = payment.hours_purchased - payment.hours_used
               
               # Check if expired
               from django.utils import timezone
               expiry_date = payment.payment_date + timedelta(days=payment.payment_plan.expiration_period)
               is_expired = expiry_date < timezone.now().date()
               
               results.append({
                   'payment': payment,
                   'remaining_hours': remaining_hours,
                   'expiry_date': expiry_date,
                   'is_expired': is_expired
               })
           
           return results
   ```

4. Create API endpoints to expose these services in api/views.py:
   ```python
   from rest_framework.views import APIView
   from rest_framework.response import Response
   from rest_framework import permissions, status
   from django.utils import timezone
   from datetime import timedelta
   from .services.calendar_service import CalendarService
   from .services.financial_service import FinancialService
   from .serializers import TeacherCompensationSerializer, ClassSessionSerializer
   
   class SyncCalendarView(APIView):
       permission_classes = [permissions.IsAuthenticated]
       
       def post(self, request):
           # Get parameters
           calendar_id = request.data.get('calendar_id', 'primary')
           
           # Default to fetching last 30 days and next 30 days
           now = timezone.now()
           time_min = request.data.get('time_min', (now - timedelta(days=30)).isoformat() + 'Z')
           time_max = request.data.get('time_max', (now + timedelta(days=30)).isoformat() + 'Z')
           
           # Call service
           results = CalendarService.sync_calendar_events(
               user=request.user,
               calendar_id=calendar_id,
               time_min=time_min,
               time_max=time_max
           )
           
           return Response(results)
   
   class CalculateTeacherCompensationView(APIView):
       permission_classes = [permissions.IsAuthenticated]
       
       def post(self, request):
           # Get parameters
           teacher_id = request.data.get('teacher_id')
           period_start = request.data.get('period_start')
           period_end = request.data.get('period_end')
           
           # Validations
           if not teacher_id or not period_start or not period_end:
               return Response(
                   {"error": "teacher_id, period_start, and period_end are required"},
                   status=status.HTTP_400_BAD_REQUEST
               )
           
           # Only admins can calculate for other teachers
           if str(teacher_id) != str(request.user.id) and not request.user.is_admin:
               return Response(
                   {"error": "You can only calculate your own compensation"},
                   status=status.HTTP_403_FORBIDDEN
               )
           
           try:
               from accounts.models import User
               teacher = User.objects.get(id=teacher_id, role='teacher')
           except User.DoesNotExist:
               return Response(
                   {"error": "Teacher not found"},
                   status=status.HTTP_404_NOT_FOUND
               )
           
           # Call service
           compensation = FinancialService.calculate_teacher_compensation(
               teacher=teacher,
               period_start=period_start,
               period_end=period_end
           )
           
           serializer = TeacherCompensationSerializer(compensation)
           return Response(serializer.data)
   
   class StudentRemainingHoursView(APIView):
       permission_classes = [permissions.IsAuthenticated]
       
       def get(self, request, student_id=None):
           # Determine which student to calculate for
           if student_id:
               # Check permissions
               if str(student_id) != str(request.user.id) and not request.user.is_admin:
                   # Check if parent
                   is_parent = request.user.role == 'parent' and hasattr(request.user, 'parentprofile')
                   is_child = is_parent and request.user.parentprofile.children.filter(user_id=student_id).exists()
                   
                   if not is_child:
                       return Response(
                           {"error": "You can only view your own or your children's hours"},
                           status=status.HTTP_403_FORBIDDEN
                       )
               
               try:
                   from accounts.models import User
                   student = User.objects.get(id=student_id, role='student')
               except User.DoesNotExist:
                   return Response(
                       {"error": "Student not found"},
                       status=status.HTTP_404_NOT_FOUND
                   )
           else:
               # Use the current user
               if request.user.role != 'student':
                   return Response(
                       {"error": "User is not a student"},
                       status=status.HTTP_400_BAD_REQUEST
                   )
               student = request.user
           
           # Call service
           results = FinancialService.calculate_student_remaining_hours(student)
           
           # Format response
           response_data = []
           for item in results:
               payment_data = {
                   'payment_id': item['payment'].id,
                   'payment_date': item['payment'].payment_date,
                   'plan_name': item['payment'].payment_plan.name,
                   'hours_purchased': item['payment'].hours_purchased,
                   'hours_used': item['payment'].hours_used,
                   'remaining_hours': item['remaining_hours'],
                   'expiry_date': item['expiry_date'],
                   'is_expired': item['is_expired']
               }
               response_data.append(payment_data)
           
           return Response(response_data)
   ```

5. Add these API views to api/urls.py:
   ```python
   # In api/urls.py
   from .views import SyncCalendarView, CalculateTeacherCompensationView, StudentRemainingHoursView
   
   urlpatterns = [
       # Existing URLs
       
       # Service endpoints
       path('sync-calendar/', SyncCalendarView.as_view(), name='sync_calendar'),
       path('calculate-compensation/', CalculateTeacherCompensationView.as_view(), name='calculate_compensation'),
       path('student-remaining-hours/', StudentRemainingHoursView.as_view(), name='student_remaining_hours'),
       path('student-remaining-hours/<int:student_id>/', StudentRemainingHoursView.as_view(), name='student_remaining_hours_by_id'),
   ]
   ```

6. Test these service endpoints:
   - Test calendar synchronization with mock Google Calendar data
   - Test financial calculations with various scenarios
   - Ensure permissions work correctly for different user roles
```

## Phase 2: Create React Native Application

### Step 1: Set Up React Native with Expo
1. Install Expo CLI:
   ```bash
   npm install -g expo-cli
   ```

2. Create new project:
   ```bash
   expo init aprendecomigo-app --template blank-typescript
   ```

3. Add web support:
   ```bash
   cd aprendecomigo-app
   expo install react-native-web react-dom @expo/webpack-config
   ```

4. Install additional dependencies:
   ```bash
   expo install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack
   expo install axios @react-native-async-storage/async-storage
   expo install react-native-paper
   ```

#### Execution Prompt for Step 1:
```
Set up a React Native project with Expo that supports web, iOS, and Android platforms:

1. Ensure the development environment is prepared:
   - Node.js is installed (v14.x or higher recommended)
   - You have a package manager (npm or yarn)
   - Xcode is installed (for iOS development on Mac)
   - Android Studio is set up (for Android development)

2. Install Expo CLI globally:
   ```bash
   npm install -g expo-cli
   ```

3. Create a new React Native project with TypeScript:
   ```bash
   expo init aprendecomigo-app --template blank-typescript
   ```
   When prompted, select the "blank TypeScript" template.

4. Navigate to the project directory:
   ```bash
   cd aprendecomigo-app
   ```

5. Add web support to the Expo project:
   ```bash
   expo install react-native-web react-dom @expo/webpack-config
   ```

6. Install navigation packages:
   ```bash
   expo install @react-navigation/native
   expo install @react-navigation/native-stack
   expo install @react-navigation/bottom-tabs
   expo install @react-navigation/drawer
   expo install react-native-screens react-native-safe-area-context
   ```

7. Install libraries for API requests and storage:
   ```bash
   expo install axios
   expo install @react-native-async-storage/async-storage
   ```

8. Install UI libraries:
   ```bash
   expo install react-native-paper
   expo install react-native-vector-icons
   ```

9. Install additional utilities:
   ```bash
   npm install date-fns 
   npm install react-native-dotenv
   npm install react-native-calendar-events
   npm install react-native-community/datetimepicker
   ```

10. Create a .env file for configuration:
    ```
    API_URL=http://localhost:8000/api
    ```

11. Configure the app.json file:
    ```json
    {
      "expo": {
        "name": "Aprende Comigo",
        "slug": "aprendecomigo-app",
        "version": "1.0.0",
        "orientation": "portrait",
        "icon": "./assets/icon.png",
        "splash": {
          "image": "./assets/splash.png",
          "resizeMode": "contain",
          "backgroundColor": "#ffffff"
        },
        "updates": {
          "fallbackToCacheTimeout": 0
        },
        "assetBundlePatterns": [
          "**/*"
        ],
        "ios": {
          "supportsTablet": true,
          "bundleIdentifier": "com.yourdomain.aprendecomigo"
        },
        "android": {
          "adaptiveIcon": {
            "foregroundImage": "./assets/adaptive-icon.png",
            "backgroundColor": "#FFFFFF"
          },
          "package": "com.yourdomain.aprendecomigo"
        },
        "web": {
          "favicon": "./assets/favicon.png"
        }
      }
    }
    ```

12. Update the babel.config.js to support the environment variables:
    ```javascript
    module.exports = function(api) {
      api.cache(true);
      return {
        presets: ['babel-preset-expo'],
        plugins: [
          ["module:react-native-dotenv", {
            "moduleName": "@env",
            "path": ".env",
            "blacklist": null,
            "whitelist": null,
            "safe": false,
            "allowUndefined": true
          }]
        ],
      };
    };
    ```

13. Create a tsconfig.json to handle path aliases:
    ```json
    {
      "extends": "expo/tsconfig.base",
      "compilerOptions": {
        "allowSyntheticDefaultImports": true,
        "jsx": "react-native",
        "lib": ["dom", "esnext"],
        "moduleResolution": "node",
        "noEmit": true,
        "skipLibCheck": true,
        "resolveJsonModule": true,
        "strict": true,
        "baseUrl": ".",
        "paths": {
          "@/*": ["src/*"]
        }
      }
    }
    ```

14. Test the installation by running:
    ```bash
    # For mobile development
    expo start
    
    # For web development
    expo start --web
    ```

15. Create a minimal App.tsx to verify everything is working:
    ```tsx
    import React from 'react';
    import { StatusBar } from 'expo-status-bar';
    import { SafeAreaProvider } from 'react-native-safe-area-context';
    import { Text, View } from 'react-native';
    
    export default function App() {
      return (
        <SafeAreaProvider>
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <Text>Welcome to Aprende Comigo!</Text>
            <StatusBar style="auto" />
          </View>
        </SafeAreaProvider>
      );
    }
    ```

16. Ensure that everything loads correctly on web and mobile platforms.
```

### Step 2: Set Up Project Structure
```
src/
├── api/              # API client and services
├── components/       # Reusable UI components
├── contexts/         # React contexts (auth, etc)
├── hooks/            # Custom hooks
├── navigation/       # Navigation configuration
├── screens/          # App screens by feature
├── styles/           # Theme and shared styles
└── utils/            # Helper functions
```

### Step 3: Implement Authentication Flow
1. Create authentication context:
   ```typescript
   // src/contexts/AuthContext.tsx
   import React, { createContext, useState } from 'react';
   import * as authApi from '../api/auth';
   
   export const AuthContext = createContext({});
   
   export const AuthProvider = ({ children }) => {
     const [user, setUser] = useState(null);
     const [loading, setLoading] = useState(false);
     
     const login = async (email, password) => {
       setLoading(true);
       try {
         const response = await authApi.login(email, password);
         // Store tokens, fetch user data, etc.
         setUser(response.user);
         return true;
       } catch (error) {
         console.error(error);
         return false;
       } finally {
         setLoading(false);
       }
     };
     
     // Add logout, signup, etc.
     
     return (
       <AuthContext.Provider value={{ user, loading, login /* etc */ }}>
         {children}
       </AuthContext.Provider>
     );
   };
   ```

2. Create authentication screens:
   - Login
   - Signup
   - Password reset
   - Profile

### Step 4: Implement Core Features
1. Calendar view:
   - Class schedule component
   - Calendar integration
   
2. Financial screens:
   - Payment tracking
   - Teacher compensation
   
3. User management:
   - Role-specific dashboards
   - Profile management

## Phase 3: Mobile-Specific Enhancements

### Step 1: Add Push Notifications
1. Install notification packages:
   ```bash
   expo install expo-notifications
   ```
   
2. Configure notification handling:
   - Token registration
   - Push handling
   - Local notification scheduling

### Step 2: Implement Offline Support
1. Create data persistence strategy:
   - AsyncStorage caching
   - Synchronization mechanism
   - Conflict resolution
   
2. Add offline indicators and handling

### Step 3: Add Deep Linking
1. Configure app.json:
   ```json
   {
     "expo": {
       "scheme": "aprendecomigo",
       "ios": {
         "associatedDomains": ["applinks:example.com"]
       },
       "android": {
         "intentFilters": [
           {
             "action": "VIEW",
             "data": [
               {
                 "scheme": "https",
                 "host": "example.com",
                 "pathPrefix": "/"
               }
             ],
             "category": ["BROWSABLE", "DEFAULT"]
           }
         ]
       }
     }
   }
   ```
   
2. Add deep link handling in navigation

## Phase 4: Deployment Preparation

### Step 1: Backend API Deployment
1. Update production settings:
   - CORS configuration
   - Security settings
   - Database optimization
   
2. Deploy to PythonAnywhere or similar cloud hosting:
   - Configure static files
   - Set up environment variables
   - Configure database

### Step 2: Web Deployment
1. Build web version:
   ```bash
   expo build:web
   ```
   
2. Deploy to Vercel, Netlify, or similar service:
   - Configure environment variables
   - Set up build process
   - Configure domain

### Step 3: iOS Deployment
1. Prepare App Store assets:
   - Icons
   - Screenshots
   - App Store listing
   
2. Build iOS app:
   ```bash
   expo build:ios
   ```
   
3. Submit to App Store Connect

### Step 4: Android Deployment
1. Prepare Google Play assets:
   - Icons
   - Screenshots
   - Store listing
   
2. Build Android app:
   ```bash
   expo build:android
   ```
   
3. Submit to Google Play Console

## Migration Timeline Estimate

- **Phase 1: Backend API Transition** - 4-6 weeks
- **Phase 2: React Native Implementation** - 6-8 weeks
- **Phase 3: Mobile Enhancements** - 3-4 weeks
- **Phase 4: Deployment** - 2-3 weeks

**Total Migration Time: 15-21 weeks**

## Challenges and Considerations

### Authentication
- Current django-allauth system needs to be replaced with JWT
- Social auth flows differ on mobile vs web
- Secure token storage requirements vary by platform

### Calendar Integration
- Mobile devices have native calendar capabilities
- Consider using different approaches for web vs native

### Offline Support
- Critical for mobile user experience
- Requires careful synchronization design
- Data conflicts must be handled gracefully

### Testing Requirements
- Cross-platform testing needed
- Test on multiple device sizes and OS versions
- API integration testing becomes more important

## Conclusion

This migration will transform the platform into a modern, cross-platform application capable of reaching users on web, iOS, and Android with a single codebase. While the transition requires significant effort, the resulting application will provide a superior user experience and position the platform for future growth.
