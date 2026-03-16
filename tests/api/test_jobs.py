from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_job_status_pending():
    response = client.get('/jobs/not-real-task-id')
    assert response.status_code == 200
    body = response.json()
    assert body['task_id'] == 'not-real-task-id'
    assert 'state' in body
    assert 'ready' in body
