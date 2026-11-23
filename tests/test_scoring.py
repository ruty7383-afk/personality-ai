import copy
from pathlib import Path

import pytest

from src.scoring import calculate_scores, load_questionnaire

QUESTIONNAIRE_PATH = Path(__file__).resolve().parent.parent / "src" / "questionnaire.json"


@pytest.fixture
def questionnaire():
    return load_questionnaire(QUESTIONNAIRE_PATH)


def all_answers(questionnaire, value):
    return {item["id"]: value for item in questionnaire["items"]}


def openness_answers(questionnaire, high, low):
    """פריטים רגילים מקבלים high, והפוכים מקבלים low.
    אחרי היפוך כל הפריטים של openness נותנים את אותו ערך, כלומר high."""
    answers = all_answers(questionnaire, 3)
    for item in questionnaire["items"]:
        if item["trait"] == "openness":
            answers[item["id"]] = low if item["reverse"] else high
    return answers


def test_all_threes_give_middle_score(questionnaire):
    scores = calculate_scores(questionnaire, all_answers(questionnaire, 3))
    assert all(value == 3.0 for value in scores.values())
    assert set(scores) == {
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    }


def test_reverse_items_are_flipped(questionnaire):
    scores = calculate_scores(questionnaire, openness_answers(questionnaire, high=5, low=1))
    assert scores["openness"] == 5.0


def test_reverse_uses_scale_bounds_from_questionnaire(questionnaire):
    seven_point = copy.deepcopy(questionnaire)
    seven_point["meta"]["scale"] = {"min": 1, "max": 7}
    scores = calculate_scores(seven_point, openness_answers(seven_point, high=7, low=1))
    assert scores["openness"] == 7.0


def test_same_input_gives_same_scores(questionnaire):
    answers = all_answers(questionnaire, 2)
    assert calculate_scores(questionnaire, answers) == calculate_scores(questionnaire, answers)


def test_missing_answer_raises_before_scoring(questionnaire):
    answers = all_answers(questionnaire, 3)
    del answers["I02"]
    with pytest.raises(ValueError):
        calculate_scores(questionnaire, answers)
