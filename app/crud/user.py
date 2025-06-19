from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_name(db: Session, name: str) -> Optional[User]:
    return db.query(User).filter(User.name == name).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        creation_date=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_or_update_google_user(
    db: Session, 
    email: str, 
    name: str, 
    first_name: Optional[str] = None, 
    last_name: Optional[str] = None
) -> User:
    """
    Создание или обновление пользователя аутентифицированного через Google
    """
    user = get_user_by_email(db, email=email)
    
    if not user:
        db_user = User(
            email=email,
            name=name,
            hashed_password=None,  # Google пользователи не имеют пароля
            first_name=first_name,
            last_name=last_name,
            creation_date=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    
    db.commit()
    db.refresh(user)
    return user