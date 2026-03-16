
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class TicketStatus(enum.Enum):
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class TicketPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(TicketStatus),
                    default=TicketStatus.NEW, nullable=False)
    priority = Column(Enum(TicketPriority),
                      default=TicketPriority.MEDIUM, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assignee_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)
    closed_at = Column(DateTime, nullable=True, default=None)

    authors = relationship('User', back_populates='ticket_authors',
                           foreign_keys=[author_id])
    assignees = relationship(
        'User', back_populates='ticket_assignees', foreign_keys=[assignee_id])
    comments = relationship('Comment', back_populates='ticket')
    statushistory = relationship('StatusHistory', back_populates='ticket')
