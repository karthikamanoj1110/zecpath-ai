from typing import List, Dict   
import re

from utils.logger import get_logger
logger = get_logger(__name__, "job_description.log")

ROLE_SYNONYMS = {
    "AI Engineer": [
        "ai engineer", "artificial intelligence engineer","ai application engineer","ai solution engineer",  "Junior AI Engineer", "Associate AI Engineer", "Mid-Level AI Engineer", 
        "Applied AI Engineer","ai software engineer","intelligent systems engineer","AI Data Engineer", "Machine Learning Data Engineer",
        "Machine Learning Engineer (MLE)", "Senior Machine Learning Engineer", "Principal Machine Learning Engineer", 
        "Applied Machine Learning Engineer", "ML Software Engineer", "ML Platform Engineer", "ML Infrastructure Engineer", "MLOps Engineer", "AI/ML Engineer", 
        "Deep Learning Engineer", "Neural Network Engineer", "Computer Vision Engineer", "NLP Engineer (Natural Language Processing)", "Speech Recognition Engineer", 
        "Multimodal AI Engineer", "Reinforcement Learning Engineer", "Generative AI Engineer", "LLM Engineer (Large Language Models)",  
        "AI Analytics Engineer", "Data Scientist (AI-Focused)", "AI Modeling Engineer", "AI Algorithm Engineer", "Statistical Learning Engineer", "MLOps Engineer", "AI Platform Engineer", 
        "AI Infrastructure Engineer", "AI Cloud Engineer", "ML Systems Engineer", "Model Deployment Engineer", "AI DevOps Engineer", "AI Reliability Engineer"," Healthcare AI Engineer", 
        "FinTech AI Engineer", "EdTech AI Engineer", "Retail AI Engineer", "Manufacturing AI Engineer", "Autonomous Systems Engineer", "Robotics AI Engineer", "Game AI Engineer", 
        "Cybersecurity AI Engineer", "AI Product Engineer", "Applied AI Scientist", "AI Solutions Architect", "AI Technical Consultant", "AI Pre-Sales Engineer", "AI Integration Engineer", 
        "AI Customer Success Engineer", "AI Research Engineer", "AI Research Scientist", "Research Engineer (AI/ML)", "AI Scientist", "Computational Intelligence Engineer",
        "Cognitive Systems Engineer", "AI Engineer Intern", "Senior AI Engineer", "Lead AI Engineer", "Principal AI Engineer",
        "Staff AI Engineer", "Freelance AI Engineer", "Contract AI Engineer", "Independent AI Consultant", "AI Implementation Partner", "AI Automation Engineer", "AI Startup Engineer",
        "AI Technical Advisor", "Prompt Engineer", "AI Agent Engineer", "Autonomous AI Engineer", "Human-in-the-Loop AI Engineer", "AI Ethics Engineer", 
        "Responsible AI Engineer", "Trustworthy AI Engineer", "Synthetic Data Engineer"
         ]
}

def _clean(t: str) -> str:
    t = t.lower()
    t = re.sub(r'[^\w\s]', '', t)
    return t.strip()

def extract_roles(text: str) -> Dict[str, List[str]]:
    if not text:
        return {"raw_title": [], "normalized_title": []}
    cleaned_text = _clean(text)

    raw  = []
    normalized = []

    for canonical,variants in ROLE_SYNONYMS.items():
        for v in variants:
            v_clean = _clean(v)
            pattern = r'\b' + re.escape(v_clean) + r'\b'
            if re.search(pattern, cleaned_text):
                raw.append(v)
                normalized.append(canonical)


    raw = list(dict.fromkeys(raw))
    normalized = list(dict.fromkeys(normalized))

    return {
        "raw_title": raw,
        "normalized_title": normalized
    }