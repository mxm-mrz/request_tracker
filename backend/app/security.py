from datetime import timedelta
import uuid

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt


from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.time_utils import utc_now
from app.models.user import User, UserRole

from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.blacklist_service import TokenBlacklistService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'}
)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire, 'jti': str(uuid.uuid4())})
    encode_jwt = jwt.encode(to_encode, settings.secret_key,
                            algorithm=settings.algorithm)
    return encode_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key,
                             algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    user_id = payload.get('sub')
    if user_id is None:
        raise credentials_exception

    jti = payload.get('jti')

    cache_service = TokenBlacklistService()
    user_repo = UserRepository(db)

    if cache_service.is_jti_blacklisted(jti):
        raise credentials_exception

    user = user_repo.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception

    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied'
        )
    return current_user
