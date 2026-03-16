import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30,
                          description='User name')

    @field_validator('username')
    @classmethod
    def check_not_empty_space(cls, uname: str) -> str:
        if not uname.strip():
            raise ValueError("Поле не может состоять только из пробелов")
        if not USERNAME_PATTERN.fullmatch(uname):
            raise ValueError(
                "Username может содержать только буквы, цифры, _ и -"
            )
        return uname


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
