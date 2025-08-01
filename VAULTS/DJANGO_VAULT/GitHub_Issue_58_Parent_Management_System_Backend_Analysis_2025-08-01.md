# GitHub Issue #58: Parent Management System - Backend Analysis

**Date:** 2025-08-01  
**Issue:** Parent Management System Implementation  
**Focus:** Backend infrastructure and API design  

## Executive Summary

The parent management system represents a significant expansion of the Aprende Comigo platform, introducing family account hierarchies, spending controls, and approval workflows. The existing system has solid foundations but requires new models, relationships, and API endpoints to support comprehensive parent oversight capabilities.

## Current System Analysis

### Existing Infrastructure (Strengths)

1. **Multi-role User System**: Already supports SCHOOL_OWNER, SCHOOL_ADMIN, TEACHER, SCHOOL_STAFF, STUDENT roles
2. **Payment Infrastructure**: Sophisticated Stripe integration with StudentAccountBalance, PurchaseTransaction, and HourConsumption models
3. **School Settings**: `require_parent_approval` field already exists, indicating prior consideration of parent functionality
4. **Session Management**: Comprehensive ClassSession model with status tracking and hour deduction
5. **Multi-tenancy**: School-based permissions and data isolation already implemented

### Current Gaps for Parent Management

1. **No PARENT Role**: Missing from SchoolRole enum
2. **No Parent-Child Relationships**: No family structure models
3. **No Spending Controls**: No budget limits or approval workflows
4. **No Parent Notifications**: No parent-specific communication system
5. **No Oversight Dashboard**: No parent view of child activities

## Required Backend Infrastructure

### 1. New Models and Database Relationships

#### A. Enhanced Role System
```python
# Addition to SchoolRole enum in accounts/models.py
class SchoolRole(models.TextChoices):
    # ... existing roles
    PARENT = "parent", _("Parent")  # NEW ROLE
```

#### B. Parent Profile Model
```python
class ParentProfile(models.Model):
    """
    Parent profile with family management capabilities.
    A user can be a parent managing multiple children across different schools.
    """
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="parent_profile"
    )
    
    # Contact and verification
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[("email", "Email"), ("sms", "SMS"), ("both", "Both")],
        default="email"
    )
    
    # Payment settings
    default_payment_method_id = models.CharField(max_length=255, blank=True)  # Stripe PM ID
    billing_address = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### C. Parent-Child Relationship Model
```python
class ParentChildRelationship(models.Model):
    """
    Links parents to their children with relationship type and permissions.
    Supports multiple parents per child (separated parents, guardians).
    """
    
    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="child_relationships"
    )
    child = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="parent_relationships"
    )
    
    relationship_type = models.CharField(
        max_length=20,
        choices=[
            ("parent", "Parent"),
            ("guardian", "Legal Guardian"),
            ("stepparent", "Step Parent"),
            ("grandparent", "Grandparent"),
            ("other", "Other")
        ]
    )
    
    # Permissions for this parent-child relationship
    can_approve_purchases = models.BooleanField(default=True)
    can_schedule_sessions = models.BooleanField(default=True)
    can_view_progress = models.BooleanField(default=True)
    can_communicate_with_teachers = models.BooleanField(default=True)
    
    is_primary = models.BooleanField(default=False)  # Primary contact parent
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ["parent", "child"]
        constraints = [
            models.UniqueConstraint(
                fields=["child"],
                condition=models.Q(is_primary=True),
                name="unique_primary_parent_per_child"
            )
        ]
```

#### D. Family Budget Control Model
```python
class FamilyBudgetControl(models.Model):
    """
    Budget controls and spending limits for family accounts.
    Allows parents to set monthly/weekly limits and approval thresholds.
    """
    
    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="budget_controls"
    )
    child = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="budget_controls"
    )
    
    # Budget limits
    monthly_limit = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly spending limit in euros"
    )
    weekly_limit = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weekly spending limit in euros"
    )
    
    # Approval thresholds
    approval_threshold = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount requiring parent approval"
    )
    
    # Auto-approval settings
    auto_approve_up_to = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Auto-approve purchases up to this amount"
    )
    
    # Current period tracking
    current_month_spent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    current_week_spent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ["parent", "child"]
```

#### E. Purchase Approval Workflow Model
```python
class PurchaseApprovalRequest(models.Model):
    """
    Approval requests for child purchases requiring parent consent.
    """
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("expired", "Expired"),
    ]
    
    child = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="purchase_requests"
    )
    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="approval_requests"
    )
    
    # Purchase details
    pricing_plan = models.ForeignKey(
        'finances.PricingPlan',
        on_delete=models.CASCADE,
        related_name="approval_requests"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Request details
    child_message = models.TextField(blank=True, help_text="Message from child")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    # Response details
    parent_response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()  # Auto-expire after X days
    
    # Related transaction (created after approval)
    purchase_transaction = models.OneToOneField(
        'finances.PurchaseTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_request"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### F. Enhanced Student Account Balance (Modifications)
```python
# Add to existing StudentAccountBalance model
class StudentAccountBalance(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS for parent oversight
    is_managed_by_parent = models.BooleanField(default=False)
    parent_manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_student_accounts"
    )
    requires_approval_for_purchases = models.BooleanField(default=False)
```

### 2. Key API Endpoints Required

#### A. Parent Management Endpoints
```python
# accounts/urls.py additions
router.register(r"parents", ParentViewSet, basename="parent")
router.register(r"parent-child-relationships", ParentChildRelationshipViewSet, basename="parent-child")
router.register(r"family-budget-controls", FamilyBudgetControlViewSet, basename="family-budget")
router.register(r"purchase-approval-requests", PurchaseApprovalRequestViewSet, basename="purchase-approval")

# Additional endpoints
path("parents/<int:parent_id>/children/", ParentChildrenListView.as_view(), name="parent-children"),
path("parents/<int:parent_id>/dashboard/", ParentDashboardView.as_view(), name="parent-dashboard"),
path("parents/spending-summary/<int:child_id>/", ParentSpendingSummaryView.as_view(), name="parent-spending-summary"),
```

#### B. Child-Initiated Purchase Flow
```python
path("students/<int:student_id>/request-purchase/", StudentPurchaseRequestView.as_view(), name="student-purchase-request"),
path("students/<int:student_id>/purchase-history/", StudentPurchaseHistoryView.as_view(), name="student-purchase-history"),
```

#### C. Parent Approval Workflow
```python
path("purchase-approvals/<int:request_id>/approve/", ApprovePurchaseView.as_view(), name="approve-purchase"),
path("purchase-approvals/<int:request_id>/deny/", DenyPurchaseView.as_view(), name="deny-purchase"),
```

### 3. Main Technical Challenges and Considerations

#### A. Multi-Parent Scenarios
**Challenge**: Children with separated parents or multiple guardians  
**Solution**: 
- Support multiple ParentChildRelationship records per child
- Primary parent designation for billing
- Permission-based access control per relationship

#### B. Cross-School Family Management
**Challenge**: Parents managing children across different schools  
**Solution**:
- Parent profiles independent of school membership
- School-specific budget controls and permissions
- Aggregated family dashboard across schools

#### C. Payment Method Management
**Challenge**: Parent payment methods for child purchases  
**Solution**:
- Stripe Customer/PaymentMethod linking in ParentProfile
- Default payment method inheritance for child purchases
- Parent approval required for payment method changes

#### D. Session Scheduling Oversight
**Challenge**: Parent approval for session bookings  
**Solution**:
- Extended ClassSession model with approval fields
- Parent notification system for session bookings
- Approval workflow integration with existing session management

#### E. Progress Tracking Access
**Challenge**: Parent access to child's academic progress  
**Solution**:
- Enhanced permissions in StudentProgress model
- Parent-specific progress report API endpoints
- Privacy controls for sensitive academic information

### 4. Integration with Current Authentication System

#### A. Enhanced Permission System
```python
# accounts/permissions.py additions
class IsParentOfStudent(BasePermission):
    """Permission class to check if user is parent of the student"""
    
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'parent_profile'):
            return False
        
        return ParentChildRelationship.objects.filter(
            parent=request.user,
            child=obj,
            is_active=True
        ).exists()

class CanManageChildPurchases(BasePermission):
    """Permission to check if parent can manage child's purchases"""
    
    def has_object_permission(self, request, view, obj):
        relationship = ParentChildRelationship.objects.filter(
            parent=request.user,
            child=obj,
            is_active=True
        ).first()
        
        return relationship and relationship.can_approve_purchases
```

#### B. Enhanced User Serializer
```python
# accounts/serializers.py modifications
class UserSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    is_parent = serializers.SerializerMethodField()
    managed_children = serializers.SerializerMethodField()
    parent_managers = serializers.SerializerMethodField()
    
    def get_is_parent(self, obj):
        return hasattr(obj, 'parent_profile')
    
    def get_managed_children(self, obj):
        """Get children managed by this parent"""
        if hasattr(obj, 'parent_profile'):
            relationships = obj.child_relationships.filter(is_active=True)
            return [rel.child.id for rel in relationships]
        return []
    
    def get_parent_managers(self, obj):
        """Get parents managing this user (if they're a student)"""
        if obj.school_memberships.filter(role=SchoolRole.STUDENT).exists():
            relationships = obj.parent_relationships.filter(is_active=True)
            return [rel.parent.id for rel in relationships]
        return []
```

## Implementation Priority

### Phase 1: Core Infrastructure (Week 1-2)
1. Add PARENT role to SchoolRole enum
2. Create ParentProfile and ParentChildRelationship models
3. Basic parent-child linking API endpoints
4. Enhanced permissions system

### Phase 2: Budget Controls (Week 3-4)
1. FamilyBudgetControl model
2. Purchase approval workflow models
3. Budget tracking and limit enforcement
4. Basic parent dashboard API

### Phase 3: Full Approval Workflow (Week 5-6)
1. Complete purchase approval request system
2. Parent notification system integration
3. Session scheduling oversight
4. Progress tracking access controls

### Phase 4: Advanced Features (Week 7-8)
1. Multi-parent scenario handling
2. Cross-school family management
3. Advanced reporting and analytics
4. Mobile app integration APIs

## Security Considerations

1. **Data Privacy**: Parent access must respect child privacy settings and school policies
2. **Financial Security**: Strong authentication required for purchase approvals
3. **Cross-School Data**: Ensure proper data isolation between schools
4. **Audit Trails**: Comprehensive logging of all parent actions and approvals
5. **GDPR Compliance**: Parent consent and data processing transparency

## Testing Strategy

1. **Unit Tests**: All new models and business logic
2. **Integration Tests**: Parent-child relationship workflows
3. **API Tests**: All new endpoints with permission scenarios
4. **End-to-End Tests**: Complete purchase approval workflows
5. **Performance Tests**: Family dashboard queries with multiple children

## Next Steps

1. **Database Migration Planning**: Design migrations for new models and role additions
2. **API Design Review**: Finalize endpoint specifications with frontend team
3. **Security Review**: Validate permission system with security team
4. **UI/UX Coordination**: Ensure backend APIs support planned frontend features
5. **Deployment Strategy**: Plan staged rollout with feature flags

---

**Status**: Analysis Complete - Ready for Implementation Planning  
**Estimated Effort**: 6-8 weeks for complete backend infrastructure  
**Dependencies**: None - can proceed independently  
**Risk Level**: Medium - significant new functionality but builds on solid existing foundation