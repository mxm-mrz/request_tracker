from time import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, decode_access_token
from app.utils.hashing import verify_password
from app.services.blacklist_service import TokenBlacklistService


class AuthService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def registration(self, user_create_data: UserCreate) -> User:
        email = self.repository.get_user_by_email(user_create_data.email)
        if email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this email already exists'
            )
        username = self.repository.get_user_by_username(
            user_create_data.username)
        if username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='A user with this username already exists'
            )

        new_user = self.repository.create(user_create_data)
        return new_user

    def login(self, user_login_data: LoginRequest) -> TokenResponse:
        if '@' in user_login_data.login:
            user = self.repository.get_user_by_email(user_login_data.login)
        else:
            user = self.repository.get_user_by_username(user_login_data.login)

        if not user or not verify_password(user_login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User or password is wrong'
            )

        access_token = create_access_token({'sub': str(user.id)})
        return TokenResponse(access_token=access_token, token_type="bearer")

    def logout(self, token: str):
        payload = decode_access_token(token)
        jti = payload.get('jti')
        exp = payload.get('exp')

        current_time = int(time())
        expire_time = exp - current_time

        cache_service = TokenBlacklistService()

        if expire_time > 0:
            cache_service.add_to_blacklist(jti, expire_time)
