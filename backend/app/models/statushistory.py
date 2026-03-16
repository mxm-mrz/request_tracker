from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.ticket import TicketStatus


class StatusHistory(Base):
    __tablename__ = 'statushistory'

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(ForeignKey('tickets.id'), nullable=False, index=True)
    changed_by = Column(ForeignKey('users.id'), nullable=False)
    old_status = Column(Enum(TicketStatus), nullable=True)
    new_status = Column(Enum(TicketStatus), nullable=False)
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)

    ticket = relationship(
        'Ticket', back_populates='statushistory', foreign_keys=[ticket_id])
    changed_user = relationship(
        'User', back_populates='statushistory', foreign_keys=[changed_by])
