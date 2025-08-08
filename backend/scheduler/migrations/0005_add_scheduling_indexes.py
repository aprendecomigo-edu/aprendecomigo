# Generated for GitHub Issue #152 - Scheduling Rules Performance Optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0004_classschedule_actual_duration_minutes_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Add indexes for frequently queried combinations
            sql=[
                "CREATE INDEX IF NOT EXISTS idx_classschedule_teacher_school_date_status ON scheduler_classschedule(teacher_id, school_id, scheduled_date, status);",
                "CREATE INDEX IF NOT EXISTS idx_classschedule_student_date_status ON scheduler_classschedule(student_id, scheduled_date, status);",
                "CREATE INDEX IF NOT EXISTS idx_classschedule_date_time_range ON scheduler_classschedule(scheduled_date, start_time, end_time);",
                "CREATE INDEX IF NOT EXISTS idx_teacheravailability_teacher_school_day ON scheduler_teacheravailability(teacher_id, school_id, day_of_week, is_active);",
                "CREATE INDEX IF NOT EXISTS idx_teacherunavailability_teacher_date ON scheduler_teacherunavailability(teacher_id, school_id, date);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS idx_classschedule_teacher_school_date_status;",
                "DROP INDEX IF EXISTS idx_classschedule_student_date_status;", 
                "DROP INDEX IF EXISTS idx_classschedule_date_time_range;",
                "DROP INDEX IF EXISTS idx_teacheravailability_teacher_school_day;",
                "DROP INDEX IF EXISTS idx_teacherunavailability_teacher_date;",
            ]
        ),
    ]