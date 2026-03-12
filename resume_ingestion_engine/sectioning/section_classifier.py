from typing import List, Dict
import re
from pathlib import Path
import json

SECTION_ALIASES = {
    "experience": ["experience", "work experience", "professional experience", "employment history","employment", "career history", "industry experience",],
    "education": ["education", "academic background", "qualifications","qualification","academics"],
    "skills": ["skills", "technical skills", "core competencies","core skills","technologies","tooling","key skills"],
    "projects": ["projects", "personal projects", "academic projects","professional projects"],
    "certifications": ["certifications", "licenses", "professional certifications"],
    "summary": ["summary", "professional summary", "profile","about me","objective"]
}

HEADING_LOOKUP = {}
for section, aliases in SECTION_ALIASES.items():
    for a in aliases:
        HEADING_LOOKUP[a.lower()] = section 

def normalize_heading(text: str) -> str:
    
    text = re.sub(r"[^a-zA-Z ]", "", text)
    return text.strip().lower()

def detect_heading(text: str) :
    cleaned = normalize_heading(text)
    if not cleaned:
        return None
    if cleaned in HEADING_LOOKUP:
        return HEADING_LOOKUP[cleaned]

    if len(cleaned.split()) <= 4:
        for alias, section in HEADING_LOOKUP.items():
            if cleaned == alias:
                return section
    return None

SECTION_KEYWORDS = {
    "skills": ["python", "java", "sql", "aws", "docker", "kubernetes"],
    "experience": ["company", "responsible", "worked", "role", "client"],
    "education": ["university", "college", "bachelor", "master", "degree"],
    "projects": ["project", "developed", "built", "implemented"],
    "certifications": ["certified", "certification", "license"]
}


def guess_section_from_content(text: str):

    t = text.lower()
    scores = {}

    for section, words in SECTION_KEYWORDS.items():
        score = sum(1 for w in words if w in t)
        scores[section] = score

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return None

    return best


# ----------------------------
# main API
# ----------------------------

def classify_resume_sections(blocks: List[Dict]) -> List[Dict]:
    """
    Adds:
        block["section"]
    """

    current_section = "OTHER"
    output = []

    for block in blocks:
        text = block.get("text", "").strip()

        new_block = dict(block)

        # 1. try heading detection
        heading_section = detect_heading(text)

        if heading_section:
            current_section = heading_section
            new_block["section"] = current_section
            new_block["is_section_header"] = True
            output.append(new_block)
            continue

        # 2. content-based guess (only when section still OTHER)
        if current_section == "OTHER":
            guessed = guess_section_from_content(text)
            if guessed:
                current_section = guessed

        new_block["section"] = current_section
        new_block["is_section_header"] = False

        output.append(new_block)

    return output
def save_section_output(blocks,output_file_name: str):
    out_dir = Path("resume_ingestion_engine/sectioning/output/section_predictions")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / output_file_name

    playload = {
        "blocks": blocks
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(playload, f, indent=2, ensure_ascii=False)

    return out_file

if __name__ == "__main__":

    from pathlib import Path

    input_file = Path("samples/labeled_resumes/KarthikaM.json")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    blocks = data.get("blocks", [])

    classified = classify_resume_sections(blocks)

    out = save_section_output(classified, "KarthikaM.json")

    print("Saved section predictions to:", out)
