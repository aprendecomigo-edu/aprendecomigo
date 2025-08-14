/**
 * Text sanitization utilities for preventing XSS attacks and ensuring safe text display.
 *
 * This module provides functions to sanitize user input before displaying it in the UI,
 * preventing potential security vulnerabilities while maintaining readability.
 */

/**
 * Sanitizes text by removing potentially dangerous characters and HTML tags.
 * This is a simple sanitization for React Native Text components.
 *
 * @param text - The text to sanitize
 * @returns Sanitized text safe for display
 */
export const sanitizeText = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  return (
    text
      // Remove HTML tags
      .replace(/<[^>]*>/g, '')
      // Remove script-related content
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '')
      // Remove excessive whitespace
      .replace(/\s+/g, ' ')
      // Trim whitespace
      .trim()
      // Limit length for safety (prevent extremely long strings)
      .slice(0, 1000)
  );
};

/**
 * Sanitizes and truncates text for display in UI components.
 *
 * @param text - The text to sanitize and truncate
 * @param maxLength - Maximum length of the text (default: 500)
 * @param addEllipsis - Whether to add ellipsis when truncating (default: true)
 * @returns Sanitized and truncated text
 */
export const sanitizeAndTruncateText = (
  text: string,
  maxLength: number = 500,
  addEllipsis: boolean = true
): string => {
  const sanitized = sanitizeText(text);

  if (sanitized.length <= maxLength) {
    return sanitized;
  }

  const truncated = sanitized.slice(0, maxLength);
  return addEllipsis ? `${truncated}...` : truncated;
};

/**
 * Sanitizes text specifically for invitation custom messages.
 * This is more permissive as it allows basic punctuation and formatting.
 *
 * @param message - The custom message to sanitize
 * @returns Sanitized message
 */
export const sanitizeInvitationMessage = (message: string): string => {
  if (!message || typeof message !== 'string') {
    return '';
  }

  return (
    message
      // Remove HTML tags but preserve basic formatting characters
      .replace(/<[^>]*>/g, '')
      // Remove script-related content
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '')
      // Normalize whitespace but preserve line breaks
      .replace(/[ \t]+/g, ' ')
      .replace(/\n\s*\n/g, '\n')
      // Trim whitespace
      .trim()
      // Limit length for invitation messages
      .slice(0, 500)
  );
};

/**
 * Validates if text contains potentially dangerous content.
 *
 * @param text - The text to validate
 * @returns true if text appears safe, false if potentially dangerous
 */
export const isTextSafe = (text: string): boolean => {
  if (!text || typeof text !== 'string') {
    return true;
  }

  const dangerousPatterns = [
    /<script[^>]*>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe[^>]*>/gi,
    /<object[^>]*>/gi,
    /<embed[^>]*>/gi,
  ];

  return !dangerousPatterns.some(pattern => pattern.test(text));
};
