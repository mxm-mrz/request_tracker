from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.statushistory_repository import StatusHistoryRepository
from app.models.statushistory import StatusHistory
from app.models.user import User, UserRole
from app.repositories.ticket_repository import TicketRepository
from app.services.statushistory_cache import StatusHistoryCacheService
from app.schemas.statushistory import StatusHistoryResponse


class StatusHistoryService:
    def __init__(self, db: Session):
        self.repository = StatusHistoryRepository(db)
        self.ticket_repository = TicketRepository(db)
        self.cache = StatusHistoryCacheService()

    def get_history(self, ticket_id: int, current_user: User) -> list[dict]:
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

        cached_data = self.cache.get_status(ticket_id)
        if cached_data:
            return cached_data
        result = self.repository.get_status_by_ticket(ticket_id)
        serialize_result = [StatusHistoryResponse.model_validate(
            s).model_dump(mode='json') for s in result]
        self.cache.set_status(ticket_id, serialize_result)
        return serialize_result
