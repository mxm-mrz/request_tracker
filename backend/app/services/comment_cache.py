import json

from app.redis_client import redis_client


class CommentCacheService:
    def get_comments(self, ticket_id: int):
        redis_key = f'comments:ticket:{ticket_id}'
        cached_data = redis_client.get(redis_key)

        if cached_data:
            return json.loads(cached_data)
        return None

    def set_comments(self, ticket_id: int, comment_list):
        redis_key = f'comments:ticket:{ticket_id}'
        redis_client.setex(
            name=redis_key,
            time=200,
            value=json.dumps(comment_list)
        )

    def delete_comments(self, ticket_id):
        redis_key = f'comments:ticket:{ticket_id}'
        redis_client.delete(redis_key)
