# -*- coding: utf-8 -*-
"""
API endpoints для игроков симулятора курьера.
Обрабатывает заказы, позицию игрока и игровые действия.
"""

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User, Order
from app.utils.game_helper import (
    get_order_for_user, check_player_zones, pickup_order, 
    deliver_order, cancel_order, validate_order_action
)
from app.utils.auth_utils import login_required
import logging

# Создаем blueprint
player_bp = Blueprint('player', __name__)

# Настройка логирования
logger = logging.getLogger(__name__)

@player_bp.route('/start_shift', methods=['POST'])
@login_required
def start_shift():
    """
    Начать смену игрока.
    Устанавливает статус онлайн и подготавливает к получению заказов.
    """
    try:
        user = request.current_user
        
        # Устанавливаем статус онлайн
        user.set_online_status(True)
        
        # Проверяем, есть ли активный заказ
        active_order = user.get_active_order()
        
        logger.info(f"User {user.username} started shift")
        
        return jsonify({
            'success': True,
            'message': 'Shift started successfully',
            'user': user.to_dict(),
            'active_order': active_order.to_dict() if active_order else None
        })
        
    except Exception as e:
        logger.error(f"Error starting shift: {str(e)}")
        return jsonify({'error': 'Failed to start shift'}), 500

@player_bp.route('/stop_shift', methods=['POST'])
@login_required
def stop_shift():
    """
    Завершить смену игрока.
    Устанавливает статус офлайн.
    """
    try:
        user = request.current_user
        
        # Получаем активный заказ и отменяем его если есть
        active_order = user.get_active_order()
        if active_order:
            logger.info(f"Auto-cancelling order {active_order.id} before ending shift")
            active_order.cancel_order('shift_ended')
        
        # Устанавливаем статус офлайн
        user.set_online_status(False)
        
        logger.info(f"User {user.username} ended shift")
        
        return jsonify({
            'success': True,
            'message': 'Shift ended successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error ending shift: {str(e)}")
        return jsonify({'error': 'Failed to end shift'}), 500

@player_bp.route('/order/new', methods=['GET'])
@login_required
def get_new_order():
    """
    Получить новый заказ для игрока.
    Генерирует случайный заказ от ресторана к зданию.
    """
    try:
        user = request.current_user
        
        # Проверяем, что пользователь онлайн
        if not user.is_online:
            return jsonify({'error': 'User is not online'}), 400
        
        # Проверяем, что нет активного заказа
        active_order = user.get_active_order()
        if active_order:
            return jsonify({
                'error': 'User already has active order',
                'active_order': active_order.to_dict()
            }), 400
        
        # Генерируем новый заказ
        order = get_order_for_user(int(user.id))
        if not order:
            return jsonify({
                'success': False,
                'message': 'No orders available in your area'
            })
        
        logger.info(f"Generated new order {order['id']} for user {user.id}")
        
        return jsonify({
            'success': True,
            'order': order
        })
        
    except Exception as e:
        logger.error(f"Error getting new order: {str(e)}")
        return jsonify({'error': 'Failed to get order'}), 500


@player_bp.route('/order/accept', methods=['POST'])
@login_required
def accept_order():
    """
    Принять заказ игроком.
    Меняет статус заказа с pending на active.
    """
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        # Проверяем наличие обязательных параметров
        if not order_id:
            return jsonify({'error': 'order_id is required'}), 400
        
        user = request.current_user
        
        # Проверяем, что у пользователя нет других активных заказов
        active_order = user.get_active_order()
        if active_order and active_order.id != order_id:
            return jsonify({
                'error': 'User already has another active order',
                'active_order_id': active_order.id
            }), 400
        
        # Получаем заказ для принятия
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Защита от принятия чужого заказа
        if order.user_id and order.user_id != user.id:
            return jsonify({'error': 'Order принадлежит другому пользователю'}), 403
        
        # Проверяем, что заказ в статусе pending
        if order.status != 'pending':
            return jsonify({
                'error': f'Order cannot be accepted. Current status: {order.status}'
            }), 400
        
        # Проверяем, что заказ не истек
        if order.is_expired():
            return jsonify({'error': 'Order has expired'}), 400
        
        # Принимаем заказ - меняем статус на active
        success = order.accept_order(user.id)
        if not success:
            return jsonify({'error': 'Failed to accept order'}), 400
        
        logger.info(f"User {user.id} accepted order {order_id}")
        
        return jsonify({
            'success': True,
            'message': 'Order accepted successfully',
            'order': order.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error accepting order: {str(e)}")
        return jsonify({'error': 'Failed to accept order'}), 500

@player_bp.route('/order/pickup', methods=['POST'])
@login_required
def pickup_order_endpoint():
    """
    Забрать заказ в ресторане.
    Игрок должен быть в зоне pickup.
    """
    try:
        user = request.current_user
        
        # Проверяем валидность действия
        validation = validate_order_action(user.id, 'pickup')
        if not validation.get('valid', False):
            return jsonify({'error': validation.get('error')}), 400
        
        # Выполняем pickup
        result = pickup_order(user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400
        
    except Exception as e:
        logger.error(f"Error in pickup endpoint: {str(e)}")
        return jsonify({'error': 'Failed to pickup order'}), 500

@player_bp.route('/order/deliver', methods=['POST'])
@login_required
def deliver_order_endpoint():
    """
    Доставить заказ в здание.
    Игрок должен быть в зоне dropoff.
    """
    try:
        user = request.current_user
        
        # Проверяем валидность действия
        validation = validate_order_action(user.id, 'deliver')
        if not validation.get('valid', False):
            return jsonify({'error': validation.get('error')}), 400
        
        # Выполняем доставку
        result = deliver_order(user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400
        
    except Exception as e:
        logger.error(f"Error in deliver endpoint: {str(e)}")
        return jsonify({'error': 'Failed to deliver order'}), 500

@player_bp.route('/order/cancel', methods=['POST'])
@login_required
def cancel_order_endpoint():
    """
    Отменить заказ.
    """
    try:
        data = request.get_json()
        reason = data.get('reason', 'user_cancelled')
        user = request.current_user
        
        # Проверяем валидность действия
        validation = validate_order_action(user.id, 'cancel')
        if not validation.get('valid', False):
            return jsonify({'error': validation.get('error')}), 400
        
        # Отменяем заказ
        result = cancel_order(user.id, reason)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error')}), 400
        
    except Exception as e:
        logger.error(f"Error in cancel endpoint: {str(e)}")
        return jsonify({'error': 'Failed to cancel order'}), 500

@player_bp.route('/position', methods=['POST'])
@login_required
def update_position():
    """
    Обновить позицию игрока.
    Проверяет зоны pickup/dropoff.
    """
    try:
        data = request.get_json()
        lat = data.get('lat')
        lng = data.get('lng')
        accuracy = data.get('accuracy', 999)
        
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng are required'}), 400
        
        user = request.current_user
        
        # Проверяем точность GPS
        max_accuracy = current_app.config['GAME_CONFIG']['max_gps_accuracy']
        if accuracy > max_accuracy:
            return jsonify({
                'warning': 'GPS accuracy is too low',
                'accuracy': accuracy,
                'max_allowed': max_accuracy,
                'recommendation': 'Move to an open area for better GPS signal'
            }), 202  # Accepted but with warning
        
        # Обновляем позицию пользователя
        user.update_position(lat, lng)
        
        # Проверяем зоны заказа
        zones_status = check_player_zones(user.id, lat, lng)
        
        logger.info(f"Updated position for user {user.id}: ({lat}, {lng}) accuracy: {accuracy}m")
        
        return jsonify({
            'success': True,
            'position': {'lat': lat, 'lng': lng, 'accuracy': accuracy},
            'zones': zones_status
        })
        
    except Exception as e:
        logger.error(f"Error updating position: {str(e)}")
        return jsonify({'error': 'Failed to update position'}), 500

@player_bp.route('/status', methods=['GET'])
@login_required
def get_player_status():
    """
    Получить текущий статус игрока.
    Включает активный заказ, позицию, баланс.
    """
    try:
        user = request.current_user
        
        # Получаем активный заказ
        active_order = user.get_active_order()
        
        # Получаем статистику
        stats = user.get_statistics()
        
        return jsonify({
            'user': user.to_dict(),
            'active_order': active_order.to_dict() if active_order else None,
            'statistics': stats,
            'position': {
                'lat': user.last_position_lat,
                'lng': user.last_position_lng
            } if user.last_position_lat is not None and user.last_position_lng is not None else None
        })
        
    except Exception as e:
        logger.error(f"Error getting player status: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

@player_bp.route('/config', methods=['GET'])
@login_required
def get_game_config():
    """
    Получить игровую конфигурацию.
    Радиусы, таймеры, настройки экономики.
    """
    try:
        config = current_app.config['GAME_CONFIG']
        
        # Возвращаем только нужные клиенту настройки
        client_config = {
            'pickup_radius': config['pickup_radius'],
            'dropoff_radius': config['dropoff_radius'],
            'max_gps_accuracy': config['max_gps_accuracy'],
            'base_payment': config['base_payment'],
            'distance_rate': config['distance_rate'],
            'on_time_bonus': config['on_time_bonus']
        }
        
        return jsonify(client_config)
        
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return jsonify({'error': 'Failed to get config'}), 500

@player_bp.route('/search_radius', methods=['POST'])
@login_required
def update_search_radius():
    """
    Обновить радиус поиска заказов для игрока.
    Принимает значение от 3 до 25 км.
    """
    try:
        data = request.get_json()
        radius_km = data.get('radius_km')
        
        # Валидация входных данных
        if radius_km is None:
            return jsonify({'error': 'radius_km is required'}), 400

        user = request.current_user
        
        # Обновляем радиус через метод модели (с валидацией)
        try:
            new_radius = user.update_search_radius(radius_km)
            
            logger.info(f"User {user.id} updated search radius to {new_radius} km")
            
            return jsonify({
                'success': True,
                'message': 'Search radius updated successfully',
                'search_radius_km': new_radius
            })
            
        except ValueError as ve:
            # Ошибка валидации радиуса
            return jsonify({'error': str(ve)}), 400
        
    except Exception as e:
        logger.error(f"Error updating search radius: {str(e)}")
        return jsonify({'error': 'Failed to update search radius'}), 500
