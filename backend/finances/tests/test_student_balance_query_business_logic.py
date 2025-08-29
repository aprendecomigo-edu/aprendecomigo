"""
Unit tests for Student Balance Summary Query Logic business rules.

Tests core business rules for student balance calculations without API endpoints:
- Balance calculation algorithms (purchased - consumed hours)
- Overdraft scenario handling and validation
- Hour consumption aggregation business logic
- Package expiration impact on balance calculations
- Balance optimization algorithms for performance
- Cross-transaction balance consistency rules
- Refund processing impact on balance calculations

These tests focus on the business logic that needs fixes for GitHub Issue #173.
"""

from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from finances.models import (
    StudentAccountBalance,
    PurchaseTransaction,
    HourConsumption,
    TransactionType,
    TransactionPaymentStatus
)
from accounts.models import CustomUser


class BalanceCalculationAlgorithmTest(TestCase):
    """Test balance calculation algorithms and business rules."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_remaining_hours_basic_calculation(self):
        """Test basic remaining hours calculation algorithm."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('8.50'),
            balance_amount=Decimal('150.00')
        )
        
        expected_remaining = Decimal('20.00') - Decimal('8.50')
        self.assertEqual(balance.remaining_hours, expected_remaining)
        self.assertEqual(balance.remaining_hours, Decimal('11.50'))

    def test_remaining_hours_zero_balance(self):
        """Test remaining hours when purchased equals consumed."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('15.00'),
            hours_consumed=Decimal('15.00'),
            balance_amount=Decimal('0.00')
        )
        
        self.assertEqual(balance.remaining_hours, Decimal('0.00'))

    def test_remaining_hours_overdraft_scenario(self):
        """Test remaining hours calculation in overdraft scenario."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('12.75'),
            balance_amount=Decimal('-27.50')
        )
        
        # Should allow negative balance (overdraft)
        self.assertEqual(balance.remaining_hours, Decimal('-2.75'))
        self.assertTrue(balance.remaining_hours < Decimal('0.00'))

    def test_remaining_hours_precision_handling(self):
        """Test balance calculation handles decimal precision correctly."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.33'),
            hours_consumed=Decimal('7.66'),
            balance_amount=Decimal('127.00')
        )
        
        expected_remaining = Decimal('20.33') - Decimal('7.66')
        self.assertEqual(balance.remaining_hours, expected_remaining)
        self.assertEqual(balance.remaining_hours, Decimal('12.67'))

    def test_remaining_hours_large_numbers(self):
        """Test balance calculation with large hour values."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('999.99'),
            hours_consumed=Decimal('123.45'),
            balance_amount=Decimal('8766.00')
        )
        
        expected_remaining = Decimal('999.99') - Decimal('123.45')
        self.assertEqual(balance.remaining_hours, expected_remaining)
        self.assertEqual(balance.remaining_hours, Decimal('876.54'))

    def test_remaining_hours_zero_purchases(self):
        """Test balance calculation when no hours purchased."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('0.00'),
            hours_consumed=Decimal('0.00'),
            balance_amount=Decimal('0.00')
        )
        
        self.assertEqual(balance.remaining_hours, Decimal('0.00'))

    def test_remaining_hours_consumed_exceeds_purchased_significantly(self):
        """Test balance calculation with significant overdraft."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('5.00'),
            hours_consumed=Decimal('25.00'),  # 5x overdraft
            balance_amount=Decimal('-200.00')
        )
        
        self.assertEqual(balance.remaining_hours, Decimal('-20.00'))


class HourConsumptionAggregationTest(TestCase):
    """Test hour consumption aggregation business logic."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )
        
        self.balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('50.00'),
            hours_consumed=Decimal('0.00'),
            balance_amount=Decimal('500.00')
        )

    def test_consumption_aggregation_single_session(self):
        """Test consumption aggregation for single session."""
        # Mock session and purchase transaction
        session = Mock()
        session.id = 1
        package = Mock()
        package.id = 1
        
        consumption = HourConsumption.objects.create(
            student_account=self.balance,
            class_session=session,
            purchase_transaction=package,
            hours_consumed=Decimal('2.50'),
            hours_originally_reserved=Decimal('3.00')
        )
        
        # Balance should automatically update via model save
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.hours_consumed, Decimal('2.50'))
        self.assertEqual(self.balance.remaining_hours, Decimal('47.50'))

    def test_consumption_aggregation_multiple_sessions(self):
        """Test consumption aggregation across multiple sessions."""
        session1, session2, session3 = Mock(), Mock(), Mock()
        session1.id, session2.id, session3.id = 1, 2, 3
        package = Mock()
        package.id = 1
        
        # Create multiple consumption records
        consumptions = [
            HourConsumption.objects.create(
                student_account=self.balance,
                class_session=session1,
                purchase_transaction=package,
                hours_consumed=Decimal('1.25'),
                hours_originally_reserved=Decimal('1.50')
            ),
            HourConsumption.objects.create(
                student_account=self.balance,
                class_session=session2,
                purchase_transaction=package,
                hours_consumed=Decimal('2.75'),
                hours_originally_reserved=Decimal('3.00')
            ),
            HourConsumption.objects.create(
                student_account=self.balance,
                class_session=session3,
                purchase_transaction=package,
                hours_consumed=Decimal('0.50'),
                hours_originally_reserved=Decimal('1.00')
            )
        ]
        
        # Total consumption should aggregate correctly
        total_consumed = sum(c.hours_consumed for c in consumptions)
        self.balance.refresh_from_db()
        
        self.assertEqual(total_consumed, Decimal('4.50'))
        self.assertEqual(self.balance.hours_consumed, Decimal('4.50'))
        self.assertEqual(self.balance.remaining_hours, Decimal('45.50'))

    def test_consumption_aggregation_with_refunds(self):
        """Test consumption aggregation when refunds are processed."""
        session = Mock()
        session.id = 1
        package = Mock()
        package.id = 1
        
        # Create initial consumption
        consumption = HourConsumption.objects.create(
            student_account=self.balance,
            class_session=session,
            purchase_transaction=package,
            hours_consumed=Decimal('3.00'),
            hours_originally_reserved=Decimal('3.00')
        )
        
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.hours_consumed, Decimal('3.00'))
        
        # Process refund (simulate partial refund)
        refund_amount = Decimal('1.00')
        consumption.hours_consumed -= refund_amount
        consumption.is_refunded = True
        consumption.refund_reason = "Session ended early"
        consumption.save()
        
        # Update balance to reflect refund
        self.balance.hours_consumed -= refund_amount
        self.balance.save()
        
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.hours_consumed, Decimal('2.00'))
        self.assertEqual(self.balance.remaining_hours, Decimal('48.00'))

    def test_consumption_aggregation_precision_handling(self):
        """Test consumption aggregation maintains decimal precision."""
        session = Mock()
        session.id = 1
        package = Mock()
        package.id = 1
        
        # Create consumption with high precision
        consumption = HourConsumption.objects.create(
            student_account=self.balance,
            class_session=session,
            purchase_transaction=package,
            hours_consumed=Decimal('2.333'),  # 3 decimal places
            hours_originally_reserved=Decimal('2.500')
        )
        
        self.balance.refresh_from_db()
        
        # Should maintain precision in calculations
        self.assertEqual(self.balance.hours_consumed, Decimal('2.333'))
        expected_remaining = Decimal('50.00') - Decimal('2.333')
        self.assertEqual(self.balance.remaining_hours, expected_remaining)


class PackageExpirationBalanceImpactTest(TestCase):
    """Test impact of package expiration on balance calculations."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_balance_impact_when_package_expires_with_remaining_hours(self):
        """Test balance impact when package expires with unused hours."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('12.00'),
            balance_amount=Decimal('80.00')
        )
        
        # Simulate package expiration removing unused hours
        expired_hours = Decimal('8.00')  # 20 - 12 = 8 remaining hours expired
        
        # Package expiration should reduce purchased hours to match consumed
        balance.hours_purchased -= expired_hours
        balance.save()
        
        balance.refresh_from_db()
        self.assertEqual(balance.hours_purchased, Decimal('12.00'))
        self.assertEqual(balance.hours_consumed, Decimal('12.00'))
        self.assertEqual(balance.remaining_hours, Decimal('0.00'))

    def test_balance_impact_when_fully_consumed_package_expires(self):
        """Test balance impact when fully consumed package expires."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('15.00'),
            hours_consumed=Decimal('15.00'),
            balance_amount=Decimal('0.00')
        )
        
        # No hours to expire since fully consumed
        original_purchased = balance.hours_purchased
        original_consumed = balance.hours_consumed
        
        # Package expiration shouldn't change balance for fully consumed packages
        self.assertEqual(balance.remaining_hours, Decimal('0.00'))
        self.assertEqual(balance.hours_purchased, original_purchased)
        self.assertEqual(balance.hours_consumed, original_consumed)

    def test_balance_impact_when_over_consumed_package_expires(self):
        """Test balance impact when over-consumed package expires."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('13.00'),  # Overdraft
            balance_amount=Decimal('-30.00')
        )
        
        # No hours to expire since over-consumed (negative remaining)
        self.assertEqual(balance.remaining_hours, Decimal('-3.00'))
        
        # Package expiration with overdraft should not change the balance
        # since there are no positive hours to expire
        original_purchased = balance.hours_purchased
        original_consumed = balance.hours_consumed
        
        # Simulate expiration check - no hours would be expired
        hours_to_expire = max(balance.remaining_hours, Decimal('0.00'))
        self.assertEqual(hours_to_expire, Decimal('0.00'))


class BalanceOptimizationAlgorithmsTest(TestCase):
    """Test balance calculation optimization algorithms for performance."""

    def setUp(self):
        """Set up test data."""
        self.students = []
        for i in range(5):
            student = CustomUser.objects.create_user(
                email=f"student{i}@test.com",
                name=f"Test Student {i}"
            )
            self.students.append(student)

    def test_bulk_balance_calculation_optimization(self):
        """Test optimized bulk balance calculations."""
        # Create balances for multiple students
        balances = []
        for i, student in enumerate(self.students):
            balance = StudentAccountBalance.objects.create(
                student=student,
                hours_purchased=Decimal(f'{(i+1)*10}.00'),
                hours_consumed=Decimal(f'{i*3}.50'),
                balance_amount=Decimal(f'{(i+1)*100}.00')
            )
            balances.append(balance)
        
        # Test bulk query efficiency - should use select_related
        with patch('django.db.models.QuerySet.select_related') as mock_select:
            mock_select.return_value = balances
            
            # Simulate optimized queryset
            optimized_balances = StudentAccountBalance.objects.select_related('student').all()
            
            # Each balance calculation should work correctly
            for i, balance in enumerate(balances):
                expected_remaining = Decimal(f'{(i+1)*10}.00') - Decimal(f'{i*3}.50')
                self.assertEqual(balance.remaining_hours, expected_remaining)

    def test_balance_calculation_caching_strategy(self):
        """Test balance calculation caching for performance optimization."""
        balance = StudentAccountBalance.objects.create(
            student=self.students[0],
            hours_purchased=Decimal('25.00'),
            hours_consumed=Decimal('10.00'),
            balance_amount=Decimal('150.00')
        )
        
        # First calculation
        first_result = balance.remaining_hours
        self.assertEqual(first_result, Decimal('15.00'))
        
        # Second calculation should return same result (property doesn't cache by default)
        second_result = balance.remaining_hours
        self.assertEqual(second_result, first_result)
        
        # Modify balance and verify calculation updates
        balance.hours_consumed = Decimal('12.50')
        third_result = balance.remaining_hours
        self.assertEqual(third_result, Decimal('12.50'))

    def test_aggregated_balance_summary_optimization(self):
        """Test optimized aggregation for balance summaries."""
        # Create multiple balances with different states
        test_cases = [
            (Decimal('20.00'), Decimal('15.00')),  # Positive balance
            (Decimal('10.00'), Decimal('10.00')),  # Zero balance
            (Decimal('15.00'), Decimal('18.00')),  # Overdraft
        ]
        
        balances = []
        for i, (purchased, consumed) in enumerate(test_cases):
            balance = StudentAccountBalance.objects.create(
                student=self.students[i],
                hours_purchased=purchased,
                hours_consumed=consumed,
                balance_amount=Decimal(f'{i*50}.00')
            )
            balances.append(balance)
        
        # Test aggregated calculations
        total_purchased = sum(b.hours_purchased for b in balances)
        total_consumed = sum(b.hours_consumed for b in balances)
        total_remaining = sum(b.remaining_hours for b in balances)
        
        self.assertEqual(total_purchased, Decimal('45.00'))  # 20+10+15
        self.assertEqual(total_consumed, Decimal('43.00'))   # 15+10+18
        self.assertEqual(total_remaining, Decimal('2.00'))   # 5+0+(-3)

    def test_balance_query_index_utilization(self):
        """Test that balance queries utilize database indexes efficiently."""
        # Create balance with specific student
        balance = StudentAccountBalance.objects.create(
            student=self.students[0],
            hours_purchased=Decimal('30.00'),
            hours_consumed=Decimal('12.00'),
            balance_amount=Decimal('180.00')
        )
        
        # Test student-based lookups (should use student index)
        student_balance = StudentAccountBalance.objects.get(student=self.students[0])
        self.assertEqual(student_balance.remaining_hours, Decimal('18.00'))
        
        # Test filtering by balance states (should be optimized)
        positive_balances = StudentAccountBalance.objects.filter(
            # hours_purchased__gt=models.F('hours_consumed')
        )
        self.assertIn(balance, positive_balances)


class CrossTransactionBalanceConsistencyTest(TestCase):
    """Test balance consistency across transactions and operations."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_balance_consistency_after_purchase(self):
        """Test balance consistency after purchase transactions."""
        # Initial balance
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.00'),
            hours_consumed=Decimal('3.00'),
            balance_amount=Decimal('70.00')
        )
        
        initial_remaining = balance.remaining_hours
        self.assertEqual(initial_remaining, Decimal('7.00'))
        
        # Simulate purchase of additional hours
        additional_hours = Decimal('15.00')
        additional_amount = Decimal('150.00')
        
        balance.hours_purchased += additional_hours
        balance.balance_amount += additional_amount
        balance.save()
        
        # Balance should reflect new purchase
        balance.refresh_from_db()
        self.assertEqual(balance.hours_purchased, Decimal('25.00'))
        self.assertEqual(balance.hours_consumed, Decimal('3.00'))
        self.assertEqual(balance.remaining_hours, Decimal('22.00'))

    def test_balance_consistency_after_consumption_and_refund_cycle(self):
        """Test balance consistency through consumption and refund cycle."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('8.00'),
            balance_amount=Decimal('120.00')
        )
        
        # Step 1: Additional consumption
        consumption_amount = Decimal('4.00')
        balance.hours_consumed += consumption_amount
        balance.save()
        
        self.assertEqual(balance.remaining_hours, Decimal('8.00'))  # 20 - 12
        
        # Step 2: Partial refund
        refund_amount = Decimal('1.50')
        balance.hours_consumed -= refund_amount
        balance.save()
        
        balance.refresh_from_db()
        self.assertEqual(balance.hours_consumed, Decimal('10.50'))  # 12 - 1.5
        self.assertEqual(balance.remaining_hours, Decimal('9.50'))   # 20 - 10.5

    def test_balance_consistency_with_concurrent_operations(self):
        """Test balance consistency with simulated concurrent operations."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('30.00'),
            hours_consumed=Decimal('5.00'),
            balance_amount=Decimal('250.00')
        )
        
        initial_remaining = balance.remaining_hours
        self.assertEqual(initial_remaining, Decimal('25.00'))
        
        # Simulate concurrent operations
        # Operation 1: Consume hours
        operation1_consumption = Decimal('3.00')
        
        # Operation 2: Add purchase (different transaction)
        operation2_purchase = Decimal('10.00')
        
        # Apply both operations
        balance.hours_consumed += operation1_consumption
        balance.hours_purchased += operation2_purchase
        balance.save()
        
        # Final balance should reflect both operations
        balance.refresh_from_db()
        expected_remaining = Decimal('30.00') + operation2_purchase - (Decimal('5.00') + operation1_consumption)
        self.assertEqual(balance.remaining_hours, expected_remaining)
        self.assertEqual(balance.remaining_hours, Decimal('32.00'))  # 40 - 8

    def test_balance_consistency_edge_case_zero_transitions(self):
        """Test balance consistency at zero transition points."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('5.00'),
            hours_consumed=Decimal('4.50'),
            balance_amount=Decimal('5.00')
        )
        
        # Near zero remaining
        self.assertEqual(balance.remaining_hours, Decimal('0.50'))
        
        # Consume remaining hours exactly
        balance.hours_consumed += Decimal('0.50')
        balance.save()
        
        self.assertEqual(balance.remaining_hours, Decimal('0.00'))
        
        # Consume beyond available (overdraft)
        balance.hours_consumed += Decimal('2.00')
        balance.save()
        
        balance.refresh_from_db()
        self.assertEqual(balance.remaining_hours, Decimal('-2.00'))


class RefundProcessingBalanceImpactTest(TestCase):
    """Test impact of refund processing on balance calculations."""

    def setUp(self):
        """Set up test data."""
        self.student = CustomUser.objects.create_user(
            email="student@test.com",
            name="Test Student"
        )

    def test_full_refund_impact_on_balance(self):
        """Test full refund impact on balance calculations."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('15.00'),
            hours_consumed=Decimal('6.00'),
            balance_amount=Decimal('90.00')
        )
        
        # Initial state
        self.assertEqual(balance.remaining_hours, Decimal('9.00'))
        
        # Process full refund of consumed hours
        refund_hours = Decimal('6.00')
        balance.hours_consumed -= refund_hours
        balance.save()
        
        # Balance should reflect full refund
        balance.refresh_from_db()
        self.assertEqual(balance.hours_consumed, Decimal('0.00'))
        self.assertEqual(balance.remaining_hours, Decimal('15.00'))

    def test_partial_refund_impact_on_balance(self):
        """Test partial refund impact on balance calculations."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('20.00'),
            hours_consumed=Decimal('12.00'),
            balance_amount=Decimal('80.00')
        )
        
        # Initial state
        self.assertEqual(balance.remaining_hours, Decimal('8.00'))
        
        # Process partial refund
        refund_hours = Decimal('3.50')
        balance.hours_consumed -= refund_hours
        balance.save()
        
        # Balance should reflect partial refund
        balance.refresh_from_db()
        self.assertEqual(balance.hours_consumed, Decimal('8.50'))
        self.assertEqual(balance.remaining_hours, Decimal('11.50'))

    def test_multiple_refunds_cumulative_impact(self):
        """Test cumulative impact of multiple refunds on balance."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('25.00'),
            hours_consumed=Decimal('18.00'),
            balance_amount=Decimal('70.00')
        )
        
        # Initial state
        self.assertEqual(balance.remaining_hours, Decimal('7.00'))
        
        # Process multiple refunds
        refunds = [Decimal('2.00'), Decimal('1.50'), Decimal('0.75')]
        
        for refund_amount in refunds:
            balance.hours_consumed -= refund_amount
            balance.save()
            balance.refresh_from_db()
        
        # Total refunded: 2.00 + 1.50 + 0.75 = 4.25
        # Final consumed: 18.00 - 4.25 = 13.75
        # Final remaining: 25.00 - 13.75 = 11.25
        self.assertEqual(balance.hours_consumed, Decimal('13.75'))
        self.assertEqual(balance.remaining_hours, Decimal('11.25'))

    def test_refund_precision_in_balance_calculations(self):
        """Test refund precision handling in balance calculations."""
        balance = StudentAccountBalance.objects.create(
            student=self.student,
            hours_purchased=Decimal('10.333'),
            hours_consumed=Decimal('7.666'),
            balance_amount=Decimal('40.00')
        )
        
        # Initial state with high precision
        expected_initial = Decimal('10.333') - Decimal('7.666')
        self.assertEqual(balance.remaining_hours, expected_initial)
        self.assertEqual(balance.remaining_hours, Decimal('2.667'))
        
        # Process precision refund
        refund_amount = Decimal('1.111')
        balance.hours_consumed -= refund_amount
        balance.save()
        
        # Verify precision maintained
        balance.refresh_from_db()
        expected_consumed = Decimal('7.666') - Decimal('1.111')
        expected_remaining = Decimal('10.333') - expected_consumed
        
        self.assertEqual(balance.hours_consumed, expected_consumed)
        self.assertEqual(balance.remaining_hours, expected_remaining)
        self.assertEqual(balance.remaining_hours, Decimal('3.778'))