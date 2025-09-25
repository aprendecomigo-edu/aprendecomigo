# Revised Technical Implementation Plan: Multiple Guardians & Students (Issue #304)

## Executive Summary

This revised plan addresses GitHub issue #304 with a simpler approach: **All guardians must have user accounts**, with one designated as primary for billing purposes. This eliminates complexity around account-less guardians while maintaining the core requirements.

## Requirements

1. ✅ Multiple students per guardian (already supported)
2. ✅ Multiple guardians per student (to be implemented)
3. ✅ One primary guardian per student for billing
4. ✅ All guardians have user accounts with magic link authentication

## Simplified Solution

### Core Changes

1. **Keep existing models**: GuardianProfile and CustomUser remain unchanged
2. **Enhance GuardianStudentRelationship**: Add primary flag and permissions
3. **Update StudentProfile**: Replace single guardian ForeignKey with ManyToMany
4. **Maintain data integrity**: Database constraints ensure one primary guardian

## Implementation Details

### 1. Model Updates

#### Update GuardianStudentRelationship Model
```python
class GuardianStudentRelationship(models.Model):
    """Enhanced relationship model for guardian-student connections."""

    guardian_user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='guardian_student_relationships'
    )
    student_user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='student_guardian_relationships'
    )

    # New fields for multiple guardian support
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary guardian handles billing and is main contact"
    )

    # Granular permissions
    can_manage_finances = models.BooleanField(default=False)
    can_book_classes = models.BooleanField(default=True)
    can_view_records = models.BooleanField(default=True)
    can_edit_profile = models.BooleanField(default=True)
    can_receive_notifications = models.BooleanField(default=True)

    # Relationship metadata
    relationship_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., 'Mother', 'Father', 'Legal Guardian'"
    )

    # Existing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_relationships'
    )

    class Meta:
        unique_together = [['guardian_user', 'student_user']]
        indexes = [
            models.Index(fields=['student_user', 'is_primary']),
            models.Index(fields=['guardian_user', 'is_primary']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student_user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_guardian_per_student'
            )
        ]

    def save(self, *args, **kwargs):
        # If this is the primary guardian, update financial permissions
        if self.is_primary:
            self.can_manage_finances = True
        super().save(*args, **kwargs)
```

#### Update StudentProfile Model
```python
class StudentProfile(models.Model):
    # ... existing fields ...

    # DEPRECATED - will be removed after migration
    # guardian = models.ForeignKey(GuardianProfile, ...)

    # NEW - All guardians through enhanced relationship
    guardians = models.ManyToManyField(
        'GuardianProfile',
        through='GuardianStudentRelationship',
        through_fields=('student_user', 'guardian_user'),
        related_name='students_new'  # Temporary name to avoid conflict
    )

    @property
    def primary_guardian(self):
        """Get the primary guardian for backward compatibility."""
        rel = self.user.student_guardian_relationships.filter(is_primary=True).first()
        if rel:
            return GuardianProfile.objects.filter(user=rel.guardian_user).first()
        return None

    @property
    def all_guardians(self):
        """Get all guardians for this student."""
        guardian_users = self.user.student_guardian_relationships.values_list(
            'guardian_user', flat=True
        )
        return GuardianProfile.objects.filter(user__in=guardian_users)
```

### 2. Migration Strategy

#### Step 1: Add new fields to GuardianStudentRelationship
```python
class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='guardianstudentrelationship',
            name='is_primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='guardianstudentrelationship',
            name='can_manage_finances',
            field=models.BooleanField(default=False),
        ),
        # ... other permission fields ...
        migrations.AddConstraint(
            model_name='guardianstudentrelationship',
            constraint=models.UniqueConstraint(
                fields=['student_user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_guardian_per_student'
            ),
        ),
    ]
```

#### Step 2: Data migration for existing guardians
```python
def migrate_existing_guardians(apps, schema_editor):
    """Convert existing single guardian to primary in relationship model."""
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    GuardianStudentRelationship = apps.get_model('accounts', 'GuardianStudentRelationship')

    for student in StudentProfile.objects.exclude(guardian__isnull=True):
        # Check if relationship already exists
        existing_rel = GuardianStudentRelationship.objects.filter(
            student_user=student.user,
            guardian_user=student.guardian.user
        ).first()

        if existing_rel:
            # Update existing relationship to be primary
            existing_rel.is_primary = True
            existing_rel.can_manage_finances = True
            existing_rel.save()
        else:
            # Create new primary relationship
            GuardianStudentRelationship.objects.create(
                student_user=student.user,
                guardian_user=student.guardian.user,
                is_primary=True,
                can_manage_finances=True,
                can_book_classes=True,
                can_view_records=True,
                can_edit_profile=True,
            )

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'XXXX_add_fields'),
    ]

    operations = [
        migrations.RunPython(
            migrate_existing_guardians,
            reverse_code=migrations.RunPython.noop
        ),
    ]
```

#### Step 3: Add ManyToMany field and deprecate old field
```python
class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'XXXX_migrate_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='guardians',
            field=models.ManyToManyField(
                to='accounts.GuardianProfile',
                through='accounts.GuardianStudentRelationship',
                through_fields=('student_user', 'guardian_user'),
                related_name='students_new'
            ),
        ),
        # Keep old field for now, remove in future migration
        migrations.AlterField(
            model_name='studentprofile',
            name='guardian',
            field=models.ForeignKey(
                to='accounts.GuardianProfile',
                on_delete=models.CASCADE,
                null=True,
                blank=True,
                related_name='students_old',
                help_text='DEPRECATED - Use guardians ManyToMany instead'
            ),
        ),
    ]
```

### 3. Business Logic Updates

#### Permission Hierarchy
```python
class GuardianPermissionService:
    """Service for managing guardian permissions."""

    @staticmethod
    def can_manage_student_finances(guardian_user, student_user):
        """Check if guardian can manage student's finances."""
        rel = GuardianStudentRelationship.objects.filter(
            guardian_user=guardian_user,
            student_user=student_user,
            can_manage_finances=True
        ).exists()
        return rel

    @staticmethod
    def can_book_classes(guardian_user, student_user):
        """Check if guardian can book classes for student."""
        rel = GuardianStudentRelationship.objects.filter(
            guardian_user=guardian_user,
            student_user=student_user,
            can_book_classes=True
        ).exists()
        return rel

    @staticmethod
    def get_primary_guardian(student_user):
        """Get primary guardian for a student."""
        rel = GuardianStudentRelationship.objects.filter(
            student_user=student_user,
            is_primary=True
        ).select_related('guardian_user__guardian_profile').first()
        return rel.guardian_user.guardian_profile if rel else None
```

### 4. Form Updates

#### Add Guardian Form
```python
class AddGuardianForm(forms.Form):
    """Form for adding a new guardian to a student."""

    email = forms.EmailField(
        label="Guardian Email",
        help_text="Guardian will receive magic link to set up account"
    )
    name = forms.CharField(max_length=150, label="Guardian Name")
    relationship_type = forms.CharField(
        max_length=50,
        required=False,
        label="Relationship",
        help_text="e.g., Mother, Father, Grandmother"
    )
    is_primary = forms.BooleanField(
        required=False,
        label="Set as Primary Guardian",
        help_text="Primary guardian handles billing and is main contact"
    )

    # Permissions (only shown if not primary)
    can_book_classes = forms.BooleanField(
        initial=True,
        required=False,
        label="Can book/cancel classes"
    )
    can_view_records = forms.BooleanField(
        initial=True,
        required=False,
        label="Can view academic records"
    )
    can_edit_profile = forms.BooleanField(
        initial=True,
        required=False,
        label="Can edit student profile"
    )

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student

        # Check if student already has a primary guardian
        if student and GuardianStudentRelationship.objects.filter(
            student_user=student.user,
            is_primary=True
        ).exists():
            # Hide primary option if student already has one
            self.fields['is_primary'].widget = forms.HiddenInput()
            self.fields['is_primary'].initial = False
```

### 5. View Updates

#### Guardian Management Views
```python
@login_required
def manage_student_guardians(request, student_id):
    """View for managing a student's guardians."""
    student = get_object_or_404(StudentProfile, id=student_id)

    # Check permissions
    if not request.user.has_role(Role.ADMIN):
        current_rel = GuardianStudentRelationship.objects.filter(
            guardian_user=request.user,
            student_user=student.user,
            is_primary=True
        ).exists()
        if not current_rel:
            raise PermissionDenied

    guardians = GuardianStudentRelationship.objects.filter(
        student_user=student.user
    ).select_related('guardian_user__guardian_profile')

    if request.method == 'POST':
        form = AddGuardianForm(request.POST, student=student)
        if form.is_valid():
            # Create or get guardian user
            guardian_user, created = CustomUser.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={'name': form.cleaned_data['name']}
            )

            # Create guardian profile if needed
            if created:
                GuardianProfile.objects.create(user=guardian_user)
                # Send magic link invitation
                send_guardian_invitation(guardian_user, student)

            # Create relationship
            rel, created = GuardianStudentRelationship.objects.get_or_create(
                guardian_user=guardian_user,
                student_user=student.user,
                defaults={
                    'is_primary': form.cleaned_data['is_primary'],
                    'can_book_classes': form.cleaned_data['can_book_classes'],
                    'can_view_records': form.cleaned_data['can_view_records'],
                    'can_edit_profile': form.cleaned_data['can_edit_profile'],
                    'relationship_type': form.cleaned_data.get('relationship_type', ''),
                    'created_by': request.user,
                }
            )

            if created:
                messages.success(request, f"Guardian {guardian_user.name} added successfully")
            else:
                messages.info(request, f"Guardian {guardian_user.name} already linked to this student")

            return redirect('manage_student_guardians', student_id=student_id)
    else:
        form = AddGuardianForm(student=student)

    return render(request, 'accounts/manage_guardians.html', {
        'student': student,
        'guardians': guardians,
        'form': form,
    })
```

### 6. Template Updates

```html
<!-- templates/accounts/manage_guardians.html -->
<div class="container mx-auto p-4">
    <h2 class="text-2xl font-bold mb-4">
        Manage Guardians for {{ student.user.name }}
    </h2>

    <!-- Current Guardians -->
    <div class="mb-8">
        <h3 class="text-lg font-semibold mb-2">Current Guardians</h3>
        <div class="space-y-2">
            {% for rel in guardians %}
            <div class="border rounded p-4 {% if rel.is_primary %}border-blue-500 bg-blue-50{% endif %}">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="font-medium">
                            {{ rel.guardian_user.name }}
                            {% if rel.is_primary %}
                            <span class="ml-2 px-2 py-1 bg-blue-500 text-white text-xs rounded">PRIMARY</span>
                            {% endif %}
                        </p>
                        <p class="text-sm text-gray-600">{{ rel.guardian_user.email }}</p>
                        {% if rel.relationship_type %}
                        <p class="text-sm text-gray-500">{{ rel.relationship_type }}</p>
                        {% endif %}
                    </div>
                    <div class="text-sm">
                        <p>Permissions:</p>
                        <ul class="text-gray-600">
                            {% if rel.can_manage_finances %}<li>✓ Manage Finances</li>{% endif %}
                            {% if rel.can_book_classes %}<li>✓ Book Classes</li>{% endif %}
                            {% if rel.can_view_records %}<li>✓ View Records</li>{% endif %}
                            {% if rel.can_edit_profile %}<li>✓ Edit Profile</li>{% endif %}
                        </ul>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Add New Guardian Form -->
    <div class="border rounded p-4">
        <h3 class="text-lg font-semibold mb-4">Add New Guardian</h3>
        <form method="post" class="space-y-4">
            {% csrf_token %}
            {{ form.as_div }}
            <button type="submit" class="btn btn-primary">
                Add Guardian
            </button>
        </form>
    </div>
</div>
```

## Testing Plan

1. **Unit Tests**: Test new model methods and constraints
2. **Migration Tests**: Ensure data migration handles all edge cases
3. **Permission Tests**: Verify permission checks work correctly
4. **Integration Tests**: Test full workflow of adding/managing guardians
5. **UI Tests**: Ensure forms and templates work as expected

## Rollback Plan

If issues arise:
1. The old `guardian` field is kept temporarily for backward compatibility
2. Data migration is reversible
3. Can quickly revert to single guardian model if needed

## Success Criteria

1. ✅ Students can have multiple guardians
2. ✅ Each student has exactly one primary guardian
3. ✅ Guardians can manage multiple students
4. ✅ Permission system works correctly
5. ✅ All existing functionality remains intact
6. ✅ Migration completes without data loss
