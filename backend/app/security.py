from datetime import timedelta

from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.time_utils import utc_now


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})
    encode_jwt = jwt.encode(to_encode, settings.secret_key,
                            algorithm=settings.algorithm)
    return encode_jwt
