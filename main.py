from ats_engine.ats_ai import ATSAI
from screening_ai.screening_engine import ScreeningAI
from utils.logger import get_logger

logger = get_logger(__name__, "main.log")

def main():
    logger.info("Starting the ZecPath AI pipeline.")
    
    ats = ATSAI()
    screening = ScreeningAI()
    
    # Later you can add:
    # interview = InterviewAI()
    # scoring = ScoringAI()
    
    # Placeholder for pipeline execution
    logger.info("ATS AI initialized successfully.")
    logger.info("Screening AI initialized successfully.")
   
    logger.info("ZecPath AI pipeline execution completed.")

if __name__ == "__main__":
   main()
