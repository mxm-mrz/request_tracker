from sqlalchemy.orm import Session

from ..models.comment import Comment
from ..schemas.comment import CommentCreate


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, ticket_id: int, comment_data: CommentCreate, author_id: int) -> Comment:
        db_comment = Comment(**comment_data.model_dump(),
                             author_id=author_id, ticket_id=ticket_id)
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return db_comment

    def get_comment_by_ticket(self, ticket_id: int) -> list[Comment]:
        return self.db.query(Comment).filter(Comment.ticket_id == ticket_id).all()
