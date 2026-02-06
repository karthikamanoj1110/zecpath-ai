import re
from utils.logger import get_logger

logger = get_logger(__name__, "resume_ingestion.log")


def score_confidence(blocks, normalized_text):

    if not normalized_text.strip():
        return 0.0

    penalty = 0.0

    if len(blocks) < 20:
        penalty += 0.1

    if len(normalized_text) < 500:
        penalty += 0.2

    garbled = re.findall(r"[�]{2,}", normalized_text)
    if garbled:
        penalty += 0.2

    score = 1.0 - penalty

    return max(0.0, min(1.0, score))
