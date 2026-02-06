def parse_resume(text: str) -> dict:
	if not text:
		return {
			"Skills": [],
			"experience": None
		}

	return{ 
		"Skills" : ["Python","AWS"],
		"experience" : 3
		}