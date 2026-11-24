from pathlib import Path

from src.scoring import TRAITS

TRAIT_HE = {
    "openness": "פתיחות לחוויות חדשות",
    "conscientiousness": "מצפוניות",
    "extraversion": "מוחצנות",
    "agreeableness": "נעימות בין-אישית",
    "neuroticism": "רגישות רגשית",
}

TRAIT_EN = {
    "openness": "Openness",
    "conscientiousness": "Conscientiousness",
    "extraversion": "Extraversion",
    "agreeableness": "Agreeableness",
    "neuroticism": "Emotional sensitivity",
}

# תיאורים זהירים: מתארים את התשובות לשאלון בלבד, לא את האדם.
DESCRIPTIONS = {
    "openness": {
        "low": "נטייה להעדיף דרכים מוכרות ומעשיות",
        "mid": "שילוב של סקרנות ושל העדפה לדרכים מוכרות",
        "high": "נטייה לסקרנות, לחשיבה מופשטת ולניסוי רעיונות חדשים",
    },
    "conscientiousness": {
        "low": "נטייה לגמישות וספונטניות בתכנון",
        "mid": "שילוב של תכנון וגמישות",
        "high": "נטייה לסדר, לתכנון ולהשלמת משימות",
    },
    "extraversion": {
        "low": "נטייה לשקט ולשהות עם מעט אנשים",
        "mid": "שילוב של חברתיות ושקט",
        "high": "נטייה לחברתיות ולאנרגיה בסביבה חברתית",
    },
    "agreeableness": {
        "low": "נטייה לשיקול ישיר ולעמידה על דעה",
        "mid": "שילוב של שיתוף פעולה ושל עמידה על עמדה",
        "high": "נטייה להתחשבות, לשיתוף פעולה ולאמפתיה",
    },
    "neuroticism": {
        "low": "נטייה ליציבות רגשית והתמודדות רגועה עם לחץ",
        "mid": "שילוב של יציבות ורגישות לתנודות",
        "high": "נטייה לרגישות רגשית ולחוויית לחץ ורגשות שליליים",
    },
}

LIMITS = (
    "שאלון זה הוא הדגמה לימודית בהשראת Big Five. "
    "הוא שאלון דיווח עצמי, אינו מאומת מחקרית לעברית, אינו אבחון פסיכולוגי ואינו מדד קליני."
)


def level(score: float) -> str:
    if score < 2.5:
        return "נמוכה"
    if score <= 3.5:
        return "בינונית"
    return "גבוהה"


def band(score: float) -> str:
    if score < 2.5:
        return "low"
    if score <= 3.5:
        return "mid"
    return "high"


def highlights(scores: dict[str, float]) -> list[str]:
    """נקודות בולטות שנגזרות רק מהציונים, בלי לפרש טקסט חופשי."""
    ranked = sorted(TRAITS, key=lambda t: scores[t])
    lowest, highest = ranked[0], ranked[-1]
    if scores[highest] - scores[lowest] < 0.5:
        return ["הציונים קרובים זה לזה, ואין ממד שבולט במיוחד."]
    return [
        f"הממד הגבוה ביותר: {TRAIT_HE[highest]} ({scores[highest]:.2f}).",
        f"הממד הנמוך ביותר: {TRAIT_HE[lowest]} ({scores[lowest]:.2f}).",
    ]


def build_report(scores: dict[str, float], reviewer_note: str | None = None) -> str:
    """דוח שמבוסס רק על הציונים ועל התיאורים המאושרים."""
    lines = ["בתשובות לשאלון זה התקבלו הציונים הבאים (על סולם 1-5):"]
    for trait in TRAITS:
        score = scores[trait]
        lines.append(
            f"- {TRAIT_HE[trait]}: {score:.2f} (רמה {level(score)}). "
            f"התשובות משקפות {DESCRIPTIONS[trait][band(score)]}."
        )
    lines.extend(highlights(scores))
    lines.append(LIMITS)
    if reviewer_note:
        lines.append(f"הערת בודק שנכללה בתיקון: {reviewer_note}")
    return "\n".join(lines)


def save_chart(scores: dict[str, float], path: Path) -> Path:
    """שומר גרף עמודות של חמשת הממדים. הכותרות באנגלית כדי להימנע מבעיות תצוגה של עברית בגרף."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [TRAIT_EN[t] for t in TRAITS]
    values = [scores[t] for t in TRAITS]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color="#4a7fb0")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Score (1-5)")
    ax.set_title("Questionnaire score profile (self-report, not a diagnosis)")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
