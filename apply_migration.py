#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPRECATED: используйте Flask-Migrate/Alembic.
Этот скрипт оставлен для совместимости со старой схемой.
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def apply_migration():
    """Применить миграцию для добавления city_id"""
    print("⚠️  apply_migration.py deprecated. Use: flask db upgrade")
    return False

    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Применение миграции добавления поддержки городов...")
            
            # Проверяем, существует ли уже колонка city_id в users
            result = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'city_id' not in columns:
                print("➕ Добавление city_id в таблицу users...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN city_id VARCHAR(50) DEFAULT 'almaty'"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_city ON users(city_id)"))
            else:
                print("✅ Колонка city_id уже существует в users")
            
            # Проверяем orders
            result = db.session.execute(text("PRAGMA table_info(orders)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'city_id' not in columns:
                print("➕ Добавление city_id в таблицу orders...")
                db.session.execute(text("ALTER TABLE orders ADD COLUMN city_id VARCHAR(50) DEFAULT 'almaty'"))
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_city ON orders(city_id)"))
            else:
                print("✅ Колонка city_id уже существует в orders")
            
            db.session.commit()
            print("✅ Миграция успешно применена!")
            
        except Exception as e:
            print(f"❌ Ошибка при применении миграции: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
