import json
from pathlib import Path

TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def load_questionnaire(path: Path) -> dict:
    """קורא את השאלון מקובץ JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_answers(questionnaire: dict, answers: dict[str, int]) -> list[str]:
    """מחזיר רשימת שגיאות. רשימה ריקה אומרת שהתשובות תקינות."""
    lo = questionnaire["meta"]["scale"]["min"]
    hi = questionnaire["meta"]["scale"]["max"]
    errors = []
    for item in questionnaire["items"]:
        item_id = item["id"]
        if item_id not in answers:
            errors.append(f"חסרה תשובה ל-{item_id}")
            continue
        value = answers[item_id]
        if isinstance(value, bool) or not isinstance(value, int) or not (lo <= value <= hi):
            errors.append(f"ערך לא תקין ל-{item_id}: {value!r}")
    return errors

def calculate_scores(questionnaire: dict, answers: dict[str, int]) -> dict[str, float]:
    """מחשב ציון לכל תכונה. זורק שגיאה אם יש תשובות לא תקינות."""
    errors = validate_answers(questionnaire, answers)
    if errors:
        raise ValueError("; ".join(errors))

    lo = questionnaire["meta"]["scale"]["min"]
    hi = questionnaire["meta"]["scale"]["max"]

    values_by_trait = {trait: [] for trait in TRAITS}
    for item in questionnaire["items"]:
        value = answers[item["id"]]
        if item["reverse"]:
            value = lo + hi - value  # היפוך: 5 הופך ל-1 בסולם 1-5
        values_by_trait[item["trait"]].append(value)

    return {
        trait: round(sum(values) / len(values), 2)
        for trait, values in values_by_trait.items()
    }