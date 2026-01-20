
import os

target_block_start = '_excel_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="excel_parser")'
target_block_end = 'class RateLimiter:'

clean_block = """_excel_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="excel_parser")


# Import audit logger utilities
from utils.audit_logger import audit_action, log_audit_action, get_client_info


# Import Pydantic models
from models.leave_request import LeaveRequestCreate
from models.vacation import UsageDetailCreate, UsageDetailUpdate
from models.employee import EmployeeUpdate, BulkUpdateRequest, BulkUpdatePreview
from models.common import DateRangeQuery


# ============================================
# RATE LIMITER
# ============================================

class RateLimiter:"""

filepath = "d:\\YuKyuDATA-app1.0v\\main.py"

print(f"Reading {filepath}...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n')

# Find start
start_idx = content.find("_excel_executor = ThreadPoolExecutor")
if start_idx == -1:
    print("Error: Start block not found!")
    exit(1)

# Find end
end_idx = content.find("class RateLimiter:", start_idx)
if end_idx == -1:
    print("Error: End block not found!")
    exit(1)

# Include the end marker in replacements? 
# "class RateLimiter:" is in clean_block, so yes, we want to replace up to end of "class RateLimiter:"
end_idx += len("class RateLimiter:")

print(f"Replacing block from char {start_idx} to {end_idx}...")

old_content = content[start_idx:end_idx]
print(f"Old content length: {len(old_content)}")

new_content = content[:start_idx] + clean_block + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("File updated successfully.")
