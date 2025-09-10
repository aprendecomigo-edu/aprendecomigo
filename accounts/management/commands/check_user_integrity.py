"""
Management command to check and ensure all users have school memberships.

This command can be run periodically (e.g., via cron) to ensure data integrity
and automatically fix any users without school memberships.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import School, SchoolMembership, SchoolRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Check and fix users without school memberships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no changes will be made)',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress non-error output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quiet = options['quiet']
        
        # Find all non-superusers without active school memberships
        users_without_schools = User.objects.filter(
            is_superuser=False,
            school_memberships__isnull=True
        ).distinct() | User.objects.filter(
            is_superuser=False
        ).exclude(
            school_memberships__is_active=True
        ).distinct()
        
        count = users_without_schools.count()
        
        if count == 0:
            if not quiet:
                self.stdout.write(
                    self.style.SUCCESS('✓ All users have active school memberships. System integrity verified.')
                )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {count} users without active school memberships.')
        )
        
        if dry_run:
            self.stdout.write('DRY RUN - No changes will be made.')
            for user in users_without_schools:
                self.stdout.write(f'  - User {user.id}: {user.email} ({user.name})')
            return
        
        fixed_count = 0
        failed_count = 0
        
        for user in users_without_schools:
            try:
                with transaction.atomic():
                    # Check if user has any inactive memberships we can reactivate
                    inactive_membership = user.school_memberships.filter(is_active=False).first()
                    
                    if inactive_membership:
                        # Reactivate existing membership
                        inactive_membership.is_active = True
                        inactive_membership.save()
                        if not quiet:
                            self.stdout.write(
                                f'  ✓ Reactivated membership for user {user.id}: {user.email}'
                            )
                    else:
                        # Create new personal school and membership
                        school_name = f"Personal School - {user.email}"
                        if user.first_name:
                            school_name = f"{user.first_name}'s School"
                        
                        school = School.objects.create(
                            name=school_name,
                            description=f"Automatically created personal school for {user.email}",
                            contact_email=user.email,
                            phone_number=user.phone_number or "",
                        )
                        
                        SchoolMembership.objects.create(
                            user=user,
                            school=school,
                            role=SchoolRole.SCHOOL_OWNER,
                            is_active=True
                        )
                        
                        if not quiet:
                            self.stdout.write(
                                f'  ✓ Created school and membership for user {user.id}: {user.email}'
                            )
                    
                    fixed_count += 1
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to fix user {user.id}: {user.email} - {str(e)}')
                )
        
        # Summary
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully fixed {fixed_count} users.')
            )
        
        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to fix {failed_count} users.')
            )
        
        # Verify final state
        remaining = User.objects.filter(
            is_superuser=False,
            school_memberships__isnull=True
        ).distinct() | User.objects.filter(
            is_superuser=False
        ).exclude(
            school_memberships__is_active=True
        ).distinct()
        
        if remaining.exists():
            self.stdout.write(
                self.style.ERROR(f'\n⚠ Warning: {remaining.count()} users still without active memberships!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All users now have active school memberships!')
            )