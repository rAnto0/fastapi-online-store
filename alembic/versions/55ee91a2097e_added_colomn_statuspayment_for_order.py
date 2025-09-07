"""added_colomn_statuspayment_for_Order

Revision ID: 55ee91a2097e
Revises: 2f71e10c19a6
Create Date: 2025-09-04 19:26:17.702887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '55ee91a2097e'
down_revision: Union[str, Sequence[str], None] = '2f71e10c19a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем Enum типы сначала
    orderstatus_enum = postgresql.ENUM(
        'PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 
        'DELIVERED', 'CANCELLED', 'REFUNDED', 
        name='orderstatus'
    )
    orderstatus_enum.create(op.get_bind())
    
    paymentstatus_enum = postgresql.ENUM(
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 
        'REFUNDED', 'PARTIALLY_REFUNDED', 
        name='paymentstatus'
    )
    paymentstatus_enum.create(op.get_bind())
    
    # Теперь добавляем колонки с созданными типами
    op.add_column('orders', sa.Column('order_status', orderstatus_enum, nullable=False))
    op.add_column('orders', sa.Column('payment_status', paymentstatus_enum, nullable=False))
    
    # Удаляем старую колонку status
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_column('orders', 'status')


def downgrade() -> None:
    """Downgrade schema."""
    # Восстанавливаем старую колонку status
    op.add_column('orders', sa.Column('status', postgresql.ENUM(
        'PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 
        'DELIVERED', 'CANCELLED', 'REFUNDED', 
        name='orderstatus'), autoincrement=False, nullable=False))
    
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    
    # Удаляем новые колонки
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'order_status')
    
    # Удаляем Enum типы
    paymentstatus_enum = postgresql.ENUM(
        name='paymentstatus'
    )
    paymentstatus_enum.drop(op.get_bind())