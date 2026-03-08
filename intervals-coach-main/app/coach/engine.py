from __future__ import annotations

from app.config import settings
from app.coach.durability import analyze_durability
from app.coach.plan_alignment import align_with_training_context
from app.coach.planner import build_planning_insight
from app.coach.power_curve_analysis import assess_power_curve
from app.coach.readiness import assess_readiness
from app.coach.session_analysis import analyze_latest_session
from app.intervals_api import IntervalsAPI
from app.models import CoachRecommendation, CoachReport, DashboardSnapshot


def _build_recommendation(
    snapshot: DashboardSnapshot,
    tte_assessment,
    durability,
    alignment,
) -> CoachRecommendation:
    readiness = assess_readiness(snapshot)
    latest_session = analyze_latest_session(snapshot.activities[0] if snapshot.activities else None)
    planning = build_planning_insight(snapshot)

    observations: list[str] = []
    interpretation: list[str] = []
    recommendations: list[str] = []
    proposed_write_action: str | None = None

    observations.extend(readiness.observations)
    if latest_session is not None:
        observations.extend(latest_session.observations)
    observations.extend(planning.risks)
    if durability is not None:
        observations.extend(durability.observations)
    if alignment is not None:
        observations.extend(alignment.mismatches)

    if readiness.level == "low":
        summary = "Readiness is low; favor recovery or a reduced aerobic session."
        interpretation.append("Wellness and/or recent load point to poor absorption capacity.")
        recommendations.extend(
            [
                "Replace the next hard session with easy endurance or rest.",
                "Avoid adding extra intensity until wellness rebounds.",
            ]
        )
        proposed_write_action = "replace_next_key_session_with_easy_endurance"
    elif readiness.level == "caution":
        summary = "Readiness is mixed; keep the week intact but reduce ambition."
        interpretation.append("The athlete may still train, but quality should be protected.")
        recommendations.extend(
            [
                "Reduce the next quality workout by one repetition or shorten intervals.",
                "Protect the long run / long ride from extra intensity.",
            ]
        )
        proposed_write_action = "reduce_next_key_session"
    else:
        summary = "Athlete appears ready to continue with the planned key work."
        interpretation.append("Current signals do not justify a forced reduction.")
        recommendations.extend(
            [
                "Execute the next planned workout as scheduled.",
                "Keep write access disabled unless you explicitly approve a sync.",
            ]
        )

    if tte_assessment is None:
        interpretation.append("Power-curve data is not available yet, so threshold/TTE insights are limited.")
    else:
        interpretation.extend(tte_assessment.observations)
        if tte_assessment.limiters:
            recommendations.extend(tte_assessment.limiters[:2])
        if tte_assessment.level in {"low", "normal"}:
            recommendations.append("Bias threshold work toward over/unders or shorter sustained reps until TTE extends.")
        elif tte_assessment.level in {"strong", "excellent"}:
            recommendations.append("Longer threshold reps or race-pace continuity are supported by current TTE.")

    if durability is not None:
        if durability.drift_level in {"fatigue_visible", "poor"}:
            recommendations.append("Review fueling and avoid turning long endurance days into unplanned threshold work.")
            if proposed_write_action is None:
                proposed_write_action = "reduce_long_session_intensity"
        elif durability.drift_level == "excellent":
            interpretation.append("Durability on the latest long session looks strong.")

    if alignment is not None and alignment.mismatches:
        recommendations.extend(alignment.recommendations[:2])
        if proposed_write_action is None:
            proposed_write_action = "review_plan_alignment_before_sync"

    if planning.opportunities:
        recommendations.extend(planning.opportunities)

    # Deduplicate while keeping order.
    recommendations = list(dict.fromkeys(recommendations))
    observations = list(dict.fromkeys(observations))
    interpretation = list(dict.fromkeys(interpretation))

    return CoachRecommendation(
        summary=summary,
        observations=observations,
        interpretation=interpretation,
        recommendations=recommendations,
        requires_approval=settings.coach.approval_required_for_writes,
        proposed_write_action=proposed_write_action,
    )


def generate_coach_report(api: IntervalsAPI, snapshot: DashboardSnapshot) -> CoachReport:
    readiness = assess_readiness(snapshot)
    latest_activity = snapshot.activities[0] if snapshot.activities else None
    latest_session = analyze_latest_session(latest_activity)
    planning = build_planning_insight(snapshot)
    tte = assess_power_curve(snapshot.power_curve)
    durability = analyze_durability(api, latest_activity)
    alignment = align_with_training_context(snapshot)
    recommendation = _build_recommendation(snapshot, tte, durability, alignment)
    return CoachReport(
        readiness=readiness,
        latest_session=latest_session,
        planning=planning,
        tte=tte,
        durability=durability,
        plan_alignment=alignment,
        recommendation=recommendation,
    )
