# Angeschnittene Verlaufsrechtecke: synthetische CLI-Abnahme

Rekonstruktionspaket vom 11.11.2026. Die unabhängige reale Gesamtabnahme
und SEARCH-STRUCTURE-01 bleiben offen. HC0010 und Rail wurden nicht konvertiert.

Nachtrag 11.11.2026: Der unten dokumentierte historische Stand bleibt
unverändert erhalten. Das [anschließende Renderer-/Registrierungspaket](../clipped_side_renderer_v1/README.md)
behebt beide Zusatzfehler und besteht dieselben Eingaben mit 12/12,
12/12 und 17/17 unter beiden Renderern und allen lokalen Gates.

## Eingaben und Verfahren

Hauptseed `718293`, separater Zusatzseed `391827`, gekoppelte Varianten
`718293` auf genau einer angeschnittenen Vorlage. Die zwei unabhängigen
Zwölf-Fälle-Kohorten wurden vor den Runtimeänderungen mit librsvg gesichert.
Die zusätzliche Variantenkohorte wurde separat vorbereitet; ihre übliche
Skalierungs-/Positionsverteilung und alle 17 Versuche bleiben erhalten.
Generator-/Referenzgeometrie bleibt ausschließlich in der externen Abnahme;
die überwachten CLI-Worker dürfen keine Referenz-SVGs lesen.

Die Eingaben decken vier einzelne Schnittrichtungen, zwei benachbarte
Bildränder, Subpixellagen, scharfe und gerundete Eltern, helle/dünne Konturen,
beide Verlaufsachsen, gemischte Kinder, Überdeckungsgruppen und Einzelobjekte ab.
Eine vollständig verborgene scharfe Seite ist kein positiver Kontrollfall:
Ohne unabhängige Beobachtung bleibt ihre Lage unbestimmbar.

Native Objektarten, Boxen, Radius, Konturbreite, Verlauf und beobachtete
Eltern-/Tiefenrelationen werden unabhängig geprüft. Zusätzlich gelten globale,
objektlokale, sichtbare Eck-, sichtbare Seiten- und Restbildgates mit beiden
Renderern. Verdeckte Ecken tragen keine positiven Eckbelege bei. Die normalen
Grenzen bleiben unverändert: MSE `0,01`, Vordergrund-MSE `0,04`, IoU `0,85`,
Kantenübereinstimmung `0,72`, Boxfehler `2,5 px`, Radiusfehler `1,25 px` und
Konturbreitenfehler `0,85 px`. Bildbudget fünf Sekunden, acht Kinder und
96 Strukturzustände bleiben verbindlich.

## Ergebnisse

| Kohorte | Fälle | CLI abgenommen | Beide Renderer / alle lokalen Gates |
| --- | ---: | ---: | ---: |
| Hauptfälle vorher | 12 | 0 | 0 |
| Hauptfälle nachher | 12 | 12 | 12 |
| Separater Zusatzseed | 12 | 10 | 10 |
| Gekoppelte Varianten | 17 | 17 | 17 |

Die endgültige Szenen-/Registrierungs-/Rendererregression deckt **325/325** verschiedene aktuelle Prüffälle ab, das Kernprofil **42/42**. Der ursprüngliche breite Lauf hatte einen veralteten Negativtest, der beobachtbares Anschneiden pauschal verbot. Nach seiner Aufteilung in einen vollständig geprüften positiven und einen unbestimmbaren negativen Fall besteht das gesamte aktualisierte Modul. Der Knotenvergleich bestätigt alle aktuellen Test-IDs ohne Fehler oder Überspringungen. Der ursprüngliche Fehllauf bleibt ausdrücklich erhalten.

Die Zusatzfälle `clipped_rectangle_02` und `clipped_rectangle_10` bleiben Ablehnungen am unveränderten Fünf-Sekunden-Budget. Für `02` bestehen die exakten Referenzkontrollen mit beiden Renderern: Hier fehlt ein hinreichend guter registrierter Zwischenstand. Für `10` scheitert bereits die exakte native Referenz an den Seitengates; diese Ursachen werden getrennt weitergeführt.

`summary.json` enthält alle endgültigen Fälle einschließlich Ablehnungen,
Eingabe-/Referenz-/Beschreibungs-/Ausgabehashes, Objekt- und Relationsorakel,
lokale Messwerte beider Renderer, Runtimehashes, Testresultate und die separate
exakte Renderer-Gegenprobe. Hauptfälle vor/nach verwenden identische PNGs und
Beschreibungen. Neue Suchversuche ersetzen keine ursprünglichen Fehlversuche.
Die Vorläufe und ihre Ergebnisse sind getrennt ausgewiesen.

## Verbleibende Grenze

Der Zusatzfall `clipped_rectangle_10` besteht bereits mit seinem geometrisch
exakten Referenz-SVG die globale und native Objektprüfung. Die lokale
Seitenprüfung scheitert bei MuPDF mit ungefähr `0,6924` und `0,4769`, während
librsvg alle Seiten besteht. Ein solcher Fall darf nicht durch eine große
Elternfläche oder eine höhere anfängliche Pixelerrorgrenze freigegeben werden.
Die vollständige Zusatzkohorte bleibt im Nenner; sie wird nicht zur
erfolgreichen unabhängigen Gesamt-Abnahme umgedeutet.
Der [konkrete Renderer-Nachfolger](../../../docs/next_arbeitspaket_2026-11-11_clipped_side_renderer.md)
bleibt deshalb offen. Diese synthetische Entwicklung belegt keinen Transfer
auf neue reale Familien.

## Reproduktion

```powershell
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --prepare .tmp/cropped-primary-new --seed 718293
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/cropped-primary-new --output .tmp/cropped-primary-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/cropped-primary-new --output .tmp/cropped-primary-cli-new --audit .tmp/cropped-primary-audit-new.json --require-all
.venv/Scripts/python.exe -m pytest tests/test_clipped_rectangular_parent.py tests/test_rectangular_gradient_parent.py tests/test_rounded_gradient_parent.py tests/test_clipped_gradient_parent.py tests/detailtests/test_rounded_renderer.py tests/test_thin_rim_depth.py tests/test_same_paint_overlap.py tests/test_filled_symbols_runtime.py tests/test_search_minimum_effort.py -q
```

Zusatzkohorte mit `--seed 391827`, Varianten mit `--seed 718293 --variations`
in jeweils neuen Ordnern vorbereiten. Für den negativen Zusatzlauf
`--require-all` weglassen; seine Ablehnungen und unabhängigen Auditfehler
bleiben ausdrücklich sichtbar. Rohdaten und CLI-Bäume liegen separat unter
`.tmp/clipped-rectangle/`; nur kompakte Nachweise werden versioniert.
Der CI-Job prüft die vorab erklärte Hauptkohorte und die Negativkontrollen.
Ein GitHub-Lauf wurde hier nicht gestartet.
