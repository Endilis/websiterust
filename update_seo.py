#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO Optimization Script для RustInfo Website"""

def update_index_ru():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>RustInfo — Explore • Build • Survive</title>\n  <meta name="description" content="RustInfo: мониторинг Rust+ и серверов, быстрый статус, новости и инструменты." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>RustInfo — Discord Бот для Мониторинга Rust+ Серверов | Статус Онлайн</title>
  <meta name="description" content="🎮 RustInfo - Discord бот для мониторинга Rust+ серверов в реальном времени. Проверяй статус, онлайн игроков, управляй умными устройствами!" />
  <meta name="keywords" content="rust, rust+, rust plus, rustinfo, discord bot, rust server monitoring, rust companion, facepunch, мониторинг rust серверов" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="RustInfo — Discord Бот для Rust+" />
  <meta property="og:description" content="Мониторинг Rust+ серверов в реальном времени" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/index_en.html" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/index_ua.html" />'''
    
    content = content.replace(old, new)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ index.html (RU)')

def update_index_en():
    with open('index_en.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>RustInfo — Explore • Build • Survive</title>\n  <meta name="description" content="RustInfo: Rust+ and server monitoring, quick status checks, news and tools." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>RustInfo — Discord Bot for Rust+ Server Monitoring | Live Status</title>
  <meta name="description" content="🎮 RustInfo - Discord bot for real-time Rust+ server monitoring. Check status, online players, control smart devices. Trusted by 1000+ servers!" />
  <meta name="keywords" content="rust, rust+, rust plus, rustinfo, discord bot, rust server monitoring, rust companion, facepunch, rust game bot" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/index_en.html" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="RustInfo — Discord Bot for Rust+" />
  <meta property="og:description" content="Real-time Rust+ server monitoring via Discord" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/index_en.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/index_ua.html" />'''
    
    content = content.replace(old, new)
    with open('index_en.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ index_en.html (EN)')

def update_index_ua():
    with open('index_ua.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>RustInfo — Explore • Build • Survive</title>\n  <meta name="description" content="RustInfo: моніторинг Rust+ та серверів, швидкий статус, новини та інструменти." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>RustInfo — Discord Бот для Моніторингу Rust+ Серверів | Статус Онлайн</title>
  <meta name="description" content="🎮 RustInfo - Discord бот для моніторингу Rust+ серверів у реальному часі. Перевіряй статус, онлайн гравців, керуй розумними пристроями!" />
  <meta name="keywords" content="rust, rust+, rust plus, rustinfo, discord bot, rust server monitoring, rust companion, facepunch, моніторинг rust серверів" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/index_ua.html" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="RustInfo — Discord Бот для Rust+" />
  <meta property="og:description" content="Моніторинг Rust+ серверів у реальному часі" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/index_ua.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/index_en.html" />'''
    
    content = content.replace(old, new)
    with open('index_ua.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ index_ua.html (UA)')

def update_docs_ru():
    with open('docs.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Документация — RustInfo</title>\n  <meta name="description" content="Полное руководство по использованию RustInfo бота для мониторинга Rust серверов и управления через Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>Документация RustInfo — Полное Руководство по Discord Боту для Rust+</title>
  <meta name="description" content="📚 Полная документация RustInfo бота: команды, настройка мониторинга Rust+ серверов, управление умными устройствами, FAQ. Пошаговые инструкции с примерами." />
  <meta name="keywords" content="rustinfo документация, rust bot guide, rust+ commands, discord bot documentation, rust server monitoring guide" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/docs.html" />
  <meta property="og:title" content="Документация RustInfo — Полное Руководство" />
  <meta property="og:description" content="Полная документация по использованию RustInfo бота" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/docs.html" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/docs_en.html" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/docs_ua.html" />'''
    
    content = content.replace(old, new)
    with open('docs.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ docs.html (RU)')

def update_docs_en():
    with open('docs_en.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Documentation — RustInfo</title>\n  <meta name="description" content="Complete guide on using the RustInfo bot for Rust server monitoring and management via Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>RustInfo Documentation — Complete Guide for Discord Rust+ Bot</title>
  <meta name="description" content="📚 Complete RustInfo bot documentation: commands, Rust+ server monitoring setup, smart device control, FAQ. Step-by-step guides with examples." />
  <meta name="keywords" content="rustinfo documentation, rust bot guide, rust+ commands, discord bot docs, rust server monitoring guide" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/docs_en.html" />
  <meta property="og:title" content="RustInfo Documentation — Complete Guide" />
  <meta property="og:description" content="Complete guide for using RustInfo bot" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/docs_en.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/docs.html" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/docs_ua.html" />'''
    
    content = content.replace(old, new)
    with open('docs_en.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ docs_en.html (EN)')

def update_docs_ua():
    with open('docs_ua.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Документація — RustInfo</title>\n  <meta name="description" content="Повний посібник з використання RustInfo бота для моніторингу Rust серверів та управління через Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>Документація RustInfo — Повний Посібник по Discord Боту для Rust+</title>
  <meta name="description" content="📚 Повна документація RustInfo бота: команди, налаштування моніторингу Rust+ серверів, керування розумними пристроями, FAQ. Покрокові інструкції." />
  <meta name="keywords" content="rustinfo документація, rust bot посібник, rust+ команди, discord bot документація, rust server monitoring guide" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/docs_ua.html" />
  <meta property="og:title" content="Документація RustInfo — Повний Посібник" />
  <meta property="og:description" content="Повна документація по використанню RustInfo бота" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/docs_ua.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/docs.html" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/docs_en.html" />'''
    
    content = content.replace(old, new)
    with open('docs_ua.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ docs_ua.html (UA)')

def update_setup_ru():
    with open('setup.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Подключение — RustInfo</title>\n  <meta name="description" content="Инструкция по подключению RustInfo бота к вашему Discord серверу и настройке Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>Подключение RustInfo — Быстрая Настройка Discord Бота для Rust+</title>
  <meta name="description" content="⚙️ Подключите RustInfo бот к Discord за 2 минуты! Пошаговая инструкция по настройке мониторинга Rust+ серверов. Простая интеграция с Rust Companion." />
  <meta name="keywords" content="rustinfo setup, rust bot setup, discord bot installation, rust+ pairing, rust companion setup" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/setup.html" />
  <meta property="og:title" content="Подключение RustInfo — Быстрая Настройка" />
  <meta property="og:description" content="Подключите RustInfo бот за 2 минуты" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/setup.html" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/setup_en.html" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/setup_ua.html" />'''
    
    content = content.replace(old, new)
    with open('setup.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ setup.html (RU)')

def update_setup_en():
    with open('setup_en.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Setup — RustInfo</title>\n  <meta name="description" content="Instructions for connecting the RustInfo bot to your Discord server and setting up Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>RustInfo Setup — Quick Discord Bot Configuration for Rust+</title>
  <meta name="description" content="⚙️ Connect RustInfo bot to Discord in 2 minutes! Step-by-step guide for Rust+ server monitoring setup. Easy integration with Rust Companion." />
  <meta name="keywords" content="rustinfo setup, rust bot setup, discord bot installation, rust+ pairing, rust companion setup" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/setup_en.html" />
  <meta property="og:title" content="RustInfo Setup — Quick Configuration" />
  <meta property="og:description" content="Connect RustInfo bot in 2 minutes" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/setup_en.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/setup.html" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/setup_ua.html" />'''
    
    content = content.replace(old, new)
    with open('setup_en.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ setup_en.html (EN)')

def update_setup_ua():
    with open('setup_ua.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    old = '  <title>Підключення — RustInfo</title>\n  <meta name="description" content="Інструкція по підключенню RustInfo бота до вашого Discord сервера та налаштуванню Rust+." />'
    new = '''  <!-- SEO Meta Tags -->
  <title>Підключення RustInfo — Швидке Налаштування Discord Бота для Rust+</title>
  <meta name="description" content="⚙️ Підключіть RustInfo бот до Discord за 2 хвилини! Покрокова інструкція з налаштування моніторингу Rust+ серверів. Проста інтеграція." />
  <meta name="keywords" content="rustinfo налаштування, rust bot setup, discord bot установка, rust+ pairing, rust companion setup" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="https://rustinfo.online/setup_ua.html" />
  <meta property="og:title" content="Підключення RustInfo — Швидке Налаштування" />
  <meta property="og:description" content="Підключіть RustInfo бот за 2 хвилини" />
  <link rel="alternate" hreflang="uk" href="https://rustinfo.online/setup_ua.html" />
  <link rel="alternate" hreflang="ru" href="https://rustinfo.online/setup.html" />
  <link rel="alternate" hreflang="en" href="https://rustinfo.online/setup_en.html" />'''
    
    content = content.replace(old, new)
    with open('setup_ua.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ setup_ua.html (UA)')

if __name__ == '__main__':
    print('🚀 SEO Optimization\n')
    update_index_ru()
    update_index_en()
    update_index_ua()
    update_docs_ru()
    update_docs_en()
    update_docs_ua()
    update_setup_ru()
    update_setup_en()
    update_setup_ua()
    print('\n✨ Готово! 9 файлов обновлено')
