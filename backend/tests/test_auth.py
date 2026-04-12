import app.services.blacklist_service as blacklist_service_module


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, name: str):
        return self.store.get(name)

    def setex(self, name: str, time: int, value):
        self.store[name] = value


def test_user_registration(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True


def test_duble_user_registration(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True

    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 400


def test_login(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True

    login_response = client.post('/api/auth/login',
                                 data={
                                     'username': 'test',
                                     'password': 'joker6198'
                                 })

    assert login_response.status_code == 200


def test_login_wrong_password(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True

    login_response = client.post('/api/auth/login',
                                 data={
                                     'username': 'test',
                                     'password': 'joker61981'
                                 })

    assert login_response.status_code == 401


def test_auth_me(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True

    login_response = client.post('/api/auth/login',
                                 data={
                                     'username': 'test',
                                     'password': 'joker6198'
                                 })

    assert login_response.status_code == 200

    data = login_response.json()
    token = data['access_token']
    token_response = client.get(
        '/api/auth/me', headers={'Authorization': f'Bearer {token}'})

    assert token_response.status_code == 200


def test_auth_me_without_token(client):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    data = response.json()
    assert data['email'] == 'test@example.com'
    assert data['username'] == 'test'
    assert 'id' in data
    assert 'role' in data
    assert data['is_active'] == True

    login_response = client.post('/api/auth/login',
                                 data={
                                     'username': 'test',
                                     'password': 'joker6198'
                                 })

    assert login_response.status_code == 200

    token_response = client.get('/api/auth/me')

    assert token_response.status_code == 401


def test_logout_blacklists_token(client, monkeypatch):
    response = client.post('/api/auth/registration',
                           json={
                               "email": "test@example.com",
                               "username": "test",
                               "password": "joker6198"
                           })

    assert response.status_code == 201

    login_response = client.post('/api/auth/login',
                                 data={
                                     'username': 'test',
                                     'password': 'joker6198'
                                 })

    assert login_response.status_code == 200

    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    fake_redis = FakeRedis()
    monkeypatch.setattr(blacklist_service_module, 'redis_client', fake_redis)

    me_response = client.get('/api/auth/me', headers=headers)
    assert me_response.status_code == 200

    logout_response = client.post('/api/auth/logout', headers=headers)
    assert logout_response.status_code == 200

    assert any(key.startswith('blacklist:') for key in fake_redis.store)

    me_after_logout_response = client.get('/api/auth/me', headers=headers)
    assert me_after_logout_response.status_code == 401
