# -*- coding: utf-8 -*-
"""
Auth helpers: token generation/verification and request guards.
"""

from functools import wraps
from typing import Optional, Dict, Any

from flask import current_app, request, jsonify, session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app import db
from app.models import User


def _get_serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY", "dev-secret-key")
    return URLSafeTimedSerializer(secret_key=secret_key, salt="auth-token")


def generate_token(user_id: int, is_admin: bool = False) -> str:
    serializer = _get_serializer()
    payload = {"user_id": user_id, "is_admin": bool(is_admin)}
    return serializer.dumps(payload)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    serializer = _get_serializer()
    max_age = current_app.config.get("AUTH_TOKEN_EXPIRY_SECONDS", 604800)
    try:
        return serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def get_bearer_token() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header.split(" ", 1)[1].strip() or None


def get_current_user() -> Optional[User]:
    token = get_bearer_token()
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        if not user.is_active:
            return jsonify({"error": "User account is disabled"}), 403
        request.current_user = user
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("admin_authenticated"):
            return func(*args, **kwargs)

        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        admin_api_token = current_app.config.get("ADMIN_API_TOKEN")
        if admin_api_token and token == admin_api_token:
            return func(*args, **kwargs)

        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401
        if not payload.get("is_admin"):
            return jsonify({"error": "Forbidden"}), 403
        return func(*args, **kwargs)

    return wrapper
