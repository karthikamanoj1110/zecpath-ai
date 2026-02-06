from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__, "job_description.log")

DEGREE_MAP = {
    "bachelor": ["bachelor", "b.tech", "be "],
    "master": ["master", "m.tech", "mba "],
    "phd": ["phd", "doctorate", "doctoral" ]
}



def extract_education(text: str) -> List[Dict]:
    if not text:
        return []
    
    lower = text.lower()
    results = []

    for key, label in DEGREE_MAP.items():
        if key in lower:
            results.append({
                "degree_level": label,
                "specializations": None,
                "mandatory": False
            })
            
    return results