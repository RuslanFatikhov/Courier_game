#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI точка входа для продакшен деплоя симулятора курьера.
Используется с Gunicorn или другими WSGI серверами.
"""

import os
from app import create_app

# Создаем приложение для продакшена
app = create_app('production')
application = app

if __name__ == "__main__":
    app.run()
