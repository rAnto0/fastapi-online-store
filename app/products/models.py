from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    func,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    reserved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint(
            "stock_quantity >= 0", name="check_stock_quantity_non_negative"
        ),
        CheckConstraint("reserved >= 0", name="check_reserved_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.title}', price={self.price})>"
