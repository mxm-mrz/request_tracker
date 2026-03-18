from sqlalchemy.orm import Session

from ..models.statushistory import StatusHistory
from ..schemas.statushistory import StatusHistoryCreate


class StatusHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, statushistory_data: StatusHistoryCreate) -> StatusHistory:
        db_statushistory = StatusHistory(**statushistory_data.model_dump())
        self.db.add(db_statushistory)
        self.db.commit()
        self.db.refresh(db_statushistory)
        return db_statushistory

    def get_status_by_ticket(self, ticket_id: int) -> list[StatusHistory]:
        return self.db.query(StatusHistory).filter(StatusHistory.ticket_id == ticket_id).all()
