from utils.logger import get_logger

logger = get_logger(__name__, "resume_ingestion.log")


from typing import List, Dict
import re


def normalize_text(text: str) -> str:
    """
    Normalize capitalization, bullets and headings.
    """

    if not text:
        return ""

    # Normalize bullets
    text = re.sub(r"^[\u2022\u25CF\u25A0\-\*]+", "-", text.strip())

    # Normalize multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Capitalization normalization (lightweight)
    text = text.strip()

    return text


def normalize_text_blocks(blocks: List[Dict]) -> List[Dict]:
    """
    Applies normalize_text to each text block.
    """

    normalized = []

    for block in blocks:
        new_block = dict(block)
        new_block["text"] = normalize_text(block.get("text", ""))
        normalized.append(new_block)

    return normalized
