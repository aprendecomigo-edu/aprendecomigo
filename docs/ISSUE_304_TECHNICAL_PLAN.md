# Technical Implementation Plan: Multiple Guardians & Students (Issue #304)

## Executive Summary

This plan addresses GitHub issue #304: Supporting **multiple guardians per student** and **multiple students per guardian**. The approach prioritizes simplicity by using a single, unified relationship model that handles all guardian-student connections.

## Current State Analysis

### Existing Architecture
- **StudentProfile.guardian**: ForeignKey to GuardianProfile (single guardian)
- **GuardianProfile**: One-to-one with User, requires account
- **GuardianStudentRelationship**: Exists but designed for user-to-user relationships
- **Account Types**: STUDENT_GUARDIAN, ADULT_STUDENT, GUARDIAN_ONLY

### Key Requirements from Issue #304
1. ✅ Multiple students per guardian (already supported via ForeignKey)
2. ❌ Multiple guardians per student (needs implementation)
3. ❌ Guardians without user accounts (additional guardians may not login)

## Proposed Solution: Unified Guardian-Student Relationships

### Core Concept
- **Single ManyToMany relationship** for ALL guardian-student connections
- **Guardians can exist with or without user accounts**
- **One guardian marked as primary** for billing/main contact
- **Simplified logic** - all relationships go through same model

## Implementation Details

### 1. New Models Structure (`accounts/models/profiles.py`)

```python
class Guardian(models.Model):
    """
    Guardian model that can exist with or without a user account.
    Replaces direct dependency on GuardianProfile.
    """
    # Optional user account (null for guardians without login)
    user = models.OneToOneField(
        'CustomUser',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='guardian'
    )

    # Guardian information (always required)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    # Financial/billing info (only for primary guardians)
    address = models.TextField(blank=True)
    tax_nr = models.CharField(max_length=20, blank=True)
    invoice = models.BooleanField(default=False)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
        ]

class StudentGuardianRelation(models.Model):
    """Through model for ALL guardian-student relationships."""

    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    guardian = models.ForeignKey('Guardian', on_delete=models.CASCADE)

    # Primary guardian handles billing and main contact
    is_primary = models.BooleanField(default=False)

    # Permissions (only relevant if guardian has user account)
    can_manage_finances = models.BooleanField(default=False)
    can_book_classes = models.BooleanField(default=True)
    can_view_records = models.BooleanField(default=True)
    can_edit_profile = models.BooleanField(default=True)

    # Relationship info
    relationship_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., 'Mother', 'Father', 'Legal Guardian'"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = [['student', 'guardian']]
        indexes = [
            models.Index(fields=['student', 'is_primary']),
            models.Index(fields=['guardian', 'is_primary']),
        ]
        # Ensure only one primary guardian per student
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=models.Q(is_primary=True),
                name='unique_primary_guardian_per_student'
            )
        ]

class StudentProfile(models.Model):
    # ... existing fields ...

    # DEPRECATE: guardian = models.ForeignKey(...)

    # NEW: All guardians through ManyToMany
    guardians = models.ManyToManyField(
        'Guardian',
        through='StudentGuardianRelation',
        related_name='students'
    )

    @property
    def primary_guardian(self):
        """Get the primary guardian for backward compatibility."""
        relation = self.studentguardianrelation_set.filter(is_primary=True).first()
        return relation.guardian if relation else None
```

### 2. Migration Strategy

