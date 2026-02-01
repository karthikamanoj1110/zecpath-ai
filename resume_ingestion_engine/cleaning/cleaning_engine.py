import re
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


def clean_text(text: str) -> str:

    if not text:
        return ""

    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)

    return text.strip()


def clean_text_blocks(blocks: List[Dict]) -> List[Dict]:
    """
    Applies clean_text to each text block produced by the reader/layout stage.
    Expected block format:
        {
            "text": str,
            ...
        }
    """

    cleaned = []

    for block in blocks:
        new_block = dict(block)
        new_block["text"] = clean_text(block.get("text", ""))
        cleaned.append(new_block)

    return cleaned
