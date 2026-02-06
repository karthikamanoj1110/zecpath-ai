from utils.logger import get_logger

logger = get_logger(__name__, "resume_ingestion.log")

def process_layout(blocks):
    """
    Placeholder layout processor.
    For now, returns blocks as-is.
    Later: column detection, table handling, ordering.
    """
    return blocks


