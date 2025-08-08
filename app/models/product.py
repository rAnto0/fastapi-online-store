from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
