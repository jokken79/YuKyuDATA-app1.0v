#!/usr/bin/env python3
"""
Script to create v1 route files from v0 routes
Copies all route files to routes/v1/ and adapts prefixes
"""

import os
import shutil
from pathlib import Path

ROUTES_DIR = Path(__file__).parent.parent / "routes"
V1_DIR = ROUTES_DIR / "v1"

# Route files to copy (excluding utilities and responses)
ROUTE_FILES = [
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

def adapt_route_file(content: str, filename: str) -> str:
    """
    Adapt a route file for v1.
    Changes:
    - Change prefix from '/api' to ''
    - Update imports if necessary
    """
    # Replace /api prefix with empty string (already under /api/v1)
    content = content.replace('prefix="/api"', 'prefix=""')
    content = content.replace('prefix = "/api"', 'prefix = ""')
    
    # Make sure imports from routes work
    # If it imports from .responses, change to ..responses
    content = content.replace('from .responses import', 'from ..responses import')
    content = content.replace('from .dependencies import', 'from ..dependencies import')
    
    return content

def main():
    """Create v1 route files"""
    print(f"Creating v1 routes in {V1_DIR}")
    
    if not V1_DIR.exists():
        V1_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {V1_DIR}")
    
    for route_file in ROUTE_FILES:
        src = ROUTES_DIR / route_file
        dst = V1_DIR / route_file
        
        if not src.exists():
            print(f"⚠ Source file not found: {src}")
            continue
        
        # Read source file
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adapt content for v1
        adapted = adapt_route_file(content, route_file)
        
        # Write to v1
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(adapted)
        
        print(f"✓ Copied and adapted: {route_file}")
    
    print(f"\n✓ All v1 routes created successfully!")
    print(f"Total files: {len(ROUTE_FILES)}")

if __name__ == "__main__":
    main()
