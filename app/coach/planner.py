from __future__ import annotations

from app.models import DashboardSnapshot, PlanningInsight



def build_planning_insight(snapshot: DashboardSnapshot) -> PlanningInsight:
    """Inspect the upcoming schedule and identify obvious opportunities or risks."""
    risks: list[str] = []
    opportunities: list[str] = []

    if not snapshot.planned_workouts:
        return PlanningInsight(
            summary="No planned workouts were found in the near-term calendar.",
            risks=["Coach cannot validate spacing of key sessions yet."],
            opportunities=["Populate planned workouts to enable weekly planning checks."],
        )

    next_workout = snapshot.planned_workouts[0]
    summary = f"Next planned workout is '{next_workout.name or 'Unnamed Workout'}'."

    if len(snapshot.planned_workouts) >= 2:
        first = snapshot.planned_workouts[0]
        second = snapshot.planned_workouts[1]
        if first.start_date_local == second.start_date_local:
            risks.append("Multiple planned workouts are scheduled on the same date.")

    if snapshot.activities:
        latest_activity = snapshot.activities[0]
        latest_load = latest_activity.icu_training_load or 0.0
        if latest_load >= 120:
            risks.append(
                "The latest completed session was heavy; protect the next key workout if needed."
            )

    if next_workout.icu_training_load is None:
        opportunities.append(
            "Add expected workout load or clearer descriptions to improve planning quality."
        )

    if not risks:
        opportunities.append("Current near-term plan looks usable for coach recommendations.")

    return PlanningInsight(summary=summary, risks=risks, opportunities=opportunities)
