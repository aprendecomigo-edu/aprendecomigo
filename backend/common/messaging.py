import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_email_verification_code(email, code):
    return send_mail(
        subject="Aprende Comigo - Verification Code",
        message=f"Your verification code is: {code}\n\nThis code will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_sms(phone_number, message):
    """
    Send SMS using GatewayAPI.

    In DEBUG mode, just logs the message instead of actually sending it.

    Args:
        phone_number: Recipient's phone number (should include country code)
        message: SMS content to send

    Returns:
        dict: Response from API or simulated response in DEBUG mode
    """
    if settings.DEBUG:
        logger.info(f"SMS to {phone_number}: {message}")
        return {"success": True, "debug_mode": True}

    try:
        # Remove any potential formatting characters from phone number
        cleaned_number = "".join(filter(str.isdigit, str(phone_number)))

        # Prepare request data
        payload = {
            "message": message,
            "recipients": [{"msisdn": cleaned_number}],
            "sender": settings.SMS_SENDER_ID,
        }

        # Make API request
        response = requests.post(
            url=settings.SMS_API_URL,
            headers={"Content-Type": "application/json"},
            auth=(settings.SMS_API_KEY, ""),
            data=json.dumps(payload),
        )

        response_data = response.json()

        if response.status_code != 200:
            logger.error(f"SMS sending failed: {response_data}")
            return {"success": False, "error": response_data}

        logger.info(f"SMS sent successfully to {phone_number}")
        return {"success": True, "response": response_data}

    except Exception as e:
        logger.exception(f"Error sending SMS: {e!s}")
        return {"success": False, "error": str(e)}


def send_phone_verification_code(phone_number, code):
    return send_sms(
        phone_number, f"Your verification code is: {code}\n\nThis code will expire in 5 minutes."
    )


class TeacherInvitationEmailService:
    """
    Service for sending teacher invitation emails with proper error handling and retry logic.
    """
    
    @staticmethod
    def send_invitation_email(invitation) -> Dict[str, Any]:
        """
        Send a teacher invitation email using Django templates.
        
        Args:
            invitation: TeacherInvitation model instance
            
        Returns:
            Dict with success status and any error information
        """
        try:
            # Build the invitation link
            invitation_link = f"https://aprendecomigo.com/accept-teacher-invitation/{invitation.token}"
            
            # Prepare template context
            context = {
                'school_name': invitation.school.name,
                'school_description': invitation.school.description or '',
                'role_display': invitation.get_role_display(),
                'custom_message': invitation.custom_message or '',
                'invited_by_name': invitation.invited_by.name,
                'invited_by_email': invitation.invited_by.email,
                'recipient_email': invitation.email,
                'invitation_link': invitation_link,
                'expires_at': invitation.expires_at,
                'current_year': datetime.now().year,
            }
            
            # Render email templates
            html_content = render_to_string(
                'accounts/emails/teacher_invitation.html',
                context
            )
            text_content = render_to_string(
                'accounts/emails/teacher_invitation.txt',
                context
            )
            
            # Prepare email subject
            subject = f"Teacher Invitation: Join {invitation.school.name} on Aprende Comigo"
            
            # Send email
            success = send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            if success:
                logger.info(f"Teacher invitation email sent successfully to {invitation.email}")
                return {
                    'success': True,
                    'message': 'Email sent successfully',
                    'email': invitation.email,
                    'subject': subject
                }
            else:
                logger.error(f"Failed to send teacher invitation email to {invitation.email}")
                return {
                    'success': False,
                    'error': 'Email sending failed',
                    'email': invitation.email
                }
                
        except Exception as e:
            logger.exception(f"Error sending teacher invitation email to {invitation.email}: {e}")
            return {
                'success': False,
                'error': str(e),
                'email': invitation.email
            }
    
    @staticmethod
    def send_bulk_invitation_emails(invitations) -> Dict[str, Any]:
        """
        Send multiple invitation emails with batch processing.
        
        Args:
            invitations: List of TeacherInvitation instances
            
        Returns:
            Dict with batch results and statistics
        """
        from django.utils import timezone
        from accounts.models import EmailDeliveryStatus, InvitationStatus
        
        results = {
            'total_invitations': len(invitations),
            'successful_emails': 0,
            'failed_emails': 0,
            'errors': [],
            'successful_emails_list': [],
            'failed_emails_list': []
        }
        
        # Lists to collect invitations for bulk updates
        successful_invitations = []
        failed_invitations = []
        
        for invitation in invitations:
            try:
                email_result = TeacherInvitationEmailService.send_invitation_email(invitation)
                
                if email_result['success']:
                    results['successful_emails'] += 1
                    results['successful_emails_list'].append(invitation.email)
                    
                    # Prepare for bulk update - update fields in memory
                    invitation.email_delivery_status = EmailDeliveryStatus.SENT
                    invitation.email_sent_at = timezone.now()
                    invitation.status = InvitationStatus.SENT
                    invitation.updated_at = timezone.now()
                    successful_invitations.append(invitation)
                    
                else:
                    results['failed_emails'] += 1
                    results['failed_emails_list'].append(invitation.email)
                    results['errors'].append({
                        'email': invitation.email,
                        'error': email_result.get('error', 'Unknown error')
                    })
                    
                    # Prepare for bulk update - update fields in memory
                    invitation.email_delivery_status = EmailDeliveryStatus.FAILED
                    invitation.email_failure_reason = email_result.get('error', 'Unknown error')
                    invitation.retry_count += 1
                    invitation.updated_at = timezone.now()
                    failed_invitations.append(invitation)
                    
            except Exception as e:
                results['failed_emails'] += 1
                results['failed_emails_list'].append(invitation.email)
                results['errors'].append({
                    'email': invitation.email,
                    'error': str(e)
                })
                logger.exception(f"Unexpected error sending invitation to {invitation.email}: {e}")
                
                # Prepare for bulk update - update fields in memory
                invitation.email_delivery_status = EmailDeliveryStatus.FAILED
                invitation.email_failure_reason = f"Unexpected error: {str(e)}"
                invitation.retry_count += 1
                invitation.updated_at = timezone.now()
                failed_invitations.append(invitation)
        
        # Perform bulk updates to avoid N+1 queries
        if successful_invitations:
            # Use Django's bulk_update for successful invitations
            from accounts.models import TeacherInvitation
            TeacherInvitation.objects.bulk_update(
                successful_invitations,
                ['email_delivery_status', 'email_sent_at', 'status', 'updated_at'],
                batch_size=100
            )
        
        if failed_invitations:
            # Use Django's bulk_update for failed invitations
            from accounts.models import TeacherInvitation
            TeacherInvitation.objects.bulk_update(
                failed_invitations,
                ['email_delivery_status', 'email_failure_reason', 'retry_count', 'updated_at'],
                batch_size=100
            )
        
        # Log batch results
        logger.info(
            f"Bulk teacher invitation emails processed: "
            f"{results['successful_emails']} successful, "
            f"{results['failed_emails']} failed out of {results['total_invitations']} total"
        )
        
        return results
    
    @staticmethod
    def retry_failed_invitation_email(invitation) -> Dict[str, Any]:
        """
        Retry sending an invitation email that previously failed.
        
        Args:
            invitation: TeacherInvitation instance with failed email
            
        Returns:
            Dict with retry results
        """
        if not invitation.can_retry():
            return {
                'success': False,
                'error': f'Maximum retry attempts ({invitation.max_retries}) exceeded',
                'email': invitation.email,
                'retry_count': invitation.retry_count
            }
        
        logger.info(f"Retrying invitation email for {invitation.email} (attempt {invitation.retry_count + 1})")
        
        result = TeacherInvitationEmailService.send_invitation_email(invitation)
        
        if result['success']:
            # Reset retry count on successful send
            invitation.retry_count = 0
            invitation.email_failure_reason = None
            invitation.mark_email_sent()
        else:
            # Increment retry count on failure
            invitation.mark_email_failed(result.get('error', 'Retry failed'))
        
        return result
