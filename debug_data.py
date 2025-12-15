import database
import json

database.init_db()

# Get all employees
employees = database.get_employees()

print(f"Total employees: {len(employees)}")

# Check for any usage
total_used = sum(e['used'] for e in employees)
print(f"Total used days (sum): {total_used}")

# Check distribution
used_counts = [e['used'] for e in employees if e['used'] > 0]
print(f"Employees with usage > 0: {len(used_counts)}")

if len(used_counts) > 0:
    print(f"Max usage: {max(used_counts)}")
    print(f"Min usage (>0): {min(used_counts)}")

# Check factories
factories = {}
for e in employees:
    f = e.get('haken') or 'Unknown'
    if f not in factories:
        factories[f] = 0
    factories[f] += e['used']

print("\nFactory Usage:")
for f, usage in factories.items():
    if usage > 0:
        print(f"{f}: {usage}")
