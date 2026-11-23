from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph import END, START, StateGraph

from src.scoring import calculate_scores, load_questionnaire
from src.state import TestState

QUESTIONNAIRE = load_questionnaire(Path(__file__).resolve().parent / "questionnaire.json")
ITEMS = QUESTIONNAIRE["items"]
LO = QUESTIONNAIRE["meta"]["scale"]["min"]
HI = QUESTIONNAIRE["meta"]["scale"]["max"]


def present_question(state: TestState) -> dict:
    """מציג את השאלה הנוכחית, ואם הייתה שגיאה - גם אותה."""
    if state["validation_error"]:
        print(f"שגיאה: {state['validation_error']}. נא לענות שוב.")
    item = ITEMS[state["question_index"]]
    print(f"שאלה {state['question_index'] + 1} מתוך {len(ITEMS)}: {item['text']}")
    return {}


from langgraph.types import interrupt


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
        return "present_question"     # עוד שאלות: ממשיכים
    return "calculate_scores"         # כל השאלות נענו: מחשבים ציונים


def calculate(state: TestState) -> dict:
    """קורא לפונקציה מ-scoring.py. אין כאן שום חישוב משלנו."""
    return {"scores": calculate_scores(QUESTIONNAIRE, state["answers"])}


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


def run_demo() -> dict:
    """מריץ את הגרף עם תשובה לא תקינה אחת (9), ואחריה תשובות תקינות לכל השאלות."""
    graph = build_graph()
    inbox = [9] + [3] * len(ITEMS)
    result = graph.invoke({
        "question_index": 0,
        "answers": {},
        "inbox": inbox,
        "pending": None,
        "validation_error": None,
        "scores": None,
    })
    return result["scores"]
from langgraph.types import Command


def run_demo_with_interrupts(answers: list[int]) -> dict:
    """מריץ את הבדיקה: בכל עצירה לוקח תשובה מהרשימה וממשיך."""
    graph = build_graph()
    config = {"configurable": {"thread_id": "demo-1"}}
    initial_state = {
        "question_index": 0,
        "answers": {},
        "pending": None,
        "validation_error": None,
        "scores": None,
    }

    graph.invoke(initial_state, config)  # רץ עד העצירה הראשונה
    while graph.get_state(config).next:  # יש עוד צומת ממתין
        print("הגרף ממתין לתשובה...")
        graph.invoke(Command(resume=answers.pop(0)), config)

    return graph.get_state(config).values["scores"]

from src.report import build_report

MAX_REVISIONS = 2


def generate_report(state: TestState) -> dict:
    return {
        "draft_report": build_report(state["scores"]),
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
    # השיפור: הערת הבודק נשארת במצב הפנימי ולא נכנסת לטקסט שמוצג לנבדק
    return {
        "draft_report": build_report(state["scores"]),
        "revision_count": state["revision_count"] + 1,
        "approved": None,
    }


def finalize(state: TestState) -> dict:
    return {"final_report": state["draft_report"]}

# def run_full_demo(inputs: list) -> dict:
#     """בכל עצירה לוקח את הערך הבא מהרשימה: מספר לשאלה, או החלטה לבודק."""
#     graph = build_graph()
#     config = {"configurable": {"thread_id": "demo-1"}}
#     initial_state = {
#         "question_index": 0,
#         "answers": {},
#         "pending": None,
#         "validation_error": None,
#         "scores": None,
#         "draft_report": None,
#         "review_feedback": None,
#         "approved": None,
#         "revision_count": 0,
#         "final_report": None,
#     }
#     graph.invoke(initial_state(), config)
#     while graph.get_state(config).next:
#         graph.invoke(Command(resume=inputs.pop(0)), config)
#     values = graph.get_state(config).values
#     return {"final_report": values["final_report"], "scores": values["scores"]}

import uuid


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