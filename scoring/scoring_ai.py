from utils.logger import get_logger

logger = get_logger(__name__, "scoring_ai.log")

class DecisionEngine:
    def decide(self, Screening: int, interview: int) -> dict:
        final = int(0.5 * Screening + 0.5 * interview)
        return {
            "final_score" : final,
            "decision": "RECOMMENDED" if final >= 70 else "NOT_RECOMMENDED"
        }