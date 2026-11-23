from src.report import LIMITS, TRAIT_HE
from src.scoring import TRAITS

FORBIDDEN_PHRASES = ["אתה אדם", "הינך", "סובל", "הפרעה"]


def answer_validation_accuracy(run, example) -> dict:
    got = run.outputs["validation_errors"]
    expected = example.outputs["expected_validation_errors"]
    return {"key": "answer_validation_accuracy", "score": int(got == expected)}


def score_calculation_accuracy(run, example) -> dict:
    got = run.outputs["scores"] or {}
    expected = example.outputs["expected_scores"]
    ok = all(abs(got.get(t, -1) - expected[t]) < 1e-9 for t in TRAITS)
    return {"key": "score_calculation_accuracy", "score": int(ok)}


def workflow_completion(run, example) -> dict:
    finished = run.outputs["final_report"] is not None
    ok = (
        finished == example.outputs["expected_final_report"]
        and run.outputs["revisions"] == example.outputs["expected_revisions"]
    )
    return {"key": "workflow_completion", "score": int(ok)}


def report_groundedness(run, example) -> dict:
    report = run.outputs["final_report"]
    if report is None:
        return {"key": "report_groundedness", "score": 1, "comment": "אין דוח, אין קביעות"}

    scores = run.outputs["scores"]
    problems = []
    for trait in TRAITS:
        if f"{scores[trait]:.2f}" not in report or TRAIT_HE[trait] not in report:
            problems.append(trait)
    if LIMITS not in report:
        problems.append("limits")
    if any(phrase in report for phrase in FORBIDDEN_PHRASES):
        problems.append("forbidden_phrase")
    return {
        "key": "report_groundedness",
        "score": int(not problems),
        "comment": ", ".join(problems),
    }



def no_reviewer_note_in_final(run, example) -> dict:
    report = run.outputs["final_report"]
    if report is None:
        return {"key": "no_reviewer_note_in_final", "score": 1, "comment": "אין דוח סופי"}
    # הטקסט הזה נכתב על ידי build_report כשיש הערת בודק
    leaked = "הערת בודק" in report
    return {"key": "no_reviewer_note_in_final", "score": int(not leaked)}

ALL_EVALUATORS = [
    answer_validation_accuracy,
    score_calculation_accuracy,
    workflow_completion,
    report_groundedness,
    no_reviewer_note_in_final,
]