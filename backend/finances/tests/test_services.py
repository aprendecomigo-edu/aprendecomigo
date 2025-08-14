from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.apps import apps
from django.conf import settings
from django.test import TestCase

from ..services.business_logic_services import CompensationService, PaymentService


class CompensationServiceTest(TestCase):
    def setUp(self):
        # Arrange: Create test user
        User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        self.teacher = User.objects.create_user(
            username="testteacher", email="teacher@test.com", password="testpass123"
        )

        self.period_start = date.today().replace(day=1)
        self.period_end = date.today()

    @patch("finances.services.business_logic_services.apps.get_model")
    def test_calculate_teacher_compensation_with_bonus_returns_correct_amount(self, mock_get_model):
        # Arrange: Mock 25 completed lessons (should trigger bonus)
        mock_lesson_model = Mock()
        mock_lesson_queryset = Mock()
        mock_lesson_queryset.count.return_value = 25
        mock_lesson_model.objects.filter.return_value = mock_lesson_queryset

        mock_user_model = Mock()
        mock_teacher = Mock()
        mock_teacher.teacher_profile.hourly_rate = Decimal("60.00")
        mock_user_model.objects.get.return_value = mock_teacher

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "TeacherCompensation"): Mock(),
        }[(app, model)]

        # Act
        result = CompensationService.calculate_teacher_compensation(
            teacher_id=self.teacher.id, period_start=self.period_start, period_end=self.period_end
        )

        # Assert
        expected_base = Decimal("1500.00")  # 25 * 60.00
        expected_bonus = Decimal("150.00")  # 10% bonus
        expected_total = Decimal("1650.00")

        self.assertEqual(result["base_amount"], expected_base)
        self.assertEqual(result["bonus_amount"], expected_bonus)
        self.assertEqual(result["total_amount"], expected_total)
        self.assertEqual(result["lessons_count"], 25)

    @patch("finances.services.business_logic_services.apps.get_model")
    def test_calculate_teacher_compensation_no_bonus_for_low_lesson_count(self, mock_get_model):
        # Arrange: Mock 15 completed lessons (no bonus)
        mock_lesson_model = Mock()
        mock_lesson_queryset = Mock()
        mock_lesson_queryset.count.return_value = 15
        mock_lesson_model.objects.filter.return_value = mock_lesson_queryset

        mock_user_model = Mock()
        mock_teacher = Mock()
        mock_teacher.teacher_profile.hourly_rate = Decimal("50.00")
        mock_user_model.objects.get.return_value = mock_teacher

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "TeacherCompensation"): Mock(),
        }[(app, model)]

        # Act
        result = CompensationService.calculate_teacher_compensation(
            teacher_id=self.teacher.id, period_start=self.period_start, period_end=self.period_end
        )

        # Assert
        expected_base = Decimal("750.00")  # 15 * 50.00
        expected_bonus = Decimal("0.00")  # No bonus
        expected_total = Decimal("750.00")

        self.assertEqual(result["base_amount"], expected_base)
        self.assertEqual(result["bonus_amount"], expected_bonus)
        self.assertEqual(result["total_amount"], expected_total)
        self.assertEqual(result["lessons_count"], 15)


class PaymentServiceTest(TestCase):
    def setUp(self):
        # Arrange: Create test users
        User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
        self.student = User.objects.create_user(
            username="teststudent", email="student@test.com", password="testpass123"
        )
        self.teacher = User.objects.create_user(
            username="testteacher2", email="teacher2@test.com", password="testpass123"
        )

    @patch("finances.services.business_logic_services.apps.get_model")
    @patch("finances.services.business_logic_services.transaction.atomic")
    def test_process_lesson_payment_creates_payment_and_transaction(self, mock_atomic, mock_get_model):
        # Arrange: Mock lesson and models
        mock_lesson = Mock()
        mock_lesson.id = 1
        mock_lesson.price = Decimal("75.00")
        mock_lesson.teacher = self.teacher
        mock_lesson.title = "Python Basics"

        mock_lesson_model = Mock()
        mock_lesson_model.objects.get.return_value = mock_lesson

        mock_user_model = Mock()
        mock_user_model.objects.get.return_value = self.student

        mock_payment = Mock()
        mock_payment.id = 123
        mock_payment.amount = Decimal("75.00")
        mock_payment.status = "pending"

        mock_payment_model = Mock()
        mock_payment_model.objects.create.return_value = mock_payment

        mock_transaction_model = Mock()

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "Payment"): mock_payment_model,
            ("finances", "Transaction"): mock_transaction_model,
        }[(app, model)]

        mock_atomic.return_value.__enter__ = Mock()
        mock_atomic.return_value.__exit__ = Mock()

        # Act
        result = PaymentService.process_lesson_payment(lesson_id=1, student_id=self.student.id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["payment_id"], 123)
        self.assertEqual(result["amount"], Decimal("75.00"))
        self.assertEqual(result["status"], "pending")

        # Verify payment creation
        mock_payment_model.objects.create.assert_called_once()

        # Verify transaction creation
        mock_transaction_model.objects.create.assert_called_once()

    @patch("finances.services.business_logic_services.apps.get_model")
    def test_process_lesson_payment_handles_missing_lesson(self, mock_get_model):
        # Arrange: Mock lesson not found
        from django.core.exceptions import ObjectDoesNotExist

        mock_lesson_model = Mock()
        mock_lesson_model.objects.get.side_effect = ObjectDoesNotExist()
        mock_lesson_model.DoesNotExist = ObjectDoesNotExist

        mock_user_model = Mock()
        mock_user_model.objects.get.return_value = self.student

        mock_get_model.side_effect = lambda app, model: {
            ("classroom", "Lesson"): mock_lesson_model,
            ("accounts", "CustomUser"): mock_user_model,
            ("finances", "Payment"): Mock(),
        }[(app, model)]

        # Act
        result = PaymentService.process_lesson_payment(lesson_id=999, student_id=self.student.id)

        # Assert
        self.assertIsNone(result)
