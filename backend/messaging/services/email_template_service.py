"""
Email Template Service for Teacher Communications (Issue #99)

This service handles email template rendering with school branding integration,
template variable substitution, and consistent formatting across email clients.
"""

from datetime import datetime
import logging
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from accounts.models import School

from ..models import EmailTemplateType, SchoolEmailTemplate
from .secure_template_engine import HTMLSanitizer, SecureTemplateEngine, TemplateVariableValidator

logger = logging.getLogger(__name__)


class EmailTemplateRenderingService:
    """
    Service for rendering email templates with school branding and variable substitution.
    """

    # Default template variables available to all templates
    DEFAULT_VARIABLES = {
        "platform_name": "Aprende Comigo",
        "platform_url": "https://aprendecomigo.com",
        "support_email": "support@aprendecomigo.com",
        "current_year": datetime.now().year,
    }

    # CSS variables for school branding
    BRANDING_CSS_TEMPLATE = """
    <style>
        :root {
            --school-primary-color: {{ school_primary_color }};
            --school-secondary-color: {{ school_secondary_color }};
            --school-text-color: {{ school_text_color }};
            --school-background-color: {{ school_background_color }};
        }
        
        .school-branded {
            color: var(--school-primary-color) !important;
        }
        
        .school-branded-bg {
            background-color: var(--school-primary-color) !important;
        }
        
        .school-button {
            background-color: var(--school-primary-color) !important;
            border-color: var(--school-primary-color) !important;
        }
        
        .school-button:hover {
            background-color: var(--school-secondary-color) !important;
            border-color: var(--school-secondary-color) !important;
        }
        
        .school-border {
            border-color: var(--school-primary-color) !important;
        }
    </style>
    """

    @classmethod
    def render_template(
        cls, template: SchoolEmailTemplate, context_variables: dict[str, Any], request=None
    ) -> tuple[str, str, str]:
        """
        Securely render an email template with school branding and variable substitution.

        Args:
            template: SchoolEmailTemplate instance
            context_variables: Dictionary of variables for template rendering
            request: Optional request object for URL building

        Returns:
            Tuple of (subject, html_content, text_content)

        Raises:
            ValueError: If template rendering fails
            ValidationError: If template or context is unsafe
        """
        try:
            # Validate template content for security
            EmailTemplateSecurityService.validate_template_security(template)

            # Validate context variables
            TemplateVariableValidator.validate_context(context_variables)

            # Prepare rendering context
            context = cls._prepare_context(template.school, context_variables, request)

            # Render subject with secure engine
            subject = cls._render_subject_secure(template.subject_template, context)

            # Render HTML content with branding and security
            html_content = cls._render_html_content_secure(template, context)

            # Render text content with secure engine
            text_content = cls._render_text_content_secure(template.text_content, context)

            logger.info(f"Successfully rendered template {template.id} for school {template.school.name}")

            return subject, html_content, text_content

        except ValidationError as e:
            logger.error(f"Security validation failed for template {template.id}: {e!s}")
            raise ValueError(f"Template security validation failed: {e!s}")
        except Exception as e:
            logger.error(f"Error rendering template {template.id}: {e!s}")
            raise ValueError(f"Template rendering failed: {e!s}")

    @classmethod
    def _prepare_context(cls, school: School, context_variables: dict[str, Any], request=None) -> dict[str, Any]:
        """
        Prepare the complete context for template rendering.

        Args:
            school: School instance
            context_variables: User-provided variables
            request: Optional request object

        Returns:
            Complete context dictionary
        """
        # Start with default variables
        context = cls.DEFAULT_VARIABLES.copy()

        # Add school-specific variables
        school_context = cls._get_school_context(school)
        context.update(school_context)

        # Add user-provided variables (these can override defaults)
        context.update(context_variables)

        # Add request-specific variables if available
        if request:
            context.update(
                {
                    "request_user": getattr(request, "user", None),
                    "site_url": request.build_absolute_uri("/")
                    if hasattr(request, "build_absolute_uri")
                    else context["platform_url"],
                }
            )

        return context

    @classmethod
    def _get_school_context(cls, school: School) -> dict[str, Any]:
        """
        Get school-specific context variables for branding.

        Args:
            school: School instance

        Returns:
            Dictionary of school-specific variables
        """
        return {
            "school_name": school.name,
            "school_description": school.description or "",
            "school_contact_email": school.contact_email or "",
            "school_phone_number": school.phone_number or "",
            "school_website": school.website or "",
            "school_address": school.address or "",
            # Branding variables
            "school_primary_color": school.primary_color or "#3B82F6",
            "school_secondary_color": school.secondary_color or "#1E40AF",
            "school_text_color": "#1F2937",  # Default text color
            "school_background_color": "#FFFFFF",  # Default background color
            "school_logo_url": school.logo.url if school.logo else "",
            # School metadata
            "school_id": school.id,
        }

    @classmethod
    def _render_subject_secure(cls, subject_template: str, context: dict[str, Any]) -> str:
        """
        Securely render email subject with variable substitution.

        Args:
            subject_template: Subject template string
            context: Context variables

        Returns:
            Rendered subject string
        """
        try:
            # Use secure template engine
            rendered_subject = SecureTemplateEngine.render_template(subject_template, context, auto_escape=True)

            # Clean up subject (remove newlines, extra spaces, strip HTML)
            rendered_subject = strip_tags(rendered_subject)
            rendered_subject = " ".join(rendered_subject.split())

            # Ensure reasonable length
            if len(rendered_subject) > 300:
                rendered_subject = rendered_subject[:297] + "..."

            return rendered_subject

        except Exception as e:
            logger.error(f"Error rendering subject securely: {e!s}")
            # Fallback to a safe subject
            school_name = context.get("school_name", "Aprende Comigo")
            return f"Message from {strip_tags(str(school_name))}"

    @classmethod
    def _render_html_content_secure(cls, template: SchoolEmailTemplate, context: dict[str, Any]) -> str:
        """
        Securely render HTML email content with school branding.

        Args:
            template: SchoolEmailTemplate instance
            context: Context variables

        Returns:
            Rendered and sanitized HTML content
        """
        try:
            # Start with the base HTML content
            html_content = template.html_content

            # Apply school branding if enabled
            if template.use_school_branding:
                html_content = cls._apply_school_branding_secure(html_content, template, context)

            # Render template with secure engine
            rendered_content = SecureTemplateEngine.render_template(html_content, context, auto_escape=True)

            # Sanitize HTML content to prevent XSS
            rendered_content = HTMLSanitizer.sanitize_html(rendered_content)

            # Ensure proper HTML structure
            rendered_content = cls._ensure_html_structure(rendered_content)

            return rendered_content

        except Exception as e:
            logger.error(f"Error rendering HTML content securely: {e!s}")
            # Fallback to basic HTML
            return cls._get_fallback_html_content(context)

    @classmethod
    def _render_text_content_secure(cls, text_template: str, context: dict[str, Any]) -> str:
        """
        Securely render plain text email content.

        Args:
            text_template: Text template string
            context: Context variables

        Returns:
            Rendered text content
        """
        try:
            # Use secure template engine (auto_escape=False for plain text)
            rendered_content = SecureTemplateEngine.render_template(text_template, context, auto_escape=False)

            # Strip any HTML tags that might have been included
            rendered_content = strip_tags(rendered_content)

            # Clean up text content
            rendered_content = cls._clean_text_content(rendered_content)

            return rendered_content

        except Exception as e:
            logger.error(f"Error rendering text content securely: {e!s}")
            # Fallback to basic text
            school_name = context.get("school_name", "Aprende Comigo")
            return f"Message from {strip_tags(str(school_name))}"

    @classmethod
    def _apply_school_branding_secure(
        cls, html_content: str, template: SchoolEmailTemplate, context: dict[str, Any]
    ) -> str:
        """
        Securely apply school branding to HTML content.

        Args:
            html_content: Original HTML content
            template: SchoolEmailTemplate instance
            context: Context variables

        Returns:
            HTML content with school branding applied
        """
        # Render branding CSS with secure engine
        branding_css = SecureTemplateEngine.render_template(cls.BRANDING_CSS_TEMPLATE, context, auto_escape=True)

        # Add custom CSS if provided (sanitized)
        if template.custom_css:
            # Validate and sanitize custom CSS
            sanitized_css = cls._sanitize_custom_css(template.custom_css)
            if sanitized_css:
                branding_css += f"\n<style>\n{sanitized_css}\n</style>"

        # Insert branding CSS into HTML
        # Look for </head> tag, if not found, add at the beginning
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{branding_css}\n</head>")
        else:
            html_content = f"{branding_css}\n{html_content}"

        return html_content

    @classmethod
    def _ensure_html_structure(cls, html_content: str) -> str:
        """
        Ensure proper HTML structure for email clients.

        Args:
            html_content: HTML content

        Returns:
            Well-structured HTML content
        """
        # If no DOCTYPE or HTML tag, wrap in basic structure
        if not html_content.strip().startswith(("<!DOCTYPE", "<html")):
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email from Aprende Comigo</title>
</head>
<body>
    {html_content}
</body>
</html>"""

        return html_content

    @classmethod
    def _clean_text_content(cls, text_content: str) -> str:
        """
        Clean and format plain text content.

        Args:
            text_content: Raw text content

        Returns:
            Cleaned text content
        """
        # Remove extra whitespace and normalize line breaks
        text_content = re.sub(r"\n\s*\n\s*\n", "\n\n", text_content)  # Remove triple+ line breaks
        text_content = re.sub(r"[ \t]+", " ", text_content)  # Normalize spaces and tabs
        text_content = text_content.strip()

        return text_content

    @classmethod
    def _get_fallback_html_content(cls, context: dict[str, Any]) -> str:
        """
        Get fallback HTML content in case of rendering errors.

        Args:
            context: Context variables

        Returns:
            Basic HTML email content
        """
        school_name = context.get("school_name", "Aprende Comigo")
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message from {school_name}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #4CAF50;">Message from {school_name}</h1>
        <p>We apologize, but there was an issue rendering your email content.</p>
        <p>If you continue to experience issues, please contact us at support@aprendecomigo.com</p>
        <p>Best regards,<br>The Aprende Comigo Team</p>
    </div>
</body>
</html>"""


class EmailTemplateVariableExtractor:
    """
    Utility class for extracting template variables from email templates.
    """

    # Regex pattern to match Django template variables {{ variable_name }}
    VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\}\}")

    @classmethod
    def extract_variables(cls, template_content: str) -> set:
        """
        Extract all template variables from a template string.

        Args:
            template_content: Template content to analyze

        Returns:
            Set of variable names found in the template
        """
        matches = cls.VARIABLE_PATTERN.findall(template_content)
        return set(matches)

    @classmethod
    def extract_variables_from_template(cls, template: SchoolEmailTemplate) -> dict[str, set]:
        """
        Extract variables from all parts of an email template.

        Args:
            template: SchoolEmailTemplate instance

        Returns:
            Dictionary with variables from each template part
        """
        return {
            "subject": cls.extract_variables(template.subject_template),
            "html": cls.extract_variables(template.html_content),
            "text": cls.extract_variables(template.text_content),
        }

    @classmethod
    def get_missing_variables(cls, template: SchoolEmailTemplate, provided_context: dict[str, Any]) -> dict[str, set]:
        """
        Get variables that are used in template but not provided in context.

        Args:
            template: SchoolEmailTemplate instance
            provided_context: Context variables provided

        Returns:
            Dictionary of missing variables by template part
        """
        template_variables = cls.extract_variables_from_template(template)
        provided_variables = set(provided_context.keys())

        # Include default variables as available
        available_variables = provided_variables.union(set(EmailTemplateRenderingService.DEFAULT_VARIABLES.keys()))

        missing_variables = {}
        for part, variables in template_variables.items():
            missing = variables - available_variables
            if missing:
                missing_variables[part] = missing

        return missing_variables


class SchoolEmailTemplateManager:
    """
    Manager class for handling school email templates and defaults.
    """

    @classmethod
    def get_template_for_school(
        cls, school: School, template_type: EmailTemplateType, fallback_to_default: bool = True
    ) -> SchoolEmailTemplate | None:
        """
        Get the appropriate template for a school and template type.

        Args:
            school: School instance
            template_type: Type of email template needed
            fallback_to_default: Whether to fallback to default template

        Returns:
            SchoolEmailTemplate instance or None
        """
        try:
            # First, try to get school-specific template
            template = SchoolEmailTemplate.objects.filter(
                school=school, template_type=template_type, is_active=True
            ).first()

            if template:
                return template

            # If no school-specific template and fallback enabled, get default
            if fallback_to_default:
                template = SchoolEmailTemplate.objects.filter(
                    template_type=template_type, is_default=True, is_active=True
                ).first()

                if template:
                    return template

            logger.warning(f"No template found for school {school.id} and type {template_type}")
            return None

        except Exception as e:
            logger.error(f"Error getting template for school {school.id}: {e!s}")
            return None

    @classmethod
    def create_default_templates_for_school(cls, school: School) -> dict[str, SchoolEmailTemplate]:
        """
        Create default email templates for a new school.

        Args:
            school: School instance

        Returns:
            Dictionary of created templates by type
        """
        from .teacher_communication_templates import DefaultEmailTemplates

        created_templates = {}

        for template_type in EmailTemplateType.values:
            try:
                # Check if school already has this template type
                existing = SchoolEmailTemplate.objects.filter(school=school, template_type=template_type).exists()

                if not existing:
                    # Create from default
                    template_data = DefaultEmailTemplates.get_default_template(template_type)
                    if template_data:
                        template = SchoolEmailTemplate.objects.create(
                            school=school,
                            template_type=template_type,
                            name=template_data["name"],
                            subject_template=template_data["subject"],
                            html_content=template_data["html"],
                            text_content=template_data["text"],
                            is_default=False,
                            is_active=True,
                        )
                        created_templates[template_type] = template
                        logger.info(f"Created default {template_type} template for school {school.name}")

            except Exception as e:
                logger.error(f"Error creating default {template_type} template for school {school.id}: {e!s}")

        return created_templates


class EmailTemplateSecurityService:
    """
    Security validation service for email templates.
    """

    @classmethod
    def validate_template_security(cls, template: SchoolEmailTemplate) -> None:
        """
        Validate template content for security vulnerabilities.

        Args:
            template: SchoolEmailTemplate instance to validate

        Raises:
            ValidationError: If template contains security vulnerabilities
        """
        # Validate subject template
        SecureTemplateEngine.validate_template_content(template.subject_template)

        # Validate HTML content
        SecureTemplateEngine.validate_template_content(template.html_content)

        # Validate text content
        SecureTemplateEngine.validate_template_content(template.text_content)

        # Validate custom CSS if present
        if template.custom_css:
            cls._validate_custom_css(template.custom_css)

    @classmethod
    def _validate_custom_css(cls, css_content: str) -> None:
        """
        Validate custom CSS for security vulnerabilities.

        Args:
            css_content: CSS content to validate

        Raises:
            ValidationError: If CSS contains dangerous patterns
        """
        if not css_content:
            return

        # Check for dangerous CSS patterns
        dangerous_patterns = [
            r"@import\s+url\s*\(",
            r"javascript\s*:",
            r"expression\s*\(",
            r"behavior\s*:",
            r"-moz-binding\s*:",
            r"binding\s*:",
            r"<script",
            r"</script>",
            r"alert\s*\(",
            r"eval\s*\(",
            r"document\.",
            r"window\.",
        ]

        css_lower = css_content.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, css_lower):
                raise ValidationError(f"Custom CSS contains dangerous pattern: {pattern}")

        # Check CSS size
        if len(css_content) > 10000:  # 10KB limit
            raise ValidationError("Custom CSS too large. Maximum size is 10KB")

    @classmethod
    def _sanitize_custom_css(cls, css_content: str) -> str:
        """
        Sanitize custom CSS content.

        Args:
            css_content: CSS content to sanitize

        Returns:
            Sanitized CSS content
        """
        if not css_content:
            return ""

        try:
            # Validate first
            cls._validate_custom_css(css_content)

            # Remove dangerous patterns
            sanitized = css_content

            # Remove @import statements
            sanitized = re.sub(r"@import[^;]*;", "", sanitized, flags=re.IGNORECASE)

            # Remove javascript: URLs
            sanitized = re.sub(r"javascript\s*:", "", sanitized, flags=re.IGNORECASE)

            # Remove expression() calls
            sanitized = re.sub(r"expression\s*\([^)]*\)", "", sanitized, flags=re.IGNORECASE)

            # Remove behavior properties
            sanitized = re.sub(r"behavior\s*:[^;]*;", "", sanitized, flags=re.IGNORECASE)

            # Remove binding properties
            sanitized = re.sub(r"-?moz-binding\s*:[^;]*;", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"binding\s*:[^;]*;", "", sanitized, flags=re.IGNORECASE)

            return sanitized.strip()

        except ValidationError:
            logger.warning("Custom CSS failed validation, removing it")
            return ""
