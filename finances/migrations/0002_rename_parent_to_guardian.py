# Generated manually to rename Parent/Child to Guardian/Student in finances app

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0001_initial'),
        ('accounts', '0006_rename_parent_to_guardian'),
    ]

    operations = [
        # Remove indices that reference old field names in FamilyBudgetControl
        migrations.RemoveIndex(
            model_name='familybudgetcontrol',
            name='finances_fa_parent__285adc_idx',
        ),
        
        # Remove indices that reference old field names in PurchaseApprovalRequest  
        migrations.RemoveIndex(
            model_name='purchaseapprovalrequest',
            name='finances_pu_parent__fe52d5_idx',
        ),
        migrations.RemoveIndex(
            model_name='purchaseapprovalrequest',
            name='finances_pu_parent__04c2a5_idx',
        ),
        
        # Rename fields in FamilyBudgetControl
        migrations.RenameField(
            model_name='familybudgetcontrol',
            old_name='parent_child_relationship',
            new_name='guardian_student_relationship',
        ),
        
        # Rename fields in PurchaseApprovalRequest
        migrations.RenameField(
            model_name='purchaseapprovalrequest',
            old_name='parent',
            new_name='guardian',
        ),
        migrations.RenameField(
            model_name='purchaseapprovalrequest',
            old_name='parent_child_relationship',
            new_name='guardian_student_relationship',
        ),
        migrations.RenameField(
            model_name='purchaseapprovalrequest',
            old_name='parent_notes',
            new_name='guardian_notes',
        ),
        
        # Add back indices with correct field names for FamilyBudgetControl
        migrations.AddIndex(
            model_name='familybudgetcontrol',
            index=models.Index(fields=['guardian_student_relationship', 'is_active'], name='finances_fa_guardian_idx'),
        ),
        
        # Add back indices with correct field names for PurchaseApprovalRequest
        migrations.AddIndex(
            model_name='purchaseapprovalrequest',
            index=models.Index(fields=['guardian', 'status', '-requested_at'], name='finances_pu_guardian_status_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseapprovalrequest',
            index=models.Index(fields=['guardian_student_relationship', '-requested_at'], name='finances_pu_guardian_rel_idx'),
        ),
    ]