from sqlalchemy import Column, String
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    rol = Column(String, nullable=False, default="user")

