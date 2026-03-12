from typing import List, Dict
import re
import os
from datetime import datetime


DATE_PATTERN = re.compile(
    r'(?P<start>'
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}'
        r'|\d{1,2}/\d{4}'
        r'|\d{4}'
    r')\s*[–\-to]+\s*'
    r'(?P<end>'
        r'present|preset|current|currently|now|till\s*date|to\s*date'
        r'|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}'
        r'|\d{1,2}/\d{4}'
        r'|\d{4}'
    r')',
    re.IGNORECASE
)

TITLE_PATTERN = re.compile(
    r"(ai|ml|machine learning|data|software|backend|frontend|full\s*stack|devops|research|senior|junior|lead|principal|head|chief|manager|director|architect|consultant|specialist|analyst|scientist|engineer|developer|Artificial Intelligence Engineer|intern)([\w\s\-&/()]{0,40}?)(?=\s+[A-Z][a-z]|\s*$)",
    re.IGNORECASE
)

COMPANY_PATTERN = re.compile(
    r"(?:at|@)\s+([A-Z][A-Za-z0-9 &\-.]+)"
)

LOCATION_COUNTRY_PATTERN = re.compile(
    r'^'
    r'(?:'
        # Pattern 1: "City, Country"  or  "City, State, Country"
        r'[\w\s\.\-]+,\s*[\w\s\.\-]+'
        r'|'
        # Pattern 2: Single word (no spaces) — standalone country like "Thailand"
        r'\w+'
        r'|'
        # Pattern 3: Two words max — "New York", "Sri Lanka", "South Korea"
        r'\w+\s+\w+'
    r')'
    r'\s*$',
    re.IGNORECASE
)

BULLET_PATTERN    = re.compile(r'^[•\-]\s+')
SEPARATOR_PATTERN = re.compile(r'^_+$')


def extract_experience_section(text: str) -> str:
    start_m = re.search(
        r'(work experience|experience)\s*[_\-]{0,10}\s*\n',
        text, re.IGNORECASE
    )
    if not start_m:
        start_m = re.search(r'(work experience|experience)\b', text, re.IGNORECASE)
    if not start_m:
        return ""

    section_start = start_m.end()

    end_m = re.search(
        r'\n(projects|education|certificates?|certifications?|skills|'
        r'professional skills|awards|publications|interests)\s*[\n_\-]',
        text[section_start:], re.IGNORECASE
    )
    section_end = (section_start + end_m.start()) if end_m else len(text)
    return text[section_start:section_end]

def is_location_line(line: str) -> bool:
    """
    Detects location lines by structure — no hardcoded city/country names.
    Works for:
        "New York, United States"     ← City, Country
        "San Francisco, USA"          ← City, Abbreviation
        "Lahore, Pakistan"            ← City, Country
        "Thailand"                    ← Country only (no comma)
        "New York"                    ← City only (no comma)
        "Andhra Pradesh, India"       ← State, Country
    """
    line = line.strip()

    if not line:
        return False

    # Must be short — location lines are rarely more than 5 words
    if len(line.split()) > 5:
        return False

    # Must not contain job title keywords
    if re.search(
        r'\b(engineer|developer|scientist|analyst|manager|intern|'
        r'lead|senior|junior|architect|consultant|director|officer|'
        r'specialist|head|chief|president|associate)\b',
        line, re.IGNORECASE
    ):
        return False

    # Pattern 1: Has comma — "City, Country" structure
    if re.match(r'^[\w\s\.\-]+,\s*[\w\s\.\-]+$', line):
        return True

    # Pattern 2: 1–2 words, no comma — "Thailand", "New York"
    if re.match(r'^\w+$', line) and len(line) < 20:
        return True

    return False

# In is_skip_line()
def is_skip_line(line: str) -> bool:
    if not line:
        return True
    if BULLET_PATTERN.match(line):
        return True
    if SEPARATOR_PATTERN.match(line):
        return True
    if is_location_line(line):        # ✅ replaces both old patterns
        return True
    return False





def extract_title_company(line: str):
    line = re.sub(r'^[-•]\s*', '', line).strip()

    # Strategy 1: last ALL-CAPS word(s) = company
    # e.g. "Senior Data Scientist BLOCBELT" or "ML Engineer GOOGLE-KAGGLE"
    company_m = re.search(r'(?<!\w)([A-Z][A-Z0-9-]{2,}(?:\s[A-Z][A-Z0-9-]+)*)\s*$', line)
    if company_m:
        company = company_m.group(1).strip()
        title   = line[:company_m.start()].strip(" –-, ")
        if title and len(company) >= 3:
            return title, company

    # Strategy 2: hyphenated company like "Crypto-Express"
    hyphen_m = re.search(
        r'^(?P<title>.+?)\s+(?P<company>[A-Z][a-z]+-[A-Z][a-z]+)\s*$', line
    )
    if hyphen_m:
        return hyphen_m.group("title").strip(), hyphen_m.group("company").strip()

    # Strategy 3: "Title - Company" dash separated
    # e.g. "Senior Data Scientist - Robert Bosch"
    dash_m = re.search(
        r'^(?P<title>[A-Za-z0-9 /&()]+?)\s*[-–]\s*(?P<company>[A-Za-z0-9 .,&]+)$',
        line.strip()
    )
    if dash_m:
        t = dash_m.group("title").strip()
        c = dash_m.group("company").strip()
        if t and c and len(c) > 2:
            return t, c
    title_end_m = re.search(
    r'^(.*?\b(?:engineer|developer|scientist|analyst|manager|intern|lead|'
    r'senior|junior|architect|consultant|director|specialist|officer|'
    r'head|chief|associate|researcher|trainer|instructor)\b)',
    line, re.IGNORECASE
    )
    if title_end_m:
        title = title_end_m.group(1).strip()
        after = line[title_end_m.end():].strip(" –-, ")
        if after:
            return title, after
    # Strategy 4: longest TITLE_PATTERN match → everything after = company
    best_end = 0
    for m in TITLE_PATTERN.finditer(line):
        if m.end() > best_end:
            best_end = m.end()
    if best_end:
        title = line[:best_end].strip(" –-, ")
        after = line[best_end:].strip(" –-, ")
        return title, (after if after else None)

    return line.strip(), None


def extract_experience_blocks(text: str) -> List[Dict]:
    section = extract_experience_section(text)
    if not section.strip():
        section = text

    all_lines  = [l.strip() for l in section.splitlines()]
    results    = []
    seen_dates = set()

    for i, line in enumerate(all_lines):
        if not line:
            continue

        date_m = DATE_PATTERN.search(line)
        if not date_m:
            continue

        start_key = (date_m.group("start").lower(), date_m.group("end").lower())
        if start_key in seen_dates:
            continue
        seen_dates.add(start_key)

        sd = parse_date(date_m.group("start"))
        ed = parse_date(date_m.group("end"))

        title   = None
        company = None

        before_date = line[:date_m.start()].strip(" ,–-|()")
        

        if before_date and not is_location_line(before_date):
            title, company = extract_title_company(before_date)

        if not title:
            for j in range(i - 1, max(i - 6, -1), -1):
                prev = all_lines[j]

                if not prev:
                    continue

                # ✅ Skip location lines — go further back
                if is_location_line(prev):
                    continue

                # Skip bullet points
                if prev.startswith('•') or prev.startswith('-  '):
                    continue

                # Skip separator lines
                if re.match(r'^_+$', prev):
                    continue

                title, company = extract_title_company(prev)
                if title:
                    break

        results.append({
            "company":         company,
            "job_title":       title,
            "start_date":      sd.isoformat() if sd else None,
            "end_date":        ed.isoformat() if ed else None,
            "duration_months": months_between(sd, ed)
        })

    return results
    

def parse_date(value: str):
    if not value:
        return None

    v = value.lower().strip()

    if re.search(r'\b(present|preset|current|currently|now|till\s*date|to\s*date)\b', v):
        return datetime.today()

    if re.fullmatch(r"\d{4}", v):
        return datetime(int(v), 1, 1)

    if re.fullmatch(r"\d{1,2}/\d{4}", v):
        m, y = v.split("/")
        return datetime(int(y), int(m), 1)

    try:
        return datetime.strptime(value.strip(), "%b %Y")
    except:
        try:
            return datetime.strptime(value.strip(), "%B %Y")
        except:
            return None


def months_between(a, b):
    if not a or not b:
        return 0
    return (b.year - a.year) * 12 + (b.month - a.month)


def compute_total_experience_months(exps):
    return sum(e.get("duration_months", 0) for e in exps)


def detect_gaps_and_overlaps(exps):
    valid = []

    for e in exps:
        try:
            s  = datetime.fromisoformat(e["start_date"])
            en = datetime.fromisoformat(e["end_date"])
            valid.append({"start_date": s, "end_date": en})
        except:
            continue

    if not valid:
        return {"gaps": [], "overlaps": []}

    valid.sort(key=lambda x: x["start_date"])

    gaps     = []
    overlaps = []

    for i in range(len(valid) - 1):
        cur = valid[i]
        nxt = valid[i + 1]

        diff = (nxt["start_date"].year - cur["end_date"].year) * 12 + \
               (nxt["start_date"].month - cur["end_date"].month)

        if diff > 1:
            gaps.append({
                "from":       cur["end_date"].date().isoformat(),
                "to":         nxt["start_date"].date().isoformat(),
                "gap_months": diff - 1
            })

        if cur["end_date"] > nxt["start_date"]:
            overlaps.append({
                "from": nxt["start_date"].date().isoformat(),
                "to":   cur["end_date"].date().isoformat()
            })

    return {"gaps": gaps, "overlaps": overlaps}


def extract_experience(text: str):
    # section = extract_experience_section(text)

    # if section.strip():
    #     text = section

    roles    = extract_experience_blocks(text)
    total    = compute_total_experience_months(roles)
    timeline = detect_gaps_and_overlaps(roles)

    return {
        "roles":                   roles,
        "total_experience_months": total,
        "timeline_analysis":       timeline
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m resume_ingestion_engine.extraction.experience_parser <resume.pdf>")
        sys.exit(1)

    ext = sys.argv[1].split(".")[-1].lower()

    if ext == "pdf":
        import pdfplumber
        with pdfplumber.open(sys.argv[1]) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif ext == "txt":
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        print("Supported: .pdf, .txt")
        sys.exit(1)

    print("\n" + "="*60)
    print("RAW TEXT (first 2000 chars):")
    print("="*60)
    print(text[:2000])

    section = extract_experience_section(text)
    print("\n" + "="*60)
    print("EXPERIENCE SECTION FOUND:")
    print("="*60)
    print(repr(section[:500]) if section else "❌ SECTION NOT FOUND")

    print("\n" + "="*60)
    print("DATE PATTERN MATCHES:")
    print("="*60)
    for m in DATE_PATTERN.finditer(section or text):
        print(f"  start='{m.group('start')}'  end='{m.group('end')}'  → '{m.group(0)}'")

    result = extract_experience(text)

    os.makedirs("output", exist_ok=True)
    base_name   = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    output_path = f"output/{base_name}_experience.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print("\n" + "="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
    print(f"\n✅ Saved to: {output_path}")