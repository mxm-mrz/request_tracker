from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.schemas.ticket import TicketCreate, TicketListResponse, TicketQueryParams, TicketResponse, TicketUpdateByAdmin, TicketUpdateByUser
from app.database import get_db
from app.services.ticket_service import TicketService
from app.models.user import User
from app.security import get_current_admin_user, get_current_user
from app.models.ticket import TicketPriority, TicketStatus
from app.services.user_service import UserService


router = APIRouter(
    prefix='/api/ticket',
    tags=['ticket']
)


@router.post('/create_ticket', response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create(ticket_data: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.create(ticket_data, current_user.id)


@router.get('/tickets_list', response_model=TicketListResponse)
def get_ticket_list(params: TicketQueryParams = Depends(), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.get_ticket_list(params, current_user)


@router.put('/{ticket_id}', response_model=TicketResponse)
def update(ticket_id: int, data_for_update: TicketUpdateByUser | TicketUpdateByAdmin, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.update(ticket_id, data_for_update, current_user)


@router.patch('/{ticket_id}/appoint_an_executor', response_model=TicketResponse)
def appoint_an_executor(ticket_id: int, executor_id: int = Body(...), current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    user_service = UserService(db)
    executor = user_service.get_profile_by_user(executor_id)
    return ticket_service.appoint_an_executor(ticket_id, executor, current_user)


@router.patch('/{ticket_id}/status', response_model=TicketResponse)
def update_status(ticket_id: int, new_status: TicketStatus = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.update_status(ticket_id, new_status, current_user)


@router.patch('/{ticket_id}/priority', response_model=TicketResponse)
def update_priority(ticket_id: int, new_priority: TicketPriority = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.update_priority(ticket_id, new_priority, current_user)


@router.get('/{ticket_id}', response_model=TicketResponse)
def get_ticket_by_id(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket_service = TicketService(db)
    return ticket_service.get_ticket_by_id(ticket_id, current_user)
