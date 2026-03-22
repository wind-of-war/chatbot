from types import SimpleNamespace

from apps.api.services.usage_service import daily_quota_guard, rate_limit_guard


def test_rate_limit_guard_bypassed_in_test_mode(monkeypatch):
    monkeypatch.setattr("configs.settings.settings.test_mode_unlimited_questions", True)
    user = SimpleNamespace(role="user", id=999)
    rate_limit_guard(db=None, user=user)


def test_daily_quota_guard_bypassed_in_test_mode(monkeypatch):
    monkeypatch.setattr("configs.settings.settings.test_mode_unlimited_questions", True)
    user = SimpleNamespace(role="user", id=999)
    daily_quota_guard(db=None, user=user)
