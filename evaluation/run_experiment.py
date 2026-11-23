import sys

from dotenv import load_dotenv

load_dotenv()

from langsmith import evaluate  # noqa: E402

from evaluation.evaluators import ALL_EVALUATORS  # noqa: E402
from src.graph import run_session  # noqa: E402

DATASET_NAME = "personality-ai-v2"


def target(inputs: dict) -> dict:
    """הפונקציה שנבדקת: מריצה סשן אחד לפי הקלט מהדאטהסט."""
    return run_session(inputs["resume_values"])


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    evaluate(
        target,
        data=DATASET_NAME,
        evaluators=ALL_EVALUATORS,
        experiment_prefix=prefix,
        max_concurrency=1,
    )
    print(f"הניסוי '{prefix}' הסתיים. לפתוח אותו ב-LangSmith בלשונית Experiments.")


if __name__ == "__main__":
    main()