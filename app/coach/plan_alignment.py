from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.models import DashboardSnapshot, PlanAlignment

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_DIR = PROJECT_ROOT / "docs" / "training_context"


def _read_context(filename: str) -> str:
    path = CONTEXT_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _weekday_name(date_str: str | None) -> str | None:
    if not date_str:
        return None
    cleaned = date_str.replace("Z", "")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            dt = datetime.fromisoformat(cleaned[:10])
        except ValueError:
            return None
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]


def align_with_training_context(snapshot: DashboardSnapshot) -> PlanAlignment:
    macro = _read_context("macroplan.txt")
    meso = _read_context("mesoplan.txt")

    expected_week_structure = [
        "Tue: easy run commute + swim",
        "Wed: key bike",
        "Thu: quality run + swim",
        "Fri: second bike",
        "Sat: long run + swim",
        "Sun: long ride / race-specific bike",
    ]

    block_focus = "threshold / over-under build" if "over/under" in macro.lower() or "OU" in meso else "general endurance"
    matched_items: list[str] = []
    mismatches: list[str] = []
    recommendations: list[str] = []

    if not snapshot.planned_workouts:
        mismatches.append("No planned workouts available to compare against macro/meso structure.")
        recommendations.append("Populate calendar events so the coach can validate weekday structure.")
        return PlanAlignment(
            block_focus=block_focus,
            expected_week_structure=expected_week_structure,
            matched_items=matched_items,
            mismatches=mismatches,
            recommendations=recommendations,
        )

    seen_days: dict[str, list[str]] = {}
    for workout in snapshot.planned_workouts:
        day = _weekday_name(workout.display_date)
        if not day:
            continue
        seen_days.setdefault(day, []).append((workout.name or workout.type or "Unnamed").lower())

    if "Wed" in seen_days:
        if any(any(token in name for token in ["ou", "over", "threshold", "bike"]) for name in seen_days["Wed"]):
            matched_items.append("Wednesday bike slot is populated, which matches the fixed bike rhythm.")
        else:
            mismatches.append("Wednesday exists in the plan, but the workout does not look like a key bike session.")
    else:
        mismatches.append("No Wednesday key bike session found in the near-term calendar.")

    if "Thu" in seen_days:
        if any(any(token in name for token in ["run", "threshold", "tempo", "quality"]) for name in seen_days["Thu"]):
            matched_items.append("Thursday quality run slot is represented in the near-term plan.")
        else:
            mismatches.append("Thursday exists, but the session does not clearly match the expected quality run slot.")

    if "Sat" in seen_days and any("run" in name for name in seen_days["Sat"]):
        matched_items.append("Saturday long-run slot is present.")
    elif "Sat" in seen_days:
        mismatches.append("Saturday is scheduled, but not clearly as a run-focused day.")

    if "Sun" in seen_days and any(any(token in name for token in ["ride", "bike", "long", "endurance"]) for name in seen_days["Sun"]):
        matched_items.append("Sunday bike/long-ride slot is present.")
    elif "Sun" in seen_days:
        mismatches.append("Sunday is occupied, but it does not clearly look like the primary long bike slot.")

    if snapshot.activities:
        latest = snapshot.activities[0]
        latest_name = (latest.name or "").lower()
        if block_focus.startswith("threshold") and any(token in latest_name for token in ["vo2", "ronnestad"]):
            mismatches.append("Latest session looks VO2-dominant while the current context points toward a threshold / OU block.")
            recommendations.append("Keep VO2 work as support only unless the block has explicitly shifted away from threshold focus.")

    if not mismatches:
        recommendations.append("Near-term calendar appears broadly aligned with the fixed macro/meso rhythm.")
    else:
        recommendations.append("Review mismatched weekday slots before pushing any generated workout back to Intervals.")

    return PlanAlignment(
        block_focus=block_focus,
        expected_week_structure=expected_week_structure,
        matched_items=matched_items,
        mismatches=mismatches,
        recommendations=recommendations,
    )
