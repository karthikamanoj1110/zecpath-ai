import sys
from pathlib import Path

from job_description_engine.readers.jd_reader import  read_jd
from job_description_engine.normalization.jd_normalization_engine import normalize_jd_text
from job_description_engine.cleaning.jd_cleaning_engine import clean_jd_text

from job_description_engine.extraction.role_extractor import extract_roles
from job_description_engine.extraction.skill_extractor import extract_skills
from job_description_engine.extraction.experience_extractor import extract_experience   
from job_description_engine.extraction.education_extractor import extract_education

from job_description_engine.storage.writer import write_structured_jd   
from utils.logger import get_logger

logger = get_logger(
    "jd_pipeline",
    "job_description.log"
)

def process_jd(file_path: str):

    logger.info("Starting job description processing: %s", file_path)   

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)
    raw_text = read_jd(path)

    cleaned = clean_jd_text(raw_text)
    normalized = normalize_jd_text(cleaned)
    skills = extract_skills(normalized)
    roles = extract_roles(normalized)
    experience = extract_experience(normalized)
    education = extract_education(normalized)

    payload = {
        "job_id": path.stem,
        "source":{
                "file_name": path.name,
                "source_type": path.suffix.replace(".", "")
        },
        "roles": roles,
        "skills": skills,
        "experience": experience,
        "education": education,
        
       }
    output_path = write_structured_jd(payload, path.stem)

    return output_path

if __name__ == "__main__":

    if len(sys.argv) <  2:
        print("Usage: python -m job_description_engine.pipeline <jd_file.txt>")
        sys.exit(1)

    process_jd(sys.argv[1])