import re

# Список всех HTML файлов
files = [
    r"d:\Rustinfo\website\index.html",
    r"d:\Rustinfo\website\index_en.html",
    r"d:\Rustinfo\website\index_ua.html",
    r"d:\Rustinfo\website\docs.html",
    r"d:\Rustinfo\website\docs_en.html",
    r"d:\Rustinfo\website\docs_ua.html",
    r"d:\Rustinfo\website\setup.html",
    r"d:\Rustinfo\website\setup_en.html",
    r"d:\Rustinfo\website\setup_ua.html",
    r"d:\Rustinfo\website\binds.html"
]

for file_path in files:
    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем блок <style>...</style> на <link rel="stylesheet" href="style.css">
        # Используем регулярное выражение для удаления всего блока style
        pattern = r'<style>.*?</style>'
        replacement = '<link rel="stylesheet" href="style.css">'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ {file_path.split('\\')[-1]}")
    except Exception as e:
        print(f"✗ {file_path.split('\\')[-1]}: {e}")

print("\nЗамена завершена для всех 10 файлов!")
