
import re
from typing import List, Dict

from utils.logger import get_logger
logger = get_logger(__name__, "job_description.log")


SKILL_DICTIONARY = {
    "python": "programming_language",
    "tensorflow": "framework",
    "pytorch": "framework",
    "scikit-learn": "framework",
    "machine learning": "ai_ml",
    "deep learning": "ai_ml",
    "nlp": "ai_domain",
    "computer vision": "ai_domain",
    "generative ai": "ai_domain",
    "aws": "cloud",
    "azure": "cloud",
    "gcp": "cloud",
    "docker": "devops",
    "kubernetes": "devops",
    "mlops": "ml_platform",
    "rest api": "integration",
    "data preprocessing": "data_processing",
    "feature engineering": "data_processing"
}
def extract_skills(text: str) -> List[Dict]:
    if not text:
        return []
    
    lower = text.lower()
    results = []

    for skill,category in SKILL_DICTIONARY.items():
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, lower):
            results.append({
                "name": skill,
                "normalized_name": skill,
                "category": category,
                "is_mandatory": True
            })
                

    return results