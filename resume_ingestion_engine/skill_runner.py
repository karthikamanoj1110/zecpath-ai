import sys
from pathlib import Path
import json

from resume_ingestion_engine.readers.resume_reader import read_resume
from resume_ingestion_engine.layout.layout_processor import process_layout
from resume_ingestion_engine.cleaning.cleaning_engine import clean_text_blocks
from resume_ingestion_engine.normalization.normalization_engine import normalize_text_blocks

from resume_ingestion_engine.extraction.skill_extractor import extract_resume_skills


def run_skills_only(resume_file: str):

    path = Path(resume_file)

    raw_blocks = read_resume(path)
    layout = process_layout(raw_blocks)
    cleaned = clean_text_blocks(layout)
    normalized = normalize_text_blocks(cleaned)

    full_text = "\n".join(b.get("text", "") for b in normalized)

    skills = extract_resume_skills(full_text)

    output = {
        "resume_file": path.name,
        "skills": skills
    }

    out_dir = Path("output/skills_only")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{path.stem}_skills.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Saved:", out_file)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: python -m resume_ingestion_engine.skill_runner "
            "\"data/raw_resumes/Karthika M.pdf\""
        )
        sys.exit(1)

    run_skills_only(sys.argv[1])
