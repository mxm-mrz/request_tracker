from fastapi import HTTPException, status

from app.redis_client import redis_client


class TokenBlacklistService:
    def add_to_blacklist(self, jti: str, expire_time: int):
        try:
            redis_client.setex(
                name=f'blacklist:{jti}',
                time=expire_time,
                value=1
            )
        except Exception as e:
            print(f"Ошибка Redis (add_to_blacklist): {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Service Unavailable',
            )

    def is_jti_blacklisted(self, jti: str) -> bool:
        try:
            cached_data = redis_client.get(f'blacklist:{jti}')

            if cached_data:
                return True

            return False
        except Exception as e:
            print(f"Ошибка Redis (is_jti_blacklisted): {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Service Unavailable',
            )
