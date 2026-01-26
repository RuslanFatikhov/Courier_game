# -*- coding: utf-8 -*-
"""
Обработчики WebSocket событий для игрового процесса.
Управление real-time взаимодействием с клиентами через Socket.IO.
"""

import random
import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

from app import socketio, db
from app.models.user import User
from app.models.order import Order
from app.utils.game_helper import get_order_for_user
from app.utils.auth_utils import verify_token

# Настройка логирования для отслеживания событий WebSocket
logger = logging.getLogger(__name__)

# Глобальный словарь активных пользователей {session_id: user_data}
# Используется для быстрого доступа к информации о подключенных пользователях
active_users = {}

def _get_socket_user():
    token = request.args.get("token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@socketio.on('connect')
def handle_connect():
    """
    Обработчик подключения клиента к WebSocket.
    Логирует подключение для отладки.
    """
    session_id = request.sid
    user = _get_socket_user()
    if not user:
        logger.warning("Socket connect rejected: invalid token")
        return False

    active_users[session_id] = {
        'user_id': user.id,
        'username': user.username,
        'rooms': [f'user_{user.id}'],
        'is_searching': False
    }
    join_room(f'user_{user.id}')
    logger.info(f"🔌 Client connected: {session_id} (user_id={user.id})")


@socketio.on('disconnect')
def handle_disconnect():
    """
    Обработчик отключения клиента от WebSocket.
    Очищает данные пользователя из памяти.
    """
    try:
        session_id = request.sid
        logger.info(f"🔌 Client disconnected: {session_id}")
        
        # Удаляем пользователя из списка активных при отключении
        if session_id in active_users:
            user_data = active_users[session_id]
            logger.info(f"Removed user {user_data.get('user_id')} from active users")
            del active_users[session_id]
    except Exception as e:
        logger.error(f"Error in disconnect handler: {str(e)}")


@socketio.on('user_login')
def handle_user_login(data):
    """
    Обработчик логина пользователя через WebSocket.
    Регистрирует пользователя в системе real-time коммуникации.
    
    Args:
        data (dict): Данные с user_id от клиента
    """
    try:
        session_id = request.sid
        if session_id not in active_users:
            user = _get_socket_user()
            if not user:
                emit('error', {'message': 'Unauthorized'})
                return
            active_users[session_id] = {
                'user_id': user.id,
                'username': user.username,
                'rooms': [f'user_{user.id}'],
                'is_searching': False
            }
            join_room(f'user_{user.id}')

        user_id = active_users[session_id]['user_id']
        logger.info(f"👤 User {user_id} logged in via WebSocket (session: {session_id})")
        
        # Подтверждаем успешный логин
        emit('login_success', {
            'user_id': user_id,
            'message': 'Login successful'
        })
    except Exception as e:
        logger.error(f"Error in user_login handler: {str(e)}", exc_info=True)
        emit('error', {'message': 'Login failed'})


@socketio.on('start_order_search')
def handle_start_order_search(data):
    """
    Обработчик начала поиска заказов.
    Запускает процесс симуляции поиска и генерации заказа.
    
    Args:
        data (dict): Параметры поиска (radius_km)
    """
    try:
        session_id = request.sid
        
        # Проверяем, что пользователь аутентифицирован
        if session_id not in active_users:
            emit('error', {'message': 'User not authenticated'})
            return
        
        user_data = active_users[session_id]
        user_id = user_data['user_id']
        
        # ЗАЩИТА ОТ ДУБЛИРОВАНИЯ: проверяем, не идет ли уже поиск
        if user_data.get('is_searching', False):
            logger.warning(f"⚠️ User {user_id} tried to start search while already searching")
            emit('error', {'message': 'Search already in progress'})
            return
        
        radius_km = data.get('radius_km', 5)
        
        logger.info(f"🔍 User {user_id} started order search (radius: {radius_km}km)")
        
        # Устанавливаем флаг активного поиска
        user_data['is_searching'] = True
        
        # Создаем комнату для поиска заказов
        search_room = f'order_search_{user_id}'
        join_room(search_room)
        if search_room not in user_data['rooms']:
            user_data['rooms'].append(search_room)
        
        # Подтверждаем начало поиска
        emit('search_started', {
            'status': 'searching', 
            'radius_km': radius_km
        })
        
        # Запускаем симуляцию поиска
        simulate_order_search_sync(user_id, radius_km, session_id)
        
    except Exception as e:
        logger.error(f"Error in start order search: {str(e)}", exc_info=True)
        # Сбрасываем флаг поиска при ошибке
        if session_id in active_users:
            active_users[session_id]['is_searching'] = False
        emit('error', {'message': 'Failed to start order search'})


@socketio.on('stop_order_search')
def handle_stop_order_search():
    """
    Обработчик остановки поиска заказов.
    Останавливает текущий процесс поиска.
    """
    try:
        session_id = request.sid
        
        if session_id not in active_users:
            return
        
        user_data = active_users[session_id]
        user_id = user_data['user_id']
        
        logger.info(f"🛑 User {user_id} stopped order search")
        
        # Сбрасываем флаг поиска
        user_data['is_searching'] = False
        
        # Покидаем комнату поиска
        search_room = f'order_search_{user_id}'
        leave_room(search_room)
        if search_room in user_data['rooms']:
            user_data['rooms'].remove(search_room)
        
        emit('search_stopped', {'status': 'stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping order search: {str(e)}", exc_info=True)


@socketio.on('update_position')
def handle_update_position(data):
    """
    Обработчик обновления позиции игрока.
    Сохраняет текущие координаты в БД.
    
    Args:
        data (dict): Координаты (lat, lng, accuracy)
    """
    try:
        session_id = request.sid
        
        if session_id not in active_users:
            return
        
        user_id = active_users[session_id]['user_id']
        lat = data.get('lat')
        lng = data.get('lng')
        
        if lat is None or lng is None:
            return
        
        # Обновляем позицию в БД
        user = db.session.get(User, user_id)
        if user:
            user.update_position(lat, lng)
        
    except Exception as e:
        logger.error(f"Error updating position: {str(e)}", exc_info=True)


def simulate_order_search_sync(user_id: int, radius_km: float, session_id: str):
    """
    Синхронная симуляция поиска заказов с прогресс-баром.
    Использует socketio.sleep для совместимости с eventlet/gevent.
    
    Args:
        user_id (int): ID пользователя
        radius_km (float): Радиус поиска заказов
        session_id (str): ID сессии для сброса флага
    """
    try:
        # Проверяем, не был ли поиск остановлен
        if session_id not in active_users or not active_users[session_id].get('is_searching'):
            logger.info(f"Search cancelled for user {user_id}")
            return
        
        # Случайное время поиска от 5 до 15 секунд
        search_time = random.randint(5, 15)
        
        # Отправляем прогресс поиска каждую секунду
        for i in range(search_time):
            # Проверяем, не был ли поиск остановлен
            if session_id not in active_users or not active_users[session_id].get('is_searching'):
                logger.info(f"Search cancelled for user {user_id} at {i+1}/{search_time}s")
                return
            
            socketio.sleep(1)
            
            # Отправляем обновление прогресса
            socketio.emit('search_progress', {
                'elapsed': i + 1,
                'total': search_time,
                'percentage': round(((i + 1) / search_time) * 100)
            }, room=f'order_search_{user_id}')
        
        # После завершения поиска генерируем заказ
        generate_order_for_user(user_id)
        
    except Exception as e:
        logger.error(f"Error in sync order search for user {user_id}: {str(e)}", exc_info=True)
        socketio.emit('error', {
            'message': 'Order search failed'
        }, room=f'user_{user_id}')
    finally:
        # ВАЖНО: Всегда сбрасываем флаг поиска после завершения
        if session_id in active_users:
            active_users[session_id]['is_searching'] = False
            logger.info(f"✅ Search flag reset for user {user_id}")


def generate_order_for_user(user_id: int):
    """
    Генерация и отправка заказа пользователю.
    
    Args:
        user_id (int): ID пользователя для генерации заказа
    """
    try:
        # Получаем пользователя из БД
        user = db.session.get(User, user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            socketio.emit('no_orders_found', {
                'message': 'User not found'
            }, room=f'user_{user_id}')
            return
        
        # Генерируем заказ используя helper
        order_data = get_order_for_user(user_id)
        
        if order_data:
            logger.info(f"✅ Order generated for user {user_id}: {order_data['id']}")
            
            # Отправляем заказ клиенту
            socketio.emit('order_found', {
                'order': order_data,
                'message': 'Order found!'
            }, room=f'user_{user_id}')
        else:
            logger.warning(f"No orders available for user {user_id}")
            
            # Сообщаем что заказов не найдено
            socketio.emit('no_orders_found', {
                'message': 'No orders available in your area. Try again later.'
            }, room=f'user_{user_id}')
            
    except Exception as e:
        logger.error(f"Error generating order for user {user_id}: {str(e)}", exc_info=True)
        socketio.emit('error', {
            'message': 'Failed to generate order'
        }, room=f'user_{user_id}')
