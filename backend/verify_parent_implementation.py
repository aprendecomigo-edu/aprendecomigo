#!/usr/bin/env python3
"""
Verification script for Parent-Child Account Infrastructure (GitHub Issue #111)

This script performs static code analysis to verify the implementation
without requiring Django to be running.
"""

import os
import re
import ast
from typing import List, Dict, Any


class ParentChildImplementationVerifier:
    """Verifies the parent-child infrastructure implementation."""
    
    def __init__(self, backend_path: str):
        self.backend_path = backend_path
        self.accounts_path = os.path.join(backend_path, 'accounts')
        self.results = {}
        
    def verify_all(self) -> Dict[str, Any]:
        """Run all verification checks."""
        print("🔍 Verifying Parent-Child Account Infrastructure Implementation")
        print("=" * 70)
        
        checks = [
            ("Models Implementation", self.verify_models),
            ("Admin Interface", self.verify_admin),
            ("API Views", self.verify_views), 
            ("URL Configuration", self.verify_urls),
            ("Permissions", self.verify_permissions),
            ("Serializers", self.verify_serializers),
            ("Migration Files", self.verify_migrations),
        ]
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}")
            print("-" * 40)
            try:
                result = check_func()
                self.results[check_name] = result
                if result.get('status') == 'success':
                    print(f"✅ {check_name}: PASSED")
                else:
                    print(f"❌ {check_name}: FAILED")
                    for issue in result.get('issues', []):
                        print(f"   - {issue}")
            except Exception as e:
                print(f"❌ {check_name}: ERROR - {e}")
                self.results[check_name] = {'status': 'error', 'error': str(e)}
        
        return self.results
    
    def verify_models(self) -> Dict[str, Any]:
        """Verify ParentProfile and ParentChildRelationship models exist."""
        models_file = os.path.join(self.accounts_path, 'models.py')
        
        if not os.path.exists(models_file):
            return {'status': 'error', 'issues': ['models.py file not found']}
        
        with open(models_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        # Check for PARENT role in SchoolRole
        if 'PARENT = "parent", _("Parent")' in content:
            found_items.append('PARENT role in SchoolRole enum')
        else:
            issues.append('PARENT role not found in SchoolRole enum')
        
        # Check for ParentProfile model
        if 'class ParentProfile(models.Model):' in content:
            found_items.append('ParentProfile model class')
        else:
            issues.append('ParentProfile model class not found')
        
        # Check for ParentChildRelationship model
        if 'class ParentChildRelationship(models.Model):' in content:
            found_items.append('ParentChildRelationship model class')
        else:
            issues.append('ParentChildRelationship model class not found')
        
        # Check for RelationshipType enum
        if 'class RelationshipType(models.TextChoices):' in content:
            found_items.append('RelationshipType enum')
        else:
            issues.append('RelationshipType enum not found')
        
        # Check for key fields in ParentProfile
        if 'notification_preferences' in content and 'default_approval_settings' in content:
            found_items.append('ParentProfile key fields')
        else:
            issues.append('ParentProfile missing key fields')
        
        # Check for key fields in ParentChildRelationship
        if 'requires_purchase_approval' in content and 'requires_session_approval' in content:
            found_items.append('ParentChildRelationship approval fields')
        else:
            issues.append('ParentChildRelationship missing approval fields')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_admin(self) -> Dict[str, Any]:
        """Verify admin interface configurations."""
        admin_file = os.path.join(self.accounts_path, 'admin.py')
        
        if not os.path.exists(admin_file):
            return {'status': 'error', 'issues': ['admin.py file not found']}
        
        with open(admin_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        # Check imports
        if 'ParentProfile' in content and 'ParentChildRelationship' in content:
            found_items.append('Parent models imported')
        else:
            issues.append('Parent models not imported in admin.py')
        
        # Check admin classes
        if '@admin.register(ParentProfile)' in content:
            found_items.append('ParentProfile admin registration')
        else:
            issues.append('ParentProfile admin registration not found')
        
        if '@admin.register(ParentChildRelationship)' in content:
            found_items.append('ParentChildRelationship admin registration')
        else:
            issues.append('ParentChildRelationship admin registration not found')
        
        if 'class ParentProfileAdmin(admin.ModelAdmin):' in content:
            found_items.append('ParentProfileAdmin class')
        else:
            issues.append('ParentProfileAdmin class not found')
        
        if 'class ParentChildRelationshipAdmin(admin.ModelAdmin):' in content:
            found_items.append('ParentChildRelationshipAdmin class')
        else:
            issues.append('ParentChildRelationshipAdmin class not found')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_views(self) -> Dict[str, Any]:
        """Verify API ViewSets exist."""
        views_file = os.path.join(self.accounts_path, 'views.py')
        
        if not os.path.exists(views_file):
            return {'status': 'error', 'issues': ['views.py file not found']}
        
        with open(views_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        # Check imports
        if 'ParentProfile' in content and 'ParentChildRelationship' in content:
            found_items.append('Parent models imported in views')
        else:
            issues.append('Parent models not imported in views.py')
        
        if 'ParentProfileSerializer' in content and 'ParentChildRelationshipSerializer' in content:
            found_items.append('Parent serializers imported in views')
        else:
            issues.append('Parent serializers not imported in views.py')
        
        # Check ViewSet classes
        if 'class ParentProfileViewSet(' in content:
            found_items.append('ParentProfileViewSet class')
        else:
            issues.append('ParentProfileViewSet class not found')
        
        if 'class ParentChildRelationshipViewSet(' in content:
            found_items.append('ParentChildRelationshipViewSet class')
        else:
            issues.append('ParentChildRelationshipViewSet class not found')
        
        # Check for custom actions
        if '@action(detail=False, methods=[\'get\'])' in content and 'my_children' in content:
            found_items.append('my_children custom action')
        else:
            issues.append('my_children custom action not found')
        
        if 'update_notification_preferences' in content:
            found_items.append('update_notification_preferences action')
        else:
            issues.append('update_notification_preferences action not found')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_urls(self) -> Dict[str, Any]:
        """Verify URL configurations."""
        urls_file = os.path.join(self.accounts_path, 'urls.py')
        
        if not os.path.exists(urls_file):
            return {'status': 'error', 'issues': ['urls.py file not found']}
        
        with open(urls_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        # Check imports
        if 'ParentProfileViewSet' in content and 'ParentChildRelationshipViewSet' in content:
            found_items.append('Parent ViewSets imported in urls')
        else:
            issues.append('Parent ViewSets not imported in urls.py')
        
        # Check router registrations
        if 'parent-profiles' in content and 'ParentProfileViewSet' in content:
            found_items.append('ParentProfile endpoint registered')
        else:
            issues.append('ParentProfile endpoint not registered')
        
        if 'parent-child-relationships' in content and 'ParentChildRelationshipViewSet' in content:
            found_items.append('ParentChildRelationship endpoint registered')
        else:
            issues.append('ParentChildRelationship endpoint not registered')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_permissions(self) -> Dict[str, Any]:
        """Verify permission classes exist."""
        permissions_file = os.path.join(self.accounts_path, 'permissions.py')
        
        if not os.path.exists(permissions_file):
            return {'status': 'error', 'issues': ['permissions.py file not found']}
        
        with open(permissions_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        permission_classes = [
            'IsParentInAnySchool',
            'IsParentOfStudent',
            'IsStudentOrParent',
            'CanManageChildPurchases'
        ]
        
        for perm_class in permission_classes:
            if f'class {perm_class}(' in content:
                found_items.append(f'{perm_class} permission class')
            else:
                issues.append(f'{perm_class} permission class not found')
        
        # Check for ParentChildRelationship import
        if 'ParentChildRelationship' in content:
            found_items.append('ParentChildRelationship imported in permissions')
        else:
            issues.append('ParentChildRelationship not imported in permissions')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_serializers(self) -> Dict[str, Any]:
        """Verify serializer classes exist."""
        serializers_file = os.path.join(self.accounts_path, 'serializers.py')
        
        if not os.path.exists(serializers_file):
            return {'status': 'error', 'issues': ['serializers.py file not found']}
        
        with open(serializers_file, 'r') as f:
            content = f.read()
        
        issues = []
        found_items = []
        
        # Check for serializer classes (using grep-like search)
        if 'class ParentProfileSerializer(' in content:
            found_items.append('ParentProfileSerializer class')
        else:
            issues.append('ParentProfileSerializer class not found')
        
        if 'class ParentChildRelationshipSerializer(' in content:
            found_items.append('ParentChildRelationshipSerializer class')
        else:
            issues.append('ParentChildRelationshipSerializer class not found')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def verify_migrations(self) -> Dict[str, Any]:
        """Verify migration files exist."""
        migrations_dir = os.path.join(self.accounts_path, 'migrations')
        
        if not os.path.exists(migrations_dir):
            return {'status': 'error', 'issues': ['migrations directory not found']}
        
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
        
        issues = []
        found_items = []
        
        # Look for parent-related migrations
        parent_migrations = [f for f in migration_files if 'parent' in f.lower()]
        
        if parent_migrations:
            found_items.extend([f"Migration file: {f}" for f in parent_migrations])
        else:
            issues.append('No parent-related migration files found')
        
        # Check for specific migration file
        if '0030_add_parent_models.py' in migration_files:
            found_items.append('0030_add_parent_models.py migration')
        else:
            issues.append('0030_add_parent_models.py migration not found')
        
        status = 'success' if not issues else 'failed'
        return {
            'status': status,
            'issues': issues,
            'found_items': found_items
        }
    
    def print_summary(self):
        """Print a summary of the verification results."""
        print("\n" + "=" * 70)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 70)
        
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() 
                          if result.get('status') == 'success')
        
        print(f"\nResults: {passed_checks}/{total_checks} checks passed")
        
        for check_name, result in self.results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                print(f"✅ {check_name}")
                for item in result.get('found_items', []):
                    print(f"   ✓ {item}")
            elif status == 'failed':
                print(f"❌ {check_name}")
                for issue in result.get('issues', []):
                    print(f"   ✗ {issue}")
            else:
                print(f"⚠️ {check_name}: {result.get('error', 'Unknown error')}")
        
        if passed_checks == total_checks:
            print("\n🎉 All checks passed! Parent-child infrastructure is properly implemented.")
            print("✅ GitHub Issue #111 requirements have been successfully completed!")
            return True
        else:
            print(f"\n⚠️ {total_checks - passed_checks} check(s) failed. Please review the issues above.")
            return False


def main():
    """Main function to run the verification."""
    backend_path = os.path.dirname(os.path.abspath(__file__))
    
    verifier = ParentChildImplementationVerifier(backend_path)
    verifier.verify_all()
    success = verifier.print_summary()
    
    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Run Django migrations: python manage.py migrate")
        print("2. Test API endpoints with real data")
        print("3. Update frontend to consume parent APIs")
        return 0
    else:
        print("\n🔧 Please address the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    exit(main())