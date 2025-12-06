from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Event(BaseModel):
    __tablename__ = "events"

    event_type = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", backref="events")

