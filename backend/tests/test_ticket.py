from app.models.user import User, UserRole


def test_create_ticket_user_was_logined(client):
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

    create_ticket_response = client.post('/api/ticket/create_ticket',
                                         headers={
                                             'Authorization': f'Bearer {token}'},
                                         json={
                                             "title": "Ticket 1",
                                             "description": "Test create ticket"
                                         })
    assert create_ticket_response.status_code == 201
    ticket_data = create_ticket_response.json()
    assert ticket_data['title'] == 'Ticket 1'
    assert ticket_data['description'] == 'Test create ticket'
    assert 'id' in ticket_data
    assert ticket_data['status'] == 'new'
    assert 'author_id' in ticket_data
    assert 'assignee_id' in ticket_data
    assert 'created_at' in ticket_data
    assert 'updated_at' in ticket_data
    assert 'closed_at' in ticket_data


def test_reject_create_and_read_ticket_without_authorization(client):
    create_ticket_response = client.post('/api/ticket/create_ticket',
                                         json={
                                             "title": "Ticket 1",
                                             "description": "Test create ticket"
                                         })
    assert create_ticket_response.status_code == 401

    read_ticket_response = client.get('/api/ticket/1')

    assert read_ticket_response.status_code == 401


def test_user_can_see_only_own_tickets(client):
    # 1. Создаем Юзера 1
    client.post('/api/auth/registration', json={
        "email": "user1@example.com",
        "username": "user1",
        "password": "password123"
    })

    # 2. Создаем Юзера 2
    client.post('/api/auth/registration', json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "password123"
    })

    # 3. Логиним Юзера 1 и получаем его токен
    login_res1 = client.post('/api/auth/login', data={
        "username": "user1",
        "password": "password123"
    })
    token1 = login_res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 4. Логиним Юзера 2 и получаем его токен
    login_res2 = client.post('/api/auth/login', data={
        "username": "user2",
        "password": "password123"
    })
    token2 = login_res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 5. Создаем 1 тикет от имени Юзера 1 (С жесткой проверкой)
    create_res1 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket User 1",
        "description": "Test create ticket"
    }, headers=headers1)
    # Если сервер не вернет 201, pytest распечатает причину из .json()
    assert create_res1.status_code == 201, f"Ошибка создания Юзером 1: {create_res1.json()}"

    # 6. Создаем 2 тикета от имени Юзера 2
    create_res2_1 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket 1 User 2",
        "description": "Test create ticket"
    }, headers=headers2)
    assert create_res2_1.status_code == 201, f"Ошибка создания Юзером 2 (тикет 1): {create_res2_1.json()}"

    create_res2_2 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket 2 User 2",
        "description": "Test create ticket"
    }, headers=headers2)
    assert create_res2_2.status_code == 201, f"Ошибка создания Юзером 2 (тикет 2): {create_res2_2.json()}"

    # 7. Запрашиваем список тикетов от лица Юзера 1
    list_res1 = client.get('/api/ticket/tickets_list', headers=headers1)
    assert list_res1.status_code == 200

    data1 = list_res1.json()

    # ПРОВЕРКА: Юзер 1 должен получить строго 1 тикет
    # Обращаемся к списку внутри ключа 'tickets' и проверяем счетчик 'total'
    assert data1["total"] == 1
    assert len(data1["tickets"]) == 1
    assert "Ticket User 1" in [ticket["title"] for ticket in data1["tickets"]]

    # 8. Запрашиваем список тикетов от лица Юзера 2
    list_res2 = client.get('/api/ticket/tickets_list', headers=headers2)
    assert list_res2.status_code == 200

    data2 = list_res2.json()

    # ПРОВЕРКА: Юзер 2 должен получить строго 2 тикета
    assert data2["total"] == 2
    assert len(data2["tickets"]) == 2


def test_admin_can_see_all_tickets(client, db_session):

    client.post('/api/auth/registration', json={
        "email": "admin@example.com",
        "username": "admin",
        "password": "password123"
    })

    admin_user = db_session.query(User).filter(
        User.username == 'admin').first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()

    client.post('/api/auth/registration', json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "password123"
    })

    login_admin = client.post('/api/auth/login', data={
        "username": "admin",
        "password": "password123"
    })
    token_admin = login_admin.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token_admin}"}

    login_res2 = client.post('/api/auth/login', data={
        "username": "user2",
        "password": "password123"
    })
    token2 = login_res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    create_res1 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket Admin 1",
        "description": "Test create ticket"
    }, headers=headers1)

    assert create_res1.status_code == 201, f"Ошибка создания Юзером 1: {create_res1.json()}"

    create_res2_1 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket 1 User 2",
        "description": "Test create ticket"
    }, headers=headers2)
    assert create_res2_1.status_code == 201, f"Ошибка создания Юзером 2 (тикет 1): {create_res2_1.json()}"

    create_res2_2 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket 2 User 2",
        "description": "Test create ticket"
    }, headers=headers2)
    assert create_res2_2.status_code == 201, f"Ошибка создания Юзером 2 (тикет 2): {create_res2_2.json()}"

    list_admin = client.get('/api/ticket/tickets_list', headers=headers1)
    assert list_admin.status_code == 200

    data1 = list_admin.json()

    assert data1["total"] == 3
    assert len(data1["tickets"]) == 3
    assert "Ticket Admin 1" in [ticket["title"] for ticket in data1["tickets"]]

    list_res2 = client.get('/api/ticket/tickets_list', headers=headers2)
    assert list_res2.status_code == 200

    data2 = list_res2.json()

    assert data2["total"] == 2
    assert len(data2["tickets"]) == 2


def test_admin_can_change_status(client, db_session):
    client.post('/api/auth/registration', json={
        "email": "admin@example.com",
        "username": "admin",
        "password": "password123"
    })

    admin_user = db_session.query(User).filter(
        User.username == 'admin').first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()

    client.post('/api/auth/registration', json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "password123"
    })

    login_admin = client.post('/api/auth/login', data={
        "username": "admin",
        "password": "password123"
    })
    token_admin = login_admin.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token_admin}"}

    create_res1 = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket Admin 1",
        "description": "Test create ticket"
    }, headers=headers1)

    assert create_res1.status_code == 201, f"Ошибка создания Юзером 1: {create_res1.json()}"
    ticket_id = create_res1.json()['id']
    update_ticket_status = client.patch(f'/api/ticket/{ticket_id}/status',
                                        headers=headers1,
                                        json='in_progress')
    assert update_ticket_status.status_code == 200, f"Ошибка обновления: {update_ticket_status.json()}"
    assert update_ticket_status.json()['status'] == 'in_progress'


def test_user_cant_change_status(client):
    client.post('/api/auth/registration', json={
        "email": "user2@example.com",
        "username": "user",
        "password": "password123"
    })

    login_res = client.post('/api/auth/login', data={
        "username": "user",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post('/api/ticket/create_ticket', json={
        "title": "Ticket User 1",
        "description": "Test create ticket"
    }, headers=headers)

    assert create_res.status_code == 201, f"Ошибка создания Юзером 1: {create_res.json()}"
    ticket_id = create_res.json()['id']
    update_ticket_status = client.patch(f'/api/ticket/{ticket_id}/status',
                                        headers=headers,
                                        json='in_progress')
    assert update_ticket_status.status_code == 403, f"Ошибка обновления: {update_ticket_status.json()}"
