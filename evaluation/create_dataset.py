from dotenv import load_dotenv
from langsmith import Client

from src.graph import ITEMS
from src.scoring import TRAITS

load_dotenv()

DATASET_NAME = "personality-ai-v4"
APPROVE = {"approved": True, "feedback": ""}


def reject(note: str) -> dict:
    return {"approved": False, "feedback": note}


def neutral_answers() -> list:
    return [3] * len(ITEMS)


def reverse_coded_answers() -> list:
    """פריטי openness מקבלים 5 (רגיל) או 1 (הפוך). אחרי היפוך כולם נותנים 5."""
    values = []
    for item in ITEMS:
        if item["trait"] == "openness":
            values.append(1 if item["reverse"] else 5)
        else:
            values.append(3)
    return values


ALL_MIDDLE = {trait: 3.0 for trait in TRAITS}
OPENNESS_HIGH = {**ALL_MIDDLE, "openness": 5.0}


def example(name, resume_values, scores, final, errors, revisions) -> dict:
    return {
        "inputs": {"resume_values": resume_values},
        "outputs": {
            "expected_scores": scores,
            "expected_final_report": final,
            "expected_validation_errors": errors,
            "expected_revisions": revisions,
        },
        "metadata": {"case": name},
    }


def build_examples() -> list:
    n = neutral_answers()
    return [
        example("valid_all_threes", n + [APPROVE], ALL_MIDDLE, True, 0, 0),
        example("missing_answer", [""] + n + [APPROVE], ALL_MIDDLE, True, 1, 0),
        example("out_of_range", [9] + n + [APPROVE], ALL_MIDDLE, True, 1, 0),
        example("non_numeric", ["abc"] + n + [APPROVE], ALL_MIDDLE, True, 1, 0),
        example("reverse_coded", reverse_coded_answers() + [APPROVE], OPENNESS_HIGH, True, 0, 0),
        example("reject_then_approve", n + [reject("הוסף מגבלות"), APPROVE], ALL_MIDDLE, True, 0, 1),
        example("three_rejections_stop", n + [reject("לא טוב")] * 3, ALL_MIDDLE, False, 0, 2),
    ]


def main():
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"הדאטהסט '{DATASET_NAME}' כבר קיים. לא נוצר שוב.")
        return
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="מקרי בדיקה ל-IPIP-50: תקין, חסר, לא בטווח, היפוך, תיקון ודחייה.",
    )
    examples = build_examples()
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"נוצר דאטהסט '{DATASET_NAME}' עם {len(examples)} מקרים.")


if __name__ == "__main__":
    main()
