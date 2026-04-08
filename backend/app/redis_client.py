import redis

from app.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
    retry_on_timeout=False,
)
