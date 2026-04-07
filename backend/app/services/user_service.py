from fastapi import HTTPException, status
from sqlalchemy.orm import Session


from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead
from app.services.user_cache import UserCacheService


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.cache = UserCacheService()

    def get_profile_by_user(self, user_id: int) -> dict:
        cached_user = self.cache.get_profile(user_id)
        if cached_user:
            return cached_user
        profile = self.repository.get_user_by_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Profile with id {user_id} not found'
            )
        profile_data = UserRead.model_validate(profile).model_dump(mode='json')
        self.cache.set_profile(user_id, profile_data)
        return profile_data

    def get_admin_list(self) -> list[dict]:

        cached_data = self.cache.get_admin_list()

        if cached_data:
            return cached_data
        else:
            admin_db_list = self.repository.get_admin_list()
            final_data = [UserRead.model_validate(u).model_dump(
                mode='json') for u in admin_db_list]

            self.cache.set_admin_list(final_data)

        return final_data
