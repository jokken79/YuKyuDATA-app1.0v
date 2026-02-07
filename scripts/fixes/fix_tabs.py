
# Script to replace tabs with spaces in main.py
filepath = "d:\\YuKyuDATA-app1.0v\\main.py"

print(f"Sanitizing {filepath}...")
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if tabs exist
tab_count = content.count('\t')
print(f"Found {tab_count} tabs.")

if tab_count > 0:
    new_content = content.replace('\t', '    ')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Tabs replaced with spaces.")
else:
    print("No tabs found. Checking for mixed indentation issues...")
    # Just rewrite line by line normalizing
    lines = content.splitlines()
    normalized = []
    for line in lines:
        normalized.append(line.rstrip()) # Remove trailing spaces
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(normalized) + '\n')
    print("Normalized line endings and trailing spaces.")
