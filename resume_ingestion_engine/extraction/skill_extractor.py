from typing import List, Dict
import re

TECH_SEED = {
    "python","tensorflow","pytorch","keras","nlp","computer vision","rag",
    "llm","langchain","mlflow","docker","kubernetes","aws","azure","gcp",
    "spark","airflow","pandas","numpy","scikit-learn","opencv","sql",
    "fastapi","flask","streamlit","huggingface"
}

SOFT_SEED = {
    "communication","leadership","stakeholder management",
    "project management","team leadership","presentation",
    "mentoring","collaboration","agile"
}
# -------------------------------------------------------
# Extractor
# -------------------------------------------------------

def extract_skill_section(text:str) -> str:

    m = re.search(
        r"(skills|technical skills|skill set|tools|technologies)(.*?)(experience|education|projects|certifications|summary)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    return m.group(2) if m else ""


def extract_resume_skills(text: str):

    block = extract_skill_section(text)

    tokens = re.split(r"[•,\n]", block)

    technical = []
    non_technical = []
    other = []

    for t in tokens:
        s = t.strip().lower()

        if not s or len(s) < 2:
            continue

        if s in TECH_SEED:
            technical.append(s)
        elif s in SOFT_SEED:
            non_technical.append(s)
        else:
            other.append(s)

    return {
    "technical": [
        {"skill": s, "confidence": _confidence_from_alias(s)}
        for s in sorted(set(technical))
    ],
    "non_technical": [
        {"skill": s, "confidence": _confidence_from_alias(s)}
        for s in sorted(set(non_technical))
    ],
    "other": [
        {"skill": s, "confidence": _confidence_from_alias(s)}
        for s in sorted(set(other))
    ]
}


# -------------------------------------------------------
# simple confidence logic (rule-based)
# -------------------------------------------------------

def _confidence_from_alias(alias: str) -> float:

    # longer / more explicit matches are more reliable
    if len(alias.split()) >= 2:
        return 0.92

    return 0.85
