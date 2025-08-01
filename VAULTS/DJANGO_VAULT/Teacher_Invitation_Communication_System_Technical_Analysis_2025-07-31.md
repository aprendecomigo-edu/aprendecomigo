# Teacher Invitation Communication System - Technical Analysis
*Generated: 2025-07-31*

## GitHub Issue #53: Comprehensive Teacher Invitation Communication System

### Current System Analysis

#### Existing Architecture
The platform already has a sophisticated foundation for teacher invitations:

1. **Enhanced TeacherInvitation Model** (`accounts/models.py:1257-1508`)
   - Comprehensive status tracking (pending, sent, delivered, viewed, accepted, etc.)
   - Email delivery tracking with retry logic
   - Batch processing support with `batch_id` UUID
   - Custom messaging capabilities
   - WebSocket real-time updates integration

2. **School Branding Infrastructure** (`accounts/models.py:75-122`)
   - Logo, primary/secondary colors, email domain
   - Contact information and website
   - School description for contextual messaging

3. **Email Service Layer** (`common/messaging.py:81-200`)
   - `TeacherInvitationEmailService` with HTML/text templates
   - Bulk email processing with error handling
   - Template-based email rendering with Django templates

4. **Professional Email Templates** (`templates/emails/teacher_invitation.html`)
   - Responsive HTML design with school branding
   - Mobile-optimized layout
   - Custom message support
   - Professional styling with colors and branding

5. **Django Signals Integration** (`accounts/signals.py`)
   - Automatic activity tracking for invitation events
   - WebSocket broadcasting for real-time updates
   - Cache invalidation for metrics

### Technical Recommendations

#### 1. Application Architecture Decision
**Recommendation: Extend the existing `accounts` app**

**Rationale:**
- Teacher invitations are core to user account management
- Tight integration with existing models (School, TeacherInvitation, SchoolSettings)
- Leverages existing authentication and permission systems
- Maintains single source of truth for user-related functionality

**Implementation:**
```python
# accounts/services/communication_service.py
# accounts/models.py (extend existing models)
# accounts/tasks.py (new file for background tasks)
```

#### 2. Email Template Management with School Branding

**Recommendation: Template inheritance system with dynamic branding**

**Current Template Structure:**
```
templates/
├── emails/
│   ├── base/
│   │   ├── base_email.html           # Base template with dynamic branding
│   │   └── base_email.txt            # Text version base
│   ├── teacher_invitation/
│   │   ├── invitation.html           # Main invitation template
│   │   ├── reminder_1.html           # 24h reminder
│   │   ├── reminder_2.html           # 3-day reminder
│   │   ├── welcome.html              # Post-acceptance welcome
│   │   └── onboarding_progress.html  # Progress updates
│   └── components/
│       ├── school_header.html        # Reusable school branding
│       └── action_buttons.html       # CTA components
```

**Enhanced School Model Fields (already implemented):**
```python
# School model already has:
logo = models.ImageField(upload_to="school_logos/")
primary_color = models.CharField(max_length=7, default="#3B82F6")
secondary_color = models.CharField(max_length=7, default="#1F2937")
email_domain = models.CharField(max_length=100)
```

**Template Context Enhancement:**
```python
def get_template_context(school, invitation):
    return {
        'school_branding': {
            'logo_url': school.logo.url if school.logo else None,
            'primary_color': school.primary_color,
            'secondary_color': school.secondary_color,
            'custom_domain': school.email_domain,
        },
        # ... existing context
    }
```

#### 3. Automated Email Sequence System

**Recommendation: Django background tasks with database-driven sequences**

**Why not Celery initially:**
- No existing Celery infrastructure detected
- Django's database-based task queue is simpler for MVP
- Can migrate to Celery later for scale

**Implementation Strategy:**
```python
# accounts/models.py - New models
class CommunicationTemplate(models.Model):
    """Email template configurations for different touchpoints"""
    name = models.CharField(max_length=100)
    template_type = models.CharField(choices=TEMPLATE_TYPES)
    html_template = models.TextField()
    text_template = models.TextField()
    subject_template = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

class CommunicationSequence(models.Model):
    """Defines automated email sequences"""
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    sequence_type = models.CharField(choices=SEQUENCE_TYPES)
    is_active = models.BooleanField(default=True)

class CommunicationStep(models.Model):
    """Individual steps in a communication sequence"""
    sequence = models.ForeignKey(CommunicationSequence, related_name="steps")
    template = models.ForeignKey(CommunicationTemplate)
    delay_hours = models.PositiveIntegerField()
    trigger_condition = models.CharField(choices=TRIGGER_CONDITIONS)
    order = models.PositiveIntegerField()

class CommunicationLog(models.Model):
    """Track all communications sent"""
    invitation = models.ForeignKey(TeacherInvitation, related_name="communications")
    template = models.ForeignKey(CommunicationTemplate)
    sent_at = models.DateTimeField()
    delivery_status = models.CharField(choices=EMAIL_STATUS_CHOICES)
    opened_at = models.DateTimeField(null=True, blank=True)
```

