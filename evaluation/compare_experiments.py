import csv
import sys
from pathlib import Path

EVALUATOR_KEYS = [
    "answer_validation_accuracy",
    "score_calculation_accuracy",
    "workflow_completion",
    "report_groundedness",
    "no_reviewer_note_in_final",
]


def averages(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = {}
    for key in EVALUATOR_KEYS:
        values = [float(r[key]) for r in rows if r.get(key, "").strip()]
        if values:
            result[key] = round(sum(values) / len(values), 2)
    return result


def main():
    before = averages(Path(sys.argv[1]))
    after = averages(Path(sys.argv[2]))
    print(f"{'בודק':<32}{'לפני':>8}{'אחרי':>8}")
    for key in EVALUATOR_KEYS:
        if key in before:
            print(f"{key:<32}{before[key]:>8.2f}{after.get(key, float('nan')):>8.2f}")


if __name__ == "__main__":
    main()