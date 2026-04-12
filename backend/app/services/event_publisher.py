from datetime import datetime, timezone
import json

from app.redis_client import redis_client


class EventPublisher:
    def publish_ticket_event(self, event_type: str, ticket_id: int, user_id: int):
        try:
            pre_dict = {
                'event_type': event_type,
                'ticket_id': ticket_id,
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            payload = json.dumps(pre_dict)
            redis_client.publish('ticket_events', payload)
        except Exception as e:
            print(f"Ошибка Redis (publish_ticket_event): {e}")
