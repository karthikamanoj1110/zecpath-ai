from typing import List, Dict
import re


ROLE_SYNONYMS = {
    "ai engineer": [
        "ai engineer",
        "machine learning engineer",
        "ml engineer",
        "deep learning engineer"
    ],
    "data scientist": [
        "data scientist",
        "applied scientist"
    ],
    "backend developer": [
        "backend developer",
        "backend engineer",
        "server side developer"
    ],
    "frontend developer": [
        "frontend developer",
        "ui developer"
    ],
    "full stack developer": [
        "full stack developer",
        "fullstack engineer"
    ],
    "devops engineer": [
        "devops engineer",
        "site reliability engineer",
        "platform engineer"
    ]
}

ROLE_SYNONYMS["ai engineer"].extend([
    "artificial intelligence engineer",
    "machine learning engineer",
    "machine learning software engineer"
])

ROLE_SYNONYMS["data scientist"].extend([
    "senior data scientist",
    "machine learning engineer"
])


def score_experience_relevance(
    resume_experience: List[Dict],
    jd_role: str
) -> Dict:

    if not resume_experience or not jd_role:
        return {
            "relevance_score": 0.0,
            "matched_roles": []
        }

    jd_role = jd_role.lower()

    matched = []
    total_months = 0

    role_aliases = _expand_role(jd_role)

    for exp in resume_experience:

        title = (exp.get("job_title") or "").lower()
        title = re.sub(r"[^a-z ]", " ", title)
        title = re.sub(r"\s+", " ", title)

        if not title:
            continue

        for alias in role_aliases:
            if alias in title:
                matched.append({
                    "job_title": exp.get("job_title"),
                    "company": exp.get("company"),
                    "months": exp.get("duration_months", 0)
                })
                total_months += exp.get("duration_months", 0)
                break

    score = min(total_months / 60.0, 1.0)

    return {
        "relevance_score": round(score, 2),
        "matched_roles": matched,
        "matched_experience_months": total_months
    }


# -------------------------------------------------------
def _expand_role(jd_role: str):

    jd_role = jd_role.lower()
    jd_role = re.sub(r"[^a-z ]", " ", jd_role)
    jd_role = re.sub(r"\s+", " ", jd_role).strip()

    for base, aliases in ROLE_SYNONYMS.items():

        base_norm = base.lower()

        # direct hit on base
        if base_norm in jd_role:
            return aliases

        # hit on any alias
        for a in aliases:
            if a in jd_role:
                return aliases

    return [jd_role]
