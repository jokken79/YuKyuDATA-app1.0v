
with open('d:\\YuKyuDATA-app1.0v\\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(120, 135):
        if i < len(lines):
            line = lines[i]
            prefix = "TAB" if "\t" in line else "SPACE"
            print(f"{i+1}: [{prefix}] {repr(line)}")
