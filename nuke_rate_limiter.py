
import os

filepath = "d:\\YuKyuDATA-app1.0v\\main.py"

print(f"Reading {filepath}...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n')

# 1. Restore imports (uncomment)
content = content.replace("# from utils.audit_logger", "from utils.audit_logger")
content = content.replace("# from models.leave_request", "from models.leave_request")
content = content.replace("# from models.vacation", "from models.vacation")
content = content.replace("# from models.employee", "from models.employee")
content = content.replace("# from models.common", "from models.common")

# 2. Find RateLimiter block start
start_marker = "class RateLimiter:"
start_idx = content.find(start_marker)
if start_idx == -1:
    print("Error: RateLimiter start not found!")
    # Maybe it has indentation or chars? Try searching for the substring aggressively
    # But I can search for header
    header = "# RATE LIMITER"
    header_idx = content.find(header)
    if header_idx != -1:
         # Found header, look forward
         start_idx = content.find("class RateLimiter", header_idx)
    
    if start_idx == -1:
         print("FATAL: Cannot find RateLimiter class definition.")
         exit(1)

# 3. Find RateLimiter block end
# It ends after rate_limiter = RateLimiter(...)
end_marker = "rate_limiter = RateLimiter(max_requests=100, window_seconds=60)"
end_idx = content.find(end_marker, start_idx)

if end_idx == -1:
    print("Error: RateLimiter instantiation not found!")
    exit(1)

# Move end index past the marker
end_idx += len(end_marker)

print(f"Removing RateLimiter block from char {start_idx} to {end_idx}...")

# 4. Construct new content
# Insert import statement instead
replacement = "from utils.rate_limiter import RateLimiter, rate_limiter"

new_content = content[:start_idx] + replacement + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("File updated successfully.")
