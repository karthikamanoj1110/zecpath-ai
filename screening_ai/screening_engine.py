from utils.logger import get_logger

class ScreeningAI:
    def __init__(self):
        self.logger = get_logger("Screening-AI")
        self.logger.info("Screening AI initialized")


    def screen(self, candidate_profile: dict, job_requirements: dict) -> dict:
        """
        Screens a candidate against job requirements.
        Returns screening result with pass/fail and score.
        """

        candidate_skills = set(candidate_profile.get("skills", []))
        required_skills = set(job_requirements.get("required_skills", []))

        matched_skills = candidate_skills.intersection(required_skills)
        score = len(matched_skills) / max(len(required_skills), 1)

        passed = score >= 0.7  # threshold

        self.logger.info(
            f"Screening completed | score={score:.2f} | passed={passed}"
        )

        return {
            "passed": passed,
            "score": round(score, 2),
            "matched_skills": list(matched_skills),
        }