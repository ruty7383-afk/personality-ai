import os
import uuid
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.llm import (
    ask_clarification,
    get_model,
    phrase_question,
    report_is_grounded,
    write_report_text,
)
from src.report import LIMITS, TRAIT_HE, build_report
from src.scoring import calculate_scores, load_questionnaire
from src.state import TestState

QUESTIONNAIRE = load_questionnaire(Path(__file__).resolve().parent / "questionnaire.json")
ITEMS = QUESTIONNAIRE["items"]
LO = QUESTIONNAIRE["meta"]["scale"]["min"]
HI = QUESTIONNAIRE["meta"]["scale"]["max"]
MAX_REVISIONS = 2


def llm_enabled() -> bool:
    """ה-LLM פעיל רק כש-LLM_MODE=google. בברירת המחדל הזרימה עובדת בלי מודל."""
    return os.getenv("LLM_MODE", "fake") == "google"


def present_question(state: TestState) -> dict:
    """מציג את השאלה הנוכחית. עם LLM - המודל מנסח, ואם הייתה שגיאה - מבקש הבהרה."""
    item = ITEMS[state["question_index"]]
    if llm_enabled():
        model = get_model()
        if state["validation_error"]:
            text = ask_clarification(model, item["text"], str(state["pending"]), LO, HI)
        else:
            text = phrase_question(model, item["text"], LO, HI)
    else:
        text = item["text"]
        if state["validation_error"]:
            text = f"שגיאה: {state['validation_error']}. נא לענות שוב.\n{text}"
    print(f"שאלה {state['question_index'] + 1} מתוך {len(ITEMS)}: {text}")
    return {}


def collect_answer(state: TestState) -> dict:
    """עוצר את הגרף ומחכה לתשובת הנבדק. הערך שיוחזר ב-resume הופך לתשובה."""
    item = ITEMS[state["question_index"]]
    answer = interrupt({"question": item["text"], "scale": [LO, HI]})
    return {"pending": answer}


def validate_answer(state: TestState) -> dict:
    """בודק את התשובה הממתינה. אם תקינה - שומר אותה ומתקדם לשאלה הבאה."""
    value = state["pending"]
    valid = isinstance(value, int) and not isinstance(value, bool) and LO <= value <= HI
    if not valid:
        return {
            "validation_error": f"הערך {value!r} אינו בטווח {LO}-{HI}",
            "error_count": state["error_count"] + 1,
        }
    item = ITEMS[state["question_index"]]
    return {
        "answers": {**state["answers"], item["id"]: value},
        "question_index": state["question_index"] + 1,
        "validation_error": None,
    }


def route_after_validation(state: TestState) -> str:
    """קובע לאן ללכת אחרי הבדיקה. זה הענף המותנה של הגרף."""
    if state["validation_error"]:
        return "present_question"      # לולאה: שואלים שוב את אותה שאלה
    if state["question_index"] < len(ITEMS):
        return "present_question"      # עוד שאלות: ממשיכים
    return "calculate_scores"          # כל השאלות נענו: מחשבים ציונים


def calculate(state: TestState) -> dict:
    """קורא לפונקציה מ-scoring.py. אין כאן שום חישוב משלנו."""
    return {"scores": calculate_scores(QUESTIONNAIRE, state["answers"])}


def draft_report(scores: dict) -> str:
    """עם LLM - המודל מנסח, ורק אם הטקסט עובר בדיקת הנאמנות לציונים. אחרת - תבנית."""
    if llm_enabled():
        text = write_report_text(get_model(), scores, TRAIT_HE)
        if report_is_grounded(text, scores, TRAIT_HE):
            return f"{text}\n{LIMITS}"
        print("הטקסט של ה-LLM לא עבר בדיקת הנאמנות, משתמשים בתבנית.")
    return build_report(scores)


def generate_report(state: TestState) -> dict:
    return {
        "draft_report": draft_report(state["scores"]),
        "revision_count": 0,
        "approved": None,
    }


def human_review(state: TestState) -> dict:
    """עוצר ומחכה להחלטת הבודק: {'approved': bool, 'feedback': str}."""
    decision = interrupt({"draft": state["draft_report"], "question": "לאשר את הדוח?"})
    return {
        "approved": decision["approved"],
        "review_feedback": decision.get("feedback", ""),
    }


def route_review(state: TestState) -> str:
    if state["approved"]:
        return "finalize"
    if state["revision_count"] < MAX_REVISIONS:
        return "revise_report"
    return "stop"  # יציאה בטוחה: הלולאה לא נמשכת לנצח


def revise_report(state: TestState) -> dict:
    return {
        "draft_report": draft_report(state["scores"]),
        "revision_count": state["revision_count"] + 1,
        "approved": None,
    }

def finalize(state: TestState) -> dict:
    return {"final_report": state["draft_report"]}


def build_graph():
    builder = StateGraph(TestState)
    builder.add_node("present_question", present_question)
    builder.add_node("collect_answer", collect_answer)
    builder.add_node("validate_answer", validate_answer)
    builder.add_node("calculate_scores", calculate)
    builder.add_node("generate_report", generate_report)
    builder.add_node("human_review", human_review)
    builder.add_node("revise_report", revise_report)
    builder.add_node("finalize", finalize)

    builder.add_edge(START, "present_question")
    builder.add_edge("present_question", "collect_answer")
    builder.add_edge("collect_answer", "validate_answer")
    builder.add_conditional_edges(
        "validate_answer", route_after_validation, ["present_question", "calculate_scores"]
    )
    builder.add_edge("calculate_scores", "generate_report")
    builder.add_edge("generate_report", "human_review")
    builder.add_conditional_edges(
        "human_review",
        route_review,
        {"finalize": "finalize", "revise_report": "revise_report", "stop": END},
    )
    builder.add_edge("revise_report", "human_review")
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=MemorySaver())


def initial_state() -> dict:
    return {
        "question_index": 0,
        "answers": {},
        "pending": None,
        "validation_error": None,
        "error_count": 0,
        "scores": None,
        "draft_report": None,
        "review_feedback": None,
        "approved": None,
        "revision_count": 0,
        "final_report": None,
    }


def run_session(resume_values: list) -> dict:
    """מריץ סשן אחד מלא ומחזיר את התוצאות הנדרשות למדידה."""
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    graph.invoke(initial_state(), config)
    inputs = list(resume_values)
    while graph.get_state(config).next:
        graph.invoke(Command(resume=inputs.pop(0)), config)
    values = graph.get_state(config).values
    return {
        "final_report": values["final_report"],
        "scores": values["scores"],
        "validation_errors": values["error_count"],
        "revisions": values["revision_count"],
    }
