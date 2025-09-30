# 🚴 Courier Simulator IRL

Мобильная веб-игра симулятора курьера, работающая в реальном мире с GPS-навигацией.

## 🎯 Особенности

- 🗺️ **Real-time GPS**: Реальное отслеживание позиции игрока на карте
- 📦 **Динамические заказы**: Случайная генерация заказов от ресторанов к зданиям
- 💰 **Экономическая система**: Выплаты, бонусы за своевременность, баланс игрока
- ⚡ **WebSocket**: Real-time коммуникация для поиска заказов и обновлений
- 🎮 **Геймификация**: Таймеры доставки, радиусы зон, статистика игрока

## 🛠️ Технологический стек

### Backend
- **Flask** - веб-фреймворк
- **Flask-SocketIO** - WebSocket для real-time
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL / SQLite** - база данных

### Frontend
- **Vanilla JavaScript** - без фреймворков
- **Mapbox GL JS** - интерактивные карты
- **Socket.IO Client** - WebSocket клиент
- **Geolocation API** - доступ к GPS

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd courier-simulator
```

### 2. Создание виртуального окружения

```bash
# Создаем виртуальное окружение
python -m venv venv

# Активируем (Linux/Mac)
source venv/bin/activate

# Активируем (Windows)
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

```bash
# Копируем пример файла
cp .env.example .env

# Редактируем .env и заполняем:
# - SECRET_KEY (генерируем случайный)
# - MAPBOX_ACCESS_TOKEN (получаем на mapbox.com)
# - DATABASE_URL (опционально для PostgreSQL)
```

### 5. Инициализация базы данных

```bash
# Flask автоматически создаст таблицы при первом запуске
# Или можно вручную:
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 6. Проверка здоровья системы

```bash
python scripts/healthcheck.py
```

## 🚀 Запуск

### Development режим

```bash
# Запуск Flask сервера с автоперезагрузкой
python run.py
```

Приложение будет доступно по адресу: `http://localhost:5000`

### Production режим

```bash
# Используйте gunicorn для production
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 run:app
```

## 📁 Структура проекта

```
courier-simulator/
├── app/                        # Основное Flask приложение
│   ├── __init__.py            # Factory function
│   ├── config.py              # Конфигурация
│   ├── routes.py              # Web routes (login, game)
│   ├── api/                   # API endpoints
│   │   ├── auth.py           # Авторизация
│   │   ├── player.py         # Игровые действия
│   │   └── admin.py          # Админка
│   ├── models/                # Модели базы данных
│   │   ├── user.py           # Пользователи
│   │   ├── order.py          # Заказы
│   │   └── report.py         # Жалобы
│   ├── socketio_handlers/     # WebSocket обработчики
│   │   └── game_events.py    # Игровые события
│   └── utils/                 # Вспомогательные функции
│       ├── gps_helper.py     # GPS расчеты
│       ├── economy.py        # Экономика игры
│       ├── game_helper.py    # Игровая логика
│       ├── restaurant_helper.py  # Работа с ресторанами
│       └── building_helper.py    # Работа со зданиями
├── data/                      # Данные GeoJSON
│   ├── restaurants.geojson   # Рестораны
│   └── buildings.geojson     # Здания для доставки
├── static/                    # Статические файлы
│   ├── css/                  # Стили
│   ├── js/                   # JavaScript
│   │   ├── geolocation.js   # Менеджер GPS
│   │   ├── game.js          # Главный файл
│   │   └── modules/         # Модули игры
│   └── img/                  # Изображения/иконки
├── templates/                 # HTML шаблоны
│   ├── base.html            # Базовый шаблон
│   ├── login.html           # Страница входа
│   └── game.html            # Игровой экран
├── scripts/                   # Утилитарные скрипты
│   └── healthcheck.py       # Проверка здоровья
├── .env.example              # Пример конфигурации
├── requirements.txt          # Python зависимости
├── run.py                    # Точка входа
└── README.md                 # Этот файл
```

## 🎮 Игровой процесс

### 1. Начало смены

1. Откройте приложение в браузере
2. Разрешите доступ к GPS
3. Нажмите "Начать смену"

### 2. Получение заказа

1. Нажмите "Ищем заказы"
2. Подождите 5-15 секунд
3. Появится модалка с деталями заказа
4. Нажмите "Взять заказ" или откажитесь

### 3. Забор заказа (Pickup)

