from pathlib import Path
from pipeline import process_resume


def run_tests(test_folder: str):

    test_path = Path(test_folder)

    results = []

    for file in test_path.iterdir():

        if file.suffix.lower() not in [".pdf", ".docx"]:
            continue

        try:
            result = process_resume(str(file))

            ok = (
                len(result["cleaned_text"]) > 300 and
                result["metadata"]["extraction_confidence"] >= 0.5
            )

            results.append({
                "file": file.name,
                "status": "PASS" if ok else "FAIL",
                "confidence": result["metadata"]["extraction_confidence"]
            })

        except Exception as e:
            results.append({
                "file": file.name,
                "status": "ERROR",
                "error": str(e)
            })

    return results


if __name__ == "__main__":
    out = run_tests("test_resumes")
    for r in out:
        print(r)
