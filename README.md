# Q-RYER (Courier Simulator)

## Требования
- Python: 3.12 (prod baseline, Docker)
- Python: 3.14.2 (локально проверено, возможны отличия с async/runtime)

## Быстрый старт
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local
python scripts/init_db.py
python run.py
```

## Переменные окружения
Файл: `.env.local` (не коммитится)

Ключевые:
- `SECRET_KEY` — секрет Flask (обязательно)
- `ADMIN_PASSWORD` — пароль веб-админки (обязательно в production)
- `ADMIN_API_TOKEN` — bearer-токен для `/api/admin/*`
- `AUTH_TOKEN_EXPIRY_SECONDS` — TTL токенов (сек)
- `ALLOWED_ORIGINS` — CORS origins, через запятую
- `ENABLE_DEBUG_ROUTES` — включение debug endpoints
- `SOCKETIO_ASYNC_MODE` — async mode для Socket.IO (eventlet/threading)
- `SOCKETIO_TRANSPORTS` — transports для Socket.IO (polling/websocket)

## API авторизация
Все защищенные эндпоинты ожидают `Authorization: Bearer <token>`.
Токен возвращается в ответах `/api/auth/login`, `/api/auth/register/verify`,
`/api/auth/telegram_login`, `/api/auth/google_login`.

## Пример .env.local
См. `.env.example`.

## Rotate keys (обязательно при утечке)
1) Сгенерировать новые значения для `SECRET_KEY`, `ADMIN_PASSWORD`, `ADMIN_API_TOKEN`.
2) Отозвать токены Telegram/Mapbox/почты и выпустить новые.
3) Перезапустить приложение.
4) Если секреты были в git: используйте `git filter-repo` для очистки истории.

## Запуск через Gunicorn (prod)
Основной способ (HTTP-only, Socket.IO без гарантии WebSocket):
```bash
 . .venv/bin/activate
gunicorn -k gthread -w 1 --threads 1 -b 0.0.0.0:5200 wsgi:app
```

Socket.IO с WebSocket требует eventlet/gevent и совместимую версию Python.

## Docker
```bash
docker build -t q-ryer .
docker run --env-file .env.local -p 5200:5200 q-ryer
```

```bash
docker compose up --build
```

## Docker smoke-test
```bash
docker build -t q-ryer .
docker run --env-file .env.local -p 5200:5200 q-ryer
curl http://127.0.0.1:5200/api/health
```

Docker Compose health:
```bash
docker compose ps
docker inspect --format='{{json .State.Health}}' <container_id>
```

## Smoke checks
```bash
curl http://127.0.0.1:5200/api/health
AUTH_TOKEN=<token> python scripts/socket_smoke.py
scripts/smoke.sh
```

## Static assets / PWA status
Service Worker не используется (sw.js удален). Manifest используется только для
favicon (`static/img/favicon_io/site.webmanifest`) и app_info (`manifest.json`).

## Python version policy
- Prod baseline: Python 3.12 (Docker).
- Локально можно использовать Python 3.14, но возможны отличия
  в async/WS стеке и зависимостях.

## Socket.IO transport
В проде используется polling (`SOCKETIO_TRANSPORTS=polling`). WebSocket не включен
на Python 3.14 из-за несовместимости eventlet/gevent.
Если нужен WebSocket — перейти на Python 3.12 + eventlet/gevent и включить websocket.

## Security headers
По умолчанию CSP включен в режиме Report-Only. Для enforcement:
```bash
export CSP_ENFORCE=true
```

## Миграции
Пока используется sqlite по умолчанию. Для локальной инициализации:
```bash
. .venv/bin/activate
python scripts/init_db.py
```

Для Alembic/Flask-Migrate:
```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "init"
flask db upgrade
```

## Тесты
```bash
. .venv/bin/activate
pytest -q
```

## Проверка
```bash
. .venv/bin/activate
python run.py
```
