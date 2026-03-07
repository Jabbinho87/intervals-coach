from __future__ import annotations

from app.intervals_api import IntervalsAPI, IntervalsAPIError
from app.models import DashboardSnapshot

def print_latest_activity(snapshot: DashboardSnapshot) -> None:
    """Print a small summary of the latest activity."""
    if not snapshot.activities:
        print("\nKeine Aktivitäten gefunden.")
        return

    latest = snapshot.activities[0]
    print("\nLatest activity:")
    print(f"- name: {latest.name or 'n/a'}")
    print(f"- date: {latest.display_date or 'n/a'}")
    print(f"- type: {latest.type or 'n/a'}")

def print_next_planned_workout(snapshot: DashboardSnapshot) -> None:
    """Print a small summary of the next planned workout."""
    if not snapshot.planned_workouts:
        print("\nKeine geplanten Workouts gefunden.")
        return

    next_workout = snapshot.planned_workouts[0]
    print("\nNext planned workout:")
    print(f"- name: {next_workout.name or 'n/a'}")
    print(f"- date: {next_workout.display_date or 'n/a'}")
    print(f"- type: {next_workout.type or 'n/a'}")

def print_latest_wellness(snapshot: DashboardSnapshot) -> None:
    """Print a small summary of the latest wellness entry."""
    if not snapshot.wellness_entries:
        print("\nKeine Wellness-Einträge gefunden.")
        return

    latest = snapshot.wellness_entries[0]
    print("\nLatest wellness entry:")
    print(f"- date: {latest.display_date or 'n/a'}")
    print(f"- resting HR: {latest.resting_hr if latest.resting_hr is not None else 'n/a'}")
    print(f"- HRV: {latest.hrv if latest.hrv is not None else 'n/a'}")
    print(f"- weight: {latest.weight if latest.weight is not None else 'n/a'}")

def main() -> None:
    """Entry point for the beginner-friendly read-only dashboard."""
    try:
        api = IntervalsAPI()

        activities = api.get_activities(limit=10)
        planned_workouts = api.get_planned_workouts()
        wellness_entries = api.get_wellness()

        snapshot = DashboardSnapshot(
            activities=activities,
            planned_workouts=planned_workouts,
            wellness_entries=wellness_entries,
        )

        print("Connected to Intervals successfully.")
        print(f"Activities found: {len(snapshot.activities)}")
        print(f"Planned workouts found: {len(snapshot.planned_workouts)}")
        print(f"Wellness entries found: {len(snapshot.wellness_entries)}")

        print_latest_activity(snapshot)
        print_next_planned_workout(snapshot)
        print_latest_wellness(snapshot)

    except IntervalsAPIError as exc:
        print(f"Fehler: {exc}")
    except Exception as exc:
        print(f"Unerwarteter Fehler: {exc}")

if __name__ == "__main__":
    main()