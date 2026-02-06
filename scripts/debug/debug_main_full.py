
with open('d:\\YuKyuDATA-app1.0v\\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    with open('debug_log_full.txt', 'w', encoding='utf-8') as out:
        for i in range(120, 135):
            if i < len(lines):
                 out.write(f"{i+1}: {repr(lines[i])}\n")
