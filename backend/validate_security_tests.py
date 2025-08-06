#!/usr/bin/env python3
"""
Validation script for security test files.
Checks imports and basic structure without running Django.
"""

import ast
import sys
from pathlib import Path

def check_file_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def check_imports(file_path):
    """Check if imports in the file look correct."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return True, imports
    except Exception as e:
        return False, str(e)

def validate_test_files():
    """Validate all security test files."""
    test_files = [
        'accounts/tests/test_multi_tenant_security.py',
        'accounts/tests/test_authentication_boundaries.py', 
        'accounts/tests/test_permission_escalation.py'
    ]
    
    results = []
    
    for test_file in test_files:
        file_path = Path(test_file)
        print(f"\n=== Validating {test_file} ===")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            results.append((test_file, False, "File not found"))
            continue
            
        # Check syntax
        syntax_ok, syntax_error = check_file_syntax(file_path)
        if not syntax_ok:
            print(f"❌ Syntax error: {syntax_error}")
            results.append((test_file, False, f"Syntax error: {syntax_error}"))
            continue
            
        print("✅ Syntax is valid")
        
        # Check imports
        imports_ok, imports = check_imports(file_path)
        if not imports_ok:
            print(f"❌ Import error: {imports}")
            results.append((test_file, False, f"Import error: {imports}"))
            continue
            
        print(f"✅ Imports detected: {len(imports)}")
        for imp in imports[:5]:  # Show first 5 imports
            print(f"  - {imp}")
        if len(imports) > 5:
            print(f"  ... and {len(imports) - 5} more")
            
        results.append((test_file, True, "Valid"))
    
    # Summary
    print("\n=== SUMMARY ===")
    valid_count = sum(1 for _, valid, _ in results if valid)
    total_count = len(results)
    
    print(f"Valid files: {valid_count}/{total_count}")
    
    for test_file, valid, message in results:
        status = "✅" if valid else "❌"
        print(f"{status} {test_file}: {message}")
    
    return valid_count == total_count

if __name__ == "__main__":
    success = validate_test_files()
    sys.exit(0 if success else 1)