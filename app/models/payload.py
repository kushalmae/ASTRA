"""Payload model for storing spacecraft information."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Payload(Base):
    """Payload model for storing spacecraft information."""
    
    __tablename__ = 'payloads'
    
    scid = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(String(20), nullable=False, default='ACTIVE')
    
    # Define relationships
    events = relationship("Event", back_populates="payload", cascade="all, delete-orphan")
    breach_history = relationship("BreachHistory", back_populates="payload", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Payload(scid='{self.scid}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert payload to dictionary."""
        return {
            'scid': self.scid,
            'name': self.name,
            'description': self.description,
            'status': self.status
        } 