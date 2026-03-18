from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional
from ..models.ticket import Ticket
from ..schemas.ticket import TicketCreate, TicketQueryParams, TicketUpdateByAdmin, TicketUpdateByUser


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, ticket_data: TicketCreate, author_id: int) -> Ticket:
        db_ticket = Ticket(**ticket_data.model_dump(), author_id=author_id)
        self.db.add(db_ticket)
        self.db.commit()
        self.db.refresh(db_ticket)
        return db_ticket

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def get_ticket_list(self, params: TicketQueryParams) -> dict[str, any]:
        query = self.db.query(Ticket)

        if params.status is not None:
            query = query.filter(Ticket.status == params.status)
        if params.priority is not None:
            query = query.filter(Ticket.priority == params.priority)
        if params.author_id is not None:
            query = query.filter(Ticket.author_id == params.author_id)
        if params.assignee_id is not None:
            query = query.filter(Ticket.assignee_id == params.assignee_id)
        if params.search:
            query = query.filter(
                or_(
                    Ticket.title.ilike(f'%{params.search}%'),
                    Ticket.description.ilike(f'%{params.search}%')
                )
            )

        total = query.count()

        if params.sort_by:
            if params.sort_by == 'created_at_asc':
                query = query.order_by(Ticket.created_at)
            elif params.sort_by == 'created_at_desc':
                query = query.order_by(Ticket.created_at.desc())
            elif params.sort_by == 'priority_asc':
                query = query.order_by(Ticket.priority)
            elif params.sort_by == 'priority_desc':
                query = query.order_by(Ticket.priority.desc())
            elif params.sort_by == 'updated_at_asc':
                query = query.order_by(Ticket.updated_at)
            elif params.sort_by == 'updated_at_desc':
                query = query.order_by(Ticket.updated_at.desc())

        query = query.offset((params.page - 1) *
                             params.page_size).limit(params.page_size)
        items = query.all()
        result = {'tickets': items, 'total': total,
                  'page': params.page, 'page_size': params.page_size}
        return result

    def update_ticket(self, ticket_id: int, data_for_update: TicketUpdateByUser | TicketUpdateByAdmin) -> Optional[Ticket]:
        db_ticket = self.db.query(Ticket).filter(
            Ticket.id == ticket_id).first()
        if not db_ticket:
            return None
        update_data = data_for_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_ticket, key, value)

        self.db.commit()
        self.db.refresh(db_ticket)

        return db_ticket
