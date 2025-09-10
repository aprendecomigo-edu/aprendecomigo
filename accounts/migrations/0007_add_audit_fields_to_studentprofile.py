# Generated manually to add audit fields to StudentProfile

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_rename_parent_to_guardian'),
    ]

    operations = [
        # Add created_at field with default value
        migrations.AddField(
            model_name='studentprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        
        # Add updated_at field with default value
        migrations.AddField(
            model_name='studentprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]