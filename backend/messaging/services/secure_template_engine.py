"""
Secure Template Engine for Email Templates (Security Fix)

This module provides a sandboxed template rendering engine that prevents
template injection attacks, XSS vulnerabilities, and unauthorized code execution.
"""

import logging
import re
from typing import Any

from django.core.exceptions import ValidationError
from django.template import Context, Template, TemplateSyntaxError
from django.utils.html import escape

logger = logging.getLogger(__name__)


class SecureTemplateEngine:
    """
    Secure template engine that provides sandboxed template rendering
    with protection against injection attacks and XSS vulnerabilities.
    """

    # Allowed template tags and filters (whitelist approach)
    ALLOWED_TAGS = {
        "if",
        "endif",
        "else",
        "elif",
        "for",
        "endfor",
        "empty",
        "with",
        "endwith",
        "comment",
        "endcomment",
        "now",
        "spaceless",
        "endspaceless",
        "firstof",
        "ifequal",
        "endifequal",
        "ifnotequal",
        "endifnotequal",
        "ifchanged",
        "endifchanged",
        "regroup",
        "autoescape",
        "endautoescape",
    }

    ALLOWED_FILTERS = {
        "add",
        "addslashes",
        "capfirst",
        "center",
        "cut",
        "date",
        "default",
        "default_if_none",
        "dictsort",
        "dictsortreversed",
        "divisibleby",
        "escape",
        "escapejs",
        "filesizeformat",
        "first",
        "floatformat",
        "force_escape",
        "get_digit",
        "iriencode",
        "join",
        "last",
        "length",
        "length_is",
        "linebreaks",
        "linebreaksbr",
        "linenumbers",
        "ljust",
        "lower",
        "make_list",
        "pluralize",
        "random",
        "removetags",
        "rjust",
        "safe",
        "slice",
        "slugify",
        "stringformat",
        "striptags",
        "time",
        "timesince",
        "timeuntil",
        "title",
        "truncatechars",
        "truncatewords",
        "truncatewords_html",
        "unordered_list",
        "upper",
        "urlencode",
        "urlize",
        "urlizetrunc",
        "wordcount",
        "wordwrap",
        "yesno",
    }

    # Dangerous patterns to detect and block
    DANGEROUS_PATTERNS = [
        r"__import__",
        r"eval\s*\(",
        r"exec\s*\(",
        r"open\s*\(",
        r"file\s*\(",
        r"input\s*\(",
        r"raw_input\s*\(",
        r"compile\s*\(",
        r"globals\s*\(",
        r"locals\s*\(",
        r"vars\s*\(",
        r"dir\s*\(",
        r"getattr\s*\(",
        r"setattr\s*\(",
        r"hasattr\s*\(",
        r"delattr\s*\(",
        r"callable\s*\(",
        r"subprocess",
        r"os\.",
        r"sys\.",
        r"django\.db",
        r"django\.core\.management",
        r"__.*__",  # Dunder methods
        r"request\.META",
        r"settings\.SECRET_KEY",
        r"settings\.DATABASES",
        r"request\.user\.password",
        r"request\.session",
        r"\.password",
        r"\.secret",
        r"\.private",
        r"\.environ",
        r"\.SECRET",
        r"META\[",
        r"request\..*\.password",
        r"django\.conf",
        r"\.objects\.",  # Django ORM access
        r"User\.objects",
        r"\.filter\(",
        r"\.get\(",
        r"\.all\(",
        r"\.delete\(",
        r"\.save\(",
        r"\.create\(",
        r"\.update\(",
        # XSS and script injection patterns
        r"javascript\s*:",
        r"<script[^>]*>",
        r"<\/script>",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        # CSS injection patterns
        r"expression\s*\(",
        r"@import\s+url",
        r"-moz-binding",
        r"behavior\s*:",
        r"vbscript\s*:",
        r"data\s*:",
        # Command injection patterns
        r";\s*rm\s+-rf",
        r";\s*ls\s+",
        r";\s*cat\s+",
        r";\s*echo\s+",
        r";\s*pwd",
        r";\s*whoami",
        r";\s*id\b",
        r";\s*ps\s+",
        r";\s*kill\s+",
        r";\s*chmod\s+",
        r";\s*chown\s+",
        r"\$\([^)]+\)",  # Command substitution $(command)
        r"`[^`]+`",  # Backtick command execution
        r"&&\s*\w+",  # Command chaining
        r"\|\|\s*\w+",  # Command chaining
    ]

    # Maximum template size (to prevent DoS)
    MAX_TEMPLATE_SIZE = 50000  # 50KB

    # Maximum nesting depth
    MAX_NESTING_DEPTH = 10

    @classmethod
    def validate_template_content(cls, template_content: str) -> None:
        """
        Validate template content for security vulnerabilities.

        Args:
            template_content: Template content to validate

        Raises:
            ValidationError: If template content is unsafe
        """
        if not isinstance(template_content, str):
            raise ValidationError("Template content must be a string")

        # Check template size
        if len(template_content) > cls.MAX_TEMPLATE_SIZE:
            raise ValidationError(f"Template too large. Maximum size is {cls.MAX_TEMPLATE_SIZE} characters")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, template_content, re.IGNORECASE):
                raise ValidationError(f"Template contains dangerous pattern: {pattern}")

        # Validate Django template syntax
        try:
            Template(template_content)
        except TemplateSyntaxError as e:
            raise ValidationError(f"Invalid template syntax: {e!s}")

        # Check for disallowed tags and filters
        cls._validate_template_tags_and_filters(template_content)

        # Check nesting depth
        cls._validate_nesting_depth(template_content)

    @classmethod
    def _validate_template_tags_and_filters(cls, template_content: str) -> None:
        """
        Validate that only allowed template tags and filters are used.

        Args:
            template_content: Template content to validate

        Raises:
            ValidationError: If disallowed tags or filters are found
        """
        # Extract template tags
        tag_pattern = r"\{\%\s*(\w+)"
        tags = re.findall(tag_pattern, template_content)

        for tag in tags:
            if tag not in cls.ALLOWED_TAGS:
                raise ValidationError(f"Disallowed template tag: {tag}")

        # Extract filters
        filter_pattern = r"\|\s*(\w+)"
        filters = re.findall(filter_pattern, template_content)

        for filter_name in filters:
            if filter_name not in cls.ALLOWED_FILTERS:
                raise ValidationError(f"Disallowed template filter: {filter_name}")

    @classmethod
    def _validate_nesting_depth(cls, template_content: str) -> None:
        """
        Validate template nesting depth to prevent DoS attacks.

        Args:
            template_content: Template content to validate

        Raises:
            ValidationError: If nesting depth exceeds maximum
        """
        depth = 0
        max_depth = 0

        # Parse template tags regardless of line breaks
        # Find all opening and closing template tags
        tag_pattern = r"\{\%\s*(\w+)(?:\s+[^%]+)?\s*\%\}"
        tags = re.findall(tag_pattern, template_content)

        for tag in tags:
            if tag in ["for", "if", "with", "block", "spaceless", "autoescape", "comment"]:
                depth += 1
                max_depth = max(max_depth, depth)
            elif tag.startswith("end"):  # endfor, endif, endwith, etc.
                depth -= 1

        if max_depth > cls.MAX_NESTING_DEPTH:
            raise ValidationError(f"Template nesting too deep. Maximum depth is {cls.MAX_NESTING_DEPTH}")

    @classmethod
    def sanitize_context_variables(cls, context: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize context variables to prevent injection attacks.

        Args:
            context: Context variables to sanitize

        Returns:
            Sanitized context variables
        """
        sanitized = {}

        for key, value in context.items():
            # Validate key
            if not cls._is_safe_variable_name(key):
                logger.warning(f"Skipping unsafe variable name: {key}")
                continue

            # Sanitize value
            sanitized[key] = cls._sanitize_value(value)

        return sanitized

    @classmethod
    def _is_safe_variable_name(cls, name: str) -> bool:
        """
        Check if a variable name is safe to use.

        Args:
            name: Variable name to check

        Returns:
            True if name is safe, False otherwise
        """
        # Only allow alphanumeric characters and underscores
        # Must start with letter or underscore
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        if not re.match(pattern, name):
            return False

        # Disallow dunder names
        if name.startswith("__") and name.endswith("__"):
            return False

        # Disallow certain reserved names
        reserved_names = {
            "eval",
            "exec",
            "open",
            "file",
            "input",
            "compile",
            "globals",
            "locals",
            "vars",
            "dir",
            "import",
        }
        return name.lower() not in reserved_names

    @classmethod
    def _sanitize_value(cls, value: Any) -> Any:
        """
        Sanitize a context value.

        Args:
            value: Value to sanitize

        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            # Escape HTML entities to prevent XSS
            return escape(value)
        elif isinstance(value, int | float | bool | type(None)):
            # Safe primitive types
            return value
        elif isinstance(value, list | tuple):
            # Recursively sanitize list/tuple items
            return type(value)(cls._sanitize_value(item) for item in value)
        elif isinstance(value, dict):
            # Recursively sanitize dictionary values
            return {k: cls._sanitize_value(v) for k, v in value.items() if cls._is_safe_variable_name(str(k))}
        else:
            # For other types, convert to string and escape
            return escape(str(value))

    @classmethod
    def render_template(cls, template_content: str, context: dict[str, Any], auto_escape: bool = True) -> str:
        """
        Securely render a template with the given context.

        Args:
            template_content: Template content to render
            context: Context variables for rendering
            auto_escape: Whether to auto-escape variables

        Returns:
            Rendered template content

        Raises:
            ValidationError: If template or context is unsafe
        """
        try:
            # Validate template content
            cls.validate_template_content(template_content)

            # Sanitize context variables
            sanitized_context = cls.sanitize_context_variables(context)

            # Create Django template with autoescape enabled
            template = Template(template_content)
            django_context = Context(sanitized_context, autoescape=auto_escape)

            # Render template
            rendered = template.render(django_context)

            logger.info("Template rendered securely")
            return rendered

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e!s}")
            raise ValidationError(f"Template syntax error: {e!s}")
        except Exception as e:
            logger.error(f"Template rendering error: {e!s}")
            raise ValidationError(f"Template rendering failed: {e!s}")


class HTMLSanitizer:
    """
    HTML sanitizer for email content to prevent XSS attacks.
    """

    # Allowed HTML tags for email content
    ALLOWED_TAGS = {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "span",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "a",
        "img",
        "table",
        "tr",
        "td",
        "th",
        "thead",
        "tbody",
        "blockquote",
        "pre",
        "code",
    }

    # Allowed attributes for specific tags
    ALLOWED_ATTRIBUTES = {
        "a": {"href", "title", "target"},
        "img": {"src", "alt", "width", "height", "style"},
        "span": {"style", "class"},
        "div": {"style", "class"},
        "p": {"style", "class"},
        "h1": {"style", "class"},
        "h2": {"style", "class"},
        "h3": {"style", "class"},
        "h4": {"style", "class"},
        "h5": {"style", "class"},
        "h6": {"style", "class"},
        "table": {"style", "class", "cellpadding", "cellspacing", "border"},
        "td": {"style", "class", "colspan", "rowspan"},
        "th": {"style", "class", "colspan", "rowspan"},
    }

    # Allowed CSS properties
    ALLOWED_CSS_PROPERTIES = {
        "color",
        "background-color",
        "font-family",
        "font-size",
        "font-weight",
        "text-align",
        "text-decoration",
        "line-height",
        "margin",
        "padding",
        "border",
        "border-color",
        "border-width",
        "border-style",
        "width",
        "height",
        "max-width",
        "max-height",
        "display",
        "float",
        "clear",
        "vertical-align",
    }

    @classmethod
    def sanitize_html(cls, html_content: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.

        Args:
            html_content: HTML content to sanitize

        Returns:
            Sanitized HTML content
        """
        if not html_content:
            return ""

        try:
            # First, escape any potentially dangerous content
            html_content = cls._pre_sanitize(html_content)

            # Parse and sanitize HTML structure
            sanitized = cls._sanitize_html_structure(html_content)

            # Sanitize inline styles
            sanitized = cls._sanitize_css(sanitized)

            return sanitized

        except Exception as e:
            logger.error(f"HTML sanitization error: {e!s}")
            # Return escaped version as fallback
            return escape(html_content)

    @classmethod
    def _pre_sanitize(cls, html_content: str) -> str:
        """
        Pre-sanitize HTML content by removing dangerous elements.

        Args:
            html_content: HTML content to pre-sanitize

        Returns:
            Pre-sanitized HTML content
        """
        # Remove script tags and their content
        html_content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)

        # Remove style tags with dangerous content
        html_content = re.sub(r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL | re.IGNORECASE)

        # Remove dangerous event handlers
        dangerous_attributes = [
            "onclick",
            "onload",
            "onerror",
            "onmouseover",
            "onmouseout",
            "onfocus",
            "onblur",
            "onchange",
            "onsubmit",
            "onreset",
            "onkeydown",
            "onkeyup",
            "onkeypress",
        ]

        for attr in dangerous_attributes:
            pattern = rf'{attr}\s*=\s*["\'][^"\']*["\']'
            html_content = re.sub(pattern, "", html_content, flags=re.IGNORECASE)

        # Remove javascript: URLs
        html_content = re.sub(r"javascript\s*:", "", html_content, flags=re.IGNORECASE)

        # Remove data: URLs (except for images)
        html_content = re.sub(r'href\s*=\s*["\']data:', 'href="#"', html_content, flags=re.IGNORECASE)

        return html_content

    @classmethod
    def _sanitize_html_structure(cls, html_content: str) -> str:
        """
        Sanitize HTML structure by removing disallowed tags and attributes.

        Args:
            html_content: HTML content to sanitize

        Returns:
            Sanitized HTML content
        """
        # This is a simplified implementation
        # In production, consider using a library like bleach

        # Remove all tags except allowed ones
        def replace_tag(match):
            full_tag = match.group(0)
            tag_name = match.group(2).lower()

            if tag_name in cls.ALLOWED_TAGS:
                return full_tag
            else:
                # Remove the tag but keep the content
                return ""

        # Remove disallowed tags but keep content
        html_content = re.sub(r"<(/?)(\w+)([^>]*)>", replace_tag, html_content)

        return html_content

    @classmethod
    def _sanitize_css(cls, html_content: str) -> str:
        """
        Sanitize CSS in style attributes.

        Args:
            html_content: HTML content with style attributes

        Returns:
            HTML content with sanitized CSS
        """

        def sanitize_style_attribute(match):
            style_content = match.group(1)
            sanitized_styles = []

            # Parse CSS properties
            for prop in style_content.split(";"):
                if ":" in prop:
                    property_name, property_value = prop.split(":", 1)
                    property_name = property_name.strip().lower()
                    property_value = property_value.strip()

                    if property_name in cls.ALLOWED_CSS_PROPERTIES and cls._is_safe_css_value(property_value):
                        sanitized_styles.append(f"{property_name}: {property_value}")

            return f'style="{"; ".join(sanitized_styles)}"'

        # Sanitize style attributes
        html_content = re.sub(
            r'style\s*=\s*["\']([^"\']*)["\']', sanitize_style_attribute, html_content, flags=re.IGNORECASE
        )

        return html_content

    @classmethod
    def _is_safe_css_value(cls, value: str) -> bool:
        """
        Check if a CSS value is safe.

        Args:
            value: CSS value to check

        Returns:
            True if value is safe, False otherwise
        """
        # Remove dangerous patterns from CSS values
        dangerous_patterns = [
            "expression",
            "javascript:",
            "vbscript:",
            "data:",
            "behavior:",
            "-moz-binding",
            "binding:",
        ]

        value_lower = value.lower()
        return all(pattern not in value_lower for pattern in dangerous_patterns)


class TemplateVariableValidator:
    """
    Validator for template variables and context data.
    """

    # Maximum string length for variables
    MAX_STRING_LENGTH = 10000

    # Maximum nesting depth for objects
    MAX_OBJECT_DEPTH = 5

    @classmethod
    def validate_context(cls, context: dict[str, Any]) -> None:
        """
        Validate template context for security and safety.

        Args:
            context: Context dictionary to validate

        Raises:
            ValidationError: If context contains unsafe data
        """
        if not isinstance(context, dict):
            raise ValidationError("Context must be a dictionary")

        cls._validate_object(context, depth=0)

    @classmethod
    def _validate_object(cls, obj: Any, depth: int = 0) -> None:
        """
        Recursively validate an object for safety.

        Args:
            obj: Object to validate
            depth: Current nesting depth

        Raises:
            ValidationError: If object is unsafe
        """
        if depth > cls.MAX_OBJECT_DEPTH:
            raise ValidationError(f"Object nesting too deep. Maximum depth is {cls.MAX_OBJECT_DEPTH}")

        if isinstance(obj, str):
            if len(obj) > cls.MAX_STRING_LENGTH:
                raise ValidationError(f"String too long. Maximum length is {cls.MAX_STRING_LENGTH}")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if not isinstance(key, str):
                    raise ValidationError("Dictionary keys must be strings")
                cls._validate_object(value, depth + 1)
        elif isinstance(obj, list | tuple):
            for item in obj:
                cls._validate_object(item, depth + 1)
        elif callable(obj):
            raise ValidationError("Callable objects are not allowed in template context")
        elif hasattr(obj, "__dict__") and not isinstance(obj, int | float | bool | type(None)):
            # Custom objects - validate their attributes
            for attr_name in dir(obj):
                if not attr_name.startswith("_"):  # Skip private attributes
                    try:
                        attr_value = getattr(obj, attr_name)
                        if not callable(attr_value):
                            cls._validate_object(attr_value, depth + 1)
                    except AttributeError:
                        pass  # Skip if attribute can't be accessed
