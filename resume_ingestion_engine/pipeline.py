from pathlib import Path
from typing import Dict, Any
import logging

from resume_ingestion_engine.readers.resume_reader import read_resume
from resume_ingestion_engine.layout.layout_processor import process_layout
from resume_ingestion_engine.cleaning.cleaning_engine import clean_text_blocks
from resume_ingestion_engine.normalization.normalization_engine import normalize_text_blocks
from resume_ingestion_engine.storage.writer import write_clean_resume
from resume_ingestion_engine.extraction.resume_parser import parse_resume
from utils.logger import get_logger

logger = get_logger(
    "resume_pipeline",
    "resume_ingestion.log"
)





def process_resume(file_path: str) -> Dict[str, Any]:
    """
    End-to-end resume ingestion pipeline.

    Flow:
        Reader -> Layout -> Cleaning -> Normalization -> Storage

    Returns:
        structured cleaned resume payload (dict)
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    logger.info("Starting resume ingestion: %s", file_path.name)

    # -------------------------------------------------------
    # 1. Read (PDF / DOCX auto detected)
    # -------------------------------------------------------
    raw_blocks = read_resume(file_path)

    # raw_blocks : List[TextBlock]
    # TextBlock = {
    #   "text": str,
    #   "page": int,
    #   "bbox": tuple,
    #   "font_size": float
    # }

    # -------------------------------------------------------
    # 2. Layout processing (columns, ordering, tables)
    # -------------------------------------------------------
    layout_blocks = process_layout(raw_blocks)

    # -------------------------------------------------------
    # 3. Cleaning
    # -------------------------------------------------------
    cleaned_blocks = clean_text_blocks(layout_blocks)

    # -------------------------------------------------------
    # 4. Normalization
    # -------------------------------------------------------
    normalized_blocks = normalize_text_blocks(cleaned_blocks)

    raw_text = "\n".join(
    b.get("text", "") for b in normalized_blocks)

    parsed_profile = parse_resume(raw_text)
    # -------------------------------------------------------
    # 5. Build structured payload
    # -------------------------------------------------------
    payload = {
        "source_file": file_path.name,
        "total_blocks": len(normalized_blocks),
        "blocks": normalized_blocks,
        "parsed_profile": parsed_profile
    }

    # -------------------------------------------------------
    # 6. Persist cleaned output
    # -------------------------------------------------------
    write_clean_resume(payload, source_filename=file_path.stem)

    logger.info("Completed resume ingestion: %s", file_path.name)

    return payload


if __name__ == "__main__":

    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <resume_file_path>")
        sys.exit(1)

    process_resume(sys.argv[1])
