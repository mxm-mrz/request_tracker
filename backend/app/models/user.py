import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(enum.Enum):
    USER = 'user'
    ADMIN = 'admin'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    ticket_authors = relationship(
        'Ticket', back_populates='authors', foreign_keys='Ticket.author_id')
    ticket_assignees = relationship(
        'Ticket', back_populates='assignees', foreign_keys='Ticket.assignee_id')
    comments = relationship('Comment', back_populates='author')
    statushistory = relationship(
        'StatusHistory', back_populates='changed_user')
