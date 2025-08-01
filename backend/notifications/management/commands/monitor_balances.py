"""
Management command for monitoring student balances - Issue #107: Student Balance Monitoring & Notification System

This command can be run periodically (e.g., via cron) to check for:
- Students with low balance (< 2 hours remaining)
- Packages expiring within 7 days
- Send notifications and emails automatically

Usage:
    python manage.py monitor_balances
    python manage.py monitor_balances --threshold 1.0  # Custom low balance threshold
    python manage.py monitor_balances --expiry-days 3  # Custom expiry warning days
    python manage.py monitor_balances --dry-run        # Don't send emails, just report
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal

from notifications.services import BalanceMonitoringService


class Command(BaseCommand):
    help = 'Monitor student balances and send notifications for low balances and expiring packages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=float,
            default=2.0,
            help='Low balance threshold in hours (default: 2.0)',
        )
        
        parser.add_argument(
            '--expiry-days',
            type=int,
            default=7,
            help='Days ahead to check for package expiration (default: 7)',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending emails (for testing)',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        threshold = Decimal(str(options['threshold']))
        expiry_days = options['expiry_days']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(f"Starting balance monitoring at {timezone.now()}")
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No emails will be sent")
            )
        
        try:
            # Check low balance students
            if verbose:
                self.stdout.write("Checking for students with low balance...")
            
            low_balance_students = BalanceMonitoringService.check_low_balance_students(threshold)
            self.stdout.write(
                f"Found {len(low_balance_students)} students with balance below {threshold} hours"
            )
            
            # Check expiring packages
            if verbose:
                self.stdout.write("Checking for expiring packages...")
                
            expiring_packages = BalanceMonitoringService.check_expiring_packages(expiry_days)
            self.stdout.write(
                f"Found {len(expiring_packages)} packages expiring within {expiry_days} days"
            )
            
            if dry_run:
                # In dry run mode, just report what would be done
                if verbose and low_balance_students:
                    self.stdout.write("Students with low balance:")
                    for student in low_balance_students:
                        self.stdout.write(f"  - {student.name} ({student.email})")
                        
                if verbose and expiring_packages:
                    self.stdout.write("Expiring packages:")
                    for transaction in expiring_packages:
                        days_left = (transaction.expires_at - timezone.now()).days
                        self.stdout.write(
                            f"  - {transaction.student.name} ({transaction.student.email}) "
                            f"- expires in {days_left} days"
                        )
                
                self.stdout.write(
                    self.style.WARNING("DRY RUN COMPLETE - No notifications sent")
                )
                return
            
            # Process the actual monitoring
            if verbose:
                self.stdout.write("Processing balance alerts...")
                
            result = BalanceMonitoringService.monitor_all_balances()
            
            # Report results
            self.stdout.write(
                self.style.SUCCESS("Balance monitoring completed successfully!")
            )
            
            self.stdout.write(f"Low balance alerts: {result['low_balance_alerts']}")
            self.stdout.write(f"Balance depleted alerts: {result['balance_depleted_alerts']}")
            self.stdout.write(f"Package expiring alerts: {result['package_expiring_alerts']}")
            self.stdout.write(f"Total notifications created: {result['total_notifications']}")
            self.stdout.write(f"Total emails sent: {result['total_emails_sent']}")
            
            if result['errors']:
                self.stdout.write(
                    self.style.WARNING(f"Errors encountered: {len(result['errors'])}")
                )
                if verbose:
                    for error in result['errors']:
                        self.stdout.write(f"  - {error}")
            else:
                self.stdout.write(self.style.SUCCESS("No errors encountered"))
                
        except Exception as e:
            raise CommandError(f"Error during balance monitoring: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Balance monitoring completed at {timezone.now()}")
        )