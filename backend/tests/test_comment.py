from app.models.user import User, UserRole


def test_create_comment(client):
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

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_ticket_response = client.post('/api/ticket/create_ticket',
                                         headers={
                                             'Authorization': f'Bearer {token}'},
                                         json={
                                             "title": "Ticket 1",
                                             "description": "Test create ticket"
                                         })

    assert create_ticket_response.status_code == 201
    ticket_id = create_ticket_response.json()['id']
    add_comment_response = client.post(f'/api/comment/{ticket_id}/comments',
                                       headers=headers,
                                       json={
                                           "content": "New comment"
    })

    assert add_comment_response.status_code == 200, f"Ошибка обновления: {add_comment_response.json()}"
    assert add_comment_response.json()['content'] == 'New comment'


# Не забудь импортировать нужные модели, статусы и перечисления ролей
# from app.models.user import User
# from app.models.enums import UserRole

def test_ticket_author_and_admin_can_comment(client, db_session):
    """Тест 200: Автор и Админ могут оставлять комментарии"""
    # 1. Подготовка: Создаем Юзера 1 и Админа, выдаем права
    client.post('/api/auth/registration',
                json={"email": "user1@example.com", "username": "user1", "password": "joker6198"})
    client.post('/api/auth/registration',
                json={"email": "admin@example.com", "username": "admin", "password": "joker6198"})

    admin_user = db_session.query(User).filter(
        User.username == 'admin').first()
    admin_user.role = UserRole.ADMIN  # Используй свой вариант Enum или строки
    db_session.commit()

    # 2. Логины
    token_user1 = client.post(
        '/api/auth/login', data={"username": "user1", "password": "joker6198"}).json()["access_token"]
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}

    token_admin = client.post(
        '/api/auth/login', data={"username": "admin", "password": "joker6198"}).json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 3. Юзер 1 создает тикет
    create_ticket_res = client.post('/api/ticket/create_ticket', json={
        "title": "Access Ticket", "description": "Test description long enough"
    }, headers=headers_user1)
    ticket_id = create_ticket_res.json()["id"]

    # 4. Проверка: Юзер 1 оставляет коммент на свой тикет
    comment_res_user = client.post(f'/api/comment/{ticket_id}/comments', json={
        "content": "Comment from author"
    }, headers=headers_user1)

    assert comment_res_user.status_code == 200, f"Ошибка коммента автора: {comment_res_user.json()}"
    assert comment_res_user.json()["content"] == "Comment from author"

    # 5. Проверка: Админ оставляет коммент на тикет Юзера 1
    comment_res_admin = client.post(f'/api/comment/{ticket_id}/comments', json={
        "content": "Comment from admin"
    }, headers=headers_admin)

    assert comment_res_admin.status_code == 200, f"Ошибка коммента админа: {comment_res_admin.json()}"


def test_other_user_cannot_comment_on_foreign_ticket(client):
    """Тест 403: Чужой юзер не может оставить комментарий"""
    # 1. Подготовка: Юзер 1 и Юзер 2
    client.post('/api/auth/registration',
                json={"email": "user1@example.com", "username": "user1", "password": "joker6198"})
    client.post('/api/auth/registration',
                json={"email": "user2@example.com", "username": "user2", "password": "joker6198"})

    token_user1 = client.post(
        '/api/auth/login', data={"username": "user1", "password": "joker6198"}).json()["access_token"]
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}

    token_user2 = client.post(
        '/api/auth/login', data={"username": "user2", "password": "joker6198"}).json()["access_token"]
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}

    # 2. Юзер 1 создает тикет
    create_ticket_res = client.post('/api/ticket/create_ticket', json={
        "title": "Private Ticket", "description": "Test description long enough"
    }, headers=headers_user1)
    ticket_id = create_ticket_res.json()["id"]

    # 3. Проверка: Юзер 2 пытается оставить коммент на тикет Юзера 1
    comment_res_user2 = client.post(f'/api/comment/{ticket_id}/comments', json={
        "content": "Hacker comment"
    }, headers=headers_user2)

    # Замени 403 на 404, если твой роутер отдает Not Found
    # Прямо внутри твоего assert:
    assert comment_res_user2.status_code == 403, f"Ошибка: {comment_res_user2.json()}"
