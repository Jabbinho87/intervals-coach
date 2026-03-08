from __future__ import annotations

from app.models import DashboardSnapshot, ReadinessAssessment


TEXT_NEGATIVE = {"bad", "poor", "low", "high", "sore", "fatigued", "tired"}
TEXT_POSITIVE = {"good", "great", "fresh", "normal", "ok", "okay"}


def assess_readiness(snapshot: DashboardSnapshot) -> ReadinessAssessment:
    """Simple readiness model that combines wellness and recent session context."""
    score = 0
    observations: list[str] = []

    latest_wellness = snapshot.wellness_entries[0] if snapshot.wellness_entries else None
    latest_activity = snapshot.activities[0] if snapshot.activities else None

    if latest_wellness is None:
        observations.append("No wellness data available; readiness confidence is lower.")
    else:
        if latest_wellness.resting_hr is not None:
            if latest_wellness.resting_hr >= 60:
                score -= 1
                observations.append("Resting HR is elevated.")
            else:
                score += 1
                observations.append("Resting HR looks acceptable.")

        if latest_wellness.hrv is not None:
            if latest_wellness.hrv < 40:
                score -= 1
                observations.append("HRV is on the low side.")
            else:
                score += 1
                observations.append("HRV looks stable.")

        if latest_wellness.sleep_secs is not None:
            if latest_wellness.sleep_secs < 6 * 3600:
                score -= 1
                observations.append("Sleep duration is low.")
            elif latest_wellness.sleep_secs >= 7 * 3600:
                score += 1
                observations.append("Sleep duration is supportive.")

        for label, value in {
            "mood": latest_wellness.mood,
            "soreness": latest_wellness.soreness,
            "fatigue": latest_wellness.fatigue,
            "freshness": latest_wellness.freshness,
        }.items():
            if value is None:
                continue
            lowered = str(value).strip().lower()
            if lowered in TEXT_NEGATIVE:
                score -= 1
                observations.append(f"{label.capitalize()} suggests strain.")
            elif lowered in TEXT_POSITIVE:
                score += 1
                observations.append(f"{label.capitalize()} looks acceptable.")

    if latest_activity is not None:
        session_load = latest_activity.icu_training_load or 0.0
        if session_load >= 120:
            score -= 1
            observations.append("Latest activity had high training load.")
        elif session_load > 0:
            observations.append("Latest activity load was moderate.")

    if score >= 2:
        level = "high"
    elif score >= 0:
        level = "normal"
    elif score >= -2:
        level = "caution"
    else:
        level = "low"

    return ReadinessAssessment(score=score, level=level, observations=observations)
