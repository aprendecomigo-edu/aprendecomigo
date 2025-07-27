# Generated manually for PricingPlan model

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_hourconsumption'),
    ]

    operations = [
        migrations.CreateModel(
            name='PricingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Display name for the pricing plan', max_length=100, verbose_name='plan name')),
                ('description', models.TextField(help_text='Detailed description of what the plan includes', verbose_name='description')),
                ('plan_type', models.CharField(choices=[('package', 'Package'), ('subscription', 'Subscription')], help_text='Type of plan: package (expires) or subscription (recurring)', max_length=20, verbose_name='plan type')),
                ('hours_included', models.DecimalField(decimal_places=2, help_text='Number of tutoring hours included in this plan', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='hours included')),
                ('price_eur', models.DecimalField(decimal_places=2, help_text='Price of the plan in euros', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='price (EUR)')),
                ('validity_days', models.PositiveIntegerField(blank=True, help_text='Number of days the plan is valid (null for subscriptions)', null=True, validators=[django.core.validators.MinValueValidator(1)], verbose_name='validity days')),
                ('display_order', models.PositiveIntegerField(default=1, help_text='Order in which plans should be displayed (lower numbers first)', verbose_name='display order')),
                ('is_featured', models.BooleanField(default=False, help_text='Whether this plan should be highlighted as featured/recommended', verbose_name='is featured')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this plan is currently available for purchase', verbose_name='is active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
            ],
            options={
                'verbose_name': 'Pricing Plan',
                'verbose_name_plural': 'Pricing Plans',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='pricingplan',
            index=models.Index(fields=['is_active', 'display_order'], name='finances_pr_is_acti_539f5a_idx'),
        ),
        migrations.AddIndex(
            model_name='pricingplan',
            index=models.Index(fields=['plan_type', 'is_active'], name='finances_pr_plan_ty_bc9f6c_idx'),
        ),
        migrations.AddIndex(
            model_name='pricingplan',
            index=models.Index(fields=['is_featured', 'is_active'], name='finances_pr_is_feat_e4c5f8_idx'),
        ),
    ]