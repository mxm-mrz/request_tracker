from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserRead
from app.services.user_service import UserService
from app.database import get_db
from app.models.user import User, UserRole
from app.security import get_current_admin_user


router = APIRouter(
    prefix='/api/user',
    tags=['user']
)


@router.get('/admin_list', response_model=list[UserRead])
def get_admin_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    user_service = UserService(db)
    return user_service.get_admin_list()


@router.get('/{user_id}', response_model=UserRead)
def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    user_service = UserService(db)
    return user_service.get_profile_by_user(user_id)
