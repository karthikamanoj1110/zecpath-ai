"""
education_parser.py
====================
Day 11 – Education & Certification Parsing

Extracts:
  - Degree type, field of study, institution, graduation year
  - Certifications with relevance category tagging
  - Normalizes naming conventions
  - Computes education relevance score against a target role

Pipeline integration (add to pipeline.py):
    from resume_ingestion_engine.extraction.education_parser import build_academic_profile
    payload["academic_profile"] = build_academic_profile(full_text, target_role=job_role)
"""

from typing import List, Dict, Any, Optional
import re


# ─────────────────────────────────────────────────────────────────────────────
#  NORMALIZATION MAPS
# ─────────────────────────────────────────────────────────────────────────────

DEGREE_NORMALIZATION: Dict[str, str] = {
    # Bachelor
    "b.tech": "Bachelor of Technology",      "btech": "Bachelor of Technology",
    "b.e":    "Bachelor of Engineering",     "be":    "Bachelor of Engineering",
    "b.sc":   "Bachelor of Science",         "bsc":   "Bachelor of Science",
    "b.s":    "Bachelor of Science",         "bs":    "Bachelor of Science",
    "b.a":    "Bachelor of Arts",            "ba":    "Bachelor of Arts",
    "b.com":  "Bachelor of Commerce",        "bcom":  "Bachelor of Commerce",
    "bca":    "Bachelor of Computer Applications",
    "b.ca":   "Bachelor of Computer Applications",
    # Master
    "m.tech": "Master of Technology",        "mtech": "Master of Technology",
    "m.e":    "Master of Engineering",
    "m.sc":   "Master of Science",           "msc":   "Master of Science",
    "m.s":    "Master of Science",           "ms":    "Master of Science",
    "m.a":    "Master of Arts",              "ma":    "Master of Arts",
    "mba":    "Master of Business Administration",
    "m.b.a":  "Master of Business Administration",
    "mca":    "Master of Computer Applications",
    "m.ca":   "Master of Computer Applications",
    # Doctorate
    "phd":       "Doctor of Philosophy",
    "ph.d":      "Doctor of Philosophy",
    "doctorate": "Doctor of Philosophy",
    # School
    "hsc":              "Higher Secondary Certificate",
    "higher secondary": "Higher Secondary Certificate",
    "12th":             "Higher Secondary Certificate",
    "ssc":              "Secondary School Certificate",
    "10th":             "Secondary School Certificate",
    "matriculation":    "Secondary School Certificate",
}

FIELD_NORMALIZATION: Dict[str, str] = {
    "cs":                     "Computer Science",
    "cse":                    "Computer Science and Engineering",
    "computer science":       "Computer Science",
    "it":                     "Information Technology",
    "information technology": "Information Technology",
    "ece":                    "Electronics and Communication Engineering",
    "eee":                    "Electrical and Electronics Engineering",
    "ai":                     "Artificial Intelligence",
    "ai & ml":                "Artificial Intelligence and Machine Learning",
    "ai and ml":              "Artificial Intelligence and Machine Learning",
    "data science":           "Data Science",
    "ds":                     "Data Science",
    "maths":                  "Mathematics",
    "math":                   "Mathematics",
    "stats":                  "Statistics",
    "statistics":             "Statistics",
    "commerce":               "Commerce",
    "business":               "Business Administration",
}

TECH_RELEVANT_FIELDS = {
    "computer science",
    "computer science and engineering",
    "information technology",
    "artificial intelligence",
    "artificial intelligence and machine learning",
    "data science",
    "electronics and communication engineering",
    "electrical and electronics engineering",
    "mathematics",
    "statistics",
    "software engineering",
}

DEGREE_LEVEL_SCORE: Dict[str, int] = {
    "Doctor of Philosophy":              5,
    "Master of Technology":              4,
    "Master of Engineering":             4,
    "Master of Science":                 4,
    "Master of Computer Applications":   4,
    "Master of Business Administration": 3,
    "Bachelor of Technology":            3,
    "Bachelor of Engineering":           3,
    "Bachelor of Science":               3,
    "Bachelor of Computer Applications": 3,
    "Bachelor of Arts":                  2,
    "Bachelor of Commerce":              2,
    "Higher Secondary Certificate":      1,
    "Secondary School Certificate":      1,
}


# ─────────────────────────────────────────────────────────────────────────────
#  CERTIFICATION RELEVANCE CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────

CERT_CATEGORIES: Dict[str, List[str]] = {
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "cloud practitioner",
        "solutions architect", "cloud engineer", "cloud developer",
        "vertex ai", "sysops",
    ],
    "data_science_ml": [
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "data science", "mlops", "databricks", "spark",
        "tableau", "power bi", "data analyst", "data engineer",
    ],
    "ai_generative": [
        "openai", "llm", "generative ai", "prompt engineering",
        "langchain", "rag", "chatgpt", "hugging face", "nlp",
        "large language model",
    ],
    "programming": [
        "python", "java", "javascript", "sql", "r programming",
        "full stack", "frontend", "backend", "golang", "rust",
    ],
    "cybersecurity": [
        "cissp", "ceh", "comptia security", "iso 27001", "ethical hacking",
        "penetration testing", "cybersecurity", "information security",
        "nabet", "stqc",
    ],
    "project_management": [
        "pmp", "prince2", "scrum", "agile", "safe", "csm",
        "certified scrum", "project management", "itil",
    ],
    "database": [
        "oracle", "mysql", "mongodb", "postgresql", "dba",
        "sql server", "nosql", "database administrator",
    ],
    "networking": [
        "cisco", "ccna", "ccnp", "network+", "linux",
        "comptia network", "juniper", "networking",
    ],
    "iot_embedded": [
        "iot", "internet of things", "arduino", "raspberry pi",
        "embedded systems", "icfoss",
    ],
    "other": [],
}

ISSUER_MAP: Dict[str, str] = {
    "aws":             "Amazon Web Services",
    "amazon":          "Amazon Web Services",
    "microsoft":       "Microsoft",
    "azure":           "Microsoft",
    "google":          "Google",
    "gcp":             "Google",
    "cisco":           "Cisco",
    "oracle":          "Oracle",
    "coursera":        "Coursera",
    "udemy":           "Udemy",
    "linkedin":        "LinkedIn Learning",
    "ibm":             "IBM",
    "iso":             "ISO",
    "nabet":           "NABET",
    "stqc":            "STQC",
    "icfoss":          "ICFOSS",
    "pmi":             "Project Management Institute",
    "scrum":           "Scrum Alliance",
    "comptia":         "CompTIA",
    "ec-council":      "EC-Council",
    "nvidia":          "NVIDIA",
    "deeplearning.ai": "DeepLearning.AI",
}

# Target role keyword → cert categories that boost match score
ROLE_CERT_MAP: Dict[str, List[str]] = {
    "ai":        ["ai_generative", "data_science_ml", "cloud"],
    "ml":        ["data_science_ml", "ai_generative", "cloud"],
    "data":      ["data_science_ml", "database", "cloud"],
    "cloud":     ["cloud", "networking"],
    "security":  ["cybersecurity"],
    "devops":    ["cloud", "networking"],
    "fullstack": ["programming", "database"],
    "frontend":  ["programming"],
    "backend":   ["programming", "database"],
    "manager":   ["project_management"],
    "engineer":  ["programming", "cloud", "data_science_ml"],
}


# ─────────────────────────────────────────────────────────────────────────────
#  REGEX PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

DEGREE_PATTERN = re.compile(
    r"\b("
    r"ph\.?d\.?|doctorate|"
    r"m\.?tech\.?|m\.?e\.?\b|m\.?sc\.?|m\.?s\.?\b|m\.?b\.?a\.?|m\.?c\.?a\.?|m\.?a\.?\b|"
    r"b\.?tech\.?|b\.?e\.?\b|b\.?sc\.?|b\.?s\.?\b|b\.?c\.?a\.?|b\.?a\.?\b|b\.?com\.?|"
    r"bachelor(?:\s+of)?[\w\s]{0,25}|master(?:\s+of)?[\w\s]{0,25}|"
    r"higher\s+secondary|hsc|ssc|12th|10th|matriculation"
    r")\b",
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r"\b(19[7-9]\d|20[0-3]\d)\b")

INSTITUTION_KEYWORDS = re.compile(
    r"\b(university|college|institute|school|academy|"
    r"polytechnic|iit|nit|bits|vit|srm|amrita|anna\s+university)\b",
    re.IGNORECASE,
)

EDU_SECTION_START = re.compile(
    r"\b(education|academic\s+background|academic\s+qualifications?|"
    r"qualifications?|educational\s+details?)\b",
    re.IGNORECASE,
)

EDU_SECTION_END = re.compile(
    r"\b(experience|work\s+experience|skills|projects|"
    r"certifications?|awards|publications|interests|summary)\b",
    re.IGNORECASE,
)

CERT_SECTION_START = re.compile(
    r"\b(certifications?|certificates?|professional\s+certifications?|"
    r"licenses?\s*[&and]*\s*certifications?|courses?|training|"
    r"professional\s+development)\b",
    re.IGNORECASE,
)

CERT_SECTION_END = re.compile(
    r"\b(experience|education|skills|projects|awards|publications|"
    r"interests|summary|languages?)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
#  NORMALIZATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def normalize_degree(raw: str) -> str:
    key = raw.lower().strip().rstrip(".")
    return DEGREE_NORMALIZATION.get(key, raw.title())


def normalize_field(raw: str) -> str:
    key = raw.lower().strip()
    return FIELD_NORMALIZATION.get(key, raw.title())


def tag_certification(cert_text: str) -> str:
    """Return relevance category label for a certification string."""
    lower = cert_text.lower()
    for category, keywords in CERT_CATEGORIES.items():
        if category == "other":
            continue
        if any(kw in lower for kw in keywords):
            return category
    return "other"


def detect_issuer(cert_name: str) -> Optional[str]:
    """Detect the issuing organisation from the cert name."""
    lower = cert_name.lower()
    for key, issuer in ISSUER_MAP.items():
        if key in lower:
            return issuer
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION SLICING
# ─────────────────────────────────────────────────────────────────────────────

def extract_education_section(text: str) -> str:
    """Slice out just the education section from full resume text."""
    pattern = re.compile(
        r"(?:" + EDU_SECTION_START.pattern + r")"
        r"\s*[-:]*\s*(.*?)"
        r"(?=" + EDU_SECTION_END.pattern + r"|$)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else text


def extract_certification_section(text: str) -> str:
    """Slice out just the certifications section from full resume text."""
    pattern = re.compile(
        r"(?:" + CERT_SECTION_START.pattern + r")"
        r"\s*[-:]*\s*(.*?)"
        r"(?=" + CERT_SECTION_END.pattern + r"|$)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


# ─────────────────────────────────────────────────────────────────────────────
#  EDUCATION EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extract all education entries from resume text.

    Returns
    -------
    List of dicts:
    {
        "degree":          "Bachelor of Technology",   # normalized
        "degree_raw":      "B.Tech",                   # as found in resume
        "field":           "Computer Science",         # normalized
        "institution":     "Mohandas College ...",
        "year":            "2019",
        "relevance_score": 4                           # 1–5
    }
    """
    section = extract_education_section(text)
    flat    = re.sub(r"\s+", " ", section)

    # Candidate chunks: split by bullet or comma, plus original lines
    chunks  = re.split(r"[\n•·●]|(?<=[,;])\s+", flat)
    chunks += [l.strip() for l in section.splitlines() if l.strip()]

    results   = []
    seen_keys = set()

    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 6:
            continue

        degree_m = DEGREE_PATTERN.search(chunk)
        if not degree_m:
            continue

        degree_raw  = degree_m.group(0).strip()
        degree_norm = normalize_degree(degree_raw)
        field       = _extract_field(chunk, degree_m)
        field_norm  = normalize_field(field) if field else None
        institution = _extract_institution(chunk, chunks)
        year_m      = YEAR_PATTERN.search(chunk)
        year        = year_m.group(0) if year_m else None
        score       = _edu_relevance_score(degree_norm, field_norm)

        # Deduplicate
        key = (degree_raw.lower(), (institution or "").lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)

        results.append({
            "degree":          degree_norm,
            "degree_raw":      degree_raw,
            "field":           field_norm,
            "institution":     institution,
            "year":            year,
            "relevance_score": score,
        })

    return results


def _extract_field(chunk: str, degree_match: re.Match) -> Optional[str]:
    """Pull field of study from text immediately after the degree token."""
    after = chunk[degree_match.end():]
    after = re.sub(r"^[\s,\-–in]+", "", after)   # strip connectors
    after = YEAR_PATTERN.sub("", after)            # remove years
    after = INSTITUTION_KEYWORDS.sub("", after)    # remove institution words
    field = re.split(r"[,|;(–\-]", after)[0].strip()
    if not field or len(field) < 3 or re.fullmatch(r"[\d\s]+", field):
        return None
    return field[:60].strip()


def _extract_institution(chunk: str, all_chunks: List[str]) -> Optional[str]:
    """Find institution name in current chunk or nearby chunks."""
    for c in [chunk] + all_chunks:
        if INSTITUTION_KEYWORDS.search(c):
            clean = YEAR_PATTERN.sub("", c)
            clean = DEGREE_PATTERN.sub("", clean).strip(" ,.-–()")
            if 3 < len(clean) < 120:
                return clean.strip()
    return None


def _edu_relevance_score(degree: str, field: Optional[str]) -> int:
    """Score 1–5: degree level + 1 bonus if field is tech-relevant."""
    base  = DEGREE_LEVEL_SCORE.get(degree, 2)
    bonus = 1 if field and field.lower() in TECH_RELEVANT_FIELDS else 0
    return min(base + bonus, 5)


# ─────────────────────────────────────────────────────────────────────────────
#  CERTIFICATION EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

def extract_certifications(text: str) -> List[Dict[str, Any]]:
    """
    Extract certifications from resume text.

    Returns
    -------
    List of dicts:
    {
        "name":     "AWS Certified Solutions Architect",
        "category": "cloud",
        "issuer":   "Amazon Web Services",
        "year":     "2023"
    }
    """
    section     = extract_certification_section(text)
    search_text = section if section else text   # fallback to full text

    results    = []
    seen_names = set()

    for line in re.split(r"[\n•·●|]", search_text):
        line = line.strip()

        if len(line) < 8:
            continue
        if re.fullmatch(r"[\d\s\-/.,]+", line):   # skip pure numeric lines
            continue
        # Skip lines that are clearly education entries
        if DEGREE_PATTERN.search(line) and INSTITUTION_KEYWORDS.search(line):
            continue

        year_m = YEAR_PATTERN.search(line)
        year   = year_m.group(0) if year_m else None

        name = YEAR_PATTERN.sub("", line).strip(" ,.-–")
        if len(name) < 6:
            continue

        name_key = name.lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        results.append({
            "name":     name,
            "category": tag_certification(name),
            "issuer":   detect_issuer(name),
            "year":     year,
        })

    return results


# ─────────────────────────────────────────────────────────────────────────────
#  EDUCATION RELEVANCE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def compute_education_relevance(
    education: List[Dict],
    certifications: List[Dict],
    target_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute overall education relevance profile.

    Parameters
    ----------
    education      : output of extract_education()
    certifications : output of extract_certifications()
    target_role    : optional e.g. "ai engineer"

    Returns
    -------
    {
        "highest_degree":        "Bachelor of Technology",
        "highest_degree_score":  3,
        "field_relevant":        True,
        "cert_categories":       ["cloud", "cybersecurity"],
        "total_certs":           4,
        "role_match_score":      7,
        "summary":               "..."
    }
    """
    if not education and not certifications:
        return {
            "highest_degree":       None,
            "highest_degree_score": 0,
            "field_relevant":       False,
            "cert_categories":      [],
            "total_certs":          0,
            "role_match_score":     0,
            "summary":              "No education or certifications found.",
        }

    # Sort education by degree level to find the highest
    sorted_edu = sorted(
        education,
        key=lambda e: DEGREE_LEVEL_SCORE.get(e.get("degree", ""), 0),
        reverse=True,
    )
    top_edu   = sorted_edu[0] if sorted_edu else {}
    top_score = DEGREE_LEVEL_SCORE.get(top_edu.get("degree", ""), 0)

    field_relevant = any(
        (e.get("field") or "").lower() in TECH_RELEVANT_FIELDS
        for e in education
    )

    cert_cats  = list({c["category"] for c in certifications if c["category"] != "other"})
    role_score = _compute_role_match(top_edu, certifications, target_role, field_relevant)

    return {
        "highest_degree":       top_edu.get("degree"),
        "highest_degree_score": top_score,
        "field_relevant":       field_relevant,
        "cert_categories":      cert_cats,
        "total_certs":          len(certifications),
        "role_match_score":     role_score,
        "summary":              _build_summary(top_edu, certifications, field_relevant, role_score),
    }


def _compute_role_match(
    top_edu: Dict,
    certs: List[Dict],
    target_role: Optional[str],
    field_relevant: bool,
) -> int:
    """Return 0–10 education fit score for the target role."""
    score = 0
    score += min(DEGREE_LEVEL_SCORE.get(top_edu.get("degree", ""), 0), 4)  # max 4 pts
    if field_relevant:
        score += 1                                                           # 1 pt
    score += min(len(certs), 3)                                             # max 3 pts

    if target_role:
        role_lower = target_role.lower()
        for keyword, relevant_cats in ROLE_CERT_MAP.items():
            if keyword in role_lower:
                bonus = sum(1 for c in certs if c["category"] in relevant_cats)
                score += min(bonus, 2)                                      # max 2 pts
                break

    return min(score, 10)


def _build_summary(
    top_edu: Dict,
    certs: List[Dict],
    field_relevant: bool,
    role_score: int,
) -> str:
    parts = []
    if top_edu.get("degree"):
        line = top_edu["degree"]
        if top_edu.get("field"):
            line += f" in {top_edu['field']}"
        if top_edu.get("institution"):
            line += f" from {top_edu['institution']}"
        if top_edu.get("year"):
            line += f" ({top_edu['year']})"
        parts.append(line)

    if certs:
        cats = list({c["category"] for c in certs if c["category"] != "other"})
        parts.append(f"{len(certs)} certification(s) in: {', '.join(cats)}")

    if field_relevant:
        parts.append("Field of study relevant to tech roles")

    parts.append(f"Education relevance score: {role_score}/10")
    return " | ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC API — single entry point for pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

def build_academic_profile(
    text: str,
    target_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point. Wire into pipeline.py:

        from resume_ingestion_engine.extraction.education_parser import build_academic_profile
        payload["academic_profile"] = build_academic_profile(full_text, target_role=job_role)

    Parameters
    ----------
    text        : full normalized resume text (output of rebuild_text_for_nlp)
    target_role : optional job role string e.g. "ai engineer"

    Returns
    -------
    {
        "education":      [ { degree, degree_raw, field, institution, year, relevance_score } ],
        "certifications": [ { name, category, issuer, year } ],
        "relevance":      { highest_degree, highest_degree_score, field_relevant,
                            cert_categories, total_certs, role_match_score, summary }
    }
    """
    education      = extract_education(text)
    certifications = extract_certifications(text)
    relevance      = compute_education_relevance(education, certifications, target_role)

    return {
        "education":      education,
        "certifications": certifications,
        "relevance":      relevance,
    }