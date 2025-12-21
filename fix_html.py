import re

def fix_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Function to merge classes in a tag
    def merge_classes(match):
        tag_content = match.group(1)

        # Find all class attributes
        class_matches = re.findall(r'class="([^"]*)"', tag_content)

        if len(class_matches) > 1:
            # Merge all classes
            all_classes = []
            for cls_str in class_matches:
                all_classes.extend(cls_str.split())

            # Remove duplicates while preserving order
            unique_classes = []
            for cls in all_classes:
                if cls not in unique_classes:
                    unique_classes.append(cls)

            # Reduce spacing classes
            final_classes = []
            for cls in unique_classes:
                if cls == 'mb-2xl':
                    final_classes.append('mb-lg') # Reduce margin
                elif cls == 'p-xl':
                    final_classes.append('p-lg') # Reduce padding
                elif cls == 'p-lg' and 'glass-panel' in unique_classes:
                     final_classes.append('p-md') # Further reduce padding for panels
                else:
                    final_classes.append(cls)

            merged_class_str = ' '.join(final_classes)

            # Remove existing class attributes
            new_tag_content = re.sub(r'\s*class="[^"]*"', '', tag_content)

            # Add merged class attribute at the beginning
            # We assume the tag starts with the tag name, e.g. <div ...
            # split by first space
            parts = new_tag_content.split(' ', 1)
            if len(parts) > 1:
                return f'<{parts[0]} class="{merged_class_str}" {parts[1]}>'
            else:
                return f'<{parts[0]} class="{merged_class_str}">'
        else:
            return match.group(0) # No change if 0 or 1 class attribute

    # Regex to find tags. This is a simple regex and might not cover all edge cases but works for standard HTML
    # We look for <tag ... > where ... contains class="..."
    # Note: parsing HTML with regex is generally bad, but for this specific "double class" issue it's efficient enough if we are careful.

    # Better approach: Find strings that look like `class="..." ... class="..."` inside a tag
    # But since the previous grep showed they are distinct attributes: `class="A" class="B"`.

    # Let's just iterate through the file line by line for safer replacement if the tags are on one line,
    # but often they are multi-line.

    # Let's use a regex that matches a tag opening.
    # <\w+\s+[^>]*>

    new_content = re.sub(r'<(\w+\s+[^>]*)>', merge_classes, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    fix_html('templates/index.html')
