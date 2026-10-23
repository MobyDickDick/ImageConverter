# SEARCH-STRUCTURE-01: fortsetzbare Strukturhypothesen

Ausgangsstand: `b0e6cf8ab` auf `main`.
Arbeitsbranch: `codex/search-structure-scheduling-2026-10-23`.

Die verbindliche P0-Reihenfolge steht in der
[Schwächenprüfung](../weakness_review_2026-10-23.md). Dieses Paket erledigt deren
konkreten nächsten Schritt: Restbildhypothesen als fortsetzbare Arbeitseinheiten
im vorhandenen Scheduler ausführen. Die gesamte SEARCH-STRUCTURE-01-Abnahme
bleibt wegen der unten genannten Struktur-/Übertragungsoperatoren offen.

## Verhalten

Die drei vorhandenen Zerlegungen (Restbildschwellwerte 25, 16 und 36) teilen
sich denselben `ImageSearch` und dessen vorhandenes Bildbudget. Jeder Vorschlag
gibt nach der Erkennung und anschließend nach jedem Registrierungsschritt die
Kontrolle zurück. Der bestehende FairSelector probiert alle Alternativen und
verteilt weitere Arbeit nach gemessenem Fortschritt mit wiederkehrender
Exploration. Eine schlechte erste Anpassung kann die übrigen Vorschläge nicht
mehr durch eine vollständig synchrone Optimierung verdrängen.

Gleiche Form-/Geometrie-/Farbvorschläge werden vor ihrer Optimierung verworfen,
auch wenn der erste Vorschlag gerade pausiert. Die Registrierung verwendet
weiterhin den gemeinsamen Rendercache und dieselben lokalen und vollständigen
Raster-, Instanz- und Relationsprüfungen. Eine abgeschlossene Registrierung
ist noch keine Annahme: Erst der vollständige Szenenprüfer liefert ein Ergebnis.
Aufrufer ohne Suchsession behalten den synchronen Ablauf.

Bei Annahme, Ausnahme oder Zeitablauf werden pausierte Iteratoren geschlossen.
`scene_attempts` und die protokollierten `scene_hypothesis`-Ereignisse unterscheiden
`duplicate`, `no_complete_scene`, `quality_or_geometry_rejected`, `accepted`,
`cancelled` und `time_limit`. Die Liste folgt der Startreihenfolge; der angenommene
Versuch muss wegen der verschränkten Ausführung nicht der letzte Eintrag sein.
`model_slice` und `model_schedule_finished` belegen die tatsächliche Verteilung.

Die Kooperation unterbricht keine einzelne native Erkennung oder Rasterung.
Deren harte Zeitgrenze bleibt Aufgabe der bestehenden Prozessaufsicht. Die
Vorschlagsmenge und die bisherigen Qualitätsgrenzen werden nicht verändert.

## Nachweis

Eine kontrollierte Gegenprobe verwendet echte Rasterung und Registrierung,
dieselben zwei Startvorschläge und ein injiziertes gemeinsames 0,4-Sekunden-Budget.
Jede Rasterung kostet auf der Testuhr 0,03 Sekunden. Die erste Zerlegung hat eine
falsche Kinderfarbe, die zweite die vollständige Szene. Die bisherige serielle
Ausführung erschöpft das Budget ohne angenommenes Ergebnis. Die verschränkte
Ausführung nimmt die zweite an, verwirft einen dritten doppelten Vorschlag und
schließt den ersten. Unabhängige Objekt-/Regions-/Pixelprüfungen bestehen.
Das ist ein deterministischer Fairnessnachweis, keine reale Laufzeitmessung.
Ein weiterer Test erreicht die gemeinsame Deadline mit drei pausierten Fits
und prüft deren vollständiges Schließen und die negativen Ereignisse.

Die echte überwachte CLI wurde auf allen neun bereits bekannten synthetischen
Entwicklungseingaben mit fünf Sekunden pro Bild und Seed 17 wiederholt:
**7/9 bestanden**, wie im bisherigen Endstand. Die zwei kontrastarmen Fälle
bleiben negativ im Nenner. Ausgaben, Aufsichts-/Zugriffsbelege, Workerlogs und
Runtime-Prüfsummen stehen unter
`artifacts/evaluation/structure_scheduler_v1/cli/` und wurden aus dieser
dauerhaften Ablage unabhängig erneut geprüft. Referenz-SVG-Zugriffe sind leer.
Die Eingaben werden aus dem bereits versionierten `residual_scene_v1/final-input`
wiederverwendet. Es gibt keine neue reale Familien- oder Katalogabnahme.

Der abschließende Regressionslauf besteht mit **339/339 Tests** aus 14 Modulen:
Restbild-/Misch-/Verlaufsszenen, zugehörige Evidenzprüfer, Primitive,
Schichten, Fusion, Sichtbarkeit, Szenenbezüge, Scheduler, adaptive Suche und
Such-Bots. Beide neuen Fairness-/Deadline-Tests sind darin enthalten und wurden
nach einer rein sprachlichen Parameternamensänderung nochmals bestanden.
Syntaxprüfung und Whitespace-Prüfung mit der bestehenden CRLF-Konvention bestehen.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_residual_scene_search.py tests/test_conversion_search_scheduler.py -q
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/final-input --output artifacts/evaluation/structure_scheduler_v1/cli --verify-only
.venv/Scripts/python.exe -m tools.evaluate_residual_scene --inputs artifacts/evaluation/residual_scene_v1/final-input --output .tmp/structure-scheduled-repeat
```

## Restumfang

SEARCH-STRUCTURE-01 bleibt offen für Add/Remove/Replace von Instanzen und
Formklassen, gemeinsame negative Evidenz über Registrierungen und unabhängige
reale Übertragung. Danach folgt GENERAL-SCENE-COMPOSITION-09 mit gemeinsamen
Rundungs-/Überdeckungsoperatoren. Vor dieser realen Entwicklung müssen andere
reale Prüffamilien gesperrt werden; GE0018/GE0307 bleiben Entwicklung.
Eine vollständige Archiv-Neukonvertierung und Standardsuite gehören nicht zu
dieser gezielten Abnahme und wurden hier nicht erneut ausgeführt.
