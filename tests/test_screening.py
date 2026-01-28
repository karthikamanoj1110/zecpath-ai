from screening_ai.screening_engine import ScreeningAI

def test_screening_init():
    ai = ScreeningAI()
    assert ai is not None
def test_screening_pass():
    ai = ScreeningAI()
    result = ai.screen(
        {"skills": ["Python", "AWS"]},
        {"required_skills": ["Python", "AWS"]}
    )
    assert result["passed"] is True
    assert result["score"] == 1.0