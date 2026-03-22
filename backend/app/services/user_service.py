from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_profile_by_user(self, user_id: int) -> Optional[User]:
        profile = self.repository.get_user_by_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Profile with id {user_id} not found'
            )
        return profile

    def get_admin_list(self) -> list[User]:
        admin_list = self.repository.get_admin_list()
        return admin_list
