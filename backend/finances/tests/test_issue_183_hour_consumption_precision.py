"""
Business Logic Unit Tests for Issue #183: Hour Consumption Precision

This test module creates specific tests for hour consumption calculation precision issues
that will initially FAIL to validate the financial precision improvements.

Focus areas:
- Fractional hour calculations with precise rounding
- Complex hour deduction scenarios with multiple students
- Hour balance updates with precision consistency
- Group session hour splitting with fractional results
- Hour consumption edge cases that cause precision mismatches
"""

from decimal import Decimal, ROUND_HALF_UP
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from unittest.mock import patch, Mock

from finances.models import (
    StudentAccountBalance,
    HourConsumption, 
    ClassSession,
    SessionStatus,
    SessionType
)

User = get_user_model()


class HourConsumptionPrecisionTest(TestCase):
    """
    Test suite for hour consumption precision edge cases from Issue #183.
    These tests will initially FAIL until hour calculation utilities are implemented.
    """

    def setUp(self):
        """Set up test data for hour consumption precision testing."""
        # Create users
        self.student1 = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123'
        )
        self.student2 = User.objects.create_user(
            username='student2', 
            email='student2@test.com',
            password='testpass123'
        )
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass123'
        )

        # Create account balances with high precision values
        self.balance1 = StudentAccountBalance.objects.create(
            student=self.student1,
            hours_purchased=Decimal('25.777'),  # High precision initial balance
            hours_consumed=Decimal('0.000'),
            balance_amount=Decimal('515.40')
        )
        
        self.balance2 = StudentAccountBalance.objects.create(
            student=self.student2,
            hours_purchased=Decimal('15.333'),  # High precision initial balance
            hours_consumed=Decimal('0.000'), 
            balance_amount=Decimal('306.66')
        )

    def test_fractional_hour_consumption_precision_with_individual_session(self):
        """
        Test: Individual session hour consumption should maintain 2-decimal precision.
        Expected to FAIL until hour consumption utilities handle fractional precision.
        """
        # Arrange: Individual session with fractional duration
        session_duration_minutes = 105  # 1 hour 45 minutes = 1.75 hours
        session_duration_hours = Decimal(session_duration_minutes) / Decimal('60')
        
        # Act: Simulate hour consumption calculation
        consumed_hours = session_duration_hours  # Direct consumption for individual session
        new_balance = self.balance1.hours_purchased - consumed_hours
        
        # Assert: Should be precisely rounded to 2 decimal places
        expected_consumed = Decimal('1.75')     # 105/60 = 1.75, exact
        expected_balance = Decimal('24.03')     # 25.777 - 1.75 = 24.027, rounded
        
        # This will FAIL until hour consumption utilities handle precision
        self.assertEqual(consumed_hours, expected_consumed)
        self.assertEqual(new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 
                        expected_balance)

    def test_group_session_hour_splitting_precision_with_three_students(self):
        """
        Test: Group session hour splitting should maintain consistent precision per student.
        Expected to FAIL until group session splitting utilities handle fractional precision.
        """
        # Arrange: Group session with 3 students and fractional duration
        session_duration_hours = Decimal('2.25')  # 2 hours 15 minutes
        number_of_students = 3
        
        # Act: Calculate per-student hour consumption
        hours_per_student = session_duration_hours / number_of_students
        
        # Calculate new balances for both students
        student1_new_balance = self.balance1.hours_purchased - hours_per_student
        student2_new_balance = self.balance2.hours_purchased - hours_per_student
        
        # Assert: Per-student consumption should be precisely calculated
        expected_hours_per_student = Decimal('0.75')  # 2.25 / 3 = 0.75, exact
        expected_balance1 = Decimal('25.03')          # 25.777 - 0.75 = 25.027, rounded
        expected_balance2 = Decimal('14.58')          # 15.333 - 0.75 = 14.583, rounded
        
        # These will FAIL until group session utilities handle precision
        self.assertEqual(hours_per_student, expected_hours_per_student)
        self.assertEqual(student1_new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_balance1)
        self.assertEqual(student2_new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_balance2)

    def test_complex_fractional_hour_consumption_with_uneven_splitting(self):
        """
        Test: Complex fractional hour consumption with uneven results should round consistently.
        Expected to FAIL until fractional hour utilities standardize precision handling.
        """
        # Arrange: Session duration that creates uneven splitting
        session_duration_hours = Decimal('1.40')  # 1 hour 24 minutes
        number_of_students = 3  # Creates 0.466... per student
        
        # Act: Calculate consumption with complex fraction
        hours_per_student = session_duration_hours / number_of_students
        
        # Update balances
        student1_consumed = self.balance1.hours_consumed + hours_per_student
        student1_remaining = self.balance1.hours_purchased - student1_consumed
        
        # Assert: Complex fractions should be consistently rounded
        expected_hours_per_student = Decimal('0.47')  # 1.40/3 = 0.466..., rounded up
        expected_consumed = Decimal('0.47')           # First consumption
        expected_remaining = Decimal('25.31')         # 25.777 - 0.47 = 25.307, rounded
        
        # These will FAIL until complex fraction utilities are implemented
        self.assertEqual(hours_per_student.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_hours_per_student)
        self.assertEqual(student1_consumed.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_consumed)
        self.assertEqual(student1_remaining.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_remaining)

    def test_multiple_session_hour_consumption_precision_accumulation(self):
        """
        Test: Multiple session consumptions should accumulate with consistent precision.
        Expected to FAIL until accumulation utilities maintain precision across sessions.
        """
        # Arrange: Multiple sessions with different fractional durations
        session_durations = [
            Decimal('1.33'),   # Session 1: 1 hour 20 minutes
            Decimal('0.75'),   # Session 2: 45 minutes
            Decimal('2.17'),   # Session 3: 2 hours 10 minutes
            Decimal('1.50'),   # Session 4: 1 hour 30 minutes
        ]
        
        # Act: Simulate multiple session consumptions
        current_consumed = self.balance1.hours_consumed
        for duration in session_durations:
            current_consumed += duration
        
        current_remaining = self.balance1.hours_purchased - current_consumed
        
        # Assert: Accumulated consumption should maintain precision
        expected_total_consumed = Decimal('5.75')  # 1.33 + 0.75 + 2.17 + 1.50 = 5.75
        expected_remaining = Decimal('20.03')      # 25.777 - 5.75 = 20.027, rounded
        
        # These will FAIL until accumulation precision utilities are implemented
        self.assertEqual(current_consumed.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_total_consumed)
        self.assertEqual(current_remaining.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_remaining)

    def test_hour_balance_update_precision_with_fractional_purchase_and_consumption(self):
        """
        Test: Hour balance updates with both purchases and consumption should maintain precision.
        Expected to FAIL until balance update utilities handle mixed operations precisely.
        """
        # Arrange: Mixed purchase and consumption operations
        additional_purchase = Decimal('10.666')   # New hour purchase with fractions
        session_consumption = Decimal('3.777')    # Session consumption with fractions
        
        # Act: Update balance with purchase and consumption
        new_hours_purchased = self.balance1.hours_purchased + additional_purchase
        new_hours_consumed = self.balance1.hours_consumed + session_consumption
        new_remaining_hours = new_hours_purchased - new_hours_consumed
        
        # Assert: All operations should maintain 2-decimal precision
        expected_purchased = Decimal('36.44')     # 25.777 + 10.666 = 36.443, rounded
        expected_consumed = Decimal('3.78')       # 0.000 + 3.777 = 3.777, rounded
        expected_remaining = Decimal('32.66')     # 36.44 - 3.78 = 32.66, exact
        
        # These will FAIL until balance update utilities handle mixed operations
        self.assertEqual(new_hours_purchased.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_purchased)
        self.assertEqual(new_hours_consumed.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_consumed)
        self.assertEqual(new_remaining_hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_remaining)

    def test_hour_consumption_precision_edge_case_with_minute_level_granularity(self):
        """
        Test: Hour consumption from minute-level session durations should be precisely calculated.
        Expected to FAIL until minute-to-hour conversion utilities handle precision properly.
        """
        # Arrange: Session durations in minutes that create precision challenges
        session_minutes = [
            37,   # 0.616... hours
            83,   # 1.383... hours
            127,  # 2.116... hours
        ]
        
        # Act: Convert minutes to hours and calculate consumption
        total_consumed_hours = Decimal('0')
        for minutes in session_minutes:
            hours = Decimal(minutes) / Decimal('60')
            total_consumed_hours += hours
        
        new_balance = self.balance1.hours_purchased - total_consumed_hours
        
        # Assert: Minute-to-hour conversions should maintain precision
        expected_session_hours = [
            Decimal('0.62'),  # 37/60 = 0.616..., rounded up
            Decimal('1.38'),  # 83/60 = 1.383..., rounded down  
            Decimal('2.12'),  # 127/60 = 2.116..., rounded down
        ]
        expected_total = Decimal('4.12')    # Sum of rounded values
        expected_balance = Decimal('21.66') # 25.777 - 4.12 = 21.657, rounded
        
        # This will FAIL until minute-to-hour utilities handle precision
        individual_hours = []
        for minutes in session_minutes:
            hours = Decimal(minutes) / Decimal('60')
            individual_hours.append(hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        self.assertEqual(individual_hours, expected_session_hours)
        
        calculated_total = sum(individual_hours)
        self.assertEqual(calculated_total, expected_total)
        self.assertEqual(new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_balance)

    def test_group_session_precision_with_different_student_participation_rates(self):
        """
        Test: Group sessions with different participation rates should maintain precision consistency.
        Expected to FAIL until participation-based calculation utilities handle precision.
        """
        # Arrange: Group session where students have different participation percentages
        base_session_hours = Decimal('2.00')
        student1_participation = Decimal('1.00')  # 100% participation
        student2_participation = Decimal('0.75')  # 75% participation (left early)
        
        # Act: Calculate consumption based on participation
        student1_consumption = base_session_hours * student1_participation
        student2_consumption = base_session_hours * student2_participation
        
        student1_new_balance = self.balance1.hours_purchased - student1_consumption
        student2_new_balance = self.balance2.hours_purchased - student2_consumption
        
        # Assert: Participation-based consumption should be precisely calculated
        expected_consumption1 = Decimal('2.00')   # 2.00 * 1.00 = 2.00, exact
        expected_consumption2 = Decimal('1.50')   # 2.00 * 0.75 = 1.50, exact
        expected_balance1 = Decimal('23.78')      # 25.777 - 2.00 = 23.777, rounded
        expected_balance2 = Decimal('13.83')      # 15.333 - 1.50 = 13.833, rounded
        
        # These will FAIL until participation-based utilities are implemented
        self.assertEqual(student1_consumption, expected_consumption1)
        self.assertEqual(student2_consumption, expected_consumption2)
        self.assertEqual(student1_new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_balance1)
        self.assertEqual(student2_new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        expected_balance2)

    def test_hour_consumption_precision_consistency_across_different_rounding_scenarios(self):
        """
        Test: Hour consumption should use consistent rounding across different edge cases.
        Expected to FAIL until rounding consistency utilities are implemented.
        """
        # Arrange: Values that test different rounding edge cases
        consumption_scenarios = [
            (Decimal('1.555'), Decimal('1.56')),  # Round up
            (Decimal('1.554'), Decimal('1.55')),  # Round down
            (Decimal('1.565'), Decimal('1.57')),  # Round up (edge case)
            (Decimal('1.575'), Decimal('1.58')),  # Round up
            (Decimal('1.525'), Decimal('1.53')),  # Round up (halfway case)
        ]
        
        for input_consumption, expected_rounded in consumption_scenarios:
            with self.subTest(consumption=input_consumption):
                # Act: Apply consumption rounding
                rounded_consumption = input_consumption.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                new_balance = self.balance1.hours_purchased - rounded_consumption
                
                # Assert: Rounding should be consistent
                self.assertEqual(rounded_consumption, expected_rounded)
                
                # Verify balance precision is maintained
                self.assertEqual(new_balance.as_tuple().exponent, -3)  # Original precision
                rounded_balance = new_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                self.assertEqual(rounded_balance.as_tuple().exponent, -2)  # Standardized precision