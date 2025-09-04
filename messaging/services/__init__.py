"""
Messaging services module.

This module contains all email-related services for the Aprende Comigo platform.
"""

from .auth_email_service import send_email_verification_code, send_magic_link_email, send_sms_otp
from .balance_monitoring_service import BalanceMonitoringService
from .email_sequence_service import EmailSequenceOrchestrationService
from .email_template_service import EmailTemplateRenderingService, SchoolEmailTemplateManager
from .enhanced_email_service import EnhancedEmailService
from .secure_template_engine import HTMLSanitizer, SecureTemplateEngine, TemplateVariableValidator
from .sms import send_bulk_sms, send_bulk_sms_async, send_sms, send_sms_async, sms_service
from .teacher_communication_templates import DefaultEmailTemplates
from .teacher_invitation_service import TeacherInvitationEmailService

__all__ = [
    "BalanceMonitoringService",
    "DefaultEmailTemplates",
    "EmailSequenceOrchestrationService",
    "EmailTemplateRenderingService",
    "EnhancedEmailService",
    "HTMLSanitizer",
    "SchoolEmailTemplateManager",
    "SecureTemplateEngine",
    "TeacherInvitationEmailService",
    "TemplateVariableValidator",
    "send_bulk_sms",
    "send_bulk_sms_async",
    # Auth email functions
    "send_email_verification_code",
    "send_magic_link_email",
    # SMS functions
    "send_sms",
    "send_sms_async",
    "send_sms_otp",
    "sms_service",
]
