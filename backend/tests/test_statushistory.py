from app.models.user import User, UserRole
from app.models.ticket import TicketStatus


def test_author_and_admin_can_read_status_history(client, db_session):
    """Тест 200: Автор и Админ могут читать историю статусов тикета"""
    # 1. Подготовка: Создаем Юзера 1 и Админа
    client.post('/api/auth/registration',
                json={"email": "author@example.com", "username": "author", "password": "joker6198"})
    client.post('/api/auth/registration',
                json={"email": "admin@example.com", "username": "admin", "password": "joker6198"})

    admin_user = db_session.query(User).filter(
        User.username == 'admin').first()
    admin_user.role = UserRole.ADMIN
    db_session.commit()

    # 2. Логины
    token_author = client.post(
        '/api/auth/login', data={"username": "author", "password": "joker6198"}).json()["access_token"]
    headers_author = {"Authorization": f"Bearer {token_author}"}

    token_admin = client.post(
        '/api/auth/login', data={"username": "admin", "password": "joker6198"}).json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 3. Юзер 1 (автор) создает тикет
    create_ticket_res = client.post('/api/ticket/create_ticket', json={
        "title": "History Ticket", "description": "Testing status history"
    }, headers=headers_author)
    ticket_id = create_ticket_res.json()["id"]

    # 4. Меняем статус тикета (с жесткой проверкой)
    patch_res = client.patch(
        f'/api/ticket/{ticket_id}/status',
        json=TicketStatus.IN_PROGRESS.value,
        headers=headers_admin
    )
    assert patch_res.status_code == 200, f"Ошибка обновления статуса: {patch_res.json()}"

    # 5. Проверка: Автор читает историю своего тикета
    history_res_author = client.get(
        f'/api/statushistory/{ticket_id}/status_history', headers=headers_author)

    assert history_res_author.status_code == 200, f"Ошибка истории для автора: {history_res_author.json()}"

    history_data = history_res_author.json()

    # Проверяем длину
    assert len(
        history_data) == 1, f"Ожидалась 1 запись, получено: {len(history_data)}"

    # Проверяем, что последний статус в истории действительно IN_PROGRESS (используем правильный ключ new_status)
    assert history_data[-1]["new_status"] == TicketStatus.IN_PROGRESS.value

    # 6. Проверка: Админ читает историю тикета Юзера 1
    history_res_admin = client.get(
        f'/api/statushistory/{ticket_id}/status_history', headers=headers_admin)

    assert history_res_admin.status_code == 200, f"Ошибка истории для админа: {history_res_admin.json()}"

    admin_history_data = history_res_admin.json()
    assert len(admin_history_data) == 1
    assert admin_history_data[-1]["new_status"] == TicketStatus.IN_PROGRESS.value


def test_other_user_cannot_read_foreign_ticket_history(client):
    """Тест 403/404: Чужой юзер не может прочитать историю статусов чужого тикета"""
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
        "title": "Private History Ticket", "description": "Testing status history privacy"
    }, headers=headers_user1)
    ticket_id = create_ticket_res.json()["id"]

    # 3. Проверка: Юзер 2 пытается прочитать историю чужого тикета
    history_res_user2 = client.get(
        f'/api/statushistory/{ticket_id}/status_history', headers=headers_user2)

    # Если твой роутер отдает 404 Not Found при отсутствии прав, поменяй 403 на 404
    assert history_res_user2.status_code in [
        403, 404], f"Ожидался отказ (403/404), получено: {history_res_user2.status_code}"
