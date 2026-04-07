import json

from app.redis_client import redis_client


class TicketCacheService:
    def get_ticket(self, ticket_id: int) -> dict | None:
        redis_key = f'ticket:{ticket_id}'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)

        return None

    def set_ticket(self, ticket_id: int, ticket_data: dict) -> None:
        redis_key = f'ticket:{ticket_id}'
        redis_client.setex(
            name=redis_key,
            time=60,
            value=json.dumps(ticket_data)
        )

    def get_ticket_list(self, user_id: int, params_json: str) -> dict | None:
        redis_key = f'ticket_list:user:{user_id}:params:{params_json}'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)

        return None

    def set_ticket_list(self, user_id: int, params_json: str, list_data: dict) -> None:
        redis_key = f'ticket_list:user:{user_id}:params:{params_json}'

        redis_client.setex(
            name=redis_key,
            time=60,
            value=json.dumps(list_data)
        )

    def invalidate_ticket_list(self):
        keys_to_delete = list(redis_client.scan_iter(match='ticket_list:*'))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)

    def delete_ticket(self, ticket_id: int) -> None:
        redis_client.delete(f'ticket:{ticket_id}')
