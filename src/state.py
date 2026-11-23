from typing import TypedDict


class TestState(TypedDict):
    question_index: int
    answers: dict[str, int]
    pending: int | None
    validation_error: str | None
    scores: dict[str, float] | None
    draft_report: str | None
    review_feedback: str | None
    approved: bool | None
    revision_count: int
    final_report: str | None
    error_count: int