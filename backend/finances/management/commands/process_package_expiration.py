"""
Django management command to process package expirations.

This command handles:
- Automatic package expiration detection and processing
- Bulk expiration processing with configurable grace periods
- Student notification system for upcoming expirations
- Dry run mode for testing
- Filtering by specific students or date ranges
- Comprehensive logging and audit trails

Usage:
    python manage.py process_package_expiration
    python manage.py process_package_expiration --dry-run
    python manage.py process_package_expiration --grace-hours=48
    python manage.py process_package_expiration --student-email=student@example.com
    python manage.py process_package_expiration --send-notifications
    python manage.py process_package_expiration --verbosity=2

Following GitHub Issue #33: "Create Package Expiration Management"
"""

from decimal import Decimal
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model

from finances.services.package_expiration_service import PackageExpirationService

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to process package expirations.
    
    Processes expired packages, updates student balances, and optionally
    sends notifications about upcoming expirations.
    """
    
    help = "Process package expirations and update student balances"
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        
        parser.add_argument(
            '--grace-hours',
            type=int,
            default=24,
            help='Grace period in hours before processing expired packages (default: 24)',
        )
        
        parser.add_argument(
            '--student-email',
            type=str,
            help='Process packages only for specific student email',
        )
        
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Send expiration warning notifications for packages expiring soon',
        )
        
        parser.add_argument(
            '--notification-days',
            type=int,
            default=7,
            help='Send notifications for packages expiring within N days (default: 7)',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Process packages even if they were recently processed',
        )
    
    def handle(self, *args, **options):
        """Main command execution."""
        verbosity = options['verbosity']
        dry_run = options['dry_run']
        grace_hours = options['grace_hours']
        student_email = options['student_email']
        send_notifications = options['send_notifications']
        notification_days = options['notification_days']
        force = options['force']
        
        if verbosity >= 1:
            mode_str = "DRY RUN - " if dry_run else ""
            self.stdout.write(f"{mode_str}Processing package expirations...")
            self.stdout.write(f"Grace period: {grace_hours} hours")
            
            if student_email:
                self.stdout.write(f"Filtering by student: {student_email}")
        
        try:
            # Process expired packages
            if student_email:
                self._process_student_packages(
                    student_email, grace_hours, dry_run, verbosity
                )
            else:
                self._process_all_packages(
                    grace_hours, dry_run, verbosity
                )
            
            # Send notifications if requested
            if send_notifications:
                self._send_expiration_notifications(
                    notification_days, dry_run, verbosity
                )
                
        except Exception as e:
            raise CommandError(f"Error processing package expirations: {e}")
    
    def _process_all_packages(
        self, 
        grace_hours: int, 
        dry_run: bool, 
        verbosity: int
    ):
        """Process all expired packages."""
        # Get expired packages outside grace period
        expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
            grace_hours=grace_hours
        )
        
        if verbosity >= 1:
            self.stdout.write(f"Found {len(expired_packages)} packages to process")
        
        if not expired_packages:
            if verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS("No packages need processing")
                )
            return
        
        if dry_run:
            self._show_dry_run_results(expired_packages, verbosity)
            return
        
        # Process packages
        results = PackageExpirationService.process_bulk_expiration(
            grace_hours=grace_hours
        )
        
        # Report results
        self._report_processing_results(results, verbosity)
    
    def _process_student_packages(
        self, 
        student_email: str, 
        grace_hours: int, 
        dry_run: bool, 
        verbosity: int
    ):
        """Process expired packages for a specific student."""
        try:
            student = User.objects.get(email=student_email)
        except User.DoesNotExist:
            raise CommandError(f"Student with email {student_email} not found")
        
        # Get student's expired packages
        expired_packages = PackageExpirationService.get_expired_packages_for_student(student)
        
        # Filter by grace period
        grace_cutoff = timezone.now() - timezone.timedelta(hours=grace_hours)
        expired_packages = [
            pkg for pkg in expired_packages 
            if pkg.expires_at < grace_cutoff
        ]
        
        if verbosity >= 1:
            self.stdout.write(
                f"Found {len(expired_packages)} packages for student {student.name}"
            )
        
        if not expired_packages:
            if verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS(f"No packages need processing for {student.name}")
                )
            return
        
        if dry_run:
            self._show_dry_run_results(expired_packages, verbosity)
            return
        
        # Process packages
        results = []
        for package in expired_packages:
            result = PackageExpirationService.process_expired_package(package)
            results.append(result)
        
        # Report results
        self._report_processing_results(results, verbosity)
    
    def _send_expiration_notifications(
        self, 
        notification_days: int, 
        dry_run: bool, 
        verbosity: int
    ):
        """Send expiration warning notifications."""
        if verbosity >= 1:
            self.stdout.write(f"Sending notifications for packages expiring within {notification_days} days...")
        
        # Get packages expiring soon
        expiring_packages = PackageExpirationService.get_packages_expiring_soon(
            days_ahead=notification_days
        )
        
        if verbosity >= 1:
            self.stdout.write(f"Found {len(expiring_packages)} packages expiring soon")
        
        if not expiring_packages:
            if verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS("No expiration notifications needed")
                )
            return
        
        if dry_run:
            self._show_notification_dry_run(expiring_packages, verbosity)
            return
        
        # Send notifications
        results = PackageExpirationService.send_batch_expiration_warnings(
            expiring_packages,
            days_until_expiry=notification_days
        )
        
        # Report notification results
        self._report_notification_results(results, verbosity)
    
    def _show_dry_run_results(self, packages, verbosity: int):
        """Show what would be processed in dry run mode."""
        if verbosity >= 1:
            self.stdout.write(
                self.style.WARNING("DRY RUN - The following packages would be processed:")
            )
            
            total_hours = Decimal('0.00')
            
            for package in packages:
                hours_to_expire = PackageExpirationService.calculate_hours_to_expire(package)
                total_hours += hours_to_expire
                
                if verbosity >= 2:
                    self.stdout.write(
                        f"  Package {package.id}: {package.student.name} - "
                        f"€{package.amount} - {hours_to_expire}h to expire"
                    )
            
            self.stdout.write(
                f"Total: {len(packages)} packages, {total_hours} hours would be expired"
            )
    
    def _show_notification_dry_run(self, packages, verbosity: int):
        """Show what notifications would be sent in dry run mode."""
        if verbosity >= 1:
            self.stdout.write(
                self.style.WARNING("DRY RUN - The following notifications would be sent:")
            )
            
            for package in packages:
                days_until_expiry = (package.expires_at.date() - timezone.now().date()).days
                
                if verbosity >= 2:
                    self.stdout.write(
                        f"  {package.student.name} ({package.student.email}) - "
                        f"Package expires in {days_until_expiry} days"
                    )
            
            self.stdout.write(f"Total: {len(packages)} notifications would be sent")
    
    def _report_processing_results(self, results, verbosity: int):
        """Report the results of package processing."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_hours_expired = sum(r.hours_expired for r in successful)
        
        if verbosity >= 1:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {len(successful)} packages "
                    f"({total_hours_expired} hours expired)"
                )
            )
            
            if failed:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to process {len(failed)} packages"
                    )
                )
        
        if verbosity >= 2:
            for result in successful:
                self.stdout.write(
                    f"  ✓ Package {result.package_id}: {result.hours_expired}h expired"
                )
            
            for result in failed:
                self.stdout.write(
                    f"  ✗ Package {result.package_id}: {result.error_message}"
                )
    
    def _report_notification_results(self, results, verbosity: int):
        """Report the results of notification sending."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if verbosity >= 1:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent {len(successful)} notifications"
                )
            )
            
            if failed:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send {len(failed)} notifications"
                    )
                )
        
        if verbosity >= 2:
            for result in successful:
                self.stdout.write(f"  ✓ Sent to {result.recipient}")
            
            for result in failed:
                self.stdout.write(f"  ✗ Failed to send to {result.recipient}: {result.message}")