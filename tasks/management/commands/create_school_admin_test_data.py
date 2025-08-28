"""
Management command to create realistic test data for school admin dashboard.
Creates tasks and class schedules with Portuguese context for Aprende Comigo platform.
"""

from datetime import datetime, timedelta
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser, School, SchoolMembership, SchoolRole, TeacherProfile
from scheduler.models import ClassSchedule, ClassStatus, ClassType
from tasks.models import Task


class Command(BaseCommand):
    help = "Create realistic test data for school admin dashboard with Portuguese context"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-admin-email", type=str, default="ana.silva@example.com", help="Email for the school admin user"
        )
        parser.add_argument(
            "--clear-existing", action="store_true", help="Clear existing test data before creating new data"
        )

    def handle(self, *args, **options):
        admin_email = options["school_admin_email"]
        clear_existing = options["clear_existing"]

        try:
            with transaction.atomic():
                # Get or create school admin user
                admin_user = self.get_or_create_admin_user(admin_email)
                school = self.get_admin_school(admin_user)

                if clear_existing:
                    self.clear_existing_data(admin_user, school)

                # Create test teachers and students for the school
                teachers = self.create_test_teachers(school)
                students = self.create_test_students(school)

                # Create school admin tasks
                tasks_created = self.create_admin_tasks(admin_user)

                # Create class schedules with the teachers and students
                schedules_created = self.create_class_schedules(school, teachers, students, admin_user)

                self.stdout.write(self.style.SUCCESS("\n--- School Admin Test Data Created Successfully ---"))
                self.stdout.write(f"School: {school.name}")
                self.stdout.write(f"Admin: {admin_user.email}")
                self.stdout.write(f"Teachers created: {len(teachers)}")
                self.stdout.write(f"Students created: {len(students)}")
                self.stdout.write(f"Tasks created: {len(tasks_created)}")
                self.stdout.write(f"Class schedules created: {len(schedules_created)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating test data: {e!s}"))
            raise e

    def get_or_create_admin_user(self, email):
        """Get or create school admin user"""
        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email=email)
            self.stdout.write(self.style.WARNING(f"Using existing admin user: {email}"))
        else:
            user = CustomUser.objects.create_user(
                email=email,
                name="Ana Paula Administradora",
                email_verified=True,
                first_login_completed=True,
                onboarding_completed=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {email}"))
        return user

    def get_admin_school(self, admin_user):
        """Get or create school for admin user"""
        # Check if user has school admin membership
        admin_membership = SchoolMembership.objects.filter(
            user=admin_user, role__in=[SchoolRole.SCHOOL_ADMIN, SchoolRole.SCHOOL_OWNER], is_active=True
        ).first()

        if admin_membership:
            school = admin_membership.school
            self.stdout.write(self.style.WARNING(f"Using existing school: {school.name}"))
        else:
            # Create school and admin membership
            school = School.objects.create(
                name="Escola Aprende Comigo Lisboa",
                description="Escola de reforço escolar e tutoria especializada",
                address="Rua da Educação, 123, Lisboa",
                contact_email="contato@escolalisboa.pt",
                phone_number="+351 21 123 4567",
            )

            SchoolMembership.objects.create(
                user=admin_user, school=school, role=SchoolRole.SCHOOL_ADMIN, is_active=True, joined_at=timezone.now()
            )

            self.stdout.write(self.style.SUCCESS(f"Created school: {school.name}"))

        return school

    def clear_existing_data(self, admin_user, school):
        """Clear existing test data"""
        # Clear tasks for admin user
        Task.objects.filter(user=admin_user).delete()

        # Clear class schedules for the school
        ClassSchedule.objects.filter(school=school).delete()

        self.stdout.write(self.style.WARNING("Cleared existing test data"))

    def create_test_teachers(self, school):
        """Create realistic Portuguese teacher test data"""
        teachers_data = [
            {
                "name": "Professor João Silva",
                "email": "joao.silva@escolalisboa.pt",
                "subjects": ["Matemática", "Física"],
                "bio": "Especialista em matemática com 15 anos de experiência no ensino secundário.",
            },
            {
                "name": "Professora Maria Santos",
                "email": "maria.santos@escolalisboa.pt",
                "subjects": ["Português", "Literatura"],
                "bio": "Licenciada em Letras, apaixonada por ensinar língua portuguesa e literatura.",
            },
            {
                "name": "Professor Carlos Mendes",
                "email": "carlos.mendes@escolalisboa.pt",
                "subjects": ["História", "Geografia"],
                "bio": "Professor de História com mestrado em História Contemporânea.",
            },
            {
                "name": "Professora Ana Rodrigues",
                "email": "ana.rodrigues@escolalisboa.pt",
                "subjects": ["Inglês", "Francês"],
                "bio": "Professora de línguas estrangeiras, fluente em 4 idiomas.",
            },
        ]

        teachers = []
        for teacher_data in teachers_data:
            # Check if user exists
            if CustomUser.objects.filter(email=teacher_data["email"]).exists():
                user = CustomUser.objects.get(email=teacher_data["email"])
            else:
                user = CustomUser.objects.create_user(
                    email=teacher_data["email"],
                    name=teacher_data["name"],
                    email_verified=True,
                    first_login_completed=True,
                    onboarding_completed=True,
                )

            # Create or get teacher profile
            teacher_profile, created = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    "teaching_subjects": teacher_data["subjects"],
                    "bio": teacher_data["bio"],
                    "hourly_rate": random.randint(15, 35),
                    "teaching_experience": {
                        "years_total": random.randint(3, 20),
                        "specializations": teacher_data["subjects"],
                    },
                    "is_profile_complete": True,
                },
            )

            # Create school membership
            SchoolMembership.objects.get_or_create(
                user=user,
                school=school,
                defaults={
                    "role": SchoolRole.TEACHER,
                    "is_active": True,
                    "joined_at": timezone.now() - timedelta(days=random.randint(30, 365)),
                },
            )

            teachers.append(teacher_profile)

        return teachers

    def create_test_students(self, school):
        """Create realistic Portuguese student test data"""
        students_data = [
            {"name": "Pedro Oliveira", "email": "pedro.oliveira@email.pt", "grade": "9º ano"},
            {"name": "Sofia Costa", "email": "sofia.costa@email.pt", "grade": "10º ano"},
            {"name": "Miguel Ferreira", "email": "miguel.ferreira@email.pt", "grade": "11º ano"},
            {"name": "Beatriz Almeida", "email": "beatriz.almeida@email.pt", "grade": "12º ano"},
            {"name": "Gonçalo Pereira", "email": "goncalo.pereira@email.pt", "grade": "8º ano"},
            {"name": "Mariana Lima", "email": "mariana.lima@email.pt", "grade": "9º ano"},
        ]

        students = []
        for student_data in students_data:
            # Check if user exists
            if CustomUser.objects.filter(email=student_data["email"]).exists():
                user = CustomUser.objects.get(email=student_data["email"])
            else:
                user = CustomUser.objects.create_user(
                    email=student_data["email"],
                    name=student_data["name"],
                    email_verified=True,
                    first_login_completed=True,
                    onboarding_completed=True,
                )

            # Create school membership
            SchoolMembership.objects.get_or_create(
                user=user,
                school=school,
                defaults={
                    "role": SchoolRole.STUDENT,
                    "is_active": True,
                    "joined_at": timezone.now() - timedelta(days=random.randint(10, 180)),
                },
            )

            students.append(user)

        return students

    def create_admin_tasks(self, admin_user):
        """Create realistic school admin tasks"""
        tasks_data = [
            {
                "title": "Rever candidaturas de novos professores",
                "description": "Analisar 3 candidaturas recebidas esta semana para as disciplinas de Ciências e Inglês",
                "priority": "high",
                "due_date": timezone.now() + timedelta(days=2),
                "task_type": "system",
                "status": "pending",
            },
            {
                "title": "Atualizar perfil da escola",
                "description": "Adicionar novas fotografias e atualizar descrição dos serviços oferecidos",
                "priority": "medium",
                "due_date": timezone.now() + timedelta(days=5),
                "task_type": "personal",
                "status": "pending",
            },
            {
                "title": "Enviar newsletter mensal aos pais",
                "description": "Preparar e enviar newsletter de dezembro com resultados e atividades do mês",
                "priority": "medium",
                "due_date": timezone.now() + timedelta(days=3),
                "task_type": "system",
                "status": "in_progress",
            },
            {
                "title": "Organizar reunião de professores",
                "description": "Agendar reunião trimestral para discutir métodos pedagógicos e feedback dos alunos",
                "priority": "high",
                "due_date": timezone.now() + timedelta(days=7),
                "task_type": "personal",
                "status": "pending",
            },
            {
                "title": "Configurar horários de inverno",
                "description": "Ajustar horários de funcionamento para o período de inverno (janeiro-março)",
                "priority": "medium",
                "due_date": timezone.now() + timedelta(days=10),
                "task_type": "system",
                "status": "pending",
            },
            {
                "title": "Responder a feedback dos pais",
                "description": "Responder aos comentários e sugestões recebidos no formulário de avaliação mensal",
                "priority": "high",
                "due_date": timezone.now() + timedelta(days=1),
                "task_type": "personal",
                "status": "pending",
                "is_urgent": True,
            },
            {
                "title": "Preparar relatório financeiro",
                "description": "Compilar dados financeiros do trimestre para apresentação ao conselho administrativo",
                "priority": "high",
                "due_date": timezone.now() + timedelta(days=14),
                "task_type": "system",
                "status": "pending",
            },
            {
                "title": "Verificar equipamentos tecnológicos",
                "description": "Fazer inventário e manutenção de tablets, computadores e sistemas de videoconferência",
                "priority": "low",
                "due_date": timezone.now() + timedelta(days=21),
                "task_type": "personal",
                "status": "pending",
            },
            {
                "title": "Implementar sistema de avaliação",
                "description": "Finalizar implementação do novo sistema de avaliação contínua dos alunos",
                "priority": "medium",
                "due_date": timezone.now() + timedelta(days=12),
                "task_type": "system",
                "status": "in_progress",
            },
        ]

        tasks_created = []
        for task_data in tasks_data:
            task = Task.objects.create(user=admin_user, **task_data)
            tasks_created.append(task)

        return tasks_created

    def create_class_schedules(self, school, teachers, students, admin_user):
        """Create realistic class schedules"""
        subjects_per_teacher = {
            0: ["Matemática", "Física"],  # João Silva
            1: ["Português", "Literatura"],  # Maria Santos
            2: ["História", "Geografia"],  # Carlos Mendes
            3: ["Inglês", "Francês"],  # Ana Rodrigues
        }

        schedules_created = []
        base_date = timezone.now().date()

        # Create schedules for the next 2 weeks
        for day_offset in range(1, 15):  # Skip today, start tomorrow
            scheduled_date = base_date + timedelta(days=day_offset)

            # Skip weekends
            if scheduled_date.weekday() >= 5:
                continue

            # Create 3-4 classes per weekday
            num_classes = random.randint(3, 4)
            used_times = set()

            for _ in range(num_classes):
                # Random time between 14:00 and 20:00 (Portuguese school hours)
                hour = random.randint(14, 19)
                minute = random.choice([0, 30])
                start_time = datetime.strptime(f"{hour}:{minute:02d}", "%H:%M").time()

                # Avoid conflicts
                if start_time in used_times:
                    continue
                used_times.add(start_time)

                # Calculate end time (45min or 60min classes)
                duration = random.choice([45, 60])
                end_time = (datetime.combine(scheduled_date, start_time) + timedelta(minutes=duration)).time()

                # Random teacher and student
                teacher = random.choice(teachers)
                student = random.choice(students)
                teacher_subjects = subjects_per_teacher[teachers.index(teacher)]
                subject = random.choice(teacher_subjects)

                # Determine status based on date
                if scheduled_date < base_date:
                    status = random.choice([ClassStatus.COMPLETED, ClassStatus.CANCELLED])
                elif scheduled_date == base_date:
                    status = random.choice([ClassStatus.CONFIRMED, ClassStatus.SCHEDULED])
                else:
                    status = ClassStatus.SCHEDULED

                schedule = ClassSchedule.objects.create(
                    teacher=teacher,
                    student=student,
                    school=school,
                    title=f"Aula de {subject}",
                    description=f"Aula individual de {subject} - {student.name}",
                    class_type=ClassType.INDIVIDUAL,
                    status=status,
                    scheduled_date=scheduled_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration,
                    booked_by=admin_user,
                )

                # Add completion time for completed classes
                if status == ClassStatus.COMPLETED:
                    schedule.completed_at = timezone.make_aware(datetime.combine(scheduled_date, end_time))
                    schedule.save()

                schedules_created.append(schedule)

        return schedules_created
