from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import user_router, ticket_router, comment_router, auth_router, statushistory_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(user_router)
app.include_router(ticket_router)
app.include_router(comment_router)
app.include_router(auth_router)
app.include_router(statushistory_router)


@app.get('/')
def root():
    return {
        'message': 'Welcome to request tracker API',
        'docs': '/docs'
    }
