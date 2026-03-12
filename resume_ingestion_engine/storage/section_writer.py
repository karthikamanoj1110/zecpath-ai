import json
from pathlib import Path

OUTPUT_DIR = Path("samples/labeled_resumes")


def write_labeled_resume(payload: dict, filename: str):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out_path = OUTPUT_DIR / f"{filename}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return out_path
