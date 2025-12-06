from sqlalchemy import Column, String, JSON
from app.models.base import BaseModel


class Document(BaseModel):
    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    classification = Column(String(50), nullable=True)
    extracted_data = Column(JSON, nullable=True)
    s3_key = Column(String(1000), nullable=False, unique=True)

