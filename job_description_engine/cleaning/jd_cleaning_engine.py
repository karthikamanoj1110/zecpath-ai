import re

def clean_jd_text(jd_text: str) -> str:

    if jd_text is None:
        return ""
    
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", jd_text)
    text = re.sub(r'\s+', ' ', jd_text)  # Replace multiple whitespace with single space
    text = re.sub(r"[ \t]+", " ", jd_text)
    
    text = text.strip()