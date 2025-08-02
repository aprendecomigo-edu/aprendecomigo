#!/usr/bin/env python3
"""
Performance Test Suite for Backend Navigation APIs (Issue #67)
Tests the performance targets for all critical navigation endpoints.
"""

import os
import sys
import time
import statistics
import requests
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from knox.models import AuthToken
from accounts.models import School, SchoolRole, TeacherInvitation

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aprendecomigo.settings.testing')

import django
django.setup()

User = get_user_model()

class NavigationAPIPerformanceTestCase(TestCase):
    """Test performance targets for all navigation APIs"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user and school
        self.user = User.objects.create_user(
            email='test@school.com',
            first_name='Test',
            last_name='User'
        )
        
        self.school = School.objects.create(
            name='Test School',
            description='Test School Description'
        )
        
        # Create school role
        SchoolRole.objects.create(
            user=self.user,
            school=self.school,
            role='school_owner'
        )
        
        # Create auth token
        self.token = AuthToken.objects.create(user=self.user)[1]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')

    def time_api_call(self, method, url, data=None, iterations=5):
        """Time an API call multiple times and return statistics"""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            if method.upper() == 'GET':
                response = self.client.get(url)
            elif method.upper() == 'POST':
                response = self.client.post(url, data or {}, format='json')
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.perf_counter()
            
            # Ensure request was successful
            if response.status_code not in [200, 201]:
                print(f"Warning: {method} {url} returned {response.status_code}")
            
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds
        
        return {
            'min': min(times),
            'max': max(times),
            'avg': statistics.mean(times),
            'median': statistics.median(times),
            'times': times
        }

    def test_global_search_performance_target(self):
        """Test Global Search API performance target (<200ms)"""
        print("\n🔍 Testing Global Search API Performance...")
        
        url = '/api/accounts/search/global/?q=test&limit=10'
        stats = self.time_api_call('GET', url)
        
        print(f"Global Search API Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        # Performance target: <200ms
        target = 200
        self.assertLess(
            stats['avg'], 
            target, 
            f"Global Search API average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: Average response time {stats['avg']:.2f}ms < {target}ms target")

    def test_notification_counts_performance_target(self):
        """Test Notification Counts API performance target (<50ms)"""
        print("\n🔔 Testing Notification Counts API Performance...")
        
        url = '/api/notifications/counts/'
        stats = self.time_api_call('GET', url)
        
        print(f"Notification Counts API Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        # Performance target: <50ms
        target = 50
        self.assertLess(
            stats['avg'], 
            target, 
            f"Notification Counts API average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: Average response time {stats['avg']:.2f}ms < {target}ms target")

    def test_onboarding_progress_performance_target(self):
        """Test Onboarding Progress API performance target (<100ms)"""
        print("\n📋 Testing Onboarding Progress API Performance...")
        
        # Test GET
        url = '/api/accounts/users/onboarding_progress/'
        stats = self.time_api_call('GET', url)
        
        print(f"Onboarding Progress API (GET) Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        # Performance target: <100ms
        target = 100
        self.assertLess(
            stats['avg'], 
            target, 
            f"Onboarding Progress API (GET) average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: GET average response time {stats['avg']:.2f}ms < {target}ms target")
        
        # Test POST
        update_data = {
            'completion_percentage': 75,
            'current_step': 'profile_setup',
            'completed_steps': ['welcome', 'basic_info']
        }
        stats = self.time_api_call('POST', url, update_data)
        
        print(f"Onboarding Progress API (POST) Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        self.assertLess(
            stats['avg'], 
            target, 
            f"Onboarding Progress API (POST) average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: POST average response time {stats['avg']:.2f}ms < {target}ms target")

    def test_navigation_preferences_performance_target(self):
        """Test Navigation Preferences API performance target (<50ms)"""
        print("\n⚙️ Testing Navigation Preferences API Performance...")
        
        # Test GET
        url = '/api/accounts/users/navigation_preferences/'
        stats = self.time_api_call('GET', url)
        
        print(f"Navigation Preferences API (GET) Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        # Performance target: <50ms
        target = 50
        self.assertLess(
            stats['avg'], 
            target, 
            f"Navigation Preferences API (GET) average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: GET average response time {stats['avg']:.2f}ms < {target}ms target")
        
        # Test POST
        prefs_data = {
            'default_landing_page': 'dashboard',
            'navigation_style': 'sidebar',
            'show_quick_actions': True,
            'quick_action_items': ['add_teacher', 'view_students', 'school_settings']
        }
        stats = self.time_api_call('POST', url, prefs_data)
        
        print(f"Navigation Preferences API (POST) Performance:")
        print(f"  Average: {stats['avg']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Min: {stats['min']:.2f}ms")
        print(f"  Max: {stats['max']:.2f}ms")
        
        self.assertLess(
            stats['avg'], 
            target, 
            f"Navigation Preferences API (POST) average response time {stats['avg']:.2f}ms exceeds target of {target}ms"
        )
        
        print(f"  ✅ PASS: POST average response time {stats['avg']:.2f}ms < {target}ms target")

    def test_comprehensive_performance_summary(self):
        """Run all performance tests and provide comprehensive summary"""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE PERFORMANCE TEST RESULTS - ISSUE #67")
        print("="*80)
        
        # Test all APIs
        apis = [
            {
                'name': 'Global Search API',
                'url': '/api/accounts/search/global/?q=test&limit=10',
                'method': 'GET',
                'target': 200,
                'description': 'Search across teachers, students, and courses'
            },
            {
                'name': 'Notification Counts API',
                'url': '/api/notifications/counts/',
                'method': 'GET',
                'target': 50,
                'description': 'Get notification badge counts'
            },
            {
                'name': 'Onboarding Progress API (GET)',
                'url': '/api/accounts/users/onboarding_progress/',
                'method': 'GET',
                'target': 100,
                'description': 'Get user onboarding progress'
            },
            {
                'name': 'Navigation Preferences API (GET)',
                'url': '/api/accounts/users/navigation_preferences/',
                'method': 'GET',
                'target': 50,
                'description': 'Get user navigation preferences'
            }
        ]
        
        results = []
        total_pass = 0
        
        for api in apis:
            print(f"\nTesting {api['name']}...")
            stats = self.time_api_call(api['method'], api['url'])
            
            passed = stats['avg'] < api['target']
            if passed:
                total_pass += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            results.append({
                'name': api['name'],
                'target': api['target'],
                'avg': stats['avg'],
                'status': status,
                'passed': passed
            })
            
            print(f"  {status}: {stats['avg']:.2f}ms < {api['target']}ms target")
        
        # Summary table
        print("\n" + "="*80)
        print("PERFORMANCE TEST SUMMARY")
        print("="*80)
        print(f"{'API':<35} {'Target':<10} {'Actual':<12} {'Status':<10}")
        print("-"*80)
        
        for result in results:
            print(f"{result['name']:<35} {result['target']}ms{'':<5} {result['avg']:.2f}ms{'':<4} {result['status']}")
        
        print("-"*80)
        print(f"OVERALL RESULT: {total_pass}/{len(apis)} APIs meeting performance targets")
        
        if total_pass == len(apis):
            print("🎉 ALL PERFORMANCE TARGETS MET!")
        else:
            print(f"⚠️  {len(apis) - total_pass} APIs need performance optimization")
        
        print("="*80)


if __name__ == '__main__':
    import unittest
    
    # Create test suite focused on performance
    suite = unittest.TestSuite()
    suite.addTest(NavigationAPIPerformanceTestCase('test_comprehensive_performance_summary'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)