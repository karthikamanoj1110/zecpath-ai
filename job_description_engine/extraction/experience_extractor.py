import re
from typing import Dict,Optional
from utils.logger import get_logger
logger = get_logger(__name__, "job_description.log")

def extract_experience(text: str) -> Optional[Dict]:
    if not text:
        return None
    text_1 = text.lower()
    
    range_match = re.search(r'(\d+)\s*-\s*(\d+)\s*years?', text_1)
    if range_match:
        return{
            "min_year": int(range_match.group(1)),
            "max_year": int(range_match.group(2)),
            "raw_text": range_match.group(0)
        }
        
    single_match = re.search(r'(\d+)\s*years?', text_1)
    if single_match:
        
        return{
            "min_year": int(single_match.group(1)),
            "max_year": None,
            "raw_text": single_match.group(0)
        }

    return None
    