import json
from pathlib import Path
from collections import defaultdict

def evaluate_sections(gold_file: Path, pred_file: Path):

    with open(gold_file, "r", encoding="utf-8") as f:
        gold = json.load(f)["blocks"]

    with open(pred_file, "r", encoding="utf-8") as f:
        pred = json.load(f)["blocks"]

    assert len(gold) == len(pred), "Gold and prediction block count mismatch"

    total = len(gold)
    correct = 0

    per_section_total = defaultdict(int)
    per_section_correct = defaultdict(int)

    for g, p in zip(gold, pred):

        gold_section = (g.get("section") or "OTHER").lower()
        pred_section = (p.get("section") or "OTHER").lower()

        per_section_total[gold_section] += 1

        if gold_section == pred_section:
            correct += 1
            per_section_correct[gold_section] += 1

    overall_accuracy = correct / total if total else 0

    report = {
        "total_blocks": total,
        "correct_blocks": correct,
        "overall_accuracy": round(overall_accuracy, 4),
        "per_section_accuracy": {}
    }

    for sec in per_section_total:
        report["per_section_accuracy"][sec] = round(
            per_section_correct[sec] / per_section_total[sec], 4
        )

    return report


if __name__ == "__main__":

    base_dir = Path(__file__).resolve().parents[2]

    gold = base_dir / "samples" / "labeled_resumes" / "KarthikaM.json"
    pred = (
        base_dir
        / "resume_ingestion_engine"
        / "sectioning"
        / "output"
        / "section_predictions"
        / "KarthikaM.json"
    )

    report = evaluate_sections(gold, pred)

    out_dir = (
        base_dir
        / "resume_ingestion_engine"
        / "sectioning"
        / "output"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "section_accuracy_report.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Accuracy report saved to:", out_file)
    print(report)
