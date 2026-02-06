from utils.logger import get_logger

logger = get_logger(__name__, "ats_ai.log")

class ATSAI:
    def __init__(self):
        self.logger = get_logger("ATS-AI", "ats_ai.log")
        self.logger.info("ATS AI initialized")

