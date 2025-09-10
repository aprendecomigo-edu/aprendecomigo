# Generated manually to rename Parent/Child to Guardian/Student

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_teacherinvitation_unique_active_teacher_invitation_per_school_and_more'),
    ]

    operations = [
        # Remove old indices that reference 'parent' and 'child' fields
        migrations.RemoveIndex(
            model_name='parentchildrelationship',
            name='accounts_pa_parent__8eb724_idx',
        ),
        migrations.RemoveIndex(
            model_name='parentchildrelationship',
            name='accounts_pa_child_i_02dd2c_idx',
        ),
        migrations.RemoveIndex(
            model_name='parentchildrelationship',
            name='accounts_pa_school__f500a3_idx',
        ),
        
        # Remove old unique_together constraint
        migrations.AlterUniqueTogether(
            name='parentchildrelationship',
            unique_together=set(),
        ),
        
        # Remove the old constraint that references 'parent'
        migrations.RemoveConstraint(
            model_name='parentchildrelationship',
            name='parent_cannot_be_child',
        ),
        
        # Rename the model from ParentChildRelationship to GuardianStudentRelationship
        migrations.RenameModel(
            old_name='ParentChildRelationship',
            new_name='GuardianStudentRelationship',
        ),
        
        # Rename fields in GuardianStudentRelationship
        migrations.RenameField(
            model_name='guardianstudentrelationship',
            old_name='parent',
            new_name='guardian',
        ),
        migrations.RenameField(
            model_name='guardianstudentrelationship',
            old_name='child',
            new_name='student',
        ),
        
        # Add back the indices with correct field names
        migrations.AddIndex(
            model_name='guardianstudentrelationship',
            index=models.Index(fields=['guardian', 'is_active'], name='accounts_gu_guardia_idx'),
        ),
        migrations.AddIndex(
            model_name='guardianstudentrelationship',
            index=models.Index(fields=['student', 'is_active'], name='accounts_gu_student_idx'),
        ),
        migrations.AddIndex(
            model_name='guardianstudentrelationship',
            index=models.Index(fields=['school', 'is_active'], name='accounts_gu_school_idx'),
        ),
        
        # Add back unique_together with correct field names
        migrations.AlterUniqueTogether(
            name='guardianstudentrelationship',
            unique_together={('guardian', 'student', 'school')},
        ),
        
        # Add the new constraint with correct field names
        migrations.AddConstraint(
            model_name='guardianstudentrelationship',
            constraint=models.CheckConstraint(
                check=~models.Q(guardian=models.F('student')),
                name='guardian_cannot_be_student'
            ),
        ),
        
        # Update SchoolRole enum value from PARENT to GUARDIAN
        migrations.RunSQL(
            "UPDATE accounts_schoolmembership SET role = 'guardian' WHERE role = 'parent';",
            "UPDATE accounts_schoolmembership SET role = 'parent' WHERE role = 'guardian';"
        ),
    ]