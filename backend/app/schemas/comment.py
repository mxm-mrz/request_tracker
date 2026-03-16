import datetime

from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
    ticket_id: int
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator('content')
    @classmethod
    def check_not_empty_space(cls, desc: str) -> str:
        if not desc.strip():
            raise ValueError("Поле не может состоять только из пробелов")
        return desc


class CommentResponse(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
