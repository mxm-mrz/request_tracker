import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.comment import CommentResponse
from app.schemas.statushistory import StatusHistoryResponse


class TicketBase(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=10, max_length=2000)

    @field_validator('description', 'title')
    @classmethod
    def check_not_empty_space(cls, desc: str) -> str:
        if desc is None:
            return desc
        if not desc.strip():
            raise ValueError("Поле не может состоять только из пробелов")
        return desc


class TicketCreate(TicketBase):
    pass


class TicketUpdateByUser(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)

    @field_validator('description', 'title')
    @classmethod
    def check_not_empty_space(cls, desc: str) -> str:
        if desc is None:
            return desc
        if not desc.strip():
            raise ValueError("Поле не может состоять только из пробелов")
        return desc


class TicketUpdateByAdmin(TicketUpdateByUser):
    status: Optional[TicketStatus] = Field(None)
    priority: Optional[TicketPriority] = Field(None)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketPriorityUpdate(BaseModel):
    priority: TicketPriority


class TicketAssigneeUpdate(BaseModel):
    assignee_id: int


class TicketQueryParams(BaseModel):
    page: Optional[int] = Field(1)
    page_size: Optional[int] = Field(10)
    search: Optional[str] = Field(None)
    status: Optional[TicketStatus] = Field(None)
    priority: Optional[TicketPriority] = Field(None)
    author_id: Optional[int] = Field(None)
    assignee_id: Optional[int] = Field(None)
    sort_by: Optional[Literal[
        "created_at_asc",
        "created_at_desc",
        "priority_asc",
        "priority_desc",
        "updated_at_asc",
        "updated_at_desc",
    ]] = Field(None)


class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    priority: TicketPriority
    author_id: int
    assignee_id: Optional[int] = Field(None)
    created_at: datetime.datetime
    updated_at: datetime.datetime
    closed_at: Optional[datetime.datetime] = Field(None)
    comments: list[CommentResponse] = Field(default_factory=list)
    statushistory: list[StatusHistoryResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int
