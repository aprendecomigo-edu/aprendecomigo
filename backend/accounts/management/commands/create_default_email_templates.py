"""
Management command to create default email templates for schools.

Usage:
    python manage.py create_default_email_templates
    python manage.py create_default_email_templates --school-id 1
    python manage.py create_default_email_templates --all-schools
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import School
from messaging.models import SchoolEmailTemplate, EmailTemplateType
from accounts.services.default_templates import DefaultEmailTemplates

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create default email templates for schools'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='Create templates for a specific school ID'
        )
        parser.add_argument(
            '--all-schools',
            action='store_true',
            help='Create templates for all schools that don\'t have them'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing templates'
        )
        parser.add_argument(
            '--template-type',
            choices=[t[0] for t in EmailTemplateType.choices],
            help='Create only a specific template type'
        )
    
    def handle(self, *args, **options):
        school_id = options.get('school_id')
        all_schools = options.get('all_schools')
        overwrite = options.get('overwrite', False)
        template_type = options.get('template_type')
        
        if not school_id and not all_schools:
            raise CommandError('You must specify either --school-id or --all-schools')
        
        try:
            if school_id:
                # Create templates for specific school
                school = School.objects.get(id=school_id)
                self.create_templates_for_school(school, overwrite, template_type)
                
            elif all_schools:
                # Create templates for all schools
                schools = School.objects.all()
                self.stdout.write(f'Creating default templates for {schools.count()} schools...')
                
                for school in schools:
                    try:
                        self.create_templates_for_school(school, overwrite, template_type)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error creating templates for {school.name}: {str(e)}')
                        )
                        continue
                
        except School.DoesNotExist:
            raise CommandError(f'School with ID {school_id} does not exist')
        except Exception as e:
            raise CommandError(f'Error creating templates: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created default email templates'))
    
    def create_templates_for_school(self, school, overwrite=False, specific_type=None):
        """Create default templates for a specific school."""
        self.stdout.write(f'Creating templates for school: {school.name}')
        
        # Get template types to create
        template_types = [specific_type] if specific_type else [t[0] for t in EmailTemplateType.choices]
        
        created_count = 0
        skipped_count = 0
        updated_count = 0
        
        for template_type in template_types:
            try:
                # Check if template already exists
                existing_template = SchoolEmailTemplate.objects.filter(
                    school=school,
                    template_type=template_type
                ).first()
                
                if existing_template and not overwrite:
                    self.stdout.write(f'  - Skipped {template_type} (already exists)')
                    skipped_count += 1
                    continue
                
                # Get default template data
                try:
                    template_data = DefaultEmailTemplates.get_default_template(template_type)
                except ValueError as e:
                    self.stdout.write(
                        self.style.WARNING(f'  - Skipped {template_type}: {str(e)}')
                    )
                    continue
                
                with transaction.atomic():
                    if existing_template and overwrite:
                        # Update existing template
                        existing_template.name = template_data['name']
                        existing_template.subject_template = template_data['subject']
                        existing_template.html_content = template_data['html']
                        existing_template.text_content = template_data['text']
                        existing_template.save()
                        
                        self.stdout.write(f'  - Updated {template_type}')
                        updated_count += 1
                        
                    else:
                        # Create new template
                        SchoolEmailTemplate.objects.create(
                            school=school,
                            template_type=template_type,
                            name=template_data['name'],
                            subject_template=template_data['subject'],
                            html_content=template_data['html'],
                            text_content=template_data['text'],
                            is_default=False,  # School-specific, not global default
                            is_active=True,
                            use_school_branding=True
                        )
                        
                        self.stdout.write(f'  - Created {template_type}')
                        created_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  - Error creating {template_type}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            f'  Summary: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        )
    
    def create_global_default_templates(self):
        """Create global default templates (not tied to specific schools)."""
        self.stdout.write('Creating global default templates...')
        
        # For global defaults, we can create them without a school
        # These would be used as fallbacks when schools don't have custom templates
        
        created_count = 0
        
        for template_type_tuple in EmailTemplateType.choices:
            template_type = template_type_tuple[0]
            
            try:
                # Check if global default already exists
                existing = SchoolEmailTemplate.objects.filter(
                    school__isnull=True,  # Global template
                    template_type=template_type,
                    is_default=True
                ).first()
                
                if existing:
                    self.stdout.write(f'  - Global {template_type} already exists')
                    continue
                
                # Get default template data
                template_data = DefaultEmailTemplates.get_default_template(template_type)
                
                # Create global default template
                SchoolEmailTemplate.objects.create(
                    school=None,  # Global template
                    template_type=template_type,
                    name=f'Global Default - {template_data["name"]}',
                    subject_template=template_data['subject'],
                    html_content=template_data['html'],
                    text_content=template_data['text'],
                    is_default=True,
                    is_active=True,
                    use_school_branding=True
                )
                
                self.stdout.write(f'  - Created global {template_type} template')
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  - Error creating global {template_type}: {str(e)}')
                )
                continue
        
        self.stdout.write(f'Created {created_count} global default templates')