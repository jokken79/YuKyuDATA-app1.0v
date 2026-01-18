#!/usr/bin/env python3
"""
Validate v1 API Structure
Verifies that all endpoints are properly configured for v1
"""

import os
import re
from pathlib import Path
from collections import defaultdict

os.environ['JWT_SECRET_KEY'] = 'test-key-for-validation'

def count_endpoints_in_file(filepath):
    """Count @router.{method} decorators in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match @router.get, @router.post, etc.
        matches = re.findall(r'@router\.(get|post|put|delete|patch)', content)
        return len(matches)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0

def validate_imports_in_file(filepath):
    """Validate that imports are correctly adapted for v1"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Check for incorrect imports
        if 'from .responses import' in content:
            issues.append("Should use 'from ..responses import'")
        
        if 'from .dependencies import' in content:
            issues.append("Should use 'from ..dependencies import'")
        
        # Check prefix is correct
        if 'prefix="/api' in content:
            issues.append("Prefix should not contain '/api' (it's in the parent router)")
        
        return issues
    except Exception as e:
        return [f"Error reading file: {e}"]

def main():
    """Validate v1 structure"""
    routes_dir = Path(__file__).parent.parent / "routes"
    v0_dir = routes_dir
    v1_dir = routes_dir / "v1"
    
    print("=" * 60)
    print("API v1 STRUCTURE VALIDATION")
    print("=" * 60)
    
    # List of route files to check
    route_files = [
        "auth.py",
        "employees.py",
        "genzai.py",
        "ukeoi.py",
        "staff.py",
        "leave_requests.py",
        "yukyu.py",
        "compliance.py",
        "compliance_advanced.py",
        "fiscal.py",
        "analytics.py",
        "reports.py",
        "export.py",
        "calendar.py",
        "notifications.py",
        "system.py",
        "health.py",
        "github.py",
    ]
    
    total_v0_endpoints = 0
    total_v1_endpoints = 0
    issues = defaultdict(list)
    
    print("\nValidating route files...")
    print("-" * 60)
    
    for route_file in route_files:
        v0_path = v0_dir / route_file
        v1_path = v1_dir / route_file
        
        if not v0_path.exists():
            print(f"✗ {route_file}: v0 file not found")
            continue
        
        if not v1_path.exists():
            print(f"✗ {route_file}: v1 file not found")
            continue
        
        v0_count = count_endpoints_in_file(v0_path)
        v1_count = count_endpoints_in_file(v1_path)
        
        total_v0_endpoints += v0_count
        total_v1_endpoints += v1_count
        
        if v0_count != v1_count:
            issues[route_file].append(
                f"Endpoint count mismatch: v0={v0_count}, v1={v1_count}"
            )
        
        # Check imports in v1 file
        import_issues = validate_imports_in_file(v1_path)
        if import_issues:
            issues[route_file].extend(import_issues)
        
        status = "✓" if v0_count == v1_count and not import_issues else "⚠"
        print(f"{status} {route_file:30s} | v0: {v0_count:3d} | v1: {v1_count:3d}")
    
    # Print summary
    print("-" * 60)
    print(f"\nSUMMARY:")
    print(f"  Total v0 endpoints: {total_v0_endpoints}")
    print(f"  Total v1 endpoints: {total_v1_endpoints}")
    print(f"  Expected (156):     156")
    
    if total_v1_endpoints == 156:
        print(f"\n✓ All 156 endpoints successfully migrated to v1!")
    else:
        print(f"\n✗ Endpoint count mismatch: expected 156, got {total_v1_endpoints}")
    
    # Print issues if any
    if issues:
        print(f"\nISSUES FOUND:")
        for file, file_issues in issues.items():
            print(f"  {file}:")
            for issue in file_issues:
                print(f"    - {issue}")
    else:
        print(f"\n✓ No structural issues found!")
    
    # Test router imports
    print("\n" + "=" * 60)
    print("Testing router imports...")
    print("-" * 60)
    
    try:
        from routes.v1 import router_v1
        print(f"✓ v1 router imports successfully")
        print(f"✓ v1 router has {len(router_v1.routes)} registered routes")
    except Exception as e:
        print(f"✗ Error importing v1 router: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
