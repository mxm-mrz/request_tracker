from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.comment_repository import CommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.comment import CommentCreate
from app.models.user import User, UserRole
from app.models.comment import Comment


class CommentService:
    def __init__(self, db: Session):
        self.comment_repository = CommentRepository(db)
        self.ticket_repository = TicketRepository(db)

    def create(self, comment_data: CommentCreate, current_user: User):
        ticket = self.ticket_repository.get_ticket_by_id(
            comment_data.ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Ticket not found'
            )

        if current_user.role != UserRole.ADMIN and ticket.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете комментировать только свои заявки"
            )

        new_comment = self.comment_repository.create(
            comment_data, current_user.id)
        return new_comment

    def get_comment_by_ticket(self, ticket_id: int, current_user: User) -> list[Comment]:
        ticket = self.ticket_repository.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Ticket not found'
            )
        if current_user.id != ticket.author_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        return self.comment_repository.get_comment_by_ticket(ticket_id)
