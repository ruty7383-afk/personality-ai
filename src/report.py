from src.scoring import TRAITS

TRAIT_HE = {
    "openness": "פתיחות לחוויות חדשות",
    "conscientiousness": "מצפוניות",
    "extraversion": "מוחצנות",
    "agreeableness": "נעימות בין-אישית",
    "neuroticism": "רגישות רגשית",
}

# תיאורים לדוגמה בלבד (שאלון דמו). אפשר להחליף בתיאורים מאושרים.
TRAIT_PHRASE = {
    "openness": "נטייה לחשיבה מופשטת ולניסוי דברים חדשים",
    "conscientiousness": "נטייה לתכנון, סדר והשלמת משימות",
    "extraversion": "נטייה לחברתיות ולאנרגיה מחוץ לבית",
    "agreeableness": "נטייה לשיתוף פעולה ולהתחשבות באחרים",
    "neuroticism": "נטייה לחוויית לחץ ורגשות שליליים",
}

LIMITS = (
    "שאלון זה הוא הדגמה לימודית בהשראת Big Five. "
    "הוא אינו מאומת מחקרית, אינו אבחון פסיכולוגי ואינו מדד קליני."
)


def level(score: float) -> str:
    if score < 2.5:
        return "נמוכה"
    if score <= 3.5:
        return "בינונית"
    return "גבוהה"


def build_report(scores: dict[str, float], reviewer_note: str | None = None) -> str:
    """מייצר דוח רק מתוך הציונים ומהתיאורים המאושרים."""
    lines = ["בתשובות לשאלון זה התקבלו הציונים הבאים (על סולם 1-5):"]
    for trait in TRAITS:
        score = scores[trait]
        lines.append(
            f"- {TRAIT_HE[trait]}: {score:.2f} (רמה {level(score)}). "
            f"התשובות משקפות {TRAIT_PHRASE[trait]}."
        )
    lines.append(LIMITS)
    if reviewer_note:
        lines.append(f"הערת בודק שנכללה בתיקון: {reviewer_note}")
    return "\n".join(lines)