from __future__ import annotations

from statistics import mean
from typing import Any

from app.intervals_api import IntervalsAPI
from app.models import ActivitySummary, DurabilityAnalysis


def _compute_stream_decoupling(streams: dict[str, Any]) -> float | None:
    watts = streams.get("watts")
    heartrate = streams.get("heartrate") or streams.get("fixed_heartrate")
    if not isinstance(watts, list) or not isinstance(heartrate, list):
        return None
    if len(watts) < 120 or len(heartrate) != len(watts):
        return None

    pairs = [
        (float(w), float(hr))
        for w, hr in zip(watts, heartrate)
        if w is not None and hr not in (None, 0)
    ]
    if len(pairs) < 120:
        return None

    midpoint = len(pairs) // 2
    first = pairs[:midpoint]
    second = pairs[midpoint:]
    if not first or not second:
        return None

    first_ratio = mean(w / hr for w, hr in first)
    second_ratio = mean(w / hr for w, hr in second)
    if first_ratio == 0:
        return None
    return round(((first_ratio - second_ratio) / first_ratio) * 100, 2)


def analyze_durability(api: IntervalsAPI, activity: ActivitySummary | None) -> DurabilityAnalysis | None:
    if activity is None or activity.id is None:
        return None

    observations: list[str] = []
    duration = activity.moving_time or 0
    if duration < 75 * 60:
        return DurabilityAnalysis(
            activity_id=activity.id,
            session_label=activity.name,
            analyzed_with="summary_only",
            drift_level="not_applicable",
            observations=["Session is probably too short for a meaningful durability check."],
        )

    details = api.get_activity_details(activity.id)
    intervals = details.get("icu_intervals", []) if isinstance(details, dict) else []
    interval_decouplings = [
        float(interval.get("decoupling"))
        for interval in intervals
        if isinstance(interval, dict) and interval.get("decoupling") is not None
    ]

    decoupling_percent: float | None = None
    analyzed_with = "summary_only"

    if interval_decouplings:
        decoupling_percent = round(max(interval_decouplings), 2)
        analyzed_with = "intervals"
        observations.append("Used Intervals.icu interval decoupling values from activity details.")
    else:
        streams = api.get_activity_streams(activity.id, types=["watts", "heartrate"])
        if streams:
            decoupling_percent = _compute_stream_decoupling(streams)
            if decoupling_percent is not None:
                analyzed_with = "streams"
                observations.append("Computed power/HR decoupling from activity streams.")

    if decoupling_percent is None:
        return DurabilityAnalysis(
            activity_id=activity.id,
            session_label=activity.name,
            analyzed_with=analyzed_with,
            drift_level="unknown",
            observations=observations + ["Could not compute a reliable decoupling metric for this session."],
        )

    if decoupling_percent < 3:
        drift_level = "excellent"
        observations.append("Aerobic stability looks very strong (<3% decoupling).")
    elif decoupling_percent < 5:
        drift_level = "normal"
        observations.append("Aerobic durability looks normal (3-5% decoupling).")
    elif decoupling_percent < 7:
        drift_level = "fatigue_visible"
        observations.append("Aerobic fatigue is visible; durability or fueling may be limiting.")
    else:
        drift_level = "poor"
        observations.append("High decoupling suggests substantial fade, overpacing, or underfueling.")

    fueling_flag = None
    if duration >= 2 * 3600 and decoupling_percent >= 5:
        fueling_flag = "review_fueling"
        observations.append("For long sessions this amount of drift should trigger a fueling review.")

    return DurabilityAnalysis(
        activity_id=activity.id,
        session_label=activity.name,
        analyzed_with=analyzed_with,
        decoupling_percent=decoupling_percent,
        drift_level=drift_level,
        fueling_flag=fueling_flag,
        observations=observations,
    )
