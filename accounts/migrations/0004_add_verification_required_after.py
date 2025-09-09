# Generated manually for progressive verification feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_remove_teacherinvitation_unique_active_teacher_invitation_per_school_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="verification_required_after",
            field=models.DateTimeField(
                blank=True,
                help_text="After this time, user must verify email/phone to continue accessing the platform",
                null=True,
                verbose_name="verification required after",
            ),
        ),
    ]