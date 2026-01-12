"""SQLAlchemy models for inventory items."""

from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.sql import func
from .database import Base


class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    location = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Prevent negative inventory
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
    )
    
    def __repr__(self):
        return f"<Item {self.name} qty={self.quantity} @ {self.location}>"
