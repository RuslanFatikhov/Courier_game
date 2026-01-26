"""initial schema

Revision ID: 20260126_1605
Revises:
Create Date: 2026-01-26 16:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260126_1605'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('google_id', sa.String(length=50), nullable=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True),
        sa.Column('telegram_username', sa.String(length=100), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('balance', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_deliveries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('search_radius_km', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_online', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_position_lat', sa.Float(), nullable=True),
        sa.Column('last_position_lng', sa.Float(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('telegram_id'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('pickup_name', sa.String(length=200), nullable=False),
        sa.Column('dropoff_address', sa.String(length=300), nullable=False),
        sa.Column('pickup_lat', sa.Float(), nullable=False),
        sa.Column('pickup_lng', sa.Float(), nullable=False),
        sa.Column('dropoff_lat', sa.Float(), nullable=False),
        sa.Column('dropoff_lng', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('pickup_time', sa.DateTime(), nullable=True),
        sa.Column('delivery_time', sa.DateTime(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('timer_seconds', sa.Integer(), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])

    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('admin_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_reports_user_id', 'reports', ['user_id'])
    op.create_index('ix_reports_order_id', 'reports', ['order_id'])


def downgrade():
    op.drop_index('ix_reports_order_id', table_name='reports')
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_table('reports')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_table('orders')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