1. Идите к ресторану (зеленый маркер на карте)
2. Когда войдете в радиус 30м, кнопка станет активной
3. Нажмите "Забрать заказ"
4. Запустится таймер доставки

### 4. Доставка заказа (Dropoff)

1. Идите к адресу клиента (красный маркер)
2. Войдите в радиус 30м от здания
3. Нажмите "Доставить заказ"
4. Получите выплату и бонус (если успели вовремя)

### 5. Завершение смены

1. Нажмите "Завершить смену" когда закончите играть
2. Активные заказы будут автоматически отменены

## 💰 Экономическая система

### Формула выплаты

```
Payout = Base + Pickup + Dropoff + (Distance × Rate) + OnTimeBonus
```

**Параметры по умолчанию:**
- Base Payment: $1.50
- Pickup Fee: $0.50
- Dropoff Fee: $0.50
- Distance Rate: $0.80/км
- OnTime Bonus: $1.00

### Таймер доставки

```
Timer = (Distance / 5 км/ч) × 60 + 5 минут
```

Если доставка занимает больше времени чем таймер - бонус не начисляется.
Если больше 2× таймера - заказ автоматически отменяется.

## 🔧 API Endpoints

### Авторизация (`/api/auth`)

- `POST /guest_login` - Гостевой вход
- `POST /google_login` - Вход через Google
- `POST /verify_session` - Проверка сессии
- `POST /logout` - Выход

### Игрок (`/api`)

- `POST /start_shift` - Начать смену
- `POST /stop_shift` - Завершить смену
- `GET /order/new` - Получить новый заказ
- `POST /order/accept` - Принять заказ
- `POST /order/pickup` - Забрать заказ
- `POST /order/deliver` - Доставить заказ
- `POST /order/cancel` - Отменить заказ
- `POST /position` - Обновить позицию
- `GET /status` - Статус игрока
- `GET /config` - Игровая конфигурация

### Админка (`/api/admin`)

- `GET /users` - Список пользователей
- `GET /users/<id>` - Детали пользователя
- `GET /orders` - Список заказов
- `GET /reports` - Список жалоб
- `GET /analytics/overview` - Общая аналитика
- `POST /config` - Обновить конфигурацию

## 🐛 Отладка

### Включение debug режима

```bash
# В .env файле
FLASK_DEBUG=True
```

### Просмотр логов

```python
# В коде добавьте
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Очистка localStorage

Откройте в браузере: `http://localhost:5000/static/clear.html`

### Проверка состояния системы

```bash
python scripts/healthcheck.py
```

## 📊 База данных

### SQLite (по умолчанию для dev)

```bash
# База создается автоматически в app/courier_dev.db
# Для просмотра используйте:
sqlite3 app/courier_dev.db
```

### PostgreSQL (рекомендуется для production)

```bash
# Установите PostgreSQL
# Создайте базу данных
createdb courier_db

# В .env укажите:
DATABASE_URL=postgresql://username:password@localhost:5432/courier_db
```

## 🔐 Безопасность

### Production checklist

- [ ] Сгенерировать новый `SECRET_KEY`
- [ ] Использовать PostgreSQL вместо SQLite
- [ ] Установить `FLASK_DEBUG=False`
- [ ] Настроить HTTPS через Let's Encrypt
- [ ] Настроить CORS для конкретных доменов
- [ ] Ограничить rate limiting для API
- [ ] Настроить мониторинг и логирование
- [ ] Регулярное резервное копирование БД

## 🚀 Deployment

### VPS (Timeweb, DigitalOcean, etc.)

1. Клонируйте репозиторий на сервер
2. Установите зависимости
3. Настройте Nginx как reverse proxy
4. Используйте Gunicorn для запуска
5. Настройте systemd для автозапуска
6. Получите SSL сертификат через Certbot

Пример systemd service:

```ini
[Unit]
Description=Courier Simulator
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/courier-simulator
Environment="PATH=/var/www/courier-simulator/venv/bin"
ExecStart=/var/www/courier-simulator/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5000 run:app

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект находится под лицензией MIT.

## 👥 Авторы

- Ваше имя - начальная работа

## 📞 Поддержка

Если возникли вопросы или проблемы:
- Откройте Issue в GitHub
- Напишите на email: support@example.com

## 🙏 Благодарности

- Mapbox за отличное API карт
- OpenStreetMap за данные
- Flask и Socket.IO сообщество