#!/bin/bash
# -*- coding: utf-8 -*-
# Скрипт автоматической очистки проекта перед деплоем

echo "🧹 Начинаем очистку проекта..."

# Удаляем Python кэш
echo "Удаляем __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Удаляем скомпилированные файлы Python
echo "Удаляем .pyc и .pyo файлы..."
find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

# Удаляем бэкап файлы
echo "Удаляем бэкапы..."
find . -type f \( -name "*.bak" -o -name "*.backup" -o -name "*.backup2" -o -name "*.backup3" \) -delete

# Удаляем тестовые БД
echo "Удаляем тестовые базы данных..."
rm -f *.db *.sqlite *.sqlite3
rm -f app/*.db

# Удаляем логи
echo "Удаляем логи..."
rm -f *.log
find logs/ -type f -name "*.log" -delete 2>/dev/null

# Удаляем временные файлы macOS
echo "Удаляем .DS_Store..."
find . -name ".DS_Store" -delete

# Удаляем временные файлы редакторов
echo "Удаляем временные файлы..."
find . -type f \( -name "*~" -o -name "*.swp" -o -name "*.swo" \) -delete

# Удаляем тестовые артефакты
echo "Удаляем тестовые артефакты..."
rm -rf .pytest_cache/ htmlcov/ .coverage

echo ""
echo "✅ Очистка завершена!"
echo ""
echo "📊 Размер проекта после очистки:"
du -sh .
echo ""
echo "📁 Количество файлов:"
find . -type f -not -path "./.git/*" | wc -l
