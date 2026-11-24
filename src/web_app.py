"""ממשק דפדפן (Streamlit) שמשתמש באותו גרף בדיוק כמו ה-CLI.

כל מה שקורה בטרמינל קורה גם כאן: אותו גרף, אותה בדיקה אנושית, אותו LLM (אם LLM_MODE=google),
ואותו תיעוד ב-LangSmith (אם LANGSMITH_TRACING=true). השינוי כאן הוא תצוגה בלבד.

הרצה:  python -m streamlit run src\\web_app.py
"""
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv()

from src.graph import HI, ITEMS, LO, build_graph, initial_state  # noqa: E402
from src.report import TRAIT_HE, save_chart  # noqa: E402

CHART_PATH = Path("outputs/report_chart.png")
SCALE_LABELS = {
    1: "לא מסכים בכלל",
    2: "לא מסכים",
    3: "ניטרלי",
    4: "מסכים",
    5: "מסכים מאוד",
}

STYLE = """
<style>
  .stApp {
    background: radial-gradient(1200px 600px at 10% -10%, #312e81 0%, transparent 60%),
                radial-gradient(900px 500px at 110% 110%, #0c4a6e 0%, transparent 60%),
                linear-gradient(160deg, #0f172a, #1e1b4b);
  }
  .hero { text-align: center; margin: 8px 0 22px; }
  .hero h1 {
    font-size: 34px; margin: 0;
    background: linear-gradient(90deg, #818cf8, #38bdf8);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero p { color: #94a3b8; margin: 6px 0 0; font-size: 14px; }
  .question-card, .report-card, .review-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 22px;
    padding: 26px;
    box-shadow: 0 30px 60px -20px rgba(0,0,0,0.5);
    margin-bottom: 18px;
  }
  .question-text { font-size: 24px; font-weight: 700; line-height: 1.5; color: #f8fafc; }
  .counter { color: #94a3b8; font-size: 13px; margin-bottom: 8px; }
  .report-text {
    white-space: pre-wrap; line-height: 1.8; color: #e2e8f0;
    background: rgba(255,255,255,0.04); border-radius: 14px; padding: 16px; font-size: 15px;
  }
  .trait-row { margin: 14px 0; }
  .trait-head { display: flex; justify-content: space-between; color: #f8fafc; font-weight: 600; }
  .trait-head span:last-child { color: #38bdf8; }
  .bar { height: 12px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; margin-top: 6px; }
  .bar > div { height: 100%; background: linear-gradient(90deg, #818cf8, #38bdf8); border-radius: 999px; }
  .disclaimer { color: #94a3b8; font-size: 12.5px; line-height: 1.6; border: 1px dashed rgba(255,255,255,0.14); border-radius: 14px; padding: 12px; margin-top: 14px; }
</style>
"""


@st.cache_resource
def get_graph():
    """גרף אחד משותף לכל הסשנים. כל משתמש מקבל thread_id משלו."""
    return build_graph()


def start_session():
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    get_graph().invoke(initial_state(), config)
    st.session_state.config = config


def resume(value):
    get_graph().invoke(Command(resume=value), st.session_state.config)
    st.rerun()


def current_state():
    """מחזיר את העצירה הנוכחית (payload) ואת הערכים. payload הוא None כשהמבחן הסתיים."""
    snapshot = get_graph().get_state(st.session_state.config)
    if not snapshot.next:
        return None, snapshot.values
    return snapshot.tasks[0].interrupts[0].value, snapshot.values


def render_scores(scores: dict):
    """ציוני החמישה, כשורות עם סרגל. הציונים מגיעים מ-Python, בדיוק כמו בטרמינל."""
    rows = []
    for trait, score in scores.items():
        pct = max(0.0, min(100.0, (score - LO) / (HI - LO) * 100))
        rows.append(
            f'<div class="trait-row"><div class="trait-head"><span>{TRAIT_HE[trait]}</span>'
            f'<span>{score:.2f} / {HI}</span></div>'
            f'<div class="bar"><div style="width:{pct:.0f}%"></div></div></div>'
        )
    st.markdown('<div class="report-card">' + "".join(rows) + "</div>", unsafe_allow_html=True)


st.set_page_config(page_title="מבחן אישיות (הדגמה)", page_icon="🧭", layout="centered")
st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><h1>מבחן אישיות</h1>'
    '<p>שאלון IPIP-50 בהשראת Big Five · דיווח עצמי, לא אבחון</p></div>',
    unsafe_allow_html=True,
)

if "config" not in st.session_state:
    st.markdown('<div class="question-card">לחצו על ההתחלה כדי לענות על השאלון.</div>', unsafe_allow_html=True)
    if st.button("התחלה", type="primary", use_container_width=True):
        start_session()
        st.rerun()
    st.stop()

payload, values = current_state()

# ---- המבחן הסתיים ----
if payload is None:
    report = values.get("final_report")
    if report:
        st.success("הדוח אושר על ידי הבודק.")
        st.markdown('<div class="report-card"><div class="report-text">' + report + "</div></div>", unsafe_allow_html=True)
        render_scores(values["scores"])
        CHART_PATH.parent.mkdir(exist_ok=True)
        save_chart(values["scores"], CHART_PATH)
        st.image(str(CHART_PATH), use_container_width=True)
    else:
        st.warning("הדוח לא אושר לאחר שלוש בדיקות, ולכן לא הופק דוח סופי.")
    st.markdown(
        '<div class="disclaimer">שאלון זה הוא הדגמה לימודית בהשראת Big Five. הוא שאלון דיווח עצמי, '
        'אינו מאומת מחקרית לעברית, אינו אבחון פסיכולוגי ואינו מדד קליני.</div>',
        unsafe_allow_html=True,
    )
    if st.button("מבחן חדש", use_container_width=True):
        del st.session_state.config
        st.rerun()
    st.stop()

# ---- שאלה ----
if "scale" in payload:
    index = values["question_index"]
    st.progress(index / len(ITEMS), text=f"שאלה {index + 1} מתוך {len(ITEMS)}")
    st.markdown(
        f'<div class="question-card"><div class="counter">שאלה {index + 1} מתוך {len(ITEMS)}</div>'
        f'<div class="question-text">{payload["question"]}</div></div>',
        unsafe_allow_html=True,
    )
    if values.get("validation_error"):
        st.error(values["validation_error"])
    choice = st.radio(
        "עד כמה המשפט מתאר אותך?",
        options=list(range(LO, HI + 1)),
        format_func=lambda n: f"{n} · {SCALE_LABELS[n]}",
        index=None,
    )
    if st.button("שליחה", type="primary", disabled=choice is None, use_container_width=True):
        resume(choice)

# ---- בדיקה אנושית ----
else:
    st.markdown('<div class="review-card"><h3 style="margin-top:0">בדיקת הדוח</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="report-card"><div class="report-text">' + payload["draft"] + "</div></div>", unsafe_allow_html=True)
    feedback = st.text_input("הערה לתיקון (אופציונלי, אם דוחים)")
    col_approve, col_reject = st.columns(2)
    if col_approve.button("אישור", type="primary", use_container_width=True):
        resume({"approved": True, "feedback": ""})
    if col_reject.button("דחייה", use_container_width=True):
        resume({"approved": False, "feedback": feedback})
