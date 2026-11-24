from src.report import TRAIT_HE, build_report, summary
from src.scoring import TRAITS


def scores(**overrides):
    base = {t: 3.0 for t in TRAITS}
    base.update(overrides)
    return base


def test_summary_mentions_high_trait():
    assert TRAIT_HE["extraversion"] in summary(scores(extraversion=4.5))


def test_summary_mentions_low_trait():
    assert TRAIT_HE["neuroticism"] in summary(scores(neuroticism=1.8))


def test_summary_all_middle():
    assert "באזור הבינוני" in summary(scores())


def test_report_contains_summary_and_limits():
    report = build_report(scores(neuroticism=1.8))
    assert "סיכום:" in report
    assert "הדגמה לימודית" in report
