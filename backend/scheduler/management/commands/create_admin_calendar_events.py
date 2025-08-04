"""
Management command to create realistic calendar events for school admin dashboard.
Creates administrative events and meetings with Portuguese context for Aprende Comigo platform.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile
from scheduler.models import ClassSchedule, ClassStatus, ClassType


class Command(BaseCommand):
    help = 'Create realistic calendar events for school admin dashboard with Portuguese context'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-admin-email',
            type=str,
            default='ana.silva@example.com',
            help='Email for the school admin user'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing admin calendar events before creating new ones'
        )

    def handle(self, *args, **options):
        admin_email = options['school_admin_email']
        clear_existing = options['clear_existing']

        try:
            with transaction.atomic():
                # Get school admin user and school
                admin_user = self.get_admin_user(admin_email)
                school = self.get_admin_school(admin_user)
                
                if clear_existing:
                    self.clear_existing_admin_events(admin_user, school)
                
                # Create admin calendar events
                events_created = self.create_admin_calendar_events(admin_user, school)
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n--- Admin Calendar Events Created Successfully ---')
                )
                self.stdout.write(f'School: {school.name}')
                self.stdout.write(f'Admin: {admin_user.email}')
                self.stdout.write(f'Calendar events created: {len(events_created)}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating calendar events: {str(e)}')
            )
            raise e

    def get_admin_user(self, email):
        """Get school admin user"""
        try:
            user = CustomUser.objects.get(email=email)
            self.stdout.write(
                self.style.SUCCESS(f'Found admin user: {email}')
            )
            return user
        except CustomUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Admin user not found: {email}. Please run create_school_admin_test_data first.')
            )
            raise

    def get_admin_school(self, admin_user):
        """Get school for admin user"""
        admin_membership = SchoolMembership.objects.filter(
            user=admin_user,
            role__in=[SchoolRole.SCHOOL_ADMIN, SchoolRole.SCHOOL_OWNER],
            is_active=True
        ).first()
        
        if not admin_membership:
            self.stdout.write(
                self.style.ERROR(f'No school membership found for admin user. Please run create_school_admin_test_data first.')
            )
            raise Exception("Admin user has no school membership")
        
        self.stdout.write(
            self.style.SUCCESS(f'Using school: {admin_membership.school.name}')
        )
        return admin_membership.school

    def clear_existing_admin_events(self, admin_user, school):
        """Clear existing admin calendar events"""
        # Clear ClassSchedule entries where admin_user is the student (admin events)
        deleted_count = ClassSchedule.objects.filter(
            student=admin_user,
            school=school,
            title__icontains='Reunião'  # Admin events have "Reunião" in title
        ).delete()[0]
        
        self.stdout.write(
            self.style.WARNING(f'Cleared {deleted_count} existing admin calendar events')
        )

    def create_admin_calendar_events(self, admin_user, school):
        """Create realistic school admin calendar events"""
        # Get a dummy teacher for the events (we need a teacher for ClassSchedule)
        dummy_teacher = self.get_or_create_admin_teacher(school)
        
        events_data = [
            {
                'title': 'Reunião de Coordenação Pedagógica',
                'description': 'Reunião semanal com coordenadores de departamento para alinhar estratégias pedagógicas e revisar progresso dos alunos.',
                'duration': 90,
                'days_ahead': 1,
                'time': '09:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião do Conselho Administrativo',
                'description': 'Reunião mensal do conselho administrativo para discussão de políticas e decisões estratégicas da escola.',
                'duration': 120,
                'days_ahead': 3,
                'time': '14:30',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião de Avaliação Trimestral',
                'description': 'Análise dos resultados do trimestre e planejamento de ações de melhoria para o próximo período.',
                'duration': 60,
                'days_ahead': 5,
                'time': '16:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.INDIVIDUAL
            },
            {
                'title': 'Sessão de Formação para Professores',
                'description': 'Workshop sobre novas metodologias de ensino digital e uso de tecnologia em sala de aula.',
                'duration': 180,
                'days_ahead': 7,
                'time': '09:30',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião com Pais e Encarregados',
                'description': 'Reunião trimestral com representantes dos pais para apresentação de resultados e feedback.',
                'duration': 90,
                'days_ahead': 10,
                'time': '18:30',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião de Planejamento Orçamental',
                'description': 'Reunião para revisão do orçamento anual e aprovação de investimentos em recursos educacionais.',
                'duration': 120,
                'days_ahead': 12,
                'time': '10:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.INDIVIDUAL
            },
            {
                'title': 'Reunião de Supervisão Pedagógica',
                'description': 'Reunião com supervisores para avaliar qualidade do ensino e implementação do plano curricular.',
                'duration': 75,
                'days_ahead': 14,
                'time': '15:30',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Assembleia Geral de Professores',
                'description': 'Assembleia mensal com todos os professores para comunicações importantes e votações.',
                'duration': 60,
                'days_ahead': 17,
                'time': '17:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião de Avaliação de Desempenho',
                'description': 'Reunião individual para avaliação de desempenho de professores e definição de objetivos.',
                'duration': 45,
                'days_ahead': 19,
                'time': '11:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.INDIVIDUAL
            },
            {
                'title': 'Reunião de Preparação de Eventos',
                'description': 'Planejamento da feira de ciências anual e outros eventos escolares do próximo semestre.',
                'duration': 90,
                'days_ahead': 21,
                'time': '14:00',
                'status': ClassStatus.SCHEDULED,
                'type': ClassType.GROUP
            },
            # Add some past events for context
            {
                'title': 'Reunião de Início de Ano Letivo',
                'description': 'Reunião de preparação para o novo ano letivo com definição de objetivos e estratégias.',
                'duration': 120,
                'days_ahead': -2,
                'time': '09:00',
                'status': ClassStatus.COMPLETED,
                'type': ClassType.GROUP
            },
            {
                'title': 'Reunião de Avaliação Mensal',
                'description': 'Reunião mensal de avaliação de resultados e métricas de desempenho da escola.',
                'duration': 60,
                'days_ahead': -5,
                'time': '16:30',
                'status': ClassStatus.COMPLETED,
                'type': ClassType.INDIVIDUAL
            },
        ]
        
        events_created = []
        base_date = timezone.now().date()
        
        for event_data in events_data:
            scheduled_date = base_date + timedelta(days=event_data['days_ahead'])
            
            # Skip weekends for business meetings
            if scheduled_date.weekday() >= 5:
                # Move to next Monday
                days_to_monday = 7 - scheduled_date.weekday()
                scheduled_date = scheduled_date + timedelta(days=days_to_monday)
            
            start_time = datetime.strptime(event_data['time'], "%H:%M").time()
            end_time = (datetime.combine(scheduled_date, start_time) + 
                       timedelta(minutes=event_data['duration'])).time()
            
            event = ClassSchedule.objects.create(
                teacher=dummy_teacher,
                student=admin_user,  # Admin is the "student" for these events
                school=school,
                title=event_data['title'],
                description=event_data['description'],
                class_type=event_data['type'],
                status=event_data['status'],
                scheduled_date=scheduled_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=event_data['duration'],
                booked_by=admin_user
            )
            
            # Add completion time for completed events
            if event_data['status'] == ClassStatus.COMPLETED:
                event.completed_at = timezone.make_aware(
                    datetime.combine(scheduled_date, end_time)
                )
                event.save()
            
            events_created.append(event)
        
        return events_created

    def get_or_create_admin_teacher(self, school):
        """Get or create a dummy teacher for admin events"""
        admin_teacher_email = 'admin.events@escolalisboa.pt'
        
        # Check if admin teacher exists
        if CustomUser.objects.filter(email=admin_teacher_email).exists():
            admin_teacher_user = CustomUser.objects.get(email=admin_teacher_email)
        else:
            admin_teacher_user = CustomUser.objects.create_user(
                email=admin_teacher_email,
                name='Sistema Administrativo',
                email_verified=True,
                first_login_completed=True,
                onboarding_completed=True
            )
        
        # Create or get teacher profile
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=admin_teacher_user,
            defaults={
                'teaching_subjects': ['Administração'],
                'bio': 'Perfil do sistema para eventos administrativos.',
                'hourly_rate': 0,
                'teaching_experience': {
                    'years_total': 0,
                    'specializations': ['Administração']
                },
                'is_profile_complete': True
            }
        )
        
        # Create school membership if needed
        SchoolMembership.objects.get_or_create(
            user=admin_teacher_user,
            school=school,
            defaults={
                'role': SchoolRole.TEACHER,
                'is_active': True,
                'joined_at': timezone.now()
            }
        )
        
        return teacher_profile