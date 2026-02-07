
import re

def fix_file(filepath):
    print(f"Fixing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix RateLimiter indentation
        if "class RateLimiter" in line:
            print(f"Found RateLimiter at line {i+1}: {repr(line)}")
            if line.startswith(" ") or line.startswith("\t"):
                print("  Fixing indentation...")
                line = line.lstrip()
        
        # Check for weird indentation in imports around line 100-140
        if 100 < i < 150:
            if line.strip().startswith("from models.") or line.strip().startswith("import "):
                 if line.startswith(" ") or line.startswith("\t"):
                     print(f"Fixing import at line {i+1}: {repr(line)}")
                     line = line.lstrip()
        
        fixed_lines.append(line)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    print("Done.")

if __name__ == "__main__":
    fix_file("d:\\YuKyuDATA-app1.0v\\main.py")
