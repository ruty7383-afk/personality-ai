"""שרת Flask: מגיש את דף האתר, ומחבר אותו לגרף של התוכנית.

הרצה (מתיקיית הפרויקט):  python -m src.server
ואז פותחים בדפדפן:        http://127.0.0.1:5000
"""
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, send_file, send_from_directory  # noqa: E402
from langgraph.types import Command  # noqa: E402

from src.graph import HI, ITEMS, LO, build_graph, initial_state  # noqa: E402
from src.report import TRAIT_HE, save_chart  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_DIR / "web"
CHART_DIR = PROJECT_DIR / "outputs"

app = Flask(__name__)
graph = build_graph()
sessions: dict[str, dict] = {}  # session_id -> config של LangGraph


def describe(config) -> dict:
    """מתרגם את מצב הגרף לנתונים שהדף מציג. הגרף הוא המקור היחיד לאמת."""
    snap = graph.get_state(config)
    values = snap.values
    if not snap.next:
        return {
            "done": True,
            "final_report": values.get("final_report"),
            "scores": values.get("scores"),
            "trait_names": TRAIT_HE,
            "scale": [LO, HI],
        }
    payload = snap.tasks[0].interrupts[0].value
    if "scale" in payload:
        return {
            "done": False,
            "stage": "question",
            "index": values["question_index"],
            "total": len(ITEMS),
            "question": payload["question"],
            "scale": [LO, HI],
            "error": values.get("validation_error"),
        }
    return {"done": False, "stage": "review", "draft": payload["draft"]}


def get_config(session_id):
    config = sessions.get(session_id)
    if config is None:
        return None
    return config


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.post("/api/start")
def start():
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    try:
        graph.invoke(initial_state(), config)
    except Exception as exc:  # שגיאה מהמודל או מהגרף: מחזירים הודעה ולא מפילים את השרת
        return jsonify({"error": f"שגיאה בהפעלת המבחן: {type(exc).__name__}"}), 500
    sessions[session_id] = config
    return jsonify({"session_id": session_id, **describe(config)})


@app.get("/api/state")
def state():
    config = get_config(request.args.get("sid", ""))
    if config is None:
        return jsonify({"error": "סשן לא נמצא, התחילו מבחן חדש"}), 404
    return jsonify({"session_id": request.args["sid"], **describe(config)})


@app.post("/api/answer")
def answer():
    data = request.get_json(force=True)
    config = get_config(data.get("session_id", ""))
    if config is None:
        return jsonify({"error": "סשן לא נמצא, התחילו מבחן חדש"}), 404
    try:
        graph.invoke(Command(resume=data.get("value")), config)
    except Exception as exc:
        return jsonify({"error": f"שגיאה בשליחת התשובה: {type(exc).__name__}"}), 500
    return jsonify({"session_id": data["session_id"], **describe(config)})


@app.post("/api/review")
def review():
    data = request.get_json(force=True)
    config = get_config(data.get("session_id", ""))
    if config is None:
        return jsonify({"error": "סשן לא נמצא, התחילו מבחן חדש"}), 404
    decision = {"approved": bool(data.get("approved")), "feedback": data.get("feedback", "")}
    try:
        graph.invoke(Command(resume=decision), config)
    except Exception as exc:
        return jsonify({"error": f"שגיאה בבדיקה: {type(exc).__name__}"}), 500
    return jsonify({"session_id": data["session_id"], **describe(config)})


@app.get("/api/chart/<session_id>")
def chart(session_id):
    config = get_config(session_id)
    if config is None:
        return jsonify({"error": "סשן לא נמצא"}), 404
    values = graph.get_state(config).values
    if not values.get("scores"):
        return jsonify({"error": "אין עדיין ציונים"}), 404
    CHART_DIR.mkdir(exist_ok=True)
    path = save_chart(values["scores"], CHART_DIR / f"chart_{session_id}.png")
    return send_file(path, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
