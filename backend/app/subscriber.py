import redis
from app.config import settings

subscriber_redis = redis.from_url(settings.REDIS_URL)
pubsub = subscriber_redis.pubsub()
pubsub.subscribe('ticket_events')

for message in pubsub.listen():
    if message['type'] == 'message':
        print(message['data'])
