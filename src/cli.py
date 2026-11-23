import uuid
from dotenv import load_dotenv

load_dotenv()  # קורא את .env לפני שהגרף רץ
from langgraph.types import Command

from src.graph import build_graph


def initial_state() -> dict:
    return {
        "question_index": 0,
        "answers": {},
        "pending": None,
        "validation_error": None,
        "scores": None,
        "draft_report": None,
        "review_feedback": None,
        "approved": None,
        "revision_count": 0,
        "final_report": None,
        "error_count": 0,
    }


def ask_question(payload: dict):
    """שואל את הנבדק. אם הקלט מספר - ממיר למספר; אחרת משאיר טקסט והגרף ידחה אותו."""
    lo, hi = payload["scale"]
    raw = input(f"תשובה ({lo}-{hi}): ").strip()
    return int(raw) if raw.lstrip("-").isdigit() else raw


def ask_review(payload: dict) -> dict:
    """מציג את הטיוטה לבודק ומחזיר את החלטתו."""
    print("\n--- טיוטת דוח לאישור ---")
    print(payload["draft"])
    approved = input("\nלאשר? (y/n): ").strip().lower() == "y"
    feedback = "" if approved else input("הערות לתיקון: ").strip()
    return {"approved": approved, "feedback": feedback}

def main():
    print("שאלון דמו בהשראת Big Five. אינו מאומת ואינו אבחון.")
    print("ענו על כל שאלה בסולם 1-5. ניתן לסיים בכל שלב רק לאחר שסיימתם את כל השאלות.\n")

    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    graph.invoke(initial_state(), config)

    while True:
        snapshot = graph.get_state(config)
        if not snapshot.next:
            break
        payload = snapshot.tasks[0].interrupts[0].value
        if "scale" in payload:      # עצירה של הנבדק
            resume = ask_question(payload)
        else:                       # עצירה של הבודק
            resume = ask_review(payload)
        graph.invoke(Command(resume=resume), config)

    final = graph.get_state(config).values["final_report"]
    if final:
        print("\n=== דוח סופי ===")
        print(final)
    else:
        print("\nלא נוצר דוח סופי.")


if __name__ == "__main__":
    main()