"""
Unit tests for input sanitization business logic utilities.

These tests focus on the core business logic for input validation and sanitization
that implement "balanced security" with smart sanitization rather than strict rejection.
Tests are designed to fail initially (TDD red state) until the sanitization utilities
are implemented.

Issue #182: Align Input Validation Tests with Security Requirements
"""

import unittest

from common.security_utils import sanitize_multiline_text, sanitize_name_field, sanitize_text_content


class TestSanitizeNameField(unittest.TestCase):
    """Test sanitize_name_field() business logic for name field sanitization."""

    def test_sanitize_name_field_removes_newlines(self):
        """Test that newlines are removed from name fields."""
        input_text = "João\nSilva"
        expected = "João Silva"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_removes_carriage_returns(self):
        """Test that carriage returns are removed from name fields."""
        input_text = "Maria\rSantos"
        expected = "Maria Santos"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_removes_combined_crlf(self):
        """Test that combined CRLF sequences are properly handled."""
        input_text = "Pedro\r\nOliveira"
        expected = "Pedro Oliveira"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_preserves_international_characters(self):
        """Test that international characters are preserved."""
        input_text = "José António Ñáñez"
        expected = "José António Ñáñez"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_preserves_accents(self):
        """Test that Portuguese accents and diacritics are preserved."""
        input_text = "Conceição Çaroço"
        expected = "Conceição Çaroço"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_handles_multiple_newlines(self):
        """Test handling of multiple consecutive newlines."""
        input_text = "Ana\n\nCarla\n\n\nSilva"
        expected = "Ana Carla Silva"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_normalizes_whitespace(self):
        """Test that extra whitespace is normalized."""
        input_text = "João    Silva\nPereira"
        expected = "João Silva Pereira"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_handles_none_input(self):
        """Test handling of None input."""
        result = sanitize_name_field(None)
        self.assertIsNone(result)

    def test_sanitize_name_field_handles_empty_string(self):
        """Test handling of empty string input."""
        result = sanitize_name_field("")
        self.assertEqual(result, "")

    def test_sanitize_name_field_handles_whitespace_only(self):
        """Test handling of whitespace-only input."""
        result = sanitize_name_field("   \n\r\t   ")
        self.assertEqual(result, "")

    def test_sanitize_name_field_preserves_hyphens_and_apostrophes(self):
        """Test that valid name characters like hyphens and apostrophes are preserved."""
        input_text = "Mary-Jane O'Connor"
        expected = "Mary-Jane O'Connor"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_handles_unicode_whitespace(self):
        """Test handling of various Unicode whitespace characters."""
        input_text = "João\u00a0Silva\u2028Pereira"  # Non-breaking space and line separator
        expected = "João Silva Pereira"
        result = sanitize_name_field(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_name_field_handles_very_long_input(self):
        """Test handling of very long input strings."""
        long_name = "A" * 1000 + "\n" + "B" * 1000
        result = sanitize_name_field(long_name)
        self.assertNotIn("\n", result)
        self.assertIn("A" * 1000, result)
        self.assertIn("B" * 1000, result)


class TestSanitizeTextContent(unittest.TestCase):
    """Test sanitize_text_content() business logic for general text sanitization."""

    def test_sanitize_text_content_removes_script_tags(self):
        """Test that script tags are completely removed."""
        input_text = "Hello <script>alert('xss')</script> world"
        expected = "Hello  world"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_removes_javascript_urls(self):
        """Test that javascript: URLs are removed."""
        input_text = '<a href="javascript:alert(1)">Click me</a>'
        expected = "Click me"  # Should remove dangerous attributes but preserve text
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_removes_on_event_handlers(self):
        """Test that HTML event handlers are removed."""
        input_text = '<div onclick="alert(1)" onload="evil()">Content</div>'
        expected = "Content"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_preserves_safe_html(self):
        """Test that safe HTML tags are preserved."""
        input_text = "<p>Safe <strong>content</strong> with <em>emphasis</em></p>"
        expected = "<p>Safe <strong>content</strong> with <em>emphasis</em></p>"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_removes_iframe_tags(self):
        """Test that iframe tags are removed."""
        input_text = 'Content <iframe src="evil.com"></iframe> more content'
        expected = "Content  more content"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_removes_object_embed_tags(self):
        """Test that object and embed tags are removed."""
        input_text = "Text <object><embed></embed></object> more text"
        expected = "Text  more text"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_handles_case_variations(self):
        """Test that case variations of dangerous tags are handled."""
        input_text = "Test <SCRIPT>alert(1)</SCRIPT> and <ScRiPt>evil()</ScRiPt>"
        expected = "Test  and "
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_handles_none_input(self):
        """Test handling of None input."""
        result = sanitize_text_content(None)
        self.assertIsNone(result)

    def test_sanitize_text_content_handles_empty_string(self):
        """Test handling of empty string input."""
        result = sanitize_text_content("")
        self.assertEqual(result, "")

    def test_sanitize_text_content_preserves_plain_text(self):
        """Test that plain text without HTML is preserved."""
        input_text = "This is just plain text with no HTML"
        expected = "This is just plain text with no HTML"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_handles_encoded_attacks(self):
        """Test that HTML-encoded XSS attempts are handled."""
        input_text = "&lt;script&gt;alert(1)&lt;/script&gt;"
        result = sanitize_text_content(input_text)
        # Should not execute as JavaScript when decoded
        self.assertNotIn("<script>", result)

    def test_sanitize_text_content_removes_style_with_javascript(self):
        """Test that style attributes with JavaScript are removed."""
        input_text = '<div style="background:url(javascript:alert(1))">Content</div>'
        expected = "Content"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_preserves_international_text(self):
        """Test that international characters in text content are preserved."""
        input_text = "<p>Olá, como está? Ção é bom!</p>"
        expected = "<p>Olá, como está? Ção é bom!</p>"
        result = sanitize_text_content(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_text_content_handles_malformed_html(self):
        """Test handling of malformed HTML."""
        input_text = "<p>Unclosed paragraph <script incomplete"
        result = sanitize_text_content(input_text)
        # Should handle malformed tags gracefully
        self.assertNotIn("<script", result)


class TestSanitizeMultilineText(unittest.TestCase):
    """Test sanitize_multiline_text() business logic for notes/comments sanitization."""

    def test_sanitize_multiline_text_preserves_newlines(self):
        """Test that legitimate newlines are preserved in multiline text."""
        input_text = "Line 1\nLine 2\nLine 3"
        expected = "Line 1\nLine 2\nLine 3"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_removes_html_tags(self):
        """Test that HTML tags are removed from multiline text."""
        input_text = "Line 1\n<script>alert(1)</script>\nLine 3"
        expected = "Line 1\n\nLine 3"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_preserves_line_breaks(self):
        """Test that various line break types are handled correctly."""
        input_text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        expected = "Line 1\nLine 2\nLine 3\nLine 4"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_removes_javascript_urls(self):
        """Test that JavaScript URLs are removed from multiline content."""
        input_text = 'Comment line 1\n<a href="javascript:alert(1)">Link</a>\nComment line 2'
        expected = "Comment line 1\nLink\nComment line 2"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_handles_none_input(self):
        """Test handling of None input."""
        result = sanitize_multiline_text(None)
        self.assertIsNone(result)

    def test_sanitize_multiline_text_handles_empty_string(self):
        """Test handling of empty string input."""
        result = sanitize_multiline_text("")
        self.assertEqual(result, "")

    def test_sanitize_multiline_text_normalizes_excessive_whitespace(self):
        """Test that excessive whitespace is normalized while preserving structure."""
        input_text = "Line 1\n\n\n\nLine 2   with   spaces\n\nLine 3"
        expected = "Line 1\n\nLine 2 with spaces\n\nLine 3"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_removes_dangerous_protocols(self):
        """Test that dangerous protocols are removed."""
        input_text = "Notes:\ndata:text/html,<script>alert(1)</script>\nvbscript:msgbox(1)"
        result = sanitize_multiline_text(input_text)
        self.assertNotIn("data:", result)
        self.assertNotIn("vbscript:", result)

    def test_sanitize_multiline_text_preserves_formatting_characters(self):
        """Test that legitimate formatting characters are preserved."""
        input_text = "Notes:\n- Bullet point 1\n- Bullet point 2\n  * Sub-bullet"
        expected = "Notes:\n- Bullet point 1\n- Bullet point 2\n  * Sub-bullet"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_handles_long_content(self):
        """Test handling of very long multiline content."""
        lines = ["Line " + str(i) for i in range(100)]
        input_text = "\n".join(lines) + "\n<script>evil()</script>\nFinal line"
        result = sanitize_multiline_text(input_text)

        self.assertIn("Line 0", result)
        self.assertIn("Line 99", result)
        self.assertIn("Final line", result)
        self.assertNotIn("<script>", result)

    def test_sanitize_multiline_text_preserves_international_content(self):
        """Test that international characters are preserved in multiline text."""
        input_text = "Primeira linha\nSegunda linha com acentos: ção, ã, õ\nTerceira linha"
        expected = "Primeira linha\nSegunda linha com acentos: ção, ã, õ\nTerceira linha"
        result = sanitize_multiline_text(input_text)
        self.assertEqual(result, expected)

    def test_sanitize_multiline_text_handles_mixed_content(self):
        """Test handling of mixed legitimate and dangerous content."""
        input_text = """Student notes:
        - Good progress in mathematics
        - <script>alert('xss')</script>
        - Needs help with Portuguese
        - <iframe src="evil.com"></iframe>
        
        Teacher comments:
        - Excellent behavior in class"""

        result = sanitize_multiline_text(input_text)

        # Should preserve legitimate content
        self.assertIn("Good progress in mathematics", result)
        self.assertIn("Needs help with Portuguese", result)
        self.assertIn("Excellent behavior in class", result)

        # Should remove dangerous content
        self.assertNotIn("<script>", result)
        self.assertNotIn("<iframe>", result)

    def test_sanitize_multiline_text_removes_svg_with_javascript(self):
        """Test that SVG elements with JavaScript are removed."""
        input_text = """Notes:
        <svg onload="alert(1)">
        <text>Safe content</text>
        </svg>
        End notes"""

        result = sanitize_multiline_text(input_text)
        self.assertNotIn("<svg", result)
        self.assertNotIn("onload", result)


class TestSecurityUtilsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for security utils."""

    def test_all_functions_handle_unicode_properly(self):
        """Test that all functions handle Unicode characters properly."""
        unicode_text = "测试 🎓 العربية Ελληνικά"

        # All functions should handle Unicode without errors
        name_result = sanitize_name_field(unicode_text)
        text_result = sanitize_text_content(unicode_text)
        multiline_result = sanitize_multiline_text(unicode_text)

        self.assertIsNotNone(name_result)
        self.assertIsNotNone(text_result)
        self.assertIsNotNone(multiline_result)

    def test_functions_handle_very_large_input(self):
        """Test behavior with very large input strings."""
        large_input = "A" * 10000 + "<script>alert(1)</script>" + "B" * 10000

        # Functions should handle large inputs without crashing
        name_result = sanitize_name_field(large_input)
        text_result = sanitize_text_content(large_input)
        multiline_result = sanitize_multiline_text(large_input)

        self.assertIsNotNone(name_result)
        self.assertIsNotNone(text_result)
        self.assertIsNotNone(multiline_result)

        # Script tag should be removed from all
        self.assertNotIn("<script>", name_result)
        self.assertNotIn("<script>", text_result)
        self.assertNotIn("<script>", multiline_result)

    def test_functions_preserve_legitimate_angle_brackets(self):
        """Test that legitimate angle bracket usage is handled correctly."""
        math_text = "If x > 5 and y < 10, then x + y > 15"

        name_result = sanitize_name_field(math_text)
        text_result = sanitize_text_content(math_text)
        multiline_result = sanitize_multiline_text(math_text)

        # Should preserve mathematical operators
        self.assertIn(">", name_result)
        self.assertIn("<", name_result)
        self.assertIn(">", text_result)
        self.assertIn("<", text_result)
        self.assertIn(">", multiline_result)
        self.assertIn("<", multiline_result)

    def test_functions_are_idempotent(self):
        """Test that applying sanitization multiple times gives same result."""
        test_input = "João Silva <script>alert(1)</script>"

        # Apply sanitization twice
        first_pass = sanitize_name_field(test_input)
        second_pass = sanitize_name_field(first_pass)

        self.assertEqual(first_pass, second_pass)

        # Same for text content
        first_pass_text = sanitize_text_content(test_input)
        second_pass_text = sanitize_text_content(first_pass_text)

        self.assertEqual(first_pass_text, second_pass_text)
