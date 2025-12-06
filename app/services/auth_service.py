from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings


def create_anonymous_user(db: Session) -> User:
    user = User(rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_anonymous(db: Session) -> dict:
    user = create_anonymous_user(db)
    
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"id_usuario": user.id, "rol": user.rol},
        expires_delta=expires_delta
    )
    
    return {
        "id_usuario": user.id,
        "rol": user.rol,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expiration_minutes
    }

