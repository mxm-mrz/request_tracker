from datetime import timedelta

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt


from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.time_utils import utc_now
from app.models.user import User, UserRole

from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.models.ticket import Ticket


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})
    encode_jwt = jwt.encode(to_encode, settings.secret_key,
                            algorithm=settings.algorithm)
    return encode_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    try:
        payload = jwt.decode(token, settings.secret_key,
                             algorithms=[settings.algorithm])
        user_id: str = payload.get('sub')

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
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
