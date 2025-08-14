"""
Messaging services module.

This module contains all email-related services for the Aprende Comigo platform.
"""

from .balance_monitoring_service import BalanceMonitoringService
from .email_sequence_service import EmailSequenceOrchestrationService
from .email_template_service import EmailTemplateRenderingService, SchoolEmailTemplateManager
from .enhanced_email_service import EnhancedEmailService
from .secure_template_engine import HTMLSanitizer, SecureTemplateEngine, TemplateVariableValidator
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
]
