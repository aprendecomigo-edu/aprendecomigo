"""
Student Balance Summary Query Optimization Tests - Issue #173 Priority 6

This test suite validates that student balance summary endpoints are properly
optimized for performance, addressing query count optimization and performance
issues in balance calculation operations.

These tests are designed to initially FAIL to demonstrate current performance
issues where balance summary endpoints generate excessive database queries
or have poor performance characteristics.

Test Coverage:
- Student balance summary endpoint query count optimization
- N+1 query detection in balance calculations
- Performance benchmarks for balance operations
- Database query efficiency in multi-school scenarios
- Caching effectiveness for balance data
- Response time validation for balance endpoints
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.test.utils import override_settings
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch
import time

from accounts.models import School, StudentProfile
from finances.models import (
    StudentAccountBalance,
    StudentPackage,
    PackageStatus,
    StoredPaymentMethod,
    PurchaseTransaction,
    TransactionPaymentStatus,
    TransactionType,
    HourConsumptionRecord
)

User = get_user_model()


class StudentBalanceQueryOptimizationTests(APITestCase):
    """
    Test query count optimization for student balance endpoints.
    
    These tests validate that balance summary operations use
    efficient database queries and avoid N+1 query problems.
    """

    def setUp(self):
        """Set up test data for query optimization tests."""
        self.student = User.objects.create_user(
            email='student@test.com',
            name='Test Student',
        )
        
        self.school_owner = User.objects.create_user(
            email='owner@school.com', 
            name='School Owner',
        )
        
        # Create multiple schools for testing multi-school scenarios
        self.schools = []
        for i in range(3):
            school = School.objects.create(
                name=f'Test School {i+1}',
                owner=self.school_owner,
                time_zone='UTC'
            )
            self.schools.append(school)
        
        # Create student profiles for multiple schools
        for school in self.schools:
            StudentProfile.objects.create(
                user=self.student,
                school=school,
                grade_level='elementary'
            )
        
        # Create student balances
        self.balances = []
        for school in self.schools:
            balance = StudentAccountBalance.objects.create(
                student=self.student,
                hours_purchased=Decimal('20.00'),
                hours_consumed=Decimal('5.00'),
                balance_amount=Decimal('300.00')
            )
            self.balances.append(balance)
        
        # Create student packages
        self.packages = []
        for school in self.schools:
            for j in range(2):  # 2 packages per school
                package = StudentPackage.objects.create(
                    student=self.student,
                    school=school,
                    package_name=f'Package {j+1} - School {school.name}',
                    hours_purchased=Decimal('10.00'),
                    hours_remaining=Decimal('8.00'),
                    amount_paid=Decimal('100.00'),
                    expires_at='2025-12-31',
                    status=PackageStatus.ACTIVE
                )
                self.packages.append(package)
        
        # Create hour consumption records
        for package in self.packages:
            for k in range(3):  # 3 consumption records per package
                HourConsumptionRecord.objects.create(
                    student=self.student,
                    package=package,
                    hours_consumed=Decimal('1.0'),
                    consumed_at=f'2025-08-{k+10}',
                    description=f'Test consumption {k+1}'
                )
        
        # Create transactions
        for school in self.schools:
            for l in range(2):  # 2 transactions per school
                PurchaseTransaction.objects.create(
                    student=self.student,
                    transaction_type=TransactionType.PACKAGE,
                    amount=Decimal('50.00'),
                    payment_status=TransactionPaymentStatus.COMPLETED,
                    stripe_payment_intent_id=f'pi_test_{school.id}_{l}',
                    metadata={'school_id': school.id}
                )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_balance_summary_query_count_optimization_fails(self):
        """
        Test that balance summary uses efficient database queries.
        
        This test validates that the balance summary endpoint doesn't
        generate excessive database queries, especially N+1 queries.
        
        Expected to FAIL initially due to query count optimization issues.
        """
        # Reset query count tracking
        connection.queries_log.clear()
        
        # Make balance summary request
        url = '/api/finances/studentbalance/summary/'
        with self.assertNumQueries(
            10,  # Expected maximum queries for optimized endpoint
            msg="Balance summary should use efficient queries. "
                "Check for select_related/prefetch_related optimizations."
        ):
            response = self.client.get(url)
        
        # Should return successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Analyze the queries that were made
        queries = connection.queries
        
        # Look for N+1 query patterns
        repeated_queries = {}
        for query in queries:
            sql = query['sql']
            # Normalize the query by removing specific IDs
            import re
            normalized = re.sub(r'\b\d+\b', 'ID', sql)
            
            if normalized in repeated_queries:
                repeated_queries[normalized] += 1
            else:
                repeated_queries[normalized] = 1
        
        # Check for excessive repeated queries (N+1 pattern)
        for normalized_query, count in repeated_queries.items():
            if count > 3:  # More than 3 similar queries suggests N+1
                self.fail(
                    f"Possible N+1 query detected (repeated {count} times): {normalized_query}. "
                    f"Consider using select_related() or prefetch_related() for optimization."
                )

    def test_balance_summary_response_time_optimization_fails(self):
        """
        Test that balance summary has acceptable response times.
        
        This test validates that balance calculations complete
        within acceptable time limits even with complex data.
        
        Expected to FAIL initially due to performance issues.
        """
        # Add more data to stress test performance
        for _ in range(10):
            package = StudentPackage.objects.create(
                student=self.student,
                school=self.schools[0],
                package_name='Performance Test Package',
                hours_purchased=Decimal('5.00'),
                hours_remaining=Decimal('3.00'),
                amount_paid=Decimal('50.00'),
                expires_at='2025-12-31',
                status=PackageStatus.ACTIVE
            )
            
            # Add consumption records
            for _ in range(5):
                HourConsumptionRecord.objects.create(
                    student=self.student,
                    package=package,
                    hours_consumed=Decimal('0.5'),
                    consumed_at='2025-08-15',
                    description='Performance test consumption'
                )
        
        # Measure response time
        start_time = time.time()
        
        url = '/api/finances/studentbalance/summary/'
        response = self.client.get(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should complete within reasonable time (2 seconds max)
        self.assertLess(
            response_time,
            2.0,
            f"Balance summary took {response_time:.2f} seconds, should be < 2.0s. "
            f"Check query optimization and calculation efficiency."
        )
        
        # Should return successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_multi_school_balance_query_optimization_fails(self):
        """
        Test query optimization for multi-school balance scenarios.
        
        This test validates that balance calculations across multiple
        schools are efficiently handled without redundant queries.
        
        Expected to FAIL initially due to multi-school query inefficiency.
        """
        # Reset query tracking
        connection.queries_log.clear()
        
        # Request balance summary that spans multiple schools
        url = '/api/finances/studentbalance/summary/'
        
        # Should use efficient queries regardless of school count
        max_queries = 15  # Reasonable maximum for multi-school scenario
        
        with self.assertNumQueries(
            max_queries,
            msg=f"Multi-school balance summary should use ≤{max_queries} queries. "
                f"Check for proper joins and aggregation optimization."
        ):
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Should include data from all schools efficiently
        # Check if response includes multi-school information
        if 'schools' in data or 'school_balances' in data:
            school_data = data.get('schools', data.get('school_balances', []))
            self.assertGreaterEqual(
                len(school_data),
                len(self.schools),
                "Multi-school balance should include all schools"
            )

    def test_balance_history_pagination_optimization_fails(self):
        """
        Test that balance history pagination is optimized.
        
        This test validates that paginated balance history requests
        use efficient queries with proper LIMIT/OFFSET optimization.
        
        Expected to FAIL initially due to pagination query issues.
        """
        # Create more transaction history for pagination testing
        for i in range(25):  # Create enough for multiple pages
            PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('25.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f'pi_pagination_test_{i}',
                metadata={'page_test': True}
            )
        
        # Test paginated request
        connection.queries_log.clear()
        
        url = '/api/finances/studentbalance/history/?limit=10&offset=0'
        
        with self.assertNumQueries(
            5,  # Should be efficient even with pagination
            msg="Paginated balance history should use efficient queries. "
                "Check pagination query optimization."
        ):
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Should have pagination metadata
        self.assertIn('count', data)
        self.assertIn('results', data)
        
        # Should return requested page size
        results = data.get('results', [])
        self.assertLessEqual(
            len(results),
            10,
            "Pagination should respect limit parameter"
        )

    def test_balance_aggregation_query_optimization_fails(self):
        """
        Test that balance aggregation calculations are optimized.
        
        This test validates that complex balance aggregations
        (totals, averages, etc.) use database-level calculations.
        
        Expected to FAIL initially due to inefficient aggregation.
        """
        connection.queries_log.clear()
        
        # Request endpoint that requires aggregation
        url = '/api/finances/studentbalance/analytics/'
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Skip if analytics endpoint doesn't exist
            self.skipTest("Balance analytics endpoint not implemented")
        
        # Should use database aggregation, not Python calculations
        queries = connection.queries
        aggregation_queries = [
            q for q in queries 
            if any(keyword in q['sql'].upper() for keyword in ['SUM(', 'AVG(', 'COUNT(', 'GROUP BY'])
        ]
        
        self.assertGreater(
            len(aggregation_queries),
            0,
            "Balance aggregation should use database-level calculations (SUM, AVG, COUNT). "
            "Found no aggregation queries. Check if calculations are done in Python instead of database."
        )

    def test_balance_caching_effectiveness_fails(self):
        """
        Test that balance data caching is effective.
        
        This test validates that repeated balance requests use
        caching to improve performance.
        
        Expected to FAIL initially due to ineffective or missing caching.
        """
        # Make initial request to populate cache
        url = '/api/finances/studentbalance/summary/'
        first_response = self.client.get(url)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        
        # Reset query tracking
        connection.queries_log.clear()
        
        # Make second request - should use cache
        second_response = self.client.get(url)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        
        # Should use fewer queries due to caching
        cached_query_count = len(connection.queries)
        
        # If caching is effective, should use significantly fewer queries
        if cached_query_count > 5:  # Allow some queries for authentication, etc.
            self.fail(
                f"Balance summary caching appears ineffective. "
                f"Second request used {cached_query_count} queries, expected ≤5. "
                f"Check cache implementation for balance data."
            )
        
        # Responses should be identical
        self.assertEqual(
            first_response.json(),
            second_response.json(),
            "Cached response should be identical to original"
        )


class StudentBalancePerformanceBenchmarkTests(APITestCase):
    """
    Benchmark tests for student balance performance.
    
    These tests establish performance baselines and validate
    that balance operations meet performance requirements.
    """

    def setUp(self):
        """Set up benchmark test data."""
        self.student = User.objects.create_user(
            email='benchmark@test.com',
            name='Benchmark Student',
        )
        
        self.school = School.objects.create(
            name='Benchmark School',
            owner=self.student,
            time_zone='UTC'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_balance_calculation_scalability_fails(self):
        """
        Test balance calculation performance with large datasets.
        
        This test validates that balance calculations remain
        performant as data volume increases.
        
        Expected to FAIL initially due to scalability issues.
        """
        # Create large dataset for scalability testing
        package_count = 50
        consumption_records_per_package = 10
        
        packages = []
        for i in range(package_count):
            package = StudentPackage.objects.create(
                student=self.student,
                school=self.school,
                package_name=f'Scalability Package {i+1}',
                hours_purchased=Decimal('10.00'),
                hours_remaining=Decimal('7.00'),
                amount_paid=Decimal('100.00'),
                expires_at='2025-12-31',
                status=PackageStatus.ACTIVE
            )
            packages.append(package)
            
            # Add consumption records
            for j in range(consumption_records_per_package):
                HourConsumptionRecord.objects.create(
                    student=self.student,
                    package=package,
                    hours_consumed=Decimal('0.3'),
                    consumed_at=f'2025-08-{(j % 28) + 1:02d}',
                    description=f'Scalability test {j+1}'
                )
        
        # Measure performance with large dataset
        start_time = time.time()
        
        url = '/api/finances/studentbalance/summary/'
        response = self.client.get(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should handle large dataset efficiently
        self.assertLess(
            response_time,
            5.0,  # 5 second max for large dataset
            f"Balance calculation with {package_count} packages and "
            f"{package_count * consumption_records_per_package} records "
            f"took {response_time:.2f}s, should be <5.0s. "
            f"Check query optimization for large datasets."
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Validate response includes all data
        data = response.json()
        if 'packages' in data:
            self.assertGreaterEqual(
                len(data['packages']),
                package_count,
                "Response should include all packages even with large dataset"
            )

    def test_concurrent_balance_requests_performance_fails(self):
        """
        Test balance endpoint performance under concurrent load.
        
        This test validates that balance endpoints can handle
        multiple concurrent requests efficiently.
        
        Expected to FAIL initially due to concurrency performance issues.
        """
        # Create baseline data
        for i in range(10):
            StudentPackage.objects.create(
                student=self.student,
                school=self.school,
                package_name=f'Concurrent Test Package {i+1}',
                hours_purchased=Decimal('5.00'),
                hours_remaining=Decimal('4.00'),
                amount_paid=Decimal('50.00'),
                expires_at='2025-12-31',
                status=PackageStatus.ACTIVE
            )
        
        # Simulate concurrent requests
        import threading
        import queue
        
        url = '/api/finances/studentbalance/summary/'
        results_queue = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = self.client.get(url)
                end_time = time.time()
                
                results_queue.put({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == status.HTTP_200_OK
                })
            except Exception as e:
                results_queue.put({
                    'status_code': 500,
                    'response_time': float('inf'),
                    'success': False,
                    'error': str(e)
                })
        
        # Start multiple concurrent requests
        threads = []
        thread_count = 5
        
        start_time = time.time()
        for _ in range(thread_count):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # All requests should succeed
        successful_requests = [r for r in results if r['success']]
        self.assertEqual(
            len(successful_requests),
            thread_count,
            f"All {thread_count} concurrent requests should succeed. "
            f"Got {len(successful_requests)} successful requests. "
            f"Check concurrency handling in balance endpoints."
        )
        
        # Average response time should be reasonable
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
        self.assertLess(
            avg_response_time,
            3.0,
            f"Average response time under concurrent load: {avg_response_time:.2f}s, should be <3.0s. "
            f"Check performance optimization for concurrent requests."
        )
        
        # Total time should indicate good parallelization
        self.assertLess(
            total_time,
            8.0,  # Should complete much faster than sequential requests
            f"Concurrent requests took {total_time:.2f}s total, should be <8.0s. "
            f"Check for blocking operations that prevent concurrency."
        )

    @override_settings(DEBUG=False)  # Disable debug mode for realistic performance
    def test_production_performance_baseline_fails(self):
        """
        Test balance endpoint performance in production-like settings.
        
        This test validates performance with production settings
        and realistic data volumes.
        
        Expected to FAIL initially due to production performance issues.
        """
        # Create realistic data volume
        for i in range(20):
            package = StudentPackage.objects.create(
                student=self.student,
                school=self.school,
                package_name=f'Production Test Package {i+1}',
                hours_purchased=Decimal('8.00'),
                hours_remaining=Decimal('6.00'),
                amount_paid=Decimal('80.00'),
                expires_at='2025-12-31',
                status=PackageStatus.ACTIVE
            )
            
            # Add realistic consumption history
            for j in range(5):
                HourConsumptionRecord.objects.create(
                    student=self.student,
                    package=package,
                    hours_consumed=Decimal('0.4'),
                    consumed_at=f'2025-08-{(j % 28) + 1:02d}',
                    description=f'Production test consumption {j+1}'
                )
        
        # Add payment methods and transactions
        for i in range(3):
            StoredPaymentMethod.objects.create(
                student=self.student,
                stripe_payment_method_id=f'pm_production_test_{i}',
                stripe_customer_id=f'cus_production_test_{i}',
                card_brand='visa',
                card_last4=f'{4200 + i}',
                card_exp_month=12,
                card_exp_year=2025 + i,
                is_default=(i == 0),
                is_active=True,
            )
            
            PurchaseTransaction.objects.create(
                student=self.student,
                transaction_type=TransactionType.PACKAGE,
                amount=Decimal('80.00'),
                payment_status=TransactionPaymentStatus.COMPLETED,
                stripe_payment_intent_id=f'pi_production_test_{i}',
                metadata={'production_test': True}
            )
        
        # Test production performance
        start_time = time.time()
        
        url = '/api/finances/studentbalance/summary/'
        response = self.client.get(url)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Production performance should be excellent
        self.assertLess(
            response_time,
            1.0,  # 1 second max for production
            f"Production balance summary took {response_time:.2f}s, should be <1.0s. "
            f"Check production optimization: database indexes, query efficiency, caching."
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Response should be complete and accurate
        data = response.json()
        expected_fields = [
            'hours_available', 'hours_consumed', 'balance_amount',
            'packages_count', 'active_packages'
        ]
        
        for field in expected_fields:
            self.assertIn(
                field,
                data,
                f"Production response missing expected field: {field}"
            )