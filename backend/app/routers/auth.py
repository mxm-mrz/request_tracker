from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserRead
from app.models.user import User
from app.security import get_current_user, oauth2_scheme
from app.services.rate_limit import RateLimitService


router = APIRouter(
    prefix='/api/auth',
    tags=['auth']
)


@router.post('/login', status_code=status.HTTP_200_OK)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    client_ip = request.headers.get('x-forwarded-for') or request.client.host

    redis_key = f'rate_limit:login:{form_data.username}:{client_ip}'

    rate_limiter = RateLimitService()
    rate_limiter.check_limit(key=redis_key, limit=5, window=60)

    auth_service = AuthService(db)
    request_data = LoginRequest(
        login=form_data.username, password=form_data.password)
    return auth_service.login(request_data)


@router.post('/logout', status_code=status.HTTP_200_OK)
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    auth_service.logout(token)
    return {'message': 'Seccessfully logged out'}


@router.post('/registration', status_code=status.HTTP_201_CREATED, response_model=UserRead)
def registration(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    client_ip = request.headers.get('x-forwarded-for') or request.client.host

    redis_key = f'rate_limit:registration:{client_ip}'

    rate_limiter = RateLimitService()
    rate_limiter.check_limit(key=redis_key, limit=3, window=600)

    auth_service = AuthService(db)
    return auth_service.registration(user_data)


@router.get('/me', response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
