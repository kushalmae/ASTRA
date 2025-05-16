from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.base import Base

class Event(Base):
    """Event model for storing monitoring events."""
    
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    scid = Column(Integer, ForeignKey('payloads.scid'), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Define relationships
    payload = relationship("Payload", back_populates="events")
    breach_history = relationship("BreachHistory", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(scid='{self.scid}', metric_type='{self.metric_type}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'scid': self.scid,
            'metric_type': self.metric_type,
            'value': self.value,
            'threshold': self.threshold,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class BreachHistory(Base):
    """Breach history model for storing breach events."""
    
    __tablename__ = 'breach_history'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    scid = Column(Integer, ForeignKey('payloads.scid'), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Define relationships
    event = relationship("Event", back_populates="breach_history")
    payload = relationship("Payload", back_populates="breach_history")
    
    def __repr__(self):
        return f"<BreachHistory(scid='{self.scid}', metric_type='{self.metric_type}')>"
    
    def to_dict(self):
        """Convert breach history to dictionary."""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'scid': self.scid,
            'metric_type': self.metric_type,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        } 