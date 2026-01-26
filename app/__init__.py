from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
import os
import sys

# Инициализация расширений
db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
mail = Mail()  # Инициализация Flask-Mail

def create_app(config_name=None):
    """
    Factory функция для создания Flask приложения
    """
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"), 
                static_folder=os.path.join(os.path.dirname(__file__), "..", "static"))
    
    # Загружаем конфигурацию
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    
    from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    app.config.from_object(config_map.get(config_name, DevelopmentConfig))
    
    # Python version warning (prod baseline 3.12)
    if config_name == "production" and sys.version_info[:2] != (3, 12):
        raise RuntimeError("Unsupported Python version for production. Use Python 3.12.")
    elif sys.version_info[:2] != (3, 12):
        print("⚠️  Recommended Python for production is 3.12 (current: {}.{}).".format(
            sys.version_info[0], sys.version_info[1]
        ))

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is required. Set it in environment or .env.local.")
    
    # Инициализируем расширения
    db.init_app(app)
    migrate.init_app(app, db)
    allowed_origins = [
        origin.strip()
        for origin in app.config.get("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    transports = [
        item.strip()
        for item in app.config.get("SOCKETIO_TRANSPORTS", "polling").split(",")
        if item.strip()
    ]
    socketio.init_app(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode=app.config.get("SOCKETIO_ASYNC_MODE", "threading"),
        transports=transports
    )
    mail.init_app(app)  # Инициализация Flask-Mail с конфигурацией
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    
    # Регистрируем blueprints
    from app.api.auth import auth_bp
    from app.api.player import player_bp
    from app.api.admin import admin_bp
    from app.api.app_info import app_info_bp
    from app.api.cities import cities_bp
    from app.routes import pages_bp
    from admin.routes import admin_pages_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(player_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(app_info_bp, url_prefix="/api")
    app.register_blueprint(pages_bp)
    app.register_blueprint(admin_pages_bp, url_prefix="/admin")
    app.register_blueprint(cities_bp)
    
    # Регистрируем DEBUG blueprint только в development режиме
    if config_name == "development" and app.config.get("ENABLE_DEBUG_ROUTES"):
        from app.api.debug import debug_bp
        app.register_blueprint(debug_bp, url_prefix="/api/debug")
        print("⚠️  DEBUG endpoints включены: /api/debug/*")
    
    # Регистрируем SocketIO обработчики
    from app.socketio_handlers import game_events
    
    # Проверяем наличие данных (без создания таблиц)
    with app.app_context():
        from app.utils.data_loader import load_initial_data
        load_initial_data()
    
    # Добавляем базовые маршруты
    @app.route("/api/health")
    def health_check():
        try:
            db.session.execute(db.text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}, 500

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io https://telegram.org https://api.mapbox.com; "
            "style-src 'self' 'unsafe-inline' https://api.mapbox.com; "
            "img-src 'self' data: https://api.mapbox.com https://telegram.org; "
            "connect-src 'self' https://api.mapbox.com https://events.mapbox.com; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'"
        )

        if app.config.get("CSP_ENFORCE"):
            response.headers["Content-Security-Policy"] = csp
        else:
            response.headers["Content-Security-Policy-Report-Only"] = csp

        return response
    
    return app
