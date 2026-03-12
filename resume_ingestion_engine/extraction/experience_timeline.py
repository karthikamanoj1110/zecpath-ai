from datetime import datetime
from typing import List, Dict


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}


def parse_date(date_str: str):
    if not date_str:
        return None

    if date_str.lower() == "present":
        return datetime.today()

    try:
        mon, year = date_str.split()
        return datetime(int(year), MONTHS[mon.lower()], 1)
    except Exception:
        return None


def months_between(start: datetime, end: datetime) -> int:
    if not start or not end:
        return 0

    return max(0, (end.year - start.year) * 12 + (end.month - start.month) + 1)


def build_timeline(experiences: List[Dict]):
    """
    Adds duration, detects gaps and overlaps,
    and computes total experience.
    """

    enriched = []

    for e in experiences:
        start = parse_date(e.get("start_date"))
        end = parse_date(e.get("end_date"))

        enriched.append({
            **e,
            "start_dt": start,
            "end_dt": end,
            "duration_months": months_between(start, end)
        })

    ordered = sorted(
        enriched,
        key=lambda x: x["start_dt"] or datetime.min
    )

    gaps = []
    overlaps = []

    for i in range(len(ordered) - 1):
        current = ordered[i]
        nxt = ordered[i + 1]

        if not current["end_dt"] or not nxt["start_dt"]:
            continue

        diff = (nxt["start_dt"].year - current["end_dt"].year) * 12 + \
               (nxt["start_dt"].month - current["end_dt"].month)

        if diff > 1:
            gaps.append({
                "from": current["end_date"],
                "to": nxt["start_date"],
                "gap_months": diff - 1
            })

        if diff < 0:
            overlaps.append({
                "role_1": current["title"],
                "role_2": nxt["title"]
            })

    total_months = sum(e["duration_months"] for e in enriched)

    for e in enriched:
        e.pop("start_dt", None)
        e.pop("end_dt", None)

    return enriched, total_months, gaps, overlaps
