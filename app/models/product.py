from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    price = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.title}', price={self.price})>"
