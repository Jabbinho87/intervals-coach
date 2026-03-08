from __future__ import annotations

from app.coach.engine import generate_coach_report
from app.config import settings
from app.intervals_api import IntervalsAPI, IntervalsAPIError
from app.models import DashboardSnapshot, HistoricalTrainingSummary, PerformanceTrend


def build_history(
    activities: list,
    recent_days: int,
    medium_range_days: int,
) -> list[HistoricalTrainingSummary]:
    """Create lightweight history summaries from already-fetched activities."""
    recent = activities[: min(len(activities), 7)]
    medium = activities[: min(len(activities), 28)]

    def summarize(period_label: str, items: list) -> HistoricalTrainingSummary:
        total_duration = sum(item.moving_time or 0 for item in items)
        total_distance = sum(item.distance or 0 for item in items)
        total_load = sum(item.icu_training_load or 0 for item in items)
        active_days = sum(1 for item in items if (item.moving_time or 0) > 0)
        consistency = round(active_days / max(len(items), 1), 2) if items else None
        return HistoricalTrainingSummary(
            period_label=period_label,
            total_activities=len(items),
            total_duration_seconds=total_duration,
            total_distance=total_distance,
            total_training_load=total_load,
            consistency_score=consistency,
        )

    return [
        summarize(f"last_{recent_days}_days_proxy", recent),
        summarize(f"last_{medium_range_days}_days_proxy", medium),
    ]


def build_trends(history: list[HistoricalTrainingSummary]) -> list[PerformanceTrend]:
    if len(history) < 2:
        return []

    recent, medium = history[0], history[1]
    trends: list[PerformanceTrend] = []

    if recent.total_training_load is not None and medium.total_training_load not in (None, 0):
        change = ((recent.total_training_load - medium.total_training_load) / medium.total_training_load) * 100
        direction = "up" if change > 3 else "down" if change < -3 else "flat"
        trends.append(
            PerformanceTrend(
                metric="training_load",
                direction=direction,
                change_percent=round(change, 1),
                timeframe="recent_vs_medium_proxy",
                summary="Comparison of recent and medium-range load proxy.",
            )
        )

    return trends


def print_snapshot_summary(snapshot: DashboardSnapshot) -> None:
    print("Connected to Intervals successfully.")
    print(f"Activities found: {len(snapshot.activities)}")
    print(f"Planned workouts found: {len(snapshot.planned_workouts)}")
    print(f"Wellness entries found: {len(snapshot.wellness_entries)}")
    print(f"Power curve loaded: {'yes' if snapshot.power_curve else 'no'}")


def print_report(snapshot: DashboardSnapshot, api: IntervalsAPI) -> None:
    report = generate_coach_report(api, snapshot)

    print("\n=== Coach Report ===")
    print(f"Readiness: {report.readiness.level} (score {report.readiness.score})")
    for item in report.readiness.observations[:4]:
        print(f"- {item}")

    if report.latest_session is not None:
        print("\nLatest session analysis:")
        print(f"- type: {report.latest_session.session_type}")
        print(f"- stimulus: {report.latest_session.primary_stimulus}")
        print(f"- quality: {report.latest_session.quality}")

    if report.tte is not None:
        print("\nPower curve / TTE:")
        print(f"- level: {report.tte.level}")
        print(f"- modeled FTP: {report.tte.modeled_ftp}")
        print(f"- estimated TTE (min): {report.tte.estimated_tte_minutes}")
        for item in report.tte.observations[:3]:
            print(f"- {item}")

    if report.durability is not None:
        print("\nDurability / decoupling:")
        print(f"- analyzed with: {report.durability.analyzed_with}")
        print(f"- drift level: {report.durability.drift_level}")
        print(f"- decoupling %: {report.durability.decoupling_percent}")
        for item in report.durability.observations[:3]:
            print(f"- {item}")

    if report.plan_alignment is not None:
        print("\nMacro/Meso alignment:")
        print(f"- block focus: {report.plan_alignment.block_focus}")
        for item in report.plan_alignment.matched_items[:3]:
            print(f"- matched: {item}")
        for item in report.plan_alignment.mismatches[:3]:
            print(f"- mismatch: {item}")

    if report.planning is not None:
        print("\nPlanning insight:")
        print(f"- {report.planning.summary}")
        for risk in report.planning.risks[:3]:
            print(f"- risk: {risk}")

    print("\nRecommendation:")
    print(f"- {report.recommendation.summary}")
    for item in report.recommendation.recommendations[:6]:
        print(f"- {item}")
    if report.recommendation.requires_approval:
        print("- Any future write-back must remain approval-first.")


def main() -> None:
    try:
        api = IntervalsAPI()
        activities = api.get_activities(limit=50)
        planned_workouts = api.get_planned_workouts()
        wellness_entries = api.get_wellness() if settings.coach.enable_wellness else []
        power_curve = api.get_power_curve() if settings.coach.enable_power_curve else None

        history = build_history(
            activities,
            recent_days=settings.coach.recent_days,
            medium_range_days=settings.coach.medium_range_days,
        ) if settings.coach.enable_history else []
        trends = build_trends(history) if settings.coach.enable_performance_trends else []

        snapshot = DashboardSnapshot(
            activities=activities,
            planned_workouts=planned_workouts,
            wellness_entries=wellness_entries,
            power_curve=power_curve,
            history=history,
            trends=trends,
        )

        print_snapshot_summary(snapshot)
        print_report(snapshot, api)

    except IntervalsAPIError as exc:
        print(f"Fehler: {exc}")
    except Exception as exc:
        print(f"Unerwarteter Fehler: {exc}")


if __name__ == "__main__":
    main()
