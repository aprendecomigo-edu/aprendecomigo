from django.apps import apps
from django.conf import settings
from django.db import transaction
from decimal import Decimal
from typing import Optional

class CompensationService:
    @staticmethod
    def calculate_teacher_compensation(teacher_id: int, period_start, period_end):
        """Calculate teacher compensation for a given period using runtime model access."""
        # Get models at runtime to avoid circular imports
        Lesson = apps.get_model('classroom', 'Lesson')
        User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
        TeacherCompensation = apps.get_model('finances', 'TeacherCompensation')
        
        # Calculate completed lessons
        completed_lessons = Lesson.objects.filter(
            teacher_id=teacher_id,
            date__range=[period_start, period_end],
            status='completed'
        ).count()
        
        # Get teacher's hourly rate
        teacher = User.objects.get(id=teacher_id)
        hourly_rate = getattr(teacher.teacher_profile, 'hourly_rate', Decimal('50.00'))
        
        base_amount = completed_lessons * hourly_rate
        bonus_amount = Decimal('0.00')
        
        # Apply bonus for high lesson count
        if completed_lessons >= 20:
            bonus_amount = base_amount * Decimal('0.10')
        
        total_amount = base_amount + bonus_amount
        
        return {
            'base_amount': base_amount,
            'bonus_amount': bonus_amount,
            'total_amount': total_amount,
            'lessons_count': completed_lessons
        }

class PaymentService:
    @staticmethod
    def process_lesson_payment(lesson_id: int, student_id: int) -> Optional[dict]:
        """Process payment for a lesson using runtime model fetching."""
        # Runtime model fetching to avoid circular imports
        Lesson = apps.get_model('classroom', 'Lesson')
        Payment = apps.get_model('finances', 'Payment')
        User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
        
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            student = User.objects.get(id=student_id)
            
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=student,
                    lesson=lesson,
                    amount=lesson.price,
                    status='pending',
                    payment_method='credit_card'
                )
                
                # Create transaction record
                Transaction = apps.get_model('finances', 'Transaction')
                Transaction.objects.create(
                    payer=student,
                    payee=lesson.teacher,
                    amount=lesson.price,
                    transaction_type='lesson_payment',
                    description=f'Payment for lesson: {lesson.title}',
                    payment=payment
                )
                
                return {
                    'payment_id': payment.id,
                    'amount': payment.amount,
                    'status': payment.status
                }
                
        except (Lesson.DoesNotExist, User.DoesNotExist) as e:
            return None