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


def test_all_threes_give_middle_score(questionnaire):
    scores = calculate_scores(questionnaire, all_answers(questionnaire, 3))
    assert scores == {
        "openness": 3.0,
        "conscientiousness": 3.0,
        "extraversion": 3.0,
        "agreeableness": 3.0,
        "neuroticism": 3.0,
    }


def test_reverse_item_is_flipped(questionnaire):
    # O1 רגיל, O2 הפוך. תשובה 5 ל-O1 ותשובה 1 ל-O2 אמורה להחזיר 5.0.
    answers = all_answers(questionnaire, 3)
    answers["O1"] = 5
    answers["O2"] = 1
    scores = calculate_scores(questionnaire, answers)
    assert scores["openness"] == 5.0


def test_reverse_uses_scale_bounds_from_questionnaire(questionnaire):
    # סולם 1-7 במקום 1-5. ערך 1 בפריט הפוך צריך להפוך ל-7.
    seven_point = copy.deepcopy(questionnaire)
    seven_point["meta"]["scale"] = {"min": 1, "max": 7}
    answers = all_answers(seven_point, 4)
    answers["O2"] = 1
    scores = calculate_scores(seven_point, answers)
    # ממוצע של O1=4 ו-O2=7 (אחרי היפוך)
    assert scores["openness"] == 5.5


def test_same_input_gives_same_scores(questionnaire):
    answers = all_answers(questionnaire, 2)
    first = calculate_scores(questionnaire, answers)
    second = calculate_scores(questionnaire, answers)
    assert first == second


def test_missing_answer_raises_before_scoring(questionnaire):
    answers = all_answers(questionnaire, 3)
    del answers["A2"]
    with pytest.raises(ValueError):
        calculate_scores(questionnaire, answers)