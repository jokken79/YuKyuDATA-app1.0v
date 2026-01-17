#!/usr/bin/env python3
"""
Fix v1 route prefixes
Changes all prefixes from /api/* to /* (since v1 router already has /api/v1 prefix)
"""

import re
from pathlib import Path

V1_DIR = Path(__file__).parent.parent / "routes" / "v1"

# Mapping of old prefixes to new prefixes
PREFIX_REPLACEMENTS = {
    'prefix="/api/auth"': 'prefix="/auth"',
    'prefix="/api/yukyu"': 'prefix="/yukyu"',
    'prefix="/api/compliance"': 'prefix="/compliance"',
    'prefix="/api/fiscal"': 'prefix="/fiscal"',
    'prefix="/api/reports"': 'prefix="/reports"',
    'prefix="/api/export"': 'prefix="/export"',
    'prefix="/api/calendar"': 'prefix="/calendar"',
    'prefix="/api/notifications"': 'prefix="/notifications"',
    'prefix="/api/github"': 'prefix="/github"',
    'prefix="/api"': 'prefix=""',  # For root prefixes
}

def fix_file(filepath):
    """Fix prefixes in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply all replacements
    for old, new in PREFIX_REPLACEMENTS.items():
        content = content.replace(old, new)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all v1 prefixes"""
    print("Fixing v1 route prefixes...")
    print("-" * 60)
    
    fixed_count = 0
    
    for py_file in sorted(V1_DIR.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        
        if fix_file(py_file):
            print(f"✓ Fixed {py_file.name}")
            fixed_count += 1
        else:
            print(f"✓ {py_file.name} (already correct)")
    
    print("-" * 60)
    print(f"Total files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
