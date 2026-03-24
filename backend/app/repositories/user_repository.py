from sqlalchemy.orm import Session
from typing import Optional

from app.utils.hashing import get_password_hash
from ..models.user import User, UserRole
from ..schemas.user import UserCreate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, user_email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == user_email).first()

    def create(self, user_data: UserCreate) -> User:
        password_hash = get_password_hash(user_data.password)
        db_user = User(
            **user_data.model_dump(exclude={'password'}), hashed_password=password_hash)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_admin_list(self) -> list[User]:
        return self.db.query(User).filter(User.role == UserRole.ADMIN).all()
