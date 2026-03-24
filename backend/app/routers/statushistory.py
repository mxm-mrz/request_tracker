from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.statushistory import StatusHistoryResponse
from app.models.user import User
from app.database import get_db
from app.services.statushistory_service import StatusHistoryService
from app.security import get_current_user


router = APIRouter(
    prefix='/api/statushistory',
    tags=['statushistory']
)


@router.get('/{ticket_id}/status_history', response_model=list[StatusHistoryResponse])
def get_statushistory_by_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    statushistory_service = StatusHistoryService(db)
    return statushistory_service.get_history(ticket_id, current_user)
