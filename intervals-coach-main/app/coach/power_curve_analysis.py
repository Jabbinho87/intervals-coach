from __future__ import annotations

from app.models import PowerCurvePoint, PowerCurveSnapshot, TTEAssessment


def _nearest_point(points: list[PowerCurvePoint], target_seconds: int) -> PowerCurvePoint | None:
    valid = [p for p in points if p.watts is not None]
    if not valid:
        return None
    return min(valid, key=lambda p: abs(p.duration_seconds - target_seconds))


def _estimate_modeled_ftp(snapshot: PowerCurveSnapshot) -> float | None:
    if snapshot.modeled_ftp is not None:
        return snapshot.modeled_ftp

    p20 = _nearest_point(snapshot.points, 20 * 60)
    p30 = _nearest_point(snapshot.points, 30 * 60)
    p40 = _nearest_point(snapshot.points, 40 * 60)

    candidates: list[float] = []
    if p20 and p20.watts is not None:
        candidates.append(p20.watts * 0.95)
    if p30 and p30.watts is not None:
        candidates.append(p30.watts * 0.98)
    if p40 and p40.watts is not None:
        candidates.append(p40.watts)

    if not candidates:
        return None
    return round(sum(candidates) / len(candidates), 1)


def assess_power_curve(snapshot: PowerCurveSnapshot | None) -> TTEAssessment | None:
    if snapshot is None or not snapshot.points:
        return None

    modeled_ftp = _estimate_modeled_ftp(snapshot)
    estimated_tte_minutes: float | None = None
    observations: list[str] = []
    strengths: list[str] = []
    limiters: list[str] = []

    if snapshot.time_to_exhaustion_seconds is not None:
        estimated_tte_minutes = round(snapshot.time_to_exhaustion_seconds / 60, 1)
    elif modeled_ftp is not None:
        qualifying = [
            p.duration_seconds
            for p in snapshot.points
            if p.watts is not None and p.watts >= modeled_ftp * 0.95 and p.duration_seconds >= 8 * 60
        ]
        if qualifying:
            estimated_tte_minutes = round(max(qualifying) / 60, 1)

    p5m = _nearest_point(snapshot.points, 5 * 60)
    p20m = _nearest_point(snapshot.points, 20 * 60)
    p40m = _nearest_point(snapshot.points, 40 * 60)

    if p5m and p20m and p5m.watts and p20m.watts:
        ratio = p5m.watts / max(p20m.watts, 1)
        if ratio >= 1.22:
            strengths.append("5-min power looks strong relative to threshold power.")
            limiters.append("Ceiling may be ahead of sustained threshold stability.")
        elif ratio <= 1.12:
            strengths.append("Longer-duration power looks relatively durable.")
            limiters.append("VO2-side ceiling may lag behind endurance power.")

    if p40m and p20m and p40m.watts and p20m.watts:
        long_ratio = p40m.watts / max(p20m.watts, 1)
        if long_ratio >= 0.95:
            strengths.append("30-40 min durability looks robust.")
        elif long_ratio < 0.90:
            limiters.append("20-40 min fade suggests threshold durability still has room to grow.")

    if estimated_tte_minutes is None:
        level = "unknown"
        observations.append("TTE could not be estimated from the available power-curve points.")
    elif estimated_tte_minutes < 30:
        level = "low"
        observations.append("Estimated TTE is below 30 min, so shorter threshold reps and over/unders fit best.")
    elif estimated_tte_minutes < 40:
        level = "normal"
        observations.append("Estimated TTE is in the normal range for structured threshold work.")
    elif estimated_tte_minutes < 50:
        level = "strong"
        observations.append("Estimated TTE is strong enough for longer threshold reps and race-pace continuity.")
    else:
        level = "excellent"
        observations.append("Estimated TTE is excellent and supports continuous race-specific work.")

    if modeled_ftp is not None:
        observations.append(f"Modeled FTP proxy: {modeled_ftp:.0f} W.")

    return TTEAssessment(
        modeled_ftp=modeled_ftp,
        estimated_tte_minutes=estimated_tte_minutes,
        level=level,
        strengths=strengths,
        limiters=limiters,
        observations=observations,
    )
