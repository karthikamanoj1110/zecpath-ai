from utils.logger import get_logger

logger = get_logger(__name__, "job_description.log")

def normalize_jd_text(text: str) -> str:
    
    if not text:
        return ""
    
    # text = text.lower()
    # text = text.replace('\n', ' ').replace('\r', ' ')
    # text = ' '.join(text.split())
    
    return text.strip()