from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.statushistory_repository import StatusHistoryRepository
from app.models.statushistory import StatusHistory
from app.models.user import User, UserRole
from app.repositories.ticket_repository import TicketRepository


class StatusHistoryService:
    def __init__(self, db: Session):
        self.repository = StatusHistoryRepository(db)
        self.ticket_repository = TicketRepository(db)

    def get_history(self, ticket_id: int, current_user: User) -> list[StatusHistory]:
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
        return self.repository.get_status_by_ticket(ticket_id)
