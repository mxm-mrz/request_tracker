from fnmatch import fnmatch

from app.models.user import User, UserRole
from app.services.comment_cache import CommentCacheService
from app.services.statushistory_cache import StatusHistoryCacheService
from app.services.ticket_cache import TicketCacheService
from app.services.user_service import UserService
import app.services.comment_cache as comment_cache_module
import app.services.statushistory_cache as statushistory_cache_module
import app.services.ticket_cache as ticket_cache_module
import app.services.user_cache as user_cache_module


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}
        self.setex_calls: list[tuple[str, int, str]] = []

    def get(self, name: str):
        return self.store.get(name)

    def setex(self, name: str, time: int, value: str):
        self.store[name] = value
        self.setex_calls.append((name, time, value))

    def delete(self, *names: str):
        deleted = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                deleted += 1
        return deleted

    def scan_iter(self, match: str | None = None):
        for key in list(self.store.keys()):
            if match is None or fnmatch(key, match):
                yield key


class BrokenRedis:
    def get(self, name: str):
        raise RuntimeError("redis unavailable")

    def setex(self, name: str, time: int, value: str):
        raise RuntimeError("redis unavailable")

    def delete(self, *names: str):
        raise RuntimeError("redis unavailable")

    def scan_iter(self, match: str | None = None):
        raise RuntimeError("redis unavailable")


def test_ticket_cache_roundtrip_and_invalidate_list(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(ticket_cache_module, "redis_client", fake_redis)
    service = TicketCacheService()

    ticket_data = {"id": 1, "title": "Broken export"}
    ticket_list = {"tickets": [ticket_data],
                   "total": 1, "page": 1, "page_size": 10}
    params_json = '{"page":1,"page_size":10}'

    service.set_ticket(1, ticket_data)
    service.set_ticket_list(7, params_json, ticket_list)

    assert service.get_ticket(1) == ticket_data
    assert service.get_ticket_list(7, params_json) == ticket_list
    assert fake_redis.setex_calls[0][1] == 60
    assert fake_redis.setex_calls[1][1] == 60

    service.invalidate_ticket_list()

    assert service.get_ticket(1) == ticket_data
    assert service.get_ticket_list(7, params_json) is None

    service.delete_ticket(1)
    assert service.get_ticket(1) is None


def test_comment_cache_roundtrip_and_delete(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(comment_cache_module, "redis_client", fake_redis)
    service = CommentCacheService()

    comments = [
        {"id": 1, "content": "First comment"},
        {"id": 2, "content": "Second comment"},
    ]

    service.set_comments(12, comments)

    assert service.get_comments(12) == comments
    assert fake_redis.setex_calls[0][1] == 200

    service.delete_comments(12)
    assert service.get_comments(12) is None


def test_statushistory_cache_roundtrip_and_delete(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(statushistory_cache_module, "redis_client", fake_redis)
    service = StatusHistoryCacheService()

    history = [
        {"old_status": "new", "new_status": "in_progress"},
        {"old_status": "in_progress", "new_status": "resolved"},
    ]

    service.set_status(33, history)

    assert service.get_status(33) == history
    assert fake_redis.setex_calls[0][1] == 200

    service.delete_status(33)
    assert service.get_status(33) is None


def test_user_service_admin_list_uses_cache(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(user_cache_module, "redis_client", fake_redis)

    service = UserService(db=None)

    admin_1 = User(
        id=1,
        email="admin1@example.com",
        username="admin1",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    admin_2 = User(
        id=2,
        email="admin2@example.com",
        username="admin2",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )

    calls = {"count": 0}

    def fake_get_admin_list():
        calls["count"] += 1
        return [admin_1, admin_2]

    service.repository.get_admin_list = fake_get_admin_list

    first_result = service.get_admin_list()
    second_result = service.get_admin_list()

    assert calls["count"] == 1
    assert first_result == second_result
    assert first_result[0]["username"] == "admin1"
    assert first_result[1]["username"] == "admin2"
    assert fake_redis.setex_calls[0][0] == "admin_list"
    assert fake_redis.setex_calls[0][1] == 60


def test_user_cache_profile_roundtrip(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(user_cache_module, "redis_client", fake_redis)

    cache = user_cache_module.UserCacheService()
    profile_data = {
        "id": 11,
        "email": "user11@example.com",
        "username": "user11",
        "role": "user",
        "is_active": True,
    }

    cache.set_profile(11, profile_data)

    assert cache.get_profile(11) == profile_data
    assert fake_redis.setex_calls[0][0] == "user:11"
    assert fake_redis.setex_calls[0][1] == 60


def test_ticket_cache_degrades_gracefully_when_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(ticket_cache_module, "redis_client", BrokenRedis())
    service = TicketCacheService()

    assert service.get_ticket(1) is None
    assert service.get_ticket_list(5, '{"page":1}') is None

    service.set_ticket(1, {"id": 1, "title": "Broken export"})
    service.set_ticket_list(
        5, '{"page":1}', {"tickets": [], "total": 0, "page": 1, "page_size": 10})
    service.invalidate_ticket_list()
    service.delete_ticket(1)


def test_user_service_returns_admins_from_repository_when_cache_is_unavailable(monkeypatch):
    monkeypatch.setattr(user_cache_module, "redis_client", BrokenRedis())

    service = UserService(db=None)

    admin_1 = User(
        id=1,
        email="admin1@example.com",
        username="admin1",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    admin_2 = User(
        id=2,
        email="admin2@example.com",
        username="admin2",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )

    calls = {"count": 0}

    def fake_get_admin_list():
        calls["count"] += 1
        return [admin_1, admin_2]

    service.repository.get_admin_list = fake_get_admin_list

    result = service.get_admin_list()

    assert calls["count"] == 1
    assert [user["username"] for user in result] == ["admin1", "admin2"]


def test_comment_and_history_cache_degrade_gracefully_when_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(comment_cache_module, "redis_client", BrokenRedis())
    monkeypatch.setattr(statushistory_cache_module,
                        "redis_client", BrokenRedis())

    comment_cache = CommentCacheService()
    history_cache = StatusHistoryCacheService()

    assert comment_cache.get_comments(12) is None
    comment_cache.set_comments(12, [{"id": 1, "content": "First comment"}])
    comment_cache.delete_comments(12)

    assert history_cache.get_status(33) is None
    history_cache.set_status(
        33, [{"old_status": "new", "new_status": "in_progress"}])
    history_cache.delete_status(33)
