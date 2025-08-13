"""
DRF API tests for security validation improvements (Issue #182).

These tests implement "balanced security" approach with smart sanitization 
instead of strict rejection for input validation. Tests are initially 
designed to FAIL to follow TDD methodology.

Key improvements tested:
1. StudentInfoSerializer name validation: sanitize newlines but preserve international chars
2. PurchaseApprovalActionSerializer parent_notes: sanitize HTML but preserve safe content
3. Smart sanitization behavior instead of rejection

IMPORTANT: These tests should initially FAIL because current validation 
logic doesn't implement smart sanitization yet. We're in TDD red state.
"""

from decimal import Decimal
from django.test import TestCase
from rest_framework import serializers as drf_serializers

from common.test_base import BaseAPITestCase
from finances.serializers import StudentInfoSerializer, PurchaseApprovalActionSerializer


class TestStudentInfoSerializerSmartSanitization(BaseAPITestCase):
    """
    Test suite for StudentInfoSerializer smart sanitization (Issue #182).
    
    Tests expect SANITIZATION behavior instead of REJECTION for:
    - Names with newlines should be sanitized, not rejected
    - International characters should be preserved
    - Multiple consecutive newlines should be cleaned
    """

    def test_name_newline_sanitization_single_newline(self):
        """Test single newline in name is sanitized, not rejected."""
        data = {
            'name': 'João\nSilva',
            'email': 'joao.silva@example.com'
        }
        
        serializer = StudentInfoSerializer(data=data)
        # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
        self.assertTrue(serializer.is_valid(), 
                       f"Should sanitize newline, not reject. Errors: {serializer.errors}")
        
        # Should sanitize newline to space
        self.assertEqual(serializer.validated_data['name'], 'João Silva')

    def test_name_multiple_newlines_sanitization(self):
        """Test multiple newlines are sanitized to single spaces."""
        data = {
            'name': 'Maria\n\nSantos\nJosé',
            'email': 'maria@example.com'
        }
        
        serializer = StudentInfoSerializer(data=data)
        # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
        self.assertTrue(serializer.is_valid(),
                       f"Should sanitize multiple newlines. Errors: {serializer.errors}")
        
        # Multiple newlines should be normalized to single spaces
        self.assertEqual(serializer.validated_data['name'], 'Maria Santos José')

    def test_name_carriage_return_sanitization(self):
        """Test carriage returns (\r) are sanitized."""
        data = {
            'name': 'Pedro\rCarlos\r\nSilva',
            'email': 'pedro@example.com'
        }
        
        serializer = StudentInfoSerializer(data=data)
        # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
        self.assertTrue(serializer.is_valid(),
                       f"Should sanitize carriage returns. Errors: {serializer.errors}")
        
        # Carriage returns and CRLF should be sanitized to spaces
        self.assertEqual(serializer.validated_data['name'], 'Pedro Carlos Silva')

    def test_name_tab_character_sanitization(self):
        """Test tab characters are sanitized."""
        data = {
            'name': 'Ana\tLucia\tCosta',
            'email': 'ana@example.com'
        }
        
        serializer = StudentInfoSerializer(data=data)
        # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
        self.assertTrue(serializer.is_valid(),
                       f"Should sanitize tab characters. Errors: {serializer.errors}")
        
        # Tab characters should be sanitized to spaces
        self.assertEqual(serializer.validated_data['name'], 'Ana Lucia Costa')

    def test_name_mixed_whitespace_sanitization(self):
        """Test mixed whitespace characters are sanitized."""
        data = {
            'name': 'José\n\t  \rAntônio\n Silva',
            'email': 'jose@example.com'
        }
        
        serializer = StudentInfoSerializer(data=data)
        # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects  
        self.assertTrue(serializer.is_valid(),
                       f"Should sanitize mixed whitespace. Errors: {serializer.errors}")
        
        # Mixed whitespace should be normalized to single spaces
        self.assertEqual(serializer.validated_data['name'], 'José Antônio Silva')

    def test_name_preserves_international_characters_after_sanitization(self):
        """Test international characters are preserved during sanitization."""
        international_names = [
            ('João\nDa\nSilva', 'João Da Silva'),
            ('María\tGonzález', 'María González'), 
            ('Müller\nÖzkan', 'Müller Özkan'),
            ('François\r\nDupont', 'François Dupont'),
            ('Søren\nØlsen', 'Søren Ølsen'),
            ('Aleksandr\tПетров', 'Aleksandr Петров'),  # Mixed scripts
        ]
        
        for input_name, expected_output in international_names:
            with self.subTest(name=input_name):
                data = {
                    'name': input_name,
                    'email': 'test@example.com'
                }
                
                serializer = StudentInfoSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize and preserve international chars for: {input_name}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['name'], expected_output)

    def test_name_edge_cases_sanitization(self):
        """Test edge cases in name sanitization."""
        edge_cases = [
            ('   João\n\n  Silva   ', 'João Silva'),  # Leading/trailing whitespace + newlines
            ('\nMaria\n', 'Maria'),  # Leading/trailing newlines
            ('Pedro\n\n\n\nCarlos', 'Pedro Carlos'),  # Many consecutive newlines
            ('A\nB\nC\nD', 'A B C D'),  # Multiple single-char parts
        ]
        
        for input_name, expected_output in edge_cases:
            with self.subTest(name=input_name):
                data = {
                    'name': input_name,
                    'email': 'test@example.com'
                }
                
                serializer = StudentInfoSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should handle edge case: {repr(input_name)}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['name'], expected_output)

    def test_name_empty_after_sanitization_should_fail(self):
        """Test names that become empty after sanitization should still fail."""
        invalid_names = [
            '\n\n\n',  # Only newlines
            '\t\r\n  ',  # Only whitespace
            '',  # Already empty
        ]
        
        for name in invalid_names:
            with self.subTest(name=repr(name)):
                data = {
                    'name': name,
                    'email': 'test@example.com'
                }
                
                serializer = StudentInfoSerializer(data=data)
                # These should still fail validation after sanitization
                self.assertFalse(serializer.is_valid(),
                                f"Should reject empty name after sanitization: {repr(name)}")
                self.assertIn('name', serializer.errors)


class TestPurchaseApprovalActionSerializerSmartSanitization(BaseAPITestCase):
    """
    Test suite for PurchaseApprovalActionSerializer smart sanitization (Issue #182).
    
    Tests expect SANITIZATION behavior instead of REJECTION for:
    - HTML content should be sanitized but text preserved
    - Script tags should be removed but safe content kept
    - XSS attempts should be neutralized, not rejected entirely
    """

    def test_parent_notes_html_sanitization_basic(self):
        """Test basic HTML tags are stripped but text content preserved."""
        test_cases = [
            ('<b>Approved</b> for good grades', 'Approved for good grades'),
            ('<i>Please</i> <u>be careful</u> with spending', 'Please be careful with spending'),
            ('<div>This is approved</div>', 'This is approved'),
            ('<p>Good job this month!</p>', 'Good job this month!'),
            ('<span>Conditional approval</span>', 'Conditional approval'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize HTML, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_script_tag_sanitization(self):
        """Test script tags are removed but safe content preserved."""
        test_cases = [
            ('<script>alert(1)</script>Good job!', 'Good job!'),
            ('Approved! <script>evil()</script>Well done.', 'Approved! Well done.'),
            ('<script src="evil.js"></script>This is fine', 'This is fine'),
            ('Text<script>alert("xss")</script>More text', 'TextMore text'),
            ('Before<script>malicious</script>After', 'BeforeAfter'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve', 
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize script tags, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_javascript_url_sanitization(self):
        """Test javascript: URLs are sanitized but text preserved."""
        test_cases = [
            ('Click <a href="javascript:alert()">here</a> for info', 'Click here for info'),
            ('javascript:void(0) - This is approved', 'javascript:void(0) - This is approved'),  # Not in URL context
            ('<img src="javascript:evil()" />Good work!', 'Good work!'),
            ('Link: javascript:alert() but this text is fine', 'Link: javascript:alert() but this text is fine'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize javascript URLs, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_data_url_sanitization(self):
        """Test data: URLs are sanitized but text preserved."""
        test_cases = [
            ('<img src="data:text/html,<script>alert()</script>" />Approved!', 'Approved!'),
            ('data:text/plain,hello - this context is fine', 'data:text/plain,hello - this context is fine'),
            ('<iframe src="data:text/html,evil"></iframe>Good job', 'Good job'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize data URLs, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_vbscript_sanitization(self):
        """Test vbscript: URLs are sanitized but text preserved.""" 
        test_cases = [
            ('<a href="vbscript:msgbox()">Click</a> - Approved!', 'Click - Approved!'),
            ('vbscript:evil() but this text is okay', 'vbscript:evil() but this text is okay'),  # Not in URL
            ('<button onclick="vbscript:bad()">OK</button>Good work', 'OKGood work'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'deny',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize vbscript, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_html_entities_preserved(self):
        """Test HTML entities are properly handled during sanitization."""
        test_cases = [
            ('&lt;Approved&gt; for good behavior', '<Approved> for good behavior'), 
            ('Cost: &euro;25.50 - approved!', 'Cost: €25.50 - approved!'),
            ('Good job &amp; keep it up!', 'Good job & keep it up!'),
            ('Grade: &gt; 85% - excellent!', 'Grade: > 85% - excellent!'),
        ]
        
        for input_notes, expected_output in test_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should handle HTML entities: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_complex_xss_sanitization(self):
        """Test complex XSS attempts are sanitized but safe content preserved."""
        complex_cases = [
            (
                '<img src=x onerror="alert(1)">This purchase is approved!',
                'This purchase is approved!'
            ),
            (
                'Approved! <svg onload="alert()"></svg>Well done this month.',
                'Approved! Well done this month.'
            ),
            (
                '<div onclick="steal()">Click here</div> - Good grades!',
                'Click here - Good grades!'
            ),
            (
                'Good work! <iframe src="//evil.com"></iframe>Keep it up!',
                'Good work! Keep it up!'
            ),
        ]
        
        for input_notes, expected_output in complex_cases:
            with self.subTest(notes=input_notes):
                data = {
                    'action': 'approve',
                    'parent_notes': input_notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize complex XSS, not reject: {input_notes}. Errors: {serializer.errors}")
                
                self.assertEqual(serializer.validated_data['parent_notes'], expected_output)

    def test_parent_notes_safe_formatting_preserved(self):
        """Test safe formatting and content are preserved during sanitization."""
        safe_content = [
            'Great job this month! Keep up the good work.',
            'Approved for tutoring sessions. Budget limit: €50.',
            'Please be more careful with spending next month.',  
            'Excellent grades deserve this reward! 🎉',
            'Math tutoring approved. Focus on algebra.',
            'Conditional approval - check with me first next time.',
        ]
        
        for notes in safe_content:
            with self.subTest(notes=notes):
                data = {
                    'action': 'approve',
                    'parent_notes': notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # These should always be valid - no changes expected
                self.assertTrue(serializer.is_valid(),
                               f"Safe content should always validate: {notes}. Errors: {serializer.errors}")
                
                # Safe content should pass through unchanged
                self.assertEqual(serializer.validated_data['parent_notes'], notes)

    def test_parent_notes_empty_after_sanitization_handling(self):
        """Test handling of notes that become empty after sanitization."""
        empty_after_sanitization = [
            '<script>alert(1)</script>',  # Only script
            '<!-- comment -->',  # Only comment
            '<div></div>',  # Empty div
            '<img src="evil.js" />',  # Only dangerous content
        ]
        
        for notes in empty_after_sanitization:
            with self.subTest(notes=notes):
                data = {
                    'action': 'approve', 
                    'parent_notes': notes
                }
                
                serializer = PurchaseApprovalActionSerializer(data=data)
                # THIS TEST SHOULD INITIALLY FAIL - current implementation rejects
                self.assertTrue(serializer.is_valid(),
                               f"Should sanitize to empty, not reject: {notes}. Errors: {serializer.errors}")
                
                # Should result in empty string after sanitization
                self.assertEqual(serializer.validated_data['parent_notes'], '')