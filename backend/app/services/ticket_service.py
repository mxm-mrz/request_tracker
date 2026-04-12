from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketQueryParams, TicketResponse, TicketUpdateByAdmin, TicketUpdateByUser
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.repositories.statushistory_repository import StatusHistoryRepository
from app.schemas.statushistory import StatusHistoryCreate
from app.time_utils import utc_now
from app.services.ticket_cache import TicketCacheService
from app.services.statushistory_cache import StatusHistoryCacheService
from app.services.event_publisher import EventPublisher


class TicketService:
    def __init__(self, db: Session):
        self.ticket_repository = TicketRepository(db)
        self.user_repository = UserRepository(db)
        self.statushistory_repository = StatusHistoryRepository(db)
        self.cache = TicketCacheService()
        self.cache_statushistory = StatusHistoryCacheService()

    def check_ticket(self, found_ticket: Ticket | None) -> Ticket:
        if not found_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Ticket not found'
            )
        return found_ticket

    def check_by_admin(self, current_user: User) -> User:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )
        return current_user

    def create(self, ticket_data: TicketCreate, user_id: int) -> Ticket:
        new_ticket = self.ticket_repository.create(ticket_data, user_id)
        self.cache.invalidate_ticket_list()
        event_publisher = EventPublisher()
        event_publisher.publish_ticket_event(
            "TICKET_CREATED", new_ticket.id, user_id)
        return new_ticket

    def get_ticket_list(self, params: TicketQueryParams, current_user: User) -> dict[str, Any]:
        if current_user.role != UserRole.ADMIN:
            params.author_id = current_user.id

        cached_list = self.cache.get_ticket_list(
            current_user.id, params.model_dump_json())
        if cached_list:
            return cached_list
        else:
            db_tickets = self.ticket_repository.get_ticket_list(params)
            serialized_tickets = [TicketResponse.model_validate(
                t).model_dump(mode='json') for t in db_tickets['tickets']]

            final_data = {
                'tickets': serialized_tickets,
                'total': db_tickets['total'],
                'page': db_tickets['page'],
                'page_size': db_tickets['page_size']
            }

            self.cache.set_ticket_list(
                current_user.id, params.model_dump_json(), final_data)

        return final_data

    def get_ticket_by_id(self, ticket_id: int, current_user: User) -> dict:
        ticket_data = self.cache.get_ticket(ticket_id)

        if ticket_data:
            author_id = ticket_data.get('author_id')
        else:
            found_ticket = self.check_ticket(
                self.ticket_repository.get_ticket_by_id(ticket_id)
            )
            author_id = found_ticket.author_id

            ticket_data = TicketResponse.model_validate(
                found_ticket).model_dump(mode='json')

            self.cache.set_ticket(ticket_id, ticket_data)

        if current_user.role != UserRole.ADMIN and author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )
        return ticket_data

    def appoint_an_executor(self, ticket_id: int, executor: User, current_user: User) -> Ticket:
        found_ticket = self.check_ticket(
            self.ticket_repository.get_ticket_by_id(ticket_id))
        self.check_by_admin(current_user)
        if executor.id == found_ticket.assignee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='The contractor has already been appointed for this application.'
            )
        if executor.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='The user cannot be an executor'
            )
        found_ticket.assignee_id = executor.id
        found_ticket.updated_at = utc_now()
        saved_ticket = self.ticket_repository.save_ticket(found_ticket)
        self.cache.invalidate_ticket_list()
        self.cache.delete_ticket(ticket_id)
        event_publisher = EventPublisher()
        event_publisher.publish_ticket_event(
            "EXECUTOR_WAS_APPOINTED", ticket_id, current_user.id)
        return saved_ticket

    def update_status(self, ticket_id: int, new_status: TicketStatus, current_user: User) -> Ticket:
        found_ticket = self.check_ticket(
            self.ticket_repository.get_ticket_by_id(ticket_id))
        old_status = found_ticket.status
        if new_status == old_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Status should be new'
            )
        self.check_by_admin(current_user)

        if found_ticket.status == TicketStatus.NEW:
            if new_status not in [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Not valid status'
                )
            if new_status == TicketStatus.CLOSED:
                found_ticket.closed_at = utc_now()
        elif found_ticket.status == TicketStatus.IN_PROGRESS:
            if new_status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Not valid status'
                )
            if new_status == TicketStatus.CLOSED:
                found_ticket.closed_at = utc_now()

        elif found_ticket.status == TicketStatus.RESOLVED:
            if new_status not in [TicketStatus.CLOSED, TicketStatus.IN_PROGRESS]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Not valid status'
                )
            if new_status == TicketStatus.CLOSED:
                found_ticket.closed_at = utc_now()

        elif found_ticket.status == TicketStatus.CLOSED:
            if new_status != TicketStatus.IN_PROGRESS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Not valid status'
                )
            if found_ticket.closed_at:
                found_ticket.closed_at = None

        history_data = StatusHistoryCreate(
            ticket_id=ticket_id,
            changed_by=current_user.id,
            old_status=old_status,
            new_status=new_status
        )
        self.statushistory_repository.create(history_data)

        found_ticket.status = new_status
        found_ticket.updated_at = utc_now()
        saved_ticket = self.ticket_repository.save_ticket(found_ticket)
        self.cache.invalidate_ticket_list()
        self.cache.delete_ticket(ticket_id)
        self.cache_statushistory.delete_status(ticket_id)
        event_publisher = EventPublisher()
        event_publisher.publish_ticket_event(
            "CHANGE_STATUS", ticket_id, current_user.id)
        return saved_ticket

    def update(self, ticket_id: int, data_for_update: TicketUpdateByUser | TicketUpdateByAdmin, current_user: User) -> Ticket:
        found_ticket = self.check_ticket(
            self.ticket_repository.get_ticket_by_id(ticket_id))

        if current_user.role != UserRole.ADMIN and isinstance(data_for_update, TicketUpdateByAdmin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )

        if current_user.role != UserRole.ADMIN and found_ticket.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )

        if current_user.role == UserRole.USER and found_ticket.status == TicketStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )

        if getattr(data_for_update, 'status', None) and current_user.role == UserRole.ADMIN:
            updated_ticket = self.update_status(
                ticket_id, data_for_update.status, current_user)
            data_for_update.status = None
            remainig_data = data_for_update.model_dump(
                exclude_unset=True, exclude_none=True)
            if not remainig_data:
                return updated_ticket
            data_for_update = TicketUpdateByAdmin(**remainig_data)

        updated_ticket = self.ticket_repository.update(
            ticket_id, data_for_update)
        self.cache.invalidate_ticket_list()
        self.cache.delete_ticket(ticket_id)
        return updated_ticket

    def update_priority(self, ticket_id: int, new_priority: TicketPriority, current_user: User) -> Ticket:
        found_ticket = self.check_ticket(
            self.ticket_repository.get_ticket_by_id(ticket_id))

        self.check_by_admin(current_user)

        found_ticket.priority = new_priority
        found_ticket.updated_at = utc_now()
        saved_ticket = self.ticket_repository.save_ticket(found_ticket)
        self.cache.invalidate_ticket_list()
        self.cache.delete_ticket(ticket_id)
        return saved_ticket

    def check_author(self, ticket_id: int, current_user: User) -> int:
        found_ticket = self.check_ticket(
            self.ticket_repository.get_ticket_by_id(ticket_id))
        self.check_by_admin(current_user)
        return found_ticket.author_id
