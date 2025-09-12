"""
Management command to help mark strings for translation in Python files.
"""

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
import os
import re


class Command(BaseCommand):
    help = 'Helps identify and mark strings for translation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check for untranslated strings without modifying files'
        )
        parser.add_argument(
            '--app',
            type=str,
            help='Specific app to check (e.g., accounts, dashboard)'
        )

    def handle(self, *args, **options):
        check_only = options.get('check', False)
        app_name = options.get('app')
        
        if check_only:
            self.stdout.write(self.style.SUCCESS('Checking for untranslated strings...'))
            self.check_untranslated_strings(app_name)
        else:
            self.stdout.write(self.style.WARNING(
                'Auto-marking is not implemented. Use --check to identify strings.'
            ))

    def check_untranslated_strings(self, app_name=None):
        """Check Python files for potentially untranslated strings."""
        
        # Common patterns that likely need translation
        patterns = [
            (r'messages\.(success|error|warning|info)\([^_].*?["\']([^"\']+)["\']', 'Django messages'),
            (r'ValidationError\(["\']([^"\']+)["\']', 'Validation errors'),
            (r'help_text=["\']([^"\']+)["\']', 'Model help text'),
            (r'verbose_name=["\']([^"\']+)["\']', 'Model verbose names'),
            (r'label=["\']([^"\']+)["\']', 'Form labels'),
            (r'placeholder=["\']([^"\']+)["\']', 'Form placeholders'),
        ]
        
        apps = [app_name] if app_name else ['accounts', 'dashboard', 'classroom', 'scheduler', 'finances']
        
        findings = []
        
        for app in apps:
            if not os.path.exists(app):
                continue
                
            for root, dirs, files in os.walk(app):
                # Skip migrations
                if 'migrations' in root:
                    continue
                    
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        with open(filepath, 'r') as f:
                            content = f.read()
                            
                        # Check if file imports gettext
                        has_gettext = 'from django.utils.translation import' in content
                        
                        for pattern, pattern_type in patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                text = match.group(1) if pattern_type == 'Django messages' else match.group(0)
                                
                                # Check if already using gettext
                                if not (f'_("{text}")' in content or f"_('{text}')" in content):
                                    findings.append({
                                        'file': filepath,
                                        'line': line_num,
                                        'type': pattern_type,
                                        'text': text[:50] + '...' if len(text) > 50 else text,
                                        'has_import': has_gettext
                                    })
        
        # Display findings
        if findings:
            self.stdout.write(self.style.WARNING(f'\nFound {len(findings)} potentially untranslated strings:\n'))
            
            current_file = None
            for finding in findings:
                if finding['file'] != current_file:
                    current_file = finding['file']
                    self.stdout.write(f'\n{self.style.HTTP_INFO(current_file)}')
                    if not finding['has_import']:
                        self.stdout.write(self.style.ERROR('  ⚠️  Missing: from django.utils.translation import gettext as _'))
                
                self.stdout.write(f'  Line {finding["line"]}: {finding["type"]} - "{finding["text"]}"')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ No untranslated strings found!'))