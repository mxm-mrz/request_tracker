

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func

from app.database import Base
from sqlalchemy.orm import relationship


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(ForeignKey('tickets.id'), nullable=False, index=True)
    author_id = Column(ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    ticket = relationship(
        'Ticket', back_populates='comments', foreign_keys=[ticket_id])
    author = relationship('User', back_populates='comments',
                          foreign_keys=[author_id])
