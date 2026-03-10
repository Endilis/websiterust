# 🎨 VIDEO THUMBNAIL - ИНСТРУКЦИЯ

## ✅ Создан файл: thumbnail.svg (1280x720px)

Файл открыт в браузере! 

## 📸 Как экспортировать в PNG:

### Способ 1: Скриншот браузера
1. Открой thumbnail.svg в Chrome
2. Нажми F12 (DevTools)
3. Ctrl+Shift+P → "Capture screenshot"
4. Сохрани как thumbnail.png

### Способ 2: Онлайн конвертер
1. Открой https://cloudconvert.com/svg-to-png
2. Загрузи thumbnail.svg
3. Установи размер: 1280x720px
4. Скачай PNG

### Способ 3: Inkscape (лучшее качество)
```powershell
# Установка
winget install Inkscape.Inkscape

# Конвертация
inkscape thumbnail.svg --export-type=png --export-width=1280 --export-height=720 --export-filename=thumbnail.png
```

### Способ 4: PowerShell + ImageMagick
```powershell
# Установка
winget install ImageMagick.ImageMagick

# Конвертация
magick convert -density 300 thumbnail.svg -resize 1280x720 thumbnail.png
```

## 🎨 ДИЗАЙН ВКЛЮЧАЕТ:

✅ Discord иконка слева (синий)
✅ Rust логотип справа (оранжевый)
✅ Стрелка по центру (градиент)
✅ Заголовок: "CONTROL RUST FROM DISCORD"
✅ Бейджи: "✓ FREE" + "⚡ 2 MIN SETUP"
✅ Брендинг RustInfo внизу
✅ Темный фон с градиентом
✅ Glow эффекты

## 📋 ИСПОЛЬЗОВАНИЕ:

- YouTube thumbnail
- Twitter/X карточка
- Discord embed preview
- Website og:image

## 🔄 ХОЧЕШЬ ИЗМЕНИТЬ?

Редактируй файл `thumbnail.svg` в:
- Figma (импорт SVG)
- Adobe Illustrator
- Inkscape (бесплатно)
- Или текстовом редакторе (это просто XML!)

---

Создано для RustInfo | 2026
