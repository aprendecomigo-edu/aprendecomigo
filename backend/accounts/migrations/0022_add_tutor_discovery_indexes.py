# Generated manually for GitHub Issue #74 - Tutor Discovery Performance Indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_alter_schoolsettings_options_and_more'),
    ]

    operations = [
        # Tutor discovery performance indexes
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_teacher_profile_completion ON accounts_teacherprofile(is_profile_complete, profile_completion_score);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_profile_completion;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_teacher_profile_rate ON accounts_teacherprofile(hourly_rate);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_profile_rate;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_teacher_course_active_rate ON accounts_teachercourse(is_active, hourly_rate);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_course_active_rate;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_course_educational_system_level ON accounts_course(educational_system_id, education_level);",
            reverse_sql="DROP INDEX IF EXISTS idx_course_educational_system_level;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_school_membership_role_active ON accounts_schoolmembership(role, is_active, school_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_school_membership_role_active;"
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_teacher_profile_activity ON accounts_teacherprofile(last_activity);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_profile_activity;"
        ),
    ]