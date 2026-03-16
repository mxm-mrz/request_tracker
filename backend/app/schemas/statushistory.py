import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ticket import TicketStatus


class StatusHistoryResponse(BaseModel):
    id: int
    changed_by: int
    old_status: Optional[TicketStatus] = Field(None)
    new_status: TicketStatus
    changed_at: Optional[datetime.datetime] = Field(None)

    class Config:
        from_attributes = True