**Background Task Implementation:**
```python
# accounts/tasks.py
from django_rq import job
from datetime import timedelta
from django.utils import timezone

@job('default', timeout=300)
def process_communication_sequences():
    """Process all pending communication sequences"""
    pending_communications = get_pending_communications()
    for comm in pending_communications:
        send_sequence_email.delay(comm.id)

@job('default', timeout=60)
def send_sequence_email(communication_id):
    """Send individual email in sequence"""
    # Implementation here
```

#### 4. School Customization Models

**Recommendation: Extend existing SchoolSettings model**

```python
# Add to existing SchoolSettings model
class SchoolSettings(models.Model):
    # ... existing fields ...
    
    # Communication preferences (NEW)
    custom_invitation_message = models.TextField(
        blank=True,
        help_text="Default custom message for teacher invitations"
    )
    invitation_email_from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom 'from' name for invitation emails"
    )
    auto_send_reminders = models.BooleanField(
        default=True,
        help_text="Automatically send reminder emails"
    )
    reminder_schedule = models.JSONField(
        default=list,
        help_text="Hours after invitation to send reminders [24, 72, 168]"
    )
    
    # Template customization
    email_signature = models.TextField(
        blank=True,
        help_text="Custom email signature for school communications"
    )
    welcome_message = models.TextField(
        blank=True,
        help_text="Custom welcome message for new teachers"
    )
```

#### 5. Teacher Onboarding Progress Tracking

**Recommendation: Extend existing TeacherProfile completion system**

The system already has:
```python
class TeacherProfile(models.Model):
    profile_completion_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    is_profile_complete = models.BooleanField(default=False)
    last_profile_update = models.DateTimeField(auto_now=True)
```

**Enhancement for Communication Triggers:**
```python
# accounts/services/onboarding_service.py
class OnboardingProgressService:
    
    PROGRESS_MILESTONES = {
        'profile_created': 20,
        'basic_info_complete': 40,
        'subjects_added': 60,
        'availability_set': 80,
        'profile_complete': 100,
    }
    
    @classmethod
    def track_progress_and_trigger_communications(cls, teacher_profile):
        """Track progress and trigger appropriate communications"""
        old_score = teacher_profile.profile_completion_score
        teacher_profile.update_completion_score()
        new_score = teacher_profile.profile_completion_score
        
        # Check for milestone achievements
        milestones_achieved = cls.get_achieved_milestones(old_score, new_score)
        
        for milestone in milestones_achieved:
            cls.trigger_milestone_communication(teacher_profile, milestone)
```

#### 6. Email Delivery Reliability

**Current System Strengths:**
- Email delivery status tracking already implemented
- Retry logic with configurable max attempts
- Failure reason logging

**Enhancements Needed:**
```python
# accounts/services/email_delivery_service.py
class EmailDeliveryService:
    
    @classmethod
    def setup_webhook_handlers(cls):
        """Setup email service provider webhooks for delivery tracking"""
        # Implementation for tracking opens, clicks, bounces
        pass
    
    @classmethod
    def implement_retry_with_backoff(cls, invitation):
        """Implement exponential backoff for failed emails"""
        delay_minutes = 2 ** invitation.retry_count * 30  # 30min, 1hr, 2hr, 4hr
        # Schedule retry
        pass
```

#### 7. Template Inheritance Structure

**Recommended Template Hierarchy:**
```html
<!-- templates/emails/base/base_email.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        :root {
            --primary-color: {{ school_branding.primary_color|default:'#3B82F6' }};
            --secondary-color: {{ school_branding.secondary_color|default:'#1F2937' }};
        }
    </style>
</head>
<body>
    {% include 'emails/components/school_header.html' %}
    
    <div class="email-content">
        {% block content %}{% endblock %}
    </div>
    
    {% include 'emails/components/footer.html' %}
</body>
</html>
```

### Implementation Priority

#### Phase 1: Foundation (Week 1)
1. Extend SchoolSettings for communication preferences
2. Create CommunicationTemplate model and admin interface
3. Enhance email service with template selection

#### Phase 2: Automation (Week 2)
1. Implement CommunicationSequence models
2. Create background task system (django-rq or django-q)
3. Build progress tracking triggers

#### Phase 3: Advanced Features (Week 3)
1. Webhook integration for delivery tracking
2. Advanced template customization
3. Analytics and reporting dashboard

### Potential Challenges

1. **Email Deliverability**: Need to configure proper SPF, DKIM, DMARC records
2. **Template Maintenance**: Complex inheritance could become hard to maintain
3. **Background Task Scaling**: Simple task queue may need Celery upgrade later
4. **Storage**: Email templates and logs will grow over time

### Integration Points

1. **WebSocket Real-time Updates**: Already integrated via signals
2. **Activity Tracking**: Automatic via existing signal handlers
3. **Cache Invalidation**: Already implemented for metrics
4. **API Endpoints**: Leverage existing TeacherInvitationViewSet

### Testing Strategy

1. **Unit Tests**: Template rendering, progress calculation, sequence logic
2. **Integration Tests**: End-to-end email flows
3. **Performance Tests**: Bulk email processing
4. **Email Tests**: Template rendering across email clients

This analysis shows the platform has excellent foundations for the communication system. The recommended approach leverages existing infrastructure while adding minimal complexity.