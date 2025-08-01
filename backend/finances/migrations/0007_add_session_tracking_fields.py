# Generated migration for adding session tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0006_fix_hour_consumption_group_sessions'),
    ]

    operations = [
        migrations.AddField(
            model_name='classsession',
            name='actual_duration_hours',
            field=models.DecimalField(
                blank=True, 
                decimal_places=2, 
                help_text='Actual duration in hours when session was completed', 
                max_digits=4, 
                null=True, 
                verbose_name='actual duration hours'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='booking_confirmed_at',
            field=models.DateTimeField(
                blank=True, 
                help_text='Timestamp when the session booking was confirmed', 
                null=True, 
                verbose_name='booking confirmed at'
            ),
        ),
        migrations.AddField(
            model_name='classsession',
            name='cancelled_at',
            field=models.DateTimeField(
                blank=True, 
                help_text='Timestamp when the session was cancelled', 
                null=True, 
                verbose_name='cancelled at'
            ),
        ),
    ]