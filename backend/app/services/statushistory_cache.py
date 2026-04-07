import json

from app.redis_client import redis_client


class StatusHistoryCacheService:
    def get_status(self, ticket_id: int):
        redis_key = f'history:ticket:{ticket_id}'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)
        return None

    def set_status(self, ticket_id: int, new_status):
        redis_key = f'history:ticket:{ticket_id}'
        redis_client.setex(
            name=redis_key,
            time=200,
            value=json.dumps(new_status)
        )

    def delete_status(self, ticket_id):
        redis_key = f'history:ticket:{ticket_id}'
        redis_client.delete(redis_key)
