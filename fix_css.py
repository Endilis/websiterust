import re
import os

files = [
    "index_ua.html",
    "docs_en.html",
    "docs_ua.html",
    "setup_ua.html"
]

base_dir = r"d:\Rustinfo\website"

for filename in files:
    filepath = os.path.join(base_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найти начало <style> и конец </style>
        style_start = content.find('<style>')
        style_end = content.find('</style>') + len('</style>')
        
        if style_start != -1 and style_end != -1:
            # Удалить весь блок style
            before = content[:style_start]
            after = content[style_end:]
            
            # Вставить ссылку на CSS
            new_content = before + '<link rel="stylesheet" href="style.css">' + after
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✓ {filename} - удален CSS блок")
        else:
            print(f"⚠ {filename} - блок <style> не найден")
    
    except Exception as e:
        print(f"✗ {filename}: {e}")

print("\nГотово!")
