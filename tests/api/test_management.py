from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin-pass-123"


def _admin_headers() -> dict:
    reg = client.post('/auth/register', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
    if reg.status_code == 200:
        token = reg.json()['access_token']
    else:
        login = client.post('/auth/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
        assert login.status_code == 200
        token = login.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_management_requires_admin():
    unauthorized = client.get('/management/overview')
    assert unauthorized.status_code in (401, 403)


def test_management_overview_and_agents_admin():
    headers = _admin_headers()

    overview = client.get('/management/overview', headers=headers)
    assert overview.status_code == 200
    assert 'embedding_model' in overview.json()

    agents = client.get('/management/agents', headers=headers)
    assert agents.status_code == 200
    assert agents.json()['entrypoint'] == 'language_agent'


def test_management_rag_config_update_admin():
    headers = _admin_headers()

    current = client.get('/management/rag/config', headers=headers)
    assert current.status_code == 200
    old = current.json()

    updated = client.patch('/management/rag/config', json={'retrieval_top_k': 6}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()['retrieval_top_k'] == 6

    restore = client.patch('/management/rag/config', json={'retrieval_top_k': old['retrieval_top_k']}, headers=headers)
    assert restore.status_code == 200


def test_admin_users_management_by_id():
    headers = _admin_headers()

    users = client.get('/admin/users', headers=headers)
    assert users.status_code == 200
    assert len(users.json()) >= 1

    user_id = users.json()[0]['id']
    detail = client.get(f'/admin/users/{user_id}', headers=headers)
    assert detail.status_code == 200

    updated = client.patch(f'/admin/users/{user_id}/status', json={'status': 'active'}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()['status'] == 'active'
