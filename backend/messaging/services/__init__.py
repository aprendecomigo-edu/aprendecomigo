"""
Messaging services module.

This module contains all email-related services for the Aprende Comigo platform.
"""

from .enhanced_email_service import EnhancedEmailService
from .email_template_service import EmailTemplateRenderingService, SchoolEmailTemplateManager
from .email_sequence_service import EmailSequenceOrchestrationService
from .secure_template_engine import SecureTemplateEngine, HTMLSanitizer, TemplateVariableValidator
from .teacher_communication_templates import DefaultEmailTemplates
from .teacher_invitation_service import TeacherInvitationEmailService

__all__ = [
    'EnhancedEmailService',
    'EmailTemplateRenderingService', 
    'SchoolEmailTemplateManager',
    'EmailSequenceOrchestrationService',
    'SecureTemplateEngine',
    'HTMLSanitizer',
    'TemplateVariableValidator',
    'DefaultEmailTemplates',
    'TeacherInvitationEmailService',
]