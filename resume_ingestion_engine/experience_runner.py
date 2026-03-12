import sys
import pathlib
from pathlib import Path
import json
import re

from resume_ingestion_engine.readers.resume_reader import read_resume
from resume_ingestion_engine.layout.layout_processor import process_layout
from resume_ingestion_engine.cleaning.cleaning_engine import clean_text_blocks
from resume_ingestion_engine.normalization.normalization_engine import normalize_text_blocks

from resume_ingestion_engine.extraction.experience_parser import extract_experience
from resume_ingestion_engine.extraction.resume_parser import parse_resume
from resume_ingestion_engine.extraction.text_rebuilder import rebuild_text_for_nlp
from resume_ingestion_engine.extraction.experience_relevance import (
    score_experience_relevance
)
from datetime import datetime, date
# from resume_ingestion_engine.extraction.experience_timeline import build_timeline

def json_safe(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj

def normalize_resume_sections(text: str) -> str:
    headers = [
        "Summary",
        "Experience",
        "Work Experience",
        "Projects",
        "Education",
        "Certifications",
        "Technical Skills",
        "Skills"
    ]

    for h in headers:
        # force a line break before section headers
        text = re.sub(
            rf"\s+({h})\s+",
            r"\n\1\n",
            text,
            flags=re.IGNORECASE
        )

    return text

def run_experience_only(resume_file: str, jd_role: str):

    path = pathlib.Path(resume_file)

    raw_blocks = read_resume(path)
    layout = process_layout(raw_blocks)
    cleaned = clean_text_blocks(layout)
    normalized = normalize_text_blocks(cleaned)

    

    raw_text = "\n".join(b.get("text", "") for b in normalized)

    full_text = rebuild_text_for_nlp(raw_text)
    parseed_profile = parse_resume(full_text)
    # print("TEXT SAMPLE:")
    # print(full_text)

    

    debug_file = Path("output/debug_full_text.txt")
    debug_file.parent.mkdir(parents=True, exist_ok=True)

    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(full_text)

    print("Full rebuilt text saved to:", debug_file)
    
    full_text = normalize_resume_sections(full_text)
    experience = extract_experience(full_text)

    relevance = score_experience_relevance(
        experience["roles"],
        jd_role
    )
    
    # roles = experience["roles"]
    # total = experience["total_experience_months"]
    # timeline = experience["timeline_analysis"]
    
    

    output = {
        "resume_file": path.name,
        "jd_role": jd_role,
        "experience": experience,
        "experience_relevance": relevance
    }


    # write_experience_output(output, path.stem)

    out_dir = pathlib.Path("output/experience_only")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{path.stem}_experience.json"

    with open(out_file, "w", encoding="utf-8") as f:
       json.dump(json_safe(output), f, indent=2, ensure_ascii=False)

    print("Saved:", out_file)


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Saved the file")        
        sys.exit(1)

    run_experience_only(sys.argv[1], sys.argv[2])
