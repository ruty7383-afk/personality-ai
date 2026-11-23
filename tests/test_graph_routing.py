from src.graph import MAX_REVISIONS, route_after_validation, route_review, run_session


def state(**kwargs):
    base = {"question_index": 0, "validation_error": None, "approved": None, "revision_count": 0}
    base.update(kwargs)
    return base


def test_invalid_answer_repeats_question():
    assert route_after_validation(state(validation_error="x", question_index=3)) == "present_question"


def test_more_questions_continue():
    assert route_after_validation(state(question_index=3)) == "present_question"


def test_all_answered_goes_to_scoring():
    assert route_after_validation(state(question_index=10)) == "calculate_scores"


def test_approved_goes_to_finalize():
    assert route_review(state(approved=True)) == "finalize"


def test_rejected_revises_under_limit():
    assert route_review(state(approved=False, revision_count=0)) == "revise_report"


def test_rejected_stops_at_limit():
    assert route_review(state(approved=False, revision_count=MAX_REVISIONS)) == "stop"


def test_full_session_approved_gives_report():
    result = run_session([3] * 10 + [{"approved": True, "feedback": ""}])
    assert result["final_report"] is not None
    assert result["revisions"] == 0


def test_three_rejections_give_no_report():
    rejection = {"approved": False, "feedback": "x"}
    result = run_session([3] * 10 + [rejection] * 3)
    assert result["final_report"] is None
    assert result["revisions"] == MAX_REVISIONS