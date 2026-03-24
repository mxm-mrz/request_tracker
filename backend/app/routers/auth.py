from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserRead
from app.models.user import User
from app.security import get_current_user


router = APIRouter(
    prefix='/api/auth',
    tags=['auth']
)


@router.post('/login', status_code=status.HTTP_200_OK)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    request_data = LoginRequest(
        login=form_data.username, password=form_data.password)
    return auth_service.login(request_data)


@router.post('/registration', status_code=status.HTTP_201_CREATED, response_model=UserRead)
def registration(request: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.registration(request)


@router.get('/me', response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
