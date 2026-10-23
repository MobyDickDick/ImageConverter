# Restbildhypothesen: begrenzte synthetische Entwicklung

Basis `9a1f0b661`, Branch `codex/adaptive-generalization-review-2026-10-23`.
Diese Messung ist keine neue reale Familienabnahme. Acht vor der Runtime-Änderung
erzeugte Eingaben bleiben im Nenner; der neunte Fall kam erst während der
Entwicklung hinzu. Gesamte Untersuchung und Rangfolge:
[Schwächenprüfung](../../../docs/weakness_review_2026-10-23.md).

| Kohorte | Vorher | Nachher | Bedeutung |
| --- | --- | --- | --- |
| Acht unveränderte Entwicklungseingaben | 0/8 | 6/8 | Horizontale/vertikale Gruppen, drei bis sechs Rechtecke und beliebige getrennte Anordnungen; zwei kontrastarme Fehlversuche bleiben sichtbar. |
| Zusätzlicher Antialiasing-Repro | nicht in der ursprünglichen Matrix | 1/1 | Tatsächliche Runtime-Reihenfolge: Schwellwert 25 abgelehnt, 16 abgelehnt, 36 angenommen. Gleiche Objekt-/Regions-/Pixelgates. |

Alle Versuche liefen über die echte `semantic-only`-CLI mit demselben überwachten
Fünf-Sekunden-Budget und Suchseed 17. Die Ausgabe-SVGs wurden anschließend
unabhängig neu gerendert und anhand extern vorgegebener nativer Objekte und
Regionen geprüft. Beide Vektorzugriffswächter sind leer. Die ersten acht
Eingabebilder und Beschreibungen sind zwischen beiden Matrizen identisch.
Die Berichte enthalten die tatsächlich verwendeten Runtime-Prüfsummen; das
Git-Commit allein würde die uncommittierte Entwicklung nicht identifizieren.

`before/report.json`/`verification.json` enthalten die negativen Erstversuche.
`final/report.json`/`verification.json` enthalten alle neun Endversuche.
Eingaben, Beschreibungen, Objektmarkierungen, tatsächliche SVGs, Ergebniszeilen,
Zugriffswächter, Workerlogs und Vergleichsbilder bleiben gespeichert. Doppelte
Renderbilder und andere nicht für die Nachprüfung benötigte Reports sind
ignoriert. `summary.json` fasst die Messung zusammen.

Der zweite Schwellenwert findet die kontrastarmen Kinder, ihre unveränderten
lokalen Qualitätsprüfungen reichen aber nicht für die Abnahme. Diese beiden
Fälle werden weder übersprungen noch als Erfolge gezählt. Die Runtime darf
weiterhin einen Ersatzweg versuchen; dessen Ausgabe besteht die unabhängige
Abnahme hier ebenfalls nicht. Im endgültigen Lauf endet `residual_06` ohne SVG
am Fünf-Sekunden-Limit. Die unabhängige Nachprüfung prüft dafür gesondert die
Aufsichtsdatei, beide Zugriffswächter und das tatsächliche Fehlen von SVGs;
der Versuch bleibt negativ im Nenner. Fehlende Ergebniszeilen allein sind
weiterhin keine ausreichende Evidenz. Sechs Tests sichern diese Unterscheidung.

`checks.json` dokumentiert Tests und ihre Grenzen. Der vollständige Archivlauf
ergibt 378/379; der einzige fehlende SVG-Versuch mit langer Beobachtungslücke
besteht bei neuer Einzelprüfung. `archive-recheck.json` und
`archive-repeat.json` erhalten beide Resultate getrennt. Die Standardsuite bleibt
wegen einer reproduzierten Zeitmessungsassertion im unveränderten Deadline-Test
rot; die gezielten Szenen-/Evidenztests bestehen. Das ist keine grüne Gesamtabnahme.

Ansichten: jeweils links Quelle, mittig Ausgabe, rechts Differenz:
[Vier Kinder](final/residual_03/comparison.png),
[Strategiewechsel bei enger Lücke](final/residual_08/comparison.png).

Vorhandene Messung unabhängig erneut prüfen:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/development-input --output artifacts/evaluation/residual_scene_v1/before --verify-only
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/final-input --output artifacts/evaluation/residual_scene_v1/final --verify-only
```

Neue, getrennte Wiederholung des endgültigen Verfahrens:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --prepare .tmp/residual-new-input
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs .tmp/residual-new-input --output .tmp/residual-new-output
.venv/Scripts/python.exe -m pytest tests/test_residual_scene_search.py tests/test_mixed_gradient_scene_runtime.py -q
```

`--require-all` verlangt positive Abnahme aller Fälle; dieser Schalter schlägt
wegen der beiden bewusst erhaltenen negativen Beobachtungen fehl.
Für weitere Entwicklung andere Seeds und anschließend vorab gesperrte reale
Familien verwenden. Kein Kataloggewinn; das Erfolgsarchiv bleibt unverändert.
