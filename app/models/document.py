from sqlalchemy import Column, String, JSON
from app.models.base import BaseModel


class Document(BaseModel):
    __tablename__ = "documents"

    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    classification = Column(String, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    s3_key = Column(String, nullable=False, unique=True)

