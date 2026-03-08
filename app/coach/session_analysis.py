from __future__ import annotations

from app.models import ActivitySummary, SessionAnalysis



def analyze_latest_session(activity: ActivitySummary | None) -> SessionAnalysis | None:
    """Classify the latest session with a simple rule-based analysis."""
    if activity is None:
        return None

    stimulus = "endurance"
    session_type = activity.type or "unknown"
    quality = "acceptable"
    observations: list[str] = []

    weighted_power = activity.weighted_average_watts or 0.0
    average_power = activity.average_watts or 0.0
    moving_time = activity.moving_time or 0.0

    if weighted_power >= 250:
        stimulus = "threshold_or_above"
        observations.append("Weighted power suggests a hard bike session.")
    elif weighted_power >= 180:
        stimulus = "tempo_or_sweetspot"
        observations.append("Power suggests a moderate aerobic quality ride.")
    elif moving_time >= 2 * 3600:
        stimulus = "long_endurance"
        observations.append("Duration points toward a durability/endurance session.")
    else:
        observations.append("Session appears primarily easy or aerobic.")

    if average_power and weighted_power:
        variability_index = weighted_power / max(average_power, 1)
        if variability_index > 1.1:
            quality = "unsteady"
            observations.append("Pacing was relatively variable.")
        elif variability_index < 1.05:
            observations.append("Pacing was fairly steady.")

    if activity.average_heartrate and activity.max_heartrate:
        if activity.average_heartrate / max(activity.max_heartrate, 1) > 0.88:
            observations.append("Cardiovascular strain appears high for the session.")

    return SessionAnalysis(
        session_type=session_type,
        primary_stimulus=stimulus,
        quality=quality,
        observations=observations,
    )
