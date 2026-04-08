from fastapi import HTTPException, status

from app.redis_client import redis_client


class RateLimitService:
    def check_limit(self, key: str, limit: int, window: int):
        try:
            current_request = redis_client.incr(key)

            if current_request == 1:
                redis_client.expire(key, window)

            if current_request > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail='Too Many Requests'
                )
        except Exception as e:
            print(f"Ошибка Redis (rate_limit): {e}")
