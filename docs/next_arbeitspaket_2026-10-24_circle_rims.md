# P0: helle Kreisränder bei gemischter Überdeckung

Ausgewählt aus **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[verbindlichen Aufgabenliste](task_priority_2026-10-24.md). Ausgangscommit
`854be74c2`; eigener Branch `codex/search-structure-circle-rims-2026-10-24`.

## Änderung

Der vorhandene Verlaufskreis-/Struktursuchweg verbindet jetzt teilweise
überlappende innere Kreise mit hellen Konturen und Rechtecke mit optional
gerundeten Ecken. Der bisherige ausdrückliche Ausschluss entfällt.
Getrennte Füll- und Randdeckungen liefern zwei unabhängig beobachtete
Bögen: Innen- und Außenradius bestimmen native Kreisgeometrie und Strichbreite.
Die Mittelpunkte müssen bis auf 0,6 Pixel übereinstimmen; beide Bögen benötigen
die bestehende Mindestabdeckung von einem halben Kreisumfang. Fremde Farbe
oder verdeckte Schnittkanten begründen keinen Radius.

Inventar, native Silhouetten, beobachtete Tiefe und unabhängige Objekt-,
Relations-, lokale und globale Pixelgates bleiben erforderlich. Es gelten
weiter höchstens 96 Strukturzustände und dasselbe Bildbudget. Keine
Katalogkennung oder Referenzvektorlesung im Konvertierungsprozess.

## Zwei Hypothesen mit kontrolliertem CLI-Vergleich

Zwölf synthetische Szenen mit zwei bis vier Kindern, beiden Verlaufsachsen,
verschiedener Tiefe, Rundung und Randbreiten wurden mit Seed `731921` vor der
Runtime-Änderung gespeichert. Die serielle Gegenprobe mit dem unveränderten
Ausgangsmodul besteht **0/12**. Ein erster parallel begonnener Baseline-Lauf
wird nicht als kontrollierter Vergleich verwendet.

Hypothese 1 sucht für beide Kreisgrenzen angrenzende Elternfarbe und besteht
**3/12** über die echte CLI. Auch fehlende Ausgaben bleiben im Nenner.
Die Füllkante grenzt jedoch an die helle Kontur; diese ist mehr als Antialiasing.

Hypothese 2 verwendet an der Innenkante gemessene Randfarbe und an der
Außenkante Elternfarbe. Sie besteht auf denselben Eingaben **12/12**.
Ein zusätzlicher Seed `918527` besteht **12/12**; genau eine gekoppelte
Plan-B-Vorlage mit Seed `342781` besteht **17/17**. Alle Läufe verwenden die
echte überwachte CLI, fünf Sekunden je Bild und Suchseed 17. Die tatsächlich
gespeicherten SVGs werden unabhängig neu gerastert und geprüft.

Hashes, Einzelmessungen und Laufsteuerung stehen in
[`summary.json`](../artifacts/evaluation/circle_rims_v1/summary.json), Testsignale
in [`checks.json`](../artifacts/evaluation/circle_rims_v1/checks.json).

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 731921 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 918527 --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 342781 --rounded --outlines --variations
.venv/Scripts/python.exe -m pytest -q tests/test_mixed_overlap_outlines.py tests/test_mixed_overlap_composition.py tests/detailtests/test_plan_b_variations.py tests/detailtests/test_plan_b_failure_tasks.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Die gezielten Tests bestehen **139/139**, das Kernprofil **42/42**, jeweils
Exit 0. Fehlende/dunkle Ränder, fehlender Elternrand, Ellipse/Quadrat als
Kreisersatz, Zusatzobjekte, gleiche Farben, zu wenig sichtbarer Bogen,
Fremdtextur und falsche Überlappung bleiben Ablehnungen. Die gemeldete
Gesamtdauer des gezielten Testprozesses beträgt 2446 Sekunden; daraus
wird kein Leistungsversprechen abgeleitet.

## Grenzen und Sitzungslog

Dies ist eine synthetische Entwicklungsabnahme. Unabhängige reale Familien,
beliebige gemischte Fünf-bis-acht-Kinder-Inventare und vollständig verdeckte
Grenzen sind nicht abgenommen. **SEARCH-STRUCTURE-01 bleibt insgesamt offen.**
Keine vollständige Standardsuite und keine neue Katalogabnahme werden behauptet.
Die [CI-Diagnose](plan_b_ci_diagnostics_2026-10-24.md) erklärt separat, weshalb
lokale Entwicklungsnachweise rote zufällige Katalogläufe nicht ersetzen.

- Getestet: kontrollierter CLI-Vergleich, Zusatzseed, 17 gekoppelte Fälle, Gegenproben, Kernprofil.
- Ergebnis: 0/12 auf 12/12; zusätzliche 12/12 und 17/17; 139 und 42 Tests bestanden.
- Blocker: unabhängige reale Übertragung und breitere Komposition bleiben offen.
- Nächster Schritt: neue CI-Debug-Artefakte zur Ursachenanalyse der Katalogfehler verwenden.
- Startbefehl: `python -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 918527 --rounded --outlines`.
