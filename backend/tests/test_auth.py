
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
