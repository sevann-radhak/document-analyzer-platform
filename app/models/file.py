from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class File(BaseModel):
    __tablename__ = "files"

    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False, unique=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    validation_results = Column(JSON, nullable=True)

    user = relationship("User", backref="files")

