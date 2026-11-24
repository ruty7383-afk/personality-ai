import pytest

from src.llm import FakeModel, get_model, report_is_grounded, write_report_text

NAMES = {
    "extraversion": "מוחצנות",
    "conscientiousness": "מצפוניות",
    "agreeableness": "נעימות",
    "openness": "פתיחות לחוויות",
    "emotional_stability": "יציבות רגשית",
}
SCORES = {
    "extraversion": 4.2,
    "conscientiousness": 3.8,
    "agreeableness": 4.5,
    "openness": 3.9,
    "emotional_stability": 3.4,
}


def test_default_mode_is_fake(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    assert isinstance(get_model(), FakeModel)


def test_google_mode_without_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with pytest.raises(RuntimeError):
        get_model()


def test_write_report_text_sends_scores_to_model():
    seen = {}

    class Spy(FakeModel):
        def complete(self, system, user):
            seen["user"] = user
            return "ok"

    write_report_text(Spy(), SCORES, NAMES)
    assert "מוחצנות: 4.20" in seen["user"]
    assert "יציבות רגשית: 3.40" in seen["user"]


def test_grounded_report_passes():
    text = "מוחצנות 4.2, מצפוניות 3.8, נעימות 4.5, פתיחות לחוויות 3.9, יציבות רגשית 3.4"
    assert report_is_grounded(text, SCORES, NAMES) is True


def test_report_missing_a_trait_fails():
    text = "מוחצנות 4.2, מצפוניות 3.8, נעימות 4.5, פתיחות לחוויות 3.9"
    assert report_is_grounded(text, SCORES, NAMES) is False


def test_report_with_wrong_score_fails():
    text = "מוחצנות 4.9, מצפוניות 3.8, נעימות 4.5, פתיחות לחוויות 3.9, יציבות רגשית 3.4"
    assert report_is_grounded(text, SCORES, NAMES) is False
