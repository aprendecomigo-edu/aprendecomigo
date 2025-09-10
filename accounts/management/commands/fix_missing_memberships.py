"""
Management command to fix users with missing school memberships.

This addresses the issue where users exist in the database but have no 
school memberships, which violates the fundamental business rule that 
every user must have at least one school association.

Usage:
    python manage.py fix_missing_memberships
    python manage.py fix_missing_memberships --dry-run
    python manage.py fix_missing_memberships --user-id 31
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser, School, SchoolMembership
from accounts.models.schools import SchoolRole


class Command(BaseCommand):
    help = "Fix users with missing school memberships by creating personal schools"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be fixed without making changes",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Fix specific user ID only",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        user_id = options.get("user_id")

        # Find users without any school memberships
        if user_id:
            try:
                users_without_memberships = [CustomUser.objects.get(id=user_id)]
                self.stdout.write(f"Checking specific user ID: {user_id}")
            except CustomUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {user_id} does not exist")
                )
                return
        else:
            # Find all users without memberships
            users_with_memberships = SchoolMembership.objects.values_list("user_id", flat=True).distinct()
            users_without_memberships = CustomUser.objects.exclude(id__in=users_with_memberships)

        total_users = users_without_memberships.count() if hasattr(users_without_memberships, 'count') else len(users_without_memberships)

        if total_users == 0:
            self.stdout.write(self.style.SUCCESS("✅ All users have school memberships - nothing to fix"))
            return

        self.stdout.write(f"Found {total_users} users without school memberships:")

        fixed_count = 0
        for user in users_without_memberships:
            # Skip superusers as they don't strictly need school memberships
            if user.is_superuser:
                self.stdout.write(f"  - Skipping superuser: {user.email} (ID: {user.id})")
                continue

            self.stdout.write(f"  - {user.email} (ID: {user.id}) - {user.date_joined}")

            if not dry_run:
                try:
                    with transaction.atomic():
                        # Create a personal school for the user
                        school_name = f"Personal School - {user.email}"
                        
                        # Create school
                        school = School.objects.create(
                            name=school_name,
                            description=f"Personal tutoring school for {user.email}",
                            contact_email=user.email,
                        )

                        # Create school membership as owner
                        membership = SchoolMembership.objects.create(
                            user=user,
                            school=school,
                            role=SchoolRole.SCHOOL_OWNER,
                            is_active=True,
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    ✅ Created school '{school.name}' and owner membership"
                            )
                        )
                        fixed_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    ❌ Failed to fix user {user.email}: {e}")
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\n🔍 DRY RUN: Would fix {total_users} users")
            )
            self.stdout.write("Run without --dry-run to apply the fixes")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Fixed {fixed_count} out of {total_users} users")
            )

        # Show verification
        if not dry_run and fixed_count > 0:
            self.stdout.write("\n--- Verification ---")
            remaining_users_without_memberships = CustomUser.objects.exclude(
                id__in=SchoolMembership.objects.values_list("user_id", flat=True).distinct()
            ).exclude(is_superuser=True)

            remaining_count = remaining_users_without_memberships.count()
            if remaining_count == 0:
                self.stdout.write(self.style.SUCCESS("✅ All regular users now have school memberships"))
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ {remaining_count} users still without memberships")
                )
                for user in remaining_users_without_memberships[:5]:  # Show first 5
                    self.stdout.write(f"  - {user.email} (ID: {user.id})")