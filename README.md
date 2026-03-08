# intervals-coach

Ein Python-Projekt für einen KI-gestützten Coaching-Assistenten auf Basis von Intervals.icu-Daten.

## Ziel

Der Coach soll Trainingsdaten lesen, interpretieren und daraus fundierte Empfehlungen ableiten. Standardmäßig arbeitet das System im **Read-Only-Modus**: Es analysiert Daten und formuliert Vorschläge, schreibt aber nichts zurück, solange keine ausdrückliche Freigabe vorliegt.

Bevorzugter Ablauf:

**lesen → analysieren → vorschlagen → auf Freigabe warten → synchronisieren**

## Geplante Datenquellen

- absolvierte Aktivitäten
- geplante Workouts und Kalendereinträge
- Wellnessdaten
- historische Trainingsdaten
- Power Curve / Performance Curve
- Performance-Trends über die Zeit

## Coaching-Prinzipien

- Nie nur ein einzelnes Workout bewerten
- Wellnessdaten nur als Kontext verwenden
- Historie und aktuelle Belastung gemeinsam betrachten
- Power Curve zur Einordnung von Stärken, Schwächen und Entwicklung nutzen
- Änderungen nur nach expliziter Freigabe zurückschreiben

## Aktueller Stand

Aktuell enthält das Repository erste Pydantic-Modelle für:

- Aktivitäten
- geplante Workouts
- Wellnessdaten
- Dashboard-Snapshots

## Nächste Schritte

- Modelle für Power Curve und Historie ergänzen
- Empfehlungsmodell einführen
- Konfiguration für `write_mode` ergänzen
- Prompt- und Policy-Dateien hinzufügen
- Analyse- und Recommendation-Services aufbauen

## Approval-First Write Rule

Schreibzugriffe sind nur erlaubt, wenn:

1. `write_mode = true`
2. eine konkrete Freigabe für die jeweilige Aktion vorliegt

Ohne diese Bedingungen bleibt das System read-only.

## Coach Brain V2

Diese Version ergänzt:
- rule-based Power Curve / TTE interpretation
- Durability / Decoupling analysis via activity intervals or streams
- Macro/Meso plan alignment using files in `docs/training_context/`

Die Write-Back-Logik bleibt approval-first.
