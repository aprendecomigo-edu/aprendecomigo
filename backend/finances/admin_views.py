"""
Admin API views for package expiration management.

These views provide administrative interfaces for:
- Viewing and processing expired packages
- Extending package expiration dates
- Sending expiration notifications
- Viewing expiration analytics and reports
- Managing bulk expiration operations

Following GitHub Issue #33: "Create Package Expiration Management"
"""

import logging
from datetime import timedelta
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone

from finances.services.package_expiration_service import PackageExpirationService
from finances.models import PurchaseTransaction
from finances.serializers import PurchaseHistorySerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_expired_packages(request):
    """
    Get all expired packages.
    
    Query Parameters:
    - grace_hours: Grace period in hours (default: 24)
    - student_email: Filter by specific student email
    """
    grace_hours = int(request.GET.get('grace_hours', 24))
    student_email = request.GET.get('student_email')
    
    try:
        if student_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                student = User.objects.get(email=student_email)
                expired_packages = PackageExpirationService.get_expired_packages_for_student(student)
                
                # Apply grace period filter
                grace_cutoff = timezone.now() - timedelta(hours=grace_hours)
                expired_packages = [
                    pkg for pkg in expired_packages 
                    if pkg.expires_at < grace_cutoff
                ]
            except User.DoesNotExist:
                return Response(
                    {'error': f'Student with email {student_email} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
                grace_hours=grace_hours
            )
        
        serializer = PurchaseHistorySerializer(expired_packages, many=True)
        
        return Response({
            'expired_packages': serializer.data,
            'count': len(expired_packages),
            'grace_hours': grace_hours
        })
        
    except Exception as e:
        logger.error(f"Error retrieving expired packages: {e}")
        return Response(
            {'error': 'Failed to retrieve expired packages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def process_expired_packages(request):
    """
    Process all expired packages.
    
    Body Parameters:
    - grace_hours: Grace period in hours (default: 24)
    - dry_run: If true, return what would be processed without making changes
    """
    grace_hours = int(request.data.get('grace_hours', 24))
    dry_run = request.data.get('dry_run', False)
    
    try:
        if dry_run:
            expired_packages = PackageExpirationService.get_expired_packages_outside_grace_period(
                grace_hours=grace_hours
            )
            
            total_hours = Decimal('0.00')
            for package in expired_packages:
                hours_to_expire = PackageExpirationService.calculate_hours_to_expire(package)
                total_hours += hours_to_expire
            
            return Response({
                'dry_run': True,
                'packages_to_process': len(expired_packages),
                'total_hours_to_expire': total_hours,
                'grace_hours': grace_hours
            })
        else:
            results = PackageExpirationService.process_bulk_expiration(
                grace_hours=grace_hours
            )
            
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            total_hours_expired = sum(r.hours_expired for r in successful)
            
            return Response({
                'processed_count': len(successful),
                'failed_count': len(failed),
                'total_hours_expired': total_hours_expired,
                'grace_hours': grace_hours,
                'results': [
                    {
                        'package_id': r.package_id,
                        'student_id': r.student_id,
                        'hours_expired': r.hours_expired,
                        'success': r.success,
                        'error_message': r.error_message
                    }
                    for r in results
                ]
            })
            
    except Exception as e:
        logger.error(f"Error processing expired packages: {e}")
        return Response(
            {'error': 'Failed to process expired packages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def extend_package(request, package_id):
    """
    Extend a package expiration date.
    
    Body Parameters:
    - extension_days: Number of days to extend (required)
    - reason: Reason for extension (optional)
    - extend_from_now: Whether to extend from now or original expiry (default: false)
    """
    try:
        package = PurchaseTransaction.objects.get(id=package_id)
        
        extension_days = request.data.get('extension_days')
        if not extension_days:
            return Response(
                {'error': 'extension_days is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        extend_from_now = request.data.get('extend_from_now', False)
        
        result = PackageExpirationService.extend_package_expiration(
            package=package,
            extension_days=int(extension_days),
            reason=reason,
            extend_from_now=extend_from_now
        )
        
        if result.success:
            return Response({
                'success': True,
                'package_id': result.package_id,
                'original_expiry': result.original_expiry,
                'new_expiry': result.new_expiry,
                'extension_days': result.extension_days,
                'audit_log': result.audit_log
            })
        else:
            return Response(
                {'error': result.error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except PurchaseTransaction.DoesNotExist:
        return Response(
            {'error': 'Package not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error extending package {package_id}: {e}")
        return Response(
            {'error': 'Failed to extend package'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_expiration_analytics(request):
    """
    Get expiration analytics and metrics.
    
    Query Parameters:
    - period_days: Analysis period in days (default: 30)
    """
    period_days = int(request.GET.get('period_days', 30))
    
    try:
        # Get current analytics
        metrics = PackageExpirationService.calculate_expiration_metrics(
            period_days=period_days
        )
        
        # Get summary report
        start_date = timezone.now() - timedelta(days=period_days)
        end_date = timezone.now()
        
        summary = PackageExpirationService.generate_expiration_summary_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get at-risk students
        at_risk_students = PackageExpirationService.identify_at_risk_students(
            min_expired_packages=2,
            timeframe_days=period_days
        )
        
        return Response({
            'period_days': period_days,
            'metrics': metrics,
            'summary': summary,
            'at_risk_students': at_risk_students,
            'generated_at': timezone.now()
        })
        
    except Exception as e:
        logger.error(f"Error generating expiration analytics: {e}")
        return Response(
            {'error': 'Failed to generate analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_expiration_notifications(request):
    """
    Send expiration warning notifications to students.
    
    Body Parameters:
    - days_ahead: Send notifications for packages expiring within N days (default: 7)
    - student_email: Send notification to specific student only (optional)
    """
    days_ahead = int(request.data.get('days_ahead', 7))
    student_email = request.data.get('student_email')
    
    try:
        if student_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                student = User.objects.get(email=student_email)
                
                # Get expiring packages for specific student
                expiring_packages = [
                    pkg for pkg in PackageExpirationService.get_packages_expiring_soon(days_ahead)
                    if pkg.student == student
                ]
            except User.DoesNotExist:
                return Response(
                    {'error': f'Student with email {student_email} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            expiring_packages = PackageExpirationService.get_packages_expiring_soon(
                days_ahead=days_ahead
            )
        
        if not expiring_packages:
            return Response({
                'notifications_sent': 0,
                'message': 'No packages expiring soon',
                'days_ahead': days_ahead
            })
        
        results = PackageExpirationService.send_batch_expiration_warnings(
            expiring_packages,
            days_until_expiry=days_ahead
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return Response({
            'notifications_sent': len(successful),
            'failed_notifications': len(failed),
            'days_ahead': days_ahead,
            'results': [
                {
                    'recipient': r.recipient,
                    'success': r.success,
                    'message': r.message,
                    'sent_at': r.sent_at
                }
                for r in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Error sending expiration notifications: {e}")
        return Response(
            {'error': 'Failed to send notifications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_packages_expiring_soon(request):
    """
    Get packages expiring within specified timeframe.
    
    Query Parameters:
    - days_ahead: Number of days to look ahead (default: 7)
    """
    days_ahead = int(request.GET.get('days_ahead', 7))
    
    try:
        expiring_packages = PackageExpirationService.get_packages_expiring_soon(
            days_ahead=days_ahead
        )
        
        serializer = PurchaseHistorySerializer(expiring_packages, many=True)
        
        return Response({
            'expiring_packages': serializer.data,
            'count': len(expiring_packages),
            'days_ahead': days_ahead
        })
        
    except Exception as e:
        logger.error(f"Error retrieving packages expiring soon: {e}")
        return Response(
            {'error': 'Failed to retrieve expiring packages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_extend_packages(request):
    """
    Extend multiple packages at once.
    
    Body Parameters:
    - package_ids: List of package IDs to extend (required)
    - extension_days: Number of days to extend (required)
    - reason: Reason for bulk extension (optional)
    """
    try:
        package_ids = request.data.get('package_ids', [])
        extension_days = request.data.get('extension_days')
        reason = request.data.get('reason', 'Bulk extension via admin API')
        
        if not package_ids:
            return Response(
                {'error': 'package_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not extension_days:
            return Response(
                {'error': 'extension_days is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        packages = PurchaseTransaction.objects.filter(id__in=package_ids)
        
        if len(packages) != len(package_ids):
            return Response(
                {'error': 'Some package IDs were not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        results = PackageExpirationService.bulk_extend_packages(
            packages=list(packages),
            extension_days=int(extension_days),
            reason=reason
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return Response({
            'extended_count': len(successful),
            'failed_count': len(failed),
            'extension_days': extension_days,
            'results': [
                {
                    'package_id': r.package_id,
                    'success': r.success,
                    'original_expiry': r.original_expiry,
                    'new_expiry': r.new_expiry,
                    'error_message': r.error_message
                }
                for r in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Error bulk extending packages: {e}")
        return Response(
            {'error': 'Failed to bulk extend packages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )