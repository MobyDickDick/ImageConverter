# GitHub-Issue #2004: native Pfeilpaare

Auswahl am 25.10.2026: Die offenen GitHub-Issues tragen keine Prioritätslabels.
Das Strukturproblem bei Linien und Dreiecken betrifft viele offene Fälle der
AC0020-/AC0040-Familie. Dieses Paket nimmt ausschließlich #2004 ab; die übrigen
Fälle benötigen eigene Beschreibungs-/Quellenprüfungen und vollständige Läufe.
Die übergeordnete P0-Struktursuche bleibt offen.

## Reproduzierte Ursachen und Hypothesen

1. Der unveränderte Ausgangsstand `19911195e` reproduziert den Originalfehler:
   RGB-MSE 0,040850, Vordergrund-MSE 0,345058, Kontur 0,228928, IoU 0,084052.
   Der Originalfehler verhindert den Start der 16 Varianten.
2. Nur die Beschreibung zu ändern kann den alten, farblich festgelegten und
   geometrisch normalisierten Pfeilalgorithmus nicht ändern. Zudem fehlen dem
   alten Prüfraster die Schäfte: MuPDF ignoriert eingebettete CSS-Klassen.
3. Nur CSS aufzulösen stellt die korrekten Schäfte wieder her, beseitigt aber
   die falsche gemeinsame Pfeilgeometrie und fehlende Querlinie nicht. Der
   entsprechende echte CLI-Lauf scheitert weiterhin, einschließlich der
   Komplexitätsgrenze durch den alten Zeilenmasken-Fallback. Die Messwerte dieser
   Gegenprobe sind in `summary.json` gesichert.
4. Die kombinierte Korrektur passt beobachtete Schäfte, Dreiecke und optionale
   Querlinie unabhängig an. Zwei Geometrie-/Farbmodelle ersetzen die erzwungene
   Symmetrie. Subpixelverfeinerung und eine zusätzliche Vordergrundverlustgröße
   verhindern, dass fast weiße Kanten langer dünner Linien verloren gehen.
   Die Abnahmegrenzen werden nicht verändert.

Das Original-SVG und der vorhandene Katalog-JPEG zeigen links Rot mit Spitze
nach oben, rechts Blau mit Spitze nach unten und eine rote Querlinie. Der
AC0021-Verweis und die bisherigen Farb-/Richtungsangaben waren falsch; der
Katalogeintrag ist jetzt eigenständig und korrigiert. Das Quellen-SVG wird weder
verändert noch vom Konverter gelesen.

Die alte Rasterprüfsumme dokumentiert einen Rendererfehler. Deshalb ist der
Vorher-/Nachher-Vergleich keine Behauptung identischer Rastereingaben: die neue
Referenz enthält wieder die tatsächlich vorhandenen Schäfte. Eine unabhängig
formulierte SVG-Gegenprobe mit direkten Präsentationsattributen und der reale
JPEG prüfen die Renderkorrektur zusätzlich.

## Abnahme und Wiederholung

`manifest.json` bewahrt die vollständige Issue-Seedzahl als JSON-Integer,
Quellen-/Beschreibungsprüfsummen, die alte Beschreibung und das unveränderte
Budget von 64 Iterationen/60 Sekunden. `summary.json` enthält die Messwerte,
Hashes und native Ausgabe jedes erfolgreichen Falls. Die echte CLI bekommt
ausschließlich Raster und Beschreibung; Referenzzugriffe bleiben gesperrt.

```powershell
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/arrow_pair_issue_v1/manifest.json --output-dir .tmp/arrow-pair-frozen
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/arrow_pair_issue_v1/manifest.json --output-dir .tmp/arrow-pair-holdout --seed 817263
.venv/Scripts/python.exe -m pytest -q tests/test_arrow_pair_runtime.py tests/detailtests/test_dual_arrow_runtime_helpers.py tests/detailtests/test_rendering_gradient_compatibility.py tests/test_filled_symbols_runtime.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Neue Ausgabeverzeichnisse verwenden. CI bewahrt die vollständigen Raster, SVGs,
Vergleiche und CLI-Logs 14 Tage. Original plus 16 Varianten und der zusätzliche
Seed werden getrennt ausgewiesen. Der Katalog-JPEG ist eine zusätzliche lokale
Rastergegenprobe, keine neue unabhängige Bildfamilie. Das Erfolgsarchiv wird
nicht erhöht. #2004 wird erst durch Übernahme des Pull Requests geschlossen.

Lokale Abnahme: ursprünglicher Seed **17/17**, Zusatzseed **17/17**. Die
gezielten Form-/Rendererprüfungen bestehen **101 Tests**, die bisherigen
Panel-/Replay-/Renderprüfungen **39 Tests** und `core-green` **42 Tests**,
jeweils mit Exit-Code 0. Die Einbindung des vollständig geprüften Kandidaten in
den Bildsuchstatus beendet die erfolgreiche CLI-Suche ohne weiteren Versuch.

Die CSS-Aufbereitung unterstützt einfache Element-, Klassen- und ID-Selektoren
sowie deren Verknüpfungen, Spezifität, Quellreihenfolge und Inline-/Important-
Vorrang. Nicht unterstützte Stylesheets bleiben vollständig unverändert.
Komplexe CSS-Selektoren und allgemeine SVG/CSS-Unterstützung bleiben außerhalb
dieses Pakets. Die native Pfeilsuche benötigt sichtbare vertikale Schäfte,
entgegengesetzte Dreiecksrichtungen und gegebenenfalls eine beobachtete Querlinie.
