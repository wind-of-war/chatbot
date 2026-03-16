from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_telegram_webhook_requires_secret():
    payload = {
        "message": {
            "text": "hello",
            "chat": {"id": 123},
            "from": {"id": 456},
        }
    }
    resp = client.post('/integrations/telegram/webhook', json=payload)
    assert resp.status_code in (401, 503)