```python
# Step 1: Create new models
class Migration(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='Guardian',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('user', models.OneToOneField(null=True, blank=True...)),
                ('name', models.CharField(max_length=150)),
                ('email', models.EmailField()),
                # ... other fields
            ],
        ),
        migrations.CreateModel(
            name='StudentGuardianRelation',
            fields=[
                ('student', models.ForeignKey('StudentProfile'...)),
                ('guardian', models.ForeignKey('Guardian'...)),
                ('is_primary', models.BooleanField(default=False)),
                # ... other fields
            ],
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='guardians',
            field=models.ManyToManyField(through='StudentGuardianRelation'...),
        ),
    ]

# Step 2: Data migration to convert existing guardians
def migrate_existing_guardians(apps, schema_editor):
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    Guardian = apps.get_model('accounts', 'Guardian')
    StudentGuardianRelation = apps.get_model('accounts', 'StudentGuardianRelation')

    for student in StudentProfile.objects.exclude(guardian__isnull=True):
        # Create Guardian from existing GuardianProfile
        old_guardian_profile = student.guardian
        new_guardian = Guardian.objects.create(
            user=old_guardian_profile.user,
            name=old_guardian_profile.user.name,
            email=old_guardian_profile.user.email,
            # ... copy other fields
        )

        # Create primary relationship
        StudentGuardianRelation.objects.create(
            student=student,
            guardian=new_guardian,
            is_primary=True,
            can_manage_finances=True,
        )

# Step 3: Remove old guardian field
migrations.RemoveField(
    model_name='studentprofile',
    name='guardian',
)

### 3. Form Updates

#### Guardian Forms (`accounts/forms.py`)
```python
class GuardianForm(forms.ModelForm):
    """Form for creating/editing a guardian."""

    # Choice field to determine if guardian should have account
    has_account = forms.BooleanField(
        required=False,
        label="Guardian can login to the system",
        help_text="Check if this guardian should have their own account"
    )

    class Meta:
        model = Guardian
        fields = ['name', 'email', 'phone', 'relationship_type']

    def save(self, commit=True):
        guardian = super().save(commit=False)

        # Only create user account if has_account is True
        if self.cleaned_data['has_account'] and not guardian.user:
            # Create user account for guardian
            user = CustomUser.objects.create_user(
                email=guardian.email,
                name=guardian.name,
                is_active=True
            )
            guardian.user = user

        if commit:
            guardian.save()
        return guardian


