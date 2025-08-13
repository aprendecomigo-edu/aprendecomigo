"""
Security utilities for input sanitization and validation.

This module provides robust input sanitization functions that implement "balanced security" -
removing dangerous content while preserving legitimate user input and international characters.

Used across Django serializers to ensure consistent and secure input handling throughout
the Aprende Comigo platform.
"""

import re
import bleach
from typing import Optional, Union
import html


# Allowed HTML tags for rich text content (safe formatting tags)
ALLOWED_HTML_TAGS_RICH_TEXT = {
    'p', 'br', 'strong', 'em', 'b', 'i', 'u'
}

# Allowed HTML tags for multiline plain text (very restrictive)
ALLOWED_HTML_TAGS_PLAIN_TEXT = {
    'br'  # Only line breaks allowed
}

# Allowed HTML attributes (very restrictive)
ALLOWED_HTML_ATTRIBUTES = {}

# Dangerous protocols to remove
DANGEROUS_PROTOCOLS = {
    'javascript:', 'vbscript:', 'data:', 'file:', 'ftp:'
}


def sanitize_name_field(value: Union[str, None]) -> Optional[str]:
    """
    Sanitize name fields by removing dangerous characters while preserving international characters.
    
    - Removes newlines, carriage returns, and tabs
    - Preserves international characters (accents, diacritics, etc.)
    - Normalizes whitespace (multiple spaces become single space)
    - Handles edge cases like None, empty strings
    
    Args:
        value: The name string to sanitize
        
    Returns:
        Sanitized name string, empty string if empty, or None if input was None
        
    Examples:
        >>> sanitize_name_field("João\nSilva")
        "João Silva"
        >>> sanitize_name_field("José  María")
        "José María"
        >>> sanitize_name_field(None)
        None
        >>> sanitize_name_field("")
        ""
    """
    if value is None:
        return None
        
    if not isinstance(value, str):
        value = str(value)
    
    # If originally empty, return empty string
    if not value:
        return ""
    
    # First, remove any HTML tags (including script tags) from names - names should be plain text
    # But preserve mathematical operators like > and < when not part of HTML tags
    sanitized = re.sub(r'<[a-zA-Z/][^>]*>', '', value)
    
    # Remove newlines, carriage returns, and tabs
    sanitized = re.sub(r'[\n\r\t]+', ' ', sanitized)
    
    # Remove other problematic whitespace characters but preserve normal spaces
    # Unicode categories for whitespace: \s includes many Unicode whitespace chars
    sanitized = re.sub(r'[\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]+', ' ', sanitized)
    
    # Normalize multiple spaces to single space
    sanitized = re.sub(r' +', ' ', sanitized)
    
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    
    # Return empty string if result is empty (was only whitespace/newlines), None for actual None input
    return sanitized


def sanitize_text_content(value: Union[str, None]) -> Optional[str]:
    """
    Sanitize text content by removing dangerous HTML/JavaScript while preserving safe text.
    
    - Removes script tags and their content completely
    - Removes dangerous HTML attributes and protocols
    - Preserves legitimate text content and international characters
    - Handles various XSS attack vectors
    
    Args:
        value: The text content to sanitize
        
    Returns:
        Sanitized text content, empty string if empty, or None if input was None
        
    Examples:
        >>> sanitize_text_content("<script>alert(1)</script>Hello")
        "Hello"
        >>> sanitize_text_content("Good work, José!")
        "Good work, José!"
    """
    if value is None:
        return None
        
    if not isinstance(value, str):
        value = str(value)
    
    # If originally empty, return empty string
    if not value:
        return ""
    
    # First, decode HTML entities to catch encoded attacks
    sanitized = html.unescape(value)
    
    # Then remove script tags and their entire content, including malformed ones
    # Case insensitive removal of script tags (complete and incomplete)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    # Also remove incomplete script tags or any text starting with "<script"
    sanitized = re.sub(r'<script[^>]*$', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'<script\s[^>]*$', '', sanitized, flags=re.IGNORECASE)
    
    # Remove dangerous protocols in dangerous contexts
    # Remove protocols from HTML attribute contexts
    sanitized = re.sub(r'\b(?:src|href|action|formaction|data)\s*=\s*["\']?(?:javascript|vbscript|data|file|ftp):[^"\'>\s]*["\']?', '', sanitized, flags=re.IGNORECASE)
    
    # Remove protocols from style attributes and CSS url() functions
    sanitized = re.sub(r'url\s*\(\s*["\']?(?:javascript|vbscript|data|file):[^"\')\s]*["\']?\s*\)', '', sanitized, flags=re.IGNORECASE)
    
    # Remove dangerous protocol + content combinations that could be executable
    sanitized = re.sub(r'data:text/html,.*?<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:[^,\s]+\([^)]*\)', '', sanitized, flags=re.IGNORECASE)  # Remove js function calls
    sanitized = re.sub(r'vbscript:[^,\s]+\([^)]*\)', '', sanitized, flags=re.IGNORECASE)    # Remove vbs function calls
    
    # Remove javascript: and vbscript: from onclick and similar attributes
    sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # Use bleach to sanitize remaining HTML but don't escape standalone angle brackets
    sanitized = bleach.clean(
        sanitized,
        tags=ALLOWED_HTML_TAGS_RICH_TEXT,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    # After bleach processing, restore legitimate angle brackets that were escaped
    sanitized = sanitized.replace('&lt;', '<').replace('&gt;', '>')
    sanitized = sanitized.replace('&amp;', '&')  # Also restore ampersands
    
    # Don't normalize all whitespace - only normalize excessive whitespace but preserve intentional spaces
    sanitized = re.sub(r'[ \t]{3,}', '  ', sanitized)  # Reduce 3+ spaces to 2 spaces  
    sanitized = re.sub(r'\n+', ' ', sanitized)  # Convert newlines to spaces
    # Only strip leading whitespace, preserve trailing if it was intentional
    sanitized = sanitized.lstrip()
    
    # Return the sanitized result (could be empty string)
    return sanitized


def sanitize_multiline_text(value: Union[str, None]) -> Optional[str]:
    """
    Sanitize multiline text content (like notes/comments) while preserving legitimate formatting.
    
    - Preserves legitimate line breaks and paragraphs
    - Removes dangerous HTML/JavaScript content
    - Normalizes excessive whitespace while maintaining structure
    - Handles international characters properly
    
    Args:
        value: The multiline text to sanitize
        
    Returns:
        Sanitized multiline text, empty string if empty, or None if input was None
        
    Examples:
        >>> sanitize_multiline_text("Good job!\\nKeep it up!")
        "Good job!\\nKeep it up!"
        >>> sanitize_multiline_text("<script>evil()</script>\\nGood work!")
        "Good work!"
    """
    if value is None:
        return None
        
    if not isinstance(value, str):
        value = str(value)
    
    # If originally empty, return empty string
    if not value:
        return ""
    
    # First sanitize dangerous content like scripts using the text sanitizer
    # But we need to be careful not to lose legitimate newlines
    
    # Remove dangerous protocol + content combinations FIRST (before removing scripts)
    # Remove data:text/html URLs that contain scripts (but preserve text after HTML tags)
    # Only remove the dangerous URL itself, not everything after it
    sanitized = re.sub(r'data:text/html,[^"\'>\s]*<script[^>]*>.*?</script>[^"\'>\s]*', '', value, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove script tags and their entire content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous protocols in dangerous contexts (same as sanitize_text_content)
    # Remove protocols from HTML attribute contexts
    sanitized = re.sub(r'\b(?:src|href|action|formaction|data)\s*=\s*["\']?(?:javascript|vbscript|data|file|ftp):[^"\'>\s]*["\']?', '', sanitized, flags=re.IGNORECASE)
    
    # Remove protocols from style attributes and CSS url() functions
    sanitized = re.sub(r'url\s*\(\s*["\']?(?:javascript|vbscript|data|file):[^"\')\s]*["\']?\s*\)', '', sanitized, flags=re.IGNORECASE)
    
    # Remove only specific dangerous function calls that could be executed in certain contexts
    # Only remove when they appear to be in executable contexts (like standalone on a line)
    # Don't remove when they're clearly part of descriptive text
    sanitized = re.sub(r'^javascript:(alert|eval|confirm|prompt|setTimeout|setInterval|Function)\s*\([^)]*\)\s*$', '', sanitized, flags=re.IGNORECASE | re.MULTILINE)
    sanitized = re.sub(r'^vbscript:(msgbox|eval|execute|executeglobal)\s*\([^)]*\)\s*$', '', sanitized, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove javascript: and vbscript: from onclick and similar attributes
    sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # Use bleach to sanitize remaining HTML but preserve structure
    sanitized = bleach.clean(
        sanitized,
        tags=ALLOWED_HTML_TAGS_PLAIN_TEXT,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True
    )
    
    # Clean up HTML entities
    sanitized = html.unescape(sanitized)
    
    # Now handle multiline-specific formatting
    # Replace Windows line endings with Unix ones
    sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')
    
    # Reduce multiple consecutive newlines to maximum 2 (paragraph break)
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
    
    # Clean up trailing spaces but preserve leading spaces (for formatting like bullets)
    sanitized = re.sub(r'[ \t]+\n', '\n', sanitized)  # Remove trailing spaces
    
    # Normalize tabs to single spaces
    sanitized = sanitized.replace('\t', ' ')
    
    # Normalize multiple spaces within lines (but preserve line structure and leading spaces)
    lines = sanitized.split('\n')
    normalized_lines = []
    for line in lines:
        # Preserve leading spaces but normalize internal multiple spaces
        leading_spaces = len(line) - len(line.lstrip(' '))
        content = line.lstrip(' ')
        if content:
            normalized_content = re.sub(r' +', ' ', content)
            normalized_line = ' ' * leading_spaces + normalized_content
        else:
            normalized_line = ''
        normalized_lines.append(normalized_line)
    
    # Rejoin with newlines, but don't remove empty lines completely
    # as they might be intentional paragraph breaks
    sanitized = '\n'.join(normalized_lines)
    
    # Remove excessive empty lines at start/end but preserve internal structure
    sanitized = re.sub(r'^\n+', '', sanitized)  # Remove leading newlines
    sanitized = re.sub(r'\n+$', '', sanitized)  # Remove trailing newlines
    
    return sanitized


def is_safe_url(url: Union[str, None]) -> bool:
    """
    Check if a URL is safe (doesn't contain dangerous protocols).
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return True
        
    url_lower = url.lower().strip()
    
    for protocol in DANGEROUS_PROTOCOLS:
        if url_lower.startswith(protocol):
            return False
            
    return True


def sanitize_html_attributes(html_content: str) -> str:
    """
    Remove dangerous HTML attributes like onclick, onload, etc.
    
    Args:
        html_content: HTML content to sanitize
        
    Returns:
        HTML content with dangerous attributes removed
    """
    if not html_content:
        return html_content
    
    # Remove event handlers
    html_content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    # Remove style attributes that might contain JavaScript
    html_content = re.sub(r'style\s*=\s*["\'][^"\']*javascript[^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    return html_content


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace characters in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return text
        
    # Normalize various Unicode whitespace characters to regular spaces
    text = re.sub(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]+', ' ', text)
    
    # Normalize multiple spaces to single space
    text = re.sub(r' +', ' ', text)
    
    return text.strip()