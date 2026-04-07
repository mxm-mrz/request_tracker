import json

from app.redis_client import redis_client


class UserCacheService:
    def get_profile(self, user_id: int):
        redis_key = f'user:{user_id}'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)
        return None

    def set_profile(self, user_id: int, profile_data: dict):
        redis_key = f'user:{user_id}'
        redis_client.setex(
            name=redis_key,
            time=60,
            value=json.dumps(profile_data)
        )

    def get_admin_list(self):
        redis_key = 'admin_list'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)
        return None

    def set_admin_list(self, admin_list: list):
        redis_key = f'admin_list'

        redis_client.setex(
            name=redis_key,
            time=60,
            value=json.dumps(admin_list)
        )
