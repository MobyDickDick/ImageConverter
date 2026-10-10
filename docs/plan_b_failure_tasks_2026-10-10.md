# Plan-B-Fehler als dokumentierte Aufgaben (2026-10-10)

Branch: `codex/plan-b-failure-tasks-ac0711-2026-10-10`.

Der Workflow `Plan B random task acceptance` bleibt bei verfehlter Abnahme rot.
Nach dem Lauf erzeugt `tools.report_plan_b_failures` zusätzlich
`failure_summary.md` und `failure_tasks.json`. Die GitHub-Laufübersicht zeigt
pro fehlgeschlagenem Fall die Fehlercodes und vier Pixelmessungen. Der
Wiederholungsbeleg enthält Quelle, Originalbeschreibung, Seed, SVG-/Beschreibungs-
und Rasterhashes, Suchbudget, Timeout sowie die unveränderten Grenzen.
Prozessfehler, fehlende Ausgaben und Timeouts behalten zusätzlich den letzten
Teil des CLI-Logs, bevor der Runner seine Arbeitsdateien entfernt.

Fehler früherer Originale bleiben Aufgaben, auch wenn eine später ausgewählte
Aufgabe 17/17 besteht. Eine nicht gestartete Variante zählt weiterhin nicht als
Konvertierungsfehler. Abbruch, Vorbereitungsfehler und fehlende Berichte erzeugen
eine eigene Ausführungsaufgabe. Scheitert beispielsweise die Installation ohne
Konvertierungsbericht, ergänzt die Issue-Erfassung die fehlgeschlagenen
GitHub-Jobschritte. Auch ein Infrastrukturfehler nach bestandener Qualitätsprüfung
wird dokumentiert.

## Dauerhafte GitHub-Aufgaben

Der neue Workflow `Plan B failure tasks` verarbeitet nach jedem abgeschlossenen
Abnahmelauf dessen JSON-Artefakt. Er führt ausschließlich die Software aus dem
Default-Branch aus; der auslösende PR wird nicht ausgecheckt. Artefakte liefern
nur Daten, keine ausführbaren Befehle. Schreibrechte für Issues liegen allein
in diesem separaten Workflow. Die Abnahme selbst hat nur Repository-Leserechte.

Ein Issue-Schlüssel kombiniert Quelle, SVG-Hash, Beschreibungshash und Fehlerphase.
Ein anderer Seed erzeugt deshalb keine zweite Aufgabe für denselben Fehlerfall.
Weitere Läufe aktualisieren den Beleg; ein erneut auftretender geschlossener
Fehler öffnet dieselbe Aufgabe wieder. Die Erfassung läuft seriell, um doppelte
Erstellungen durch gleichzeitig abgeschlossene Läufe zu vermeiden. Notizen
außerhalb des markierten Belegblocks bleiben bei Aktualisierungen erhalten.
Ein erfolgreicher anderer Seed schließt eine noch offene Fehleraufgabe nicht
automatisch.

Die Gruppe verwendet ausdrücklich `queue: max`, damit neue Abschlüsse bereits
wartende Erfassungen nicht ersetzen. GitHub erlaubt dabei bis zu 100 wartende
Läufe; darüber hinaus bleiben die Fehlerentwürfe im ursprünglichen
Abnahmeartefakt erhalten. Siehe [GitHub-Concurrency-Dokumentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

Sind Issues deaktiviert oder fehlen Schreibrechte, schlägt der Erfassungsschritt
sichtbar fehl. Die Aufgabenentwürfe und `issue_sync.json` bleiben als Artefakt
90 Tage verfügbar. Die ursprünglichen Berichte und `source.png` bleiben im
Abnahmeartefakt 14 Tage verfügbar. Der Folgeworkflow wird erst nach Übernahme
dieser Änderung in den Default-Branch aktiviert; er verarbeitet neue Laufabschlüsse.

## Konkreter CI-Nachweis

Der [Lauf 38067037125](https://github.com/MobyDickDick/ImageConverter/actions/runs/38067037125)
vom 2026-10-10 hat zwei verschiedene Fehlschläge:

| Quelle | Ergebnis | Aufgabe |
|---|---|---|
| `z_111.svg` | Original verfehlt RGB-MSE, Vordergrund-MSE, Kontur und IoU; Varianten nicht gestartet | [#1908](https://github.com/MobyDickDick/ImageConverter/issues/1908) |
| `AC0552_2_L.svg` | Original besteht; acht Varianten verfehlen Kontur und/oder IoU; insgesamt 9/17 | [#1909](https://github.com/MobyDickDick/ImageConverter/issues/1909) |

Beide Issues wurden aus den tatsächlichen GitHub-Berichten erstellt. Die
heruntergeladenen JSON-Berichte, Ursprungsbilder, Aufgaben und Issue-Links stehen
dauerhaft unter `artifacts/evaluation/plan_b_ci_failure_audit_2026-10-10/`.
Die Fehlerursache wird durch die Messwerte eingegrenzt; eine Reparatur der beiden
Motivfamilien ist durch diese Dokumentation noch nicht belegt.

## Lokale Wiederholung und Prüfung

```powershell
.venv/Scripts/python.exe -m tools.report_plan_b_failures --artifact-dir artifacts/evaluation/plan_b_ci_failure_audit_2026-10-10 --run-url https://github.com/MobyDickDick/ImageConverter/actions/runs/38067037125
.venv/Scripts/python.exe -m pytest -q tests/detailtests/test_plan_b_failure_tasks.py tests/detailtests/test_plan_b_variations.py --basetemp .tmp/plan-b-task-tests
```

Die Tests prüfen unter anderem frühere Originalfehler bei erfolgreichem
Gesamtlauf, Abbruch, fehlende/malformed Berichte, Wiederholungsidentität,
Verzeichnisausbruch, fehlende Issue-Rechte und den Erhalt von CLI-Diagnosen.
Das Issue-Upsert wurde mit einem kontrollierten API-Ersatz getestet; die beiden
konkreten Issues wurden über die echte GitHub-Verbindung angelegt. Der neue
GitHub-Folgeworkflow selbst kann vor seiner Übernahme noch nicht als im
Produktivbetrieb abgenommen bezeichnet werden.
