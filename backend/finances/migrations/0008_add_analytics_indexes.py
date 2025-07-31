# Generated manually for GitHub Issue #74 - Analytics Performance Indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0007_add_session_tracking_fields'),
    ]

    operations = [
        # Analytics performance indexes for tutor analytics
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_class_session_teacher_date ON finances_classsession(teacher_id, date);",
            reverse_sql="DROP INDEX IF EXISTS idx_class_session_teacher_date;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_class_session_school_status ON finances_classsession(school_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_class_session_school_status;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_purchase_transaction_student_created ON finances_purchasetransaction(student_id, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_purchase_transaction_student_created;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_teacher_payment_entry_teacher_school ON finances_teacherpaymententry(teacher_id, school_id, billing_period);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_payment_entry_teacher_school;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_class_session_date_status ON finances_classsession(date, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_class_session_date_status;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_class_session_session_type ON finances_classsession(session_type, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_class_session_session_type;"
        ),
    ]