import json
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__, "resume_ingestion.log")


OUTPUT_DIR = Path("output/resumes")

def write_clean_resume(payload: dict, source_filename: str):
    """
    Writes final cleaned & normalized resume payload to disk.
    
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    path = OUTPUT_DIR / f"{source_filename}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path

