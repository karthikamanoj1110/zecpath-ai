from pathlib import Path
import json

from utils.logger import get_logger
logger = get_logger(__name__, "job_description.log")

OUTPUT_DIR = Path("output/job_descriptions")

def write_structured_jd(payload: dict, job_id: str):
   OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
   path = OUTPUT_DIR / f"{job_id}.json"
   with open(path, 'w', encoding='utf-8') as f:
       json.dump(payload, f, ensure_ascii=False, indent=2)
    
   return path