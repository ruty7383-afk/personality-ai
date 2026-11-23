from pathlib import Path

import pytest

from src.scoring import calculate_scores, load_questionnaire, validate_answers

QUESTIONNAIRE_PATH = Path(__file__).resolve().parent.parent / "src" / "questionnaire.json"


@pytest.fixture
def questionnaire():
    return load_questionnaire(QUESTIONNAIRE_PATH)


def all_answers(questionnaire, value):
    return {item["id"]: value for item in questionnaire["items"]}


def test_valid_answers_have_no_errors(questionnaire):
    assert validate_answers(questionnaire, all_answers(questionnaire, 3)) == []


def test_missing_answer_is_reported(questionnaire):
    answers = all_answers(questionnaire, 3)
    del answers["O1"]
    errors = validate_answers(questionnaire, answers)
    assert len(errors) == 1
    assert "O1" in errors[0]


@pytest.mark.parametrize("bad_value", [0, 6, -1])
def test_out_of_range_value_is_rejected(questionnaire, bad_value):
    answers = all_answers(questionnaire, 3)
    answers["C1"] = bad_value
    assert any("C1" in error for error in validate_answers(questionnaire, answers))


@pytest.mark.parametrize("bad_value", [True, "3", 2.5])
def test_wrong_type_is_rejected(questionnaire, bad_value):
    answers = all_answers(questionnaire, 3)
    answers["E1"] = bad_value
    assert any("E1" in error for error in validate_answers(questionnaire, answers))


def test_calculate_scores_raises_on_invalid_answers(questionnaire):
    answers = all_answers(questionnaire, 3)
    answers["N1"] = 9
    with pytest.raises(ValueError):
        calculate_scores(questionnaire, answers)