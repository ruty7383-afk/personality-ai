"""שכבת ה-LLM של הפרויקט.

ה-LLM מסביר, מנסח שאלות, מבקש הבהרות ומנסח את הדוח.
ה-LLM לא מחשב ציונים, לא מחליט אם להמשיך, ולא מאשר דוחות.
"""
import os
from typing import Protocol


class ChatModel(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class FakeModel:
    """מודל מזויף לבדיקות ולניסויים: מחזיר תמיד את אותו טקסט. בלי רשת ובלי עלות."""

    def __init__(self, reply: str = "[טקסט לדוגמה]"):
        self.reply = reply

    def complete(self, system: str, user: str) -> str:
        return self.reply


class GeminiModel:
    """מודל אמיתי דרך Google AI Studio. דורש GOOGLE_API_KEY ו-GEMINI_MODEL בקובץ .env."""

    def __init__(self, api_key: str, model_name: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model_name

    def complete(self, system: str, user: str) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        return response.text


def get_model() -> ChatModel:
    """LLM_MODE=fake (ברירת מחדל) מחזיר מודל מזויף. LLM_MODE=google מחזיר את המודל האמיתי."""
    if os.getenv("LLM_MODE", "fake") == "fake":
        return FakeModel()
    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")
    if not api_key or not model_name:
        raise RuntimeError("חסר GOOGLE_API_KEY או GEMINI_MODEL בקובץ .env")
    return GeminiModel(api_key, model_name)


# ---- הוראות למודל: כל פונקציה מקבלת רק את המידע שהיא צריכה ----

SYSTEM_BASE = (
    "אתה מנהל שיחה בעברית בשאלון אישיות הדגמה. "
    "אתה לא מחשב ציונים ולא קובע תוצאות. "
    "כל שאלה מגיעה מהמאגר הקבוע, ואינך ממציא שאלות."
)


def explain_purpose(model: ChatModel, scale_min: int, scale_max: int) -> str:
    """הסבר פתיחה: מה המטרה של השאלון ואיך לענות."""
    user = (
        f"הסבר למשתמש בקצרה מה מטרת השאלון, ושהוא יענה על כל משפט במספר "
        f"מ-{scale_min} עד {scale_max}. ציין שזה שאלון הדגמה ולא מבחן מאומת."
    )
    return model.complete(SYSTEM_BASE, user)


def phrase_question(model: ChatModel, question_text: str, scale_min: int, scale_max: int) -> str:
    """מציג את השאלה מהמאגר בניסוח ידידותי. אסור לשנות את תוכן השאלה."""
    user = (
        f"הצג למשתמש את המשפט הבא בדיוק כפי שהוא, ובקש ממנו לדרג מ-{scale_min} עד {scale_max}.\n"
        f"המשפט: {question_text}"
    )
    return model.complete(SYSTEM_BASE, user)


def ask_clarification(model: ChatModel, question_text: str, raw_answer: str,
                      scale_min: int, scale_max: int) -> str:
    """תשובה לא תקינה או לא ברורה: מבקש הבהרה, בלי לנחש מספר."""
    user = (
        f"המשתמש ענה '{raw_answer}' על המשפט '{question_text}'. "
        f"התשובה לא מספר שלם בין {scale_min} ל-{scale_max}. "
        f"בקש ממנו לענות במספר בטווח הזה. אל תנחש את הציון בעצמך."
    )
    return model.complete(SYSTEM_BASE, user)


def write_report_text(model: ChatModel, scores: dict[str, float], names: dict[str, str]) -> str:
    """מנסח דוח מילולי מתוך ציונים שכבר חושבו ב-Python. המודל לא משנה מספרים."""
    lines = "\n".join(f"- {names[trait]}: {score:.2f}" for trait, score in scores.items())
    user = (
        "כתוב דוח אישיות קצר בעברית על סמך הציונים הבאים בלבד. "
        "הדוח צריך לכלול: הצגה של כל ציון, ופסקת סיכום אחת שמחברת את הממדים. "
        "תאר את התשובות לשאלון בלבד, לא את האדם. "
        "אל תוסיף ציונים, תכונות או מספרים שלא מופיעים כאן:\n" + lines
    )
    return model.complete(SYSTEM_BASE, user)


def report_is_grounded(text: str, scores: dict[str, float], names: dict[str, str]) -> bool:
    """בדיקה דטרמיניסטית: כל תחום מופיע בדוח, ולכל תחום מופיע הציון שלו בדיוק."""
    for trait, score in scores.items():
        if names[trait] not in text:
            return False
        if f"{score:.2f}" not in text and f"{score:.1f}" not in text:
            return False
    return True
