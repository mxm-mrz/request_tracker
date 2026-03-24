from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.comment import CommentCreate, CommentResponse
from app.database import get_db
from app.models.user import User
from app.security import get_current_user
from app.services.comment_service import CommentService


router = APIRouter(
    prefix='/api/comment',
    tags=['comment']
)


@router.get('/{ticket_id}/comments', response_model=list[CommentResponse])
def get_commens_list(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment_service = CommentService(db)
    return comment_service.get_comment_by_ticket(ticket_id, current_user)


@router.post('/{ticket_id}/comments', response_model=CommentResponse)
def create(ticket_id: int, comment_data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment_service = CommentService(db)
    return comment_service.create(ticket_id, comment_data, current_user)