GuardianFormSet = forms.inlineformset_factory(
    StudentProfile,
    StudentGuardianRelation,
    form=GuardianForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
```

#### Template Updates (`templates/accounts/add_student.html`)
```html
<div class="guardian-section">
    <h3>Guardians</h3>

    <!-- Primary Guardian (Required) -->
    <div class="card mb-4 border-primary">
        <div class="card-header bg-primary text-white">
            Primary Guardian (Billing Contact)
        </div>
        <div class="card-body">
            <div class="form-group">
                <label>Name *</label>
                <input type="text" name="guardian_0_name" required>
            </div>
            <div class="form-group">
                <label>Email *</label>
                <input type="email" name="guardian_0_email" required>
            </div>
            <div class="form-check">
                <input type="checkbox" name="guardian_0_has_account" checked>
                <label>Create login account for this guardian</label>
            </div>
            <!-- Billing fields only for primary -->
            <div class="billing-fields">
                <label>Tax Number</label>
                <input type="text" name="guardian_0_tax_nr">
                <!-- ... other billing fields -->
            </div>
        </div>
    </div>

    <!-- Additional Guardians -->
    <div id="additional-guardians">
        <!-- Dynamic forms added here -->
    </div>

    <button type="button" class="btn btn-outline-primary" onclick="addGuardian()">
        + Add Another Guardian
    </button>
</div>

<script>
function addGuardian() {
    const template = `
        <div class="card mb-3">
            <div class="card-header">Additional Guardian</div>
            <div class="card-body">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="guardian_${index}_name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="guardian_${index}_email">
                </div>
                <div class="form-check">
                    <input type="checkbox" name="guardian_${index}_has_account">
                    <label>Create login account</label>
                </div>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeGuardian(this)">
                    Remove
                </button>
            </div>
        </div>
    `;
    // Add to DOM
}
</script>

### 4. View Updates

#### Guardian Dashboard View
```python
def guardian_dashboard(request):
    """Show all students this guardian manages."""
    guardian = Guardian.objects.get(user=request.user)

    # Get all student relationships
    relationships = StudentGuardianRelation.objects.filter(
        guardian=guardian
    ).select_related('student')

    students = []
    for rel in relationships:
        students.append({
            'student': rel.student,
            'is_primary': rel.is_primary,
            'can_manage_finances': rel.can_manage_finances,
            'relationship_type': rel.relationship_type
        })

    return render(request, 'guardian_dashboard.html', {
        'students': students
    })
```

#### Student Detail View
```python
def student_detail(request, student_id):
    """Show student with all their guardians."""
    student = StudentProfile.objects.get(id=student_id)

    guardians = StudentGuardianRelation.objects.filter(
        student=student
    ).select_related('guardian').order_by('-is_primary')

    return render(request, 'student_detail.html', {
        'student': student,
        'guardians': guardians
    })
```

### 5. Business Logic Rules

| Feature | Primary Guardian | Additional Guardian (w/ account) | Additional Guardian (no account) |
|---------|-----------------|----------------------------------|-----------------------------------|
| Has login access | ✅ | ✅ | ❌ |
| View student profile | ✅ | ✅ | N/A (can't login) |
| Edit student info | ✅ | ✅ | N/A |
| Receive email notifications | ✅ | ✅ | ✅ |
| Book classes | ✅ | ✅ | N/A |
| Handle billing/invoices | ✅ | ❌ | ❌ |
| View financial records | ✅ | Configurable | N/A |
| Delete student account | ✅ | ❌ | ❌ |

### Key Simplifications:
1. **One Primary Guardian**: Always required, always has account, handles all billing
2. **Additional Guardians**: Optional, may or may not have accounts
3. **Guardians without accounts**: Only receive notifications, can't access system
4. **Single Source of Truth**: All relationships go through StudentGuardianRelation

## Simplified Functional Requirements Update

### Student-Guardian Multi-Account System

#### Account Types Remain Unchanged:
1. **Student + Guardian** - Both have separate accounts
2. **Guardian-Only** - Guardian manages student profile (student has no account)
3. **Adult Student** - Self-managed student account

#### NEW: Multiple Guardian Support

**Guardian Types:**
- **Primary Guardian** (1 required per student)
  - Has user account (always)
  - Handles all billing and invoicing
  - Full access to student management
  - Receives all notifications

- **Additional Guardians** (0 or more per student)
  - May have user account (admin decides)
  - If account: Can view/book classes, edit profile
  - If no account: Only receives email notifications
  - Cannot handle financial matters

**Multiple Students per Guardian:**
- Any guardian (with account) can manage multiple students
- Guardian dashboard shows all linked students
- Clear visual distinction for primary vs additional role

**Registration Flow Updates:**
1. Admin creates student with primary guardian (required)
2. Admin can add additional guardians:
   - Toggle: "Create login account" for each guardian
   - If yes: Guardian gets magic link invitation
   - If no: Guardian only stored for notifications
3. All guardians receive welcome emails

**Permission Model:**
```
Primary Guardian:
- Full access to all student features
- Billing and payment management
- Can add/remove other guardians

Additional Guardian (with account):
- View student profile and schedule
- Book/cancel classes (if permitted)
- Edit student information (if permitted)
- NO billing access

Additional Guardian (without account):
- Receives email notifications only
- No system access
```

## Implementation Benefits

### Simplified Code:
- Single Guardian model (with optional user)
- Single relationship model (StudentGuardianRelation)
- Clear is_primary flag for business logic
- No complex branching for guardian types

### Simplified UX:
- Clear "Primary" badge in UI
- Simple "Add Guardian" button
- Checkbox: "Allow login" for each guardian
- Consistent guardian management interface

### Simplified Data Model:
```
Guardian (id, user?, name, email, phone...)
    ↕ (ManyToMany through StudentGuardianRelation)
StudentProfile (id, name, birth_date...)

StudentGuardianRelation:
- student_id
- guardian_id
- is_primary (only one per student)
- permissions (if guardian has account)
```

## Summary

This approach dramatically simplifies the implementation while meeting all requirements:
- ✅ Multiple guardians per student
- ✅ Multiple students per guardian
- ✅ Guardians with/without accounts
- ✅ Clear primary guardian for billing
- ✅ Simple, maintainable code structure
