import json

from app.redis_client import redis_client


class TicketCacheService:
    def get_ticket(self, ticket_id: int) -> dict | None:
        redis_key = f'ticket:{ticket_id}'
        try:
            cached_data = redis_client.get(redis_key)

            if cached_data:
                return json.loads(cached_data)

            return None
        except Exception as e:
            print(f"Ошибка Redis (get_ticket): {e}")
            return None

    def set_ticket(self, ticket_id: int, ticket_data: dict) -> None:
        redis_key = f'ticket:{ticket_id}'
        try:
            redis_client.setex(
                name=redis_key,
                time=60,
                value=json.dumps(ticket_data)
            )
        except Exception as e:
            print(f"Ошибка Redis (set_ticket): {e}")

    def get_ticket_list(self, user_id: int, params_json: str) -> dict | None:
        redis_key = f'ticket_list:user:{user_id}:params:{params_json}'
        try:
            cached_data = redis_client.get(redis_key)

            if cached_data:
                return json.loads(cached_data)

            return None
        except Exception as e:
            print(f"Ошибка Redis (get_ticket_list): {e}")
            return None

    def set_ticket_list(self, user_id: int, params_json: str, list_data: dict) -> None:
        redis_key = f'ticket_list:user:{user_id}:params:{params_json}'
        try:
            redis_client.setex(
                name=redis_key,
                time=60,
                value=json.dumps(list_data)
            )
        except Exception as e:
            print(f"Ошибка Redis (set_ticket_list): {e}")

    def invalidate_ticket_list(self):
        try:
            keys_to_delete = list(
                redis_client.scan_iter(match='ticket_list:*'))
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
        except Exception as e:
            print(f"Ошибка Redis (invalidate_ticket_list): {e}")

    def delete_ticket(self, ticket_id: int) -> None:
        try:
            redis_client.delete(f'ticket:{ticket_id}')
        except Exception as e:
            print(f"Ошибка Redis (delete_ticket): {e}")
