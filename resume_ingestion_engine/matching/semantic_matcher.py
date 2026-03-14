"""
semantic_matcher.py
====================
Day 12 – Semantic Matching Engine

Matches a resume against job descriptions using:
    Layer 1 (offline): TF-IDF + overlap coefficient hybrid
    Layer 2 (auto):    SentenceTransformer embeddings
                       (activates when sentence-transformers is installed)

Supports:
    • Single JD matching
    • Multi-JD ranking (e.g. all 85 AI roles from AI_Engineer_modals.pdf)
    • Section-level scoring (summary, skills, experience, projects)
    • Skill gap analysis

Pipeline usage:
    from resume_ingestion_engine.matching.semantic_matcher import (
        match_resume_to_jd, rank_resume_against_jds, load_jds_from_pdf
    )
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Optional: sentence-transformers (Layer 2) ──────────────────
try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

_ST_MODEL = None  # lazy-loaded on first use


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

THRESHOLDS = {
    "excellent": 0.75,
    "good":      0.55,
    "fair":      0.35,
    "poor":      0.20,
}

SECTION_WEIGHTS = {
    "summary":        0.15,
    "skills":         0.35,
    "experience":     0.30,
    "projects":       0.15,
    "certifications": 0.05,
}

SKILL_SYNONYMS: Dict[str, str] = {
    r"\bml\b":           "machine learning",
    r"\bdl\b":           "deep learning",
    r"\bnlp\b":          "natural language processing",
    r"\bcv\b":           "computer vision",
    r"\bgen ai\b":       "generative ai",
    r"\bgenai\b":        "generative ai",
    r"\bllm\b":          "large language model",
    r"\bllms\b":         "large language model",
    r"\brag\b":          "retrieval augmented generation",
    r"\bk8s\b":          "kubernetes",
    r"\btf\b":           "tensorflow",
    r"\bsklearn\b":      "scikit-learn",
    r"\bsci-kit\b":      "scikit-learn",
    r"\baws\b":          "amazon web services",
    r"\bgcp\b":          "google cloud platform",
    r"\bgpt\b":          "large language model",
    r"\bllama\b":        "large language model",
    r"\bbert\b":         "transformer model",
    r"\bhf\b":           "hugging face",
    r"\bhuggingface\b":  "hugging face",
    r"\bmle\b":          "machine learning engineer",
    r"\bmlops\b":        "machine learning operations",
    r"\bllmops\b":       "large language model operations",
    r"\bci\/cd\b":       "continuous integration deployment",
    r"\bpoc\b":          "proof of concept",
    r"\bapi\b":          "application programming interface",
    r"\bsdk\b":          "software development kit",
    r"\bros\b":          "robot operating system",
    r"\biot\b":          "internet of things",
    r"\bsre\b":          "site reliability engineering",
    r"\brpa\b":          "robotic process automation",
    r"\ba\/b\b":         "ab testing",
    r"\behr\b":          "electronic health records",
}

STOP_WORDS = {
    "and", "or", "the", "a", "an", "in", "of", "for", "to", "with",
    "on", "at", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "that", "this", "these",
    "those", "it", "its", "we", "our", "i", "my", "you", "your",
    "as", "also", "such", "all", "any", "more", "well", "good",
    "using", "used", "use", "including", "include", "various",
    "strong", "knowledge", "experience", "understanding", "ability",
    "role", "overview", "responsibilities", "required", "preferred",
    "skills", "qualifications", "key", "build", "ensure", "work",
}


# ─────────────────────────────────────────────────────────────────────────────
#  JD LOADER
# ─────────────────────────────────────────────────────────────────────────────

def load_jds_from_pdf(pdf_path: str) -> List[Dict[str, str]]:
    """
    Parse a multi-role JD PDF into list of { num, title, text } dicts.

    Usage:
        jds     = load_jds_from_pdf("data/jds/AI_Engineer_modals.pdf")
        results = rank_resume_against_jds(resume_text, jds)
    """
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return _parse_jd_blocks(text)


def load_jds_from_text(text: str) -> List[Dict[str, str]]:
    """Parse raw multi-role JD text into list of JD dicts."""
    return _parse_jd_blocks(text)


def _parse_jd_blocks(text: str) -> List[Dict[str, str]]:
    """Split numbered multi-role text into individual JD blocks."""
    blocks = re.split(r"\n(?=\d+\.\s*[A-Z])", text)
    jds = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        title_m = re.match(r"(\d+)\.\s*(.+?)(?:\n|$)", block)
        if not title_m:
            continue

        num   = int(title_m.group(1))
        title = title_m.group(2).strip()

        # Handle multi-line titles like "Principal Machine Learning\nEngineer"
        remainder  = block[title_m.end():].strip()
        first_line = remainder.split("\n")[0].strip() if remainder else ""
        if (first_line
                and not re.match(r"role overview", first_line, re.IGNORECASE)
                and len(first_line) < 35
                and first_line[0].isupper()):
            title     = title + " " + first_line
            remainder = "\n".join(remainder.split("\n")[1:]).strip()

        jds.append({
            "num":   num,
            "title": title.strip(),
            "text":  block,
        })

    return jds


# ─────────────────────────────────────────────────────────────────────────────
#  TEXT PRE-PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase, expand synonyms, remove noise, strip stop words."""
    if not text:
        return ""

    t = text.lower()

    for pattern, replacement in SKILL_SYNONYMS.items():
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    tokens = [w for w in t.split() if w not in STOP_WORDS and len(w) > 1]
    return " ".join(tokens)


def extract_skills_tokens(text: str) -> List[str]:
    """Extract deduplicated skill tokens from text."""
    t = text.lower()
    for pattern, replacement in SKILL_SYNONYMS.items():
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    t = re.sub(r"[•●·\-–]", " ", t)
    t = re.sub(
        r"\b(languages|frameworks|tools|libraries|platforms|practices|"
        r"systems|knowledge|cloud|database|section|responsibilities|"
        r"requirements|qualifications|preferred)\b", " ", t
    )

    tokens = re.split(r"[,|;/\n\t()]+", t)
    skills = []
    for tok in tokens:
        tok = re.sub(r"[^a-z0-9\s\.\+#]", "", tok.strip()).strip()
        if 2 <= len(tok) <= 50 and tok not in STOP_WORDS:
            skills.append(tok)

    seen, unique = set(), []
    for s in skills:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

_SEC_PATTERNS = {
    "summary": re.compile(
        r"(?:summary|professional summary|profile|about me|objective|role overview)"
        r"[\s_\-:]*\n(.*?)(?=\n(?:key responsibilities|required skills|preferred|"
        r"technical skills|experience|education|projects|certif)|\Z)",
        re.IGNORECASE | re.DOTALL
    ),
    "skills": re.compile(
        r"(?:required skills[^\n]*|preferred skills[^\n]*|technical skills[^\n]*|"
        r"skills\s*&\s*qualifications[^\n]*|key skills[^\n]*|competencies[^\n]*|"
        r"tech stack[^\n]*)"
        r"[\s_\-:]*\n(.*?)(?=\n(?:growth outcomes|engagement type|summary|"
        r"final perspective|\d+\.[A-Z])|\Z)",
        re.IGNORECASE | re.DOTALL
    ),
    "experience": re.compile(
        r"(?:experience|work experience|employment|key responsibilities)"
        r"[\s_\-:]*\n(.*?)(?=\n[A-Z][\w &]{2,}[\s_\-]{2,}|\n(?:required|preferred"
        r"|growth|engagement|summary|education|certif)|\Z)",
        re.IGNORECASE | re.DOTALL
    ),
    "projects": re.compile(
        r"(?:projects|personal projects|academic projects|portfolio)"
        r"[\s_\-:]*\n(.*?)(?=\n[A-Z][\w &]{2,}[\s_\-]{2,}|\Z)",
        re.IGNORECASE | re.DOTALL
    ),
    "certifications": re.compile(
        r"(?:certifications?|certificates?|courses?)"
        r"[\s_\-:]*\n(.*?)(?=\n[A-Z][\w &]{2,}[\s_\-]{2,}|\Z)",
        re.IGNORECASE | re.DOTALL
    ),
}


def extract_sections(text: str) -> Dict[str, str]:
    """Extract named sections from resume or JD text."""
    sections: Dict[str, str] = {}
    for name, pattern in _SEC_PATTERNS.items():
        m = pattern.search(text)
        if m:
            body = m.group(1).strip()
            if len(body) > 10:
                sections[name] = body[:2500]
    if not sections:
        sections["summary"] = text.strip()[:3000]
    return sections


# ─────────────────────────────────────────────────────────────────────────────
#  SIMILARITY BACKENDS
# ─────────────────────────────────────────────────────────────────────────────

def _hybrid_similarity(a: str, b: str) -> float:
    """
    Overlap coefficient + JD coverage + TF-IDF cosine.
    Handles resume-vs-JD length mismatch correctly.
    """
    if not a.strip() or not b.strip():
        return 0.0
    try:
        ta = set(a.split())
        tb = set(b.split())
        intersection = ta & tb

        overlap  = len(intersection) / min(len(ta), len(tb)) if tb else 0.0
        coverage = len(intersection) / len(tb) if tb else 0.0

        vec    = TfidfVectorizer(ngram_range=(1, 2), min_df=1,
                                 max_features=8000, sublinear_tf=True)
        matrix = vec.fit_transform([a, b])
        tfidf  = float(cosine_similarity(matrix[0], matrix[1])[0][0])

        score = (overlap * 0.45) + (coverage * 0.35) + (tfidf * 0.20)
        return min(float(score), 1.0)
    except Exception:
        return 0.0


def _st_similarity(a: str, b: str) -> float:
    """SentenceTransformer cosine similarity."""
    global _ST_MODEL
    if _ST_MODEL is None:
        _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    emb  = _ST_MODEL.encode([a, b], convert_to_numpy=True, show_progress_bar=False)
    norm = np.linalg.norm(emb[0]) * np.linalg.norm(emb[1])
    return max(0.0, float(np.dot(emb[0], emb[1]) / norm) if norm > 0 else 0.0)


def compute_similarity(text_a: str, text_b: str) -> Tuple[float, str]:
    """Return (similarity 0–1, backend_name)."""
    ca = clean_text(text_a)
    cb = clean_text(text_b)
    if not ca or not cb:
        return 0.0, "empty"
    if _ST_AVAILABLE:
        return _st_similarity(ca, cb), "sentence-transformers"
    return _hybrid_similarity(ca, cb), "tfidf-hybrid"


# ─────────────────────────────────────────────────────────────────────────────
#  SKILL OVERLAP
# ─────────────────────────────────────────────────────────────────────────────

def analyse_skill_overlap(
    resume_skills_text: str,
    jd_skills_text: str,
) -> Dict:
    resume_skills = set(extract_skills_tokens(resume_skills_text))
    jd_skills     = set(extract_skills_tokens(jd_skills_text))

    if not jd_skills:
        return {"matched": [], "missing": [], "extra": [],
                "match_rate": 0.0, "coverage_score": 0.0}

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    extra   = resume_skills - jd_skills

    # Fuzzy partial matching
    fuzzy_matched = set()
    for r_skill in list(extra):
        for j_skill in list(missing):
            if ((r_skill in j_skill or j_skill in r_skill)
                    and abs(len(r_skill) - len(j_skill)) <= 6):
                fuzzy_matched.add(j_skill)

    all_matched = matched | fuzzy_matched
    match_rate  = len(all_matched) / len(jd_skills)

    return {
        "matched":        sorted(all_matched),
        "missing":        sorted(missing - fuzzy_matched),
        "extra":          sorted(extra),
        "match_rate":     round(match_rate, 3),
        "coverage_score": round(len(all_matched) / max(len(jd_skills), 1), 3),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION SCORER
# ─────────────────────────────────────────────────────────────────────────────

def score_sections(
    resume_sections: Dict[str, str],
    jd_sections: Dict[str, str],
    jd_raw: str = "",
) -> Dict[str, Dict]:
    resume_full = " ".join(resume_sections.values())
    jd_full     = " ".join(v for v in jd_sections.values() if v.strip())
    if not jd_full.strip():
        jd_full = jd_raw

    results = {}
    for section in SECTION_WEIGHTS:
        r_text          = resume_sections.get(section, "")
        j_text          = jd_sections.get(section, "") or jd_full
        missing_penalty = 1.0

        if not r_text:
            r_text          = resume_full
            missing_penalty = 0.75

        score, backend = compute_similarity(r_text, j_text)
        score          = score * missing_penalty

        results[section] = {
            "score":        round(score, 4),
            "label":        _score_label(score),
            "backend":      backend,
            "resume_chars": len(r_text),
            "jd_chars":     len(j_text),
        }
    return results


def _score_label(score: float) -> str:
    if score >= THRESHOLDS["excellent"]: return "excellent"
    if score >= THRESHOLDS["good"]:      return "good"
    if score >= THRESHOLDS["fair"]:      return "fair"
    if score >= THRESHOLDS["poor"]:      return "poor"
    return "very low"


# ─────────────────────────────────────────────────────────────────────────────
#  COMPOSITE SCORE + RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_composite_score(
    section_scores: Dict[str, Dict],
    skill_overlap: Dict,
) -> Dict:
    weighted_sum = 0.0
    total_weight = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        s = section_scores.get(section, {}).get("score", 0.0)
        if section == "skills":
            s = (s + skill_overlap.get("coverage_score", 0.0)) / 2
        weighted_sum += s * weight
        total_weight += weight

    raw   = weighted_sum / total_weight if total_weight > 0 else 0.0
    final = round(raw * 100, 1)
    return {
        "composite_score":     final,
        "composite_label":     _score_label(raw),
        "hire_recommendation": _hire_recommendation(final),
    }


def _hire_recommendation(score: float) -> str:
    if score >= 75: return "Strong Match — Highly Recommended"
    if score >= 55: return "Good Match — Recommend Interview"
    if score >= 35: return "Partial Match — Consider with Reservations"
    if score >= 20: return "Weak Match — Significant Gaps"
    return "Poor Match — Not Recommended"


def build_accuracy_report(
    section_scores, skill_overlap, composite, backend, target_role
) -> Dict:
    return {
        "target_role":         target_role or "Not specified",
        "backend_used":        backend,
        "composite_score":     composite["composite_score"],
        "composite_label":     composite["composite_label"],
        "hire_recommendation": composite["hire_recommendation"],
        "sections_above_fair": (
            f"{sum(1 for s in section_scores.values() if s.get('score',0) >= THRESHOLDS['fair'])}"
            f"/{len(section_scores)}"
        ),
        "skill_match_rate": f"{round(skill_overlap.get('match_rate', 0) * 100, 1)}%",
        "skills_matched":   len(skill_overlap.get("matched", [])),
        "skills_missing":   len(skill_overlap.get("missing", [])),
        "skills_extra":     len(skill_overlap.get("extra", [])),
        "section_scores": {
            k: f"{v.get('score', 0) * 100:.1f}% ({v.get('label', '')})"
            for k, v in section_scores.items()
        },
        "thresholds_used": THRESHOLDS,
        "weights_used":    SECTION_WEIGHTS,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def match_resume_to_jd(
    resume_text: str,
    jd_text: str,
    target_role: Optional[str] = None,
) -> Dict:
    """
    Match a resume against a single job description.

    Returns
    -------
    {
        "composite":       { composite_score, composite_label, hire_recommendation },
        "section_scores":  { summary, skills, experience, projects, certifications },
        "skill_overlap":   { matched, missing, extra, match_rate, coverage_score },
        "accuracy_report": { ... },
        "backend":         str
    }
    """
    resume_sections = extract_sections(resume_text)
    jd_sections     = extract_sections(jd_text)
    section_scores  = score_sections(resume_sections, jd_sections, jd_raw=jd_text)

    # Combine required + preferred skills sections for JD skill analysis
    jd_skills_text = " ".join([
        jd_sections.get("skills", ""),
        jd_text,  # include full JD to catch all skill mentions
    ])
    skill_overlap = analyse_skill_overlap(
        resume_sections.get("skills", resume_text[:2000]),
        jd_skills_text,
    )

    composite = compute_composite_score(section_scores, skill_overlap)
    backend   = "sentence-transformers" if _ST_AVAILABLE else "tfidf-hybrid"

    return {
        "composite":       composite,
        "section_scores":  section_scores,
        "skill_overlap":   skill_overlap,
        "accuracy_report": build_accuracy_report(
            section_scores, skill_overlap, composite, backend, target_role
        ),
        "backend": backend,
    }


def rank_resume_against_jds(
    resume_text: str,
    jds: List[Dict[str, str]],
    top_n: int = 10,
) -> List[Dict]:
    """
    Match a resume against all JDs and return top_n ranked results.

    Parameters
    ----------
    resume_text : full resume text
    jds         : list of { num, title, text } from load_jds_from_pdf()
    top_n       : number of top matches to return

    Returns
    -------
    Ranked list, each item:
    {
        "rank", "num", "title", "score", "label",
        "recommendation", "matched_skills", "missing_skills", "section_scores"
    }
    """
    results = []

    for jd in jds:
        r  = match_resume_to_jd(resume_text, jd["text"], target_role=jd["title"])
        sk = r["skill_overlap"]
        sr = r["section_scores"]

        results.append({
            "rank":           0,
            "num":            jd.get("num", 0),
            "title":          jd["title"],
            "score":          r["composite"]["composite_score"],
            "label":          r["composite"]["composite_label"],
            "recommendation": r["composite"]["hire_recommendation"],
            "matched_skills": sk.get("matched", []),
            "missing_skills": sk.get("missing", []),
            "section_scores": {
                k: round(v.get("score", 0) * 100, 1)
                for k, v in sr.items()
            },
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results[:top_n]


# ─────────────────────────────────────────────────────────────────────────────
#  STANDALONE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import json
    import os

    if len(sys.argv) < 3:
        print("Usage:")
        print("  # Match resume against all roles in a JD PDF:")
        print("  python -m resume_ingestion_engine.matching.semantic_matcher <resume.pdf> <jd.pdf> [top_n]")
        print()
        print("  # Match against a single JD text file:")
        print("  python -m resume_ingestion_engine.matching.semantic_matcher <resume.pdf> <jd.txt>")
        sys.exit(1)

    # ── Read resume ───────────────────────────────────────────────
    resume_path = sys.argv[1]
    if resume_path.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(resume_path) as pdf:
            resume_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    else:
        with open(resume_path, encoding="utf-8") as f:
            resume_text = f.read()

    base_name = os.path.splitext(os.path.basename(resume_path))[0]
    jd_path   = sys.argv[2]
    top_n     = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    backend   = "sentence-transformers" if _ST_AVAILABLE else "tfidf-hybrid"

    os.makedirs("output", exist_ok=True)

    if jd_path.endswith(".pdf"):
        # ── Multi-JD mode ─────────────────────────────────────────
        jds     = load_jds_from_pdf(jd_path)
        results = rank_resume_against_jds(resume_text, jds, top_n=top_n)

        print(f"\n{'='*70}")
        print(f"  RESUME   : {base_name}")
        print(f"  JD FILE  : {os.path.basename(jd_path)}  ({len(jds)} roles loaded)")
        print(f"  BACKEND  : {backend}")
        print(f"  TOP N    : {top_n}")
        print(f"{'='*70}")

        for r in results:
            filled = int(r["score"] / 5)
            bar    = "█" * filled + "░" * (20 - filled)
            print(f"\n  #{r['rank']:2d}  [{r['num']:2d}] {r['title']}")
            print(f"       Score : {r['score']:5.1f}%  |{bar}|  {r['label'].upper()}")
            print(f"       {r['recommendation']}")
            ss = r["section_scores"]
            print(f"       Skills={ss.get('skills',0):.0f}%  "
                  f"Exp={ss.get('experience',0):.0f}%  "
                  f"Summary={ss.get('summary',0):.0f}%  "
                  f"Projects={ss.get('projects',0):.0f}%")
            if r["matched_skills"]:
                print(f"       ✅ Matched : {', '.join(r['matched_skills'][:6])}")
            if r["missing_skills"]:
                print(f"       ❌ Missing : {', '.join(r['missing_skills'][:6])}")

        out_path = f"output/{base_name}_matches.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n{'='*70}")
        print(f"✅ Full results saved to: {out_path}")

    else:
        # ── Single JD mode ────────────────────────────────────────
        with open(jd_path, encoding="utf-8") as f:
            jd_text = f.read()

        result = match_resume_to_jd(resume_text, jd_text)
        rpt    = result["accuracy_report"]

        print(f"\n{'='*65}")
        print(f"  RESUME  : {base_name}")
        print(f"  BACKEND : {backend}")
        print(f"{'='*65}")
        print(f"  Score          : {rpt['composite_score']}/100  ({rpt['composite_label'].upper()})")
        print(f"  Recommendation : {rpt['hire_recommendation']}")
        print(f"\n  Section Scores:")
        for sec, val in rpt["section_scores"].items():
            w = SECTION_WEIGHTS.get(sec, 0)
            print(f"    {sec:18s}: {val}  (weight {w*100:.0f}%)")
        sk = result["skill_overlap"]
        print(f"\n  Skill match    : {rpt['skill_match_rate']}")
        if sk["matched"]:
            print(f"  Matched        : {', '.join(sk['matched'][:8])}")
        if sk["missing"]:
            print(f"  Missing        : {', '.join(sk['missing'][:8])}")

        out_path = f"output/{base_name}_match.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✅ Saved to: {out_path}")