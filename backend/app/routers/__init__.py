from app.routers.user import router as user_router
from app.routers.ticket import router as ticket_router
from app.routers.comment import router as comment_router
from app.routers.auth import router as auth_router
from app.routers.statushistory import router as statushistory_router

__all__ = ['user_router', 'ticket_router',
           'comment_router', 'auth_router', 'statushistory_router']
