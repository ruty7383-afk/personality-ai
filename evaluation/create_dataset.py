import json
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

DATASET_NAME = "personality-ai-v2"
DATASET_PATH = Path(__file__).resolve().parent / "dataset.json"


def main():
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"הדאטהסט '{DATASET_NAME}' כבר קיים. לא נוצר שוב.")
        return

    examples = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="מקרי בדיקה לסוכן השאלון: תקין, חסר, לא בטווח, היפוך, תיקון ודחייה.",
    )
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"נוצר דאטהסט '{DATASET_NAME}' עם {len(examples)} מקרים.")


if __name__ == "__main__":
    main()