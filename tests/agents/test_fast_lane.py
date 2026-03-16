from apps.api.services.chat_service import _try_fast_lane
from core.services.intent.intent_router import IntentRouter


def test_intent_router_detects_cleanroom_grade():
    router = IntentRouter()
    assert router.classify("tieu chuan vi sinh cap sach C") == "cleanroom_grade_limit"


def test_fast_lane_matches_seed_faq():
    result = _try_fast_lane("quy trinh danh gia nha cung cap nhu the nao")
    assert result is not None
    assert result["mode"] == "faq"
    assert "nha cung cap" in result["answer"].lower()


def test_fast_lane_template_for_grade_c():
    result = _try_fast_lane("tieu chuan vi sinh cap sach C")
    assert result is not None
    assert result["mode"] in {"faq", "template"}
    assert "cap sach C" in result["answer"]
