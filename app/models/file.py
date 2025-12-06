from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class File(BaseModel):
    __tablename__ = "files"

    filename = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True)  # Changed from String to String(1000) for unique constraint
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    validation_results = Column(JSON, nullable=True)

    user = relationship("User", backref="files")

