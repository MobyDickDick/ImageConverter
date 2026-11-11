# P0: angeschnittene äußere Verlaufsrechtecke

**SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT**, synthetischer Teilumfang
**implementiert**, Abnahme und verbleibende Renderergrenze unten.
Fortsetzung von SEARCH-STRUCTURE-01 nach der
[Korrektur des Rundungsrenderers](next_arbeitspaket_2026-11-06_rounded_renderer.md).

## Ziel und Lieferumfang

Die bestehende gemeinsame Komposition soll angeschnittene äußere Rechtecke
anhand sichtbarer Seiten und Ecken rekonstruieren. Gemischte Kinder,
Überdeckungsgruppen, Einzelobjekte, Verlauf, helle Konturen und optional
beobachtete Rundungen bleiben im selben Such- und Qualitätsvertrag.

1. Vor Runtimeänderungen neue unabhängige librsvg-Raster mit Objekt-, Radius-,
   Tiefen- und Zugehörigkeitsmarkierungen sichern. Bildkanten, unterschiedliche
   Schnittrichtungen und Subpixellagen getrennt abdecken; bisherige Eingaben
   und ihre Prüfsummen erhalten.
2. Bildrandabschnitte von tatsächlich sichtbaren Elternseiten trennen.
   Fehlende Grenzen oder Radien ohne ausreichende unabhängige Beobachtung
   konservativ ablehnen. Kein Rückschluss aus Generator- oder Referenzdaten.
3. Elternhypothesen mit der vorhandenen begrenzten Strukturagenda und
   gemeinsamen Registrierung verbinden. Keine Sonderbehandlung nach Bildnamen,
   Familien oder Seeds; fünf Sekunden Bildbudget und 96 Zustände beibehalten.
4. Echte CLI vor/nach der Änderung, separate Zusatz- und Variantenkohorten,
   unabhängige native Objekt-/Relationsprüfung und beide Rasterrenderer
   verwenden. Sichtbare Ecken, Seiten und Restbild lokal prüfen; verdeckte
   Ecken nicht als positive Beobachtung zählen. Keine Qualitätsgrenze lockern.
5. Vollständig sichtbare scharfe/gerundete Eltern, angeschnittene Elternkreise,
   dünne Konturen und negative Evidenz als Regression mitprüfen.

HC0010 und Rail bleiben `sealed_unrun` ohne Konvertierungsversuch. Dieses
synthetische Teilpaket ersetzt weder SEARCH-STRUCTURE-01 noch die offene
unabhängige reale Gesamtabnahme.

## Start

```powershell
.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_rounded_gradient_parent.py tests/test_clipped_gradient_parent.py tests/detailtests/test_rounded_renderer.py -q
```

## Umsetzung vom 11.11.2026

Die gemeinsame Szenensuche misst im Randfall nur innerhalb des Bildes
beobachtete Füllungsübergänge. Bildränder erzeugen keine Messpunkte.
Ein begrenzter geometrischer Fit verlangt unabhängige Bedingungen für alle
vier Grenzen und gegebenenfalls den Radius. Mindestens zwei getrennte
sichtbare Rundungsbögen müssen den Radius stützen; ein scharfes Rechteck
mit vollständig fehlender Seite bleibt unbestimmbar und wird abgelehnt.
Die Rekonstruktion verwendet weder Generatorgeometrie noch Referenz-SVGs.

Sichtbare gerade Kanten werden zusätzlich aus integrierter Antialiasdeckung
vermessen. Konturbreite und Farbe stammen von tatsächlich sichtbaren
Seitenabschnitten. Das Messband behandelt den Bildrand ausdrücklich, damit
eine angeschnittene äußere Kontur vorhandene innere Füllkanten nicht verdeckt.
Native Kinder, ihre Rundungen, Überdeckungsgruppen und Tiefenbedingungen
verwenden weiterhin die gemeinsame Registrierung und die begrenzte Agenda.

Jede sichtbare Seite erhält zusätzlich zu Objekt-, Eck- und Restbildgates
eine eigene lokale Rasterprüfung. Acht kleine 1/16-Pixel-Korrekturen prüfen
Quantisierungsgrenzen vor dem langen
Koordinatendurchlauf. Die Registrierung kann vollständig geprüfte Kandidaten
auch dann behalten, wenn eine andere Hilfsverlustfunktion sie schlechter
bewertet; die unveränderte anfängliche Pixelerrorgrenze bleibt verbindlich.
Nur für den neuen Randpfad werden vollständige semantisch und lokal geprüfte
Zwischenstände an die bestehende Deadline-Wiederherstellung übergeben.
Die Mindestsuchzeit läuft weiter; die Aufsicht darf ausschließlich solche
quellen-/SVG-gebundenen geprüften Zwischenstände retten.

Fünf Sekunden Bildbudget, maximal acht Kinder, 96 Strukturzustände und alle
Qualitätsgrenzen bleiben unverändert. Die kleinen Registrierungsstartwerte
sind keine zusätzlichen Strukturzustände. Kein Bildname, Seed oder
Generatorparameter entscheidet im Produktionscode über die Rekonstruktion.

## Abnahme und Grenzen

Die vor der Runtimeänderung gesicherten Haupt- und Zusatzraster bleiben mit
ihren Prüfsummen erhalten. Beide wurden unabhängig mit librsvg erzeugt.
Eine zusätzliche gekoppelte Kohorte verwendet die unveränderte übliche
Skalierungs-/Positionsverteilung auf einer angeschnittenen Vorlage; sie wurde
separat vorbereitet und nicht auf erfolgreiche Varianten reduziert.
Der saubere Vorherlauf der echten CLI besteht **0/12** Hauptfälle.
Der endgültige Nachherlauf besteht **12/12** Hauptfälle, **10/12** separate
Zusatzfälle und **17/17** gekoppelte Varianten. Die unabhängige Abnahme mit
beiden Renderern bestätigt genau diese **39/41** Ausgaben; die zwei
Zusatzablehnungen bleiben im Nenner. Alle Zahlen und Prüfsummen stehen im
[kompakten Nachweis](../artifacts/evaluation/clipped_rectangular_parent_v1/README.md).

Der große Regressionslauf bestand 323/324 Tests; der einzige Fehler war die
alte pauschale Ablehnung beobachtbarer angeschnittener Rundungsrechtecke.
Dieser Test unterscheidet jetzt einen vollständig geprüften positiven und
einen unbestimmbaren negativen Anschnitt. Die vollständige Modulnachprüfung
besteht 52/52; der Vergleich mit der aktuellen Sammlung bestätigt zusammen
325/325 verschiedene Prüffälle. Das Kernprofil besteht 42/42, ohne Fehler
oder Überspringungen. Der ursprüngliche Fehllauf bleibt erhalten; nach den
CLI-Abnahmen wurden keine Produktionsdateien mehr geändert.

Die unabhängige Nachprüfung verlangt native Objektarten, Boxen, Radien,
Konturen, Verlaufsachsen und Eltern-/Tiefenrelationen sowie globale,
objektlokale, sichtbare Eck-, Seiten- und Restbildgates mit MuPDF und librsvg.
Vollständig verdeckte Ecken werden ausdrücklich als `hidden` erfasst und
nicht positiv gezählt. Fehlende Kinder, Zusatzformen, Textur, falsche Achsen,
dunkle/fehlende Konturen, unbestimmbare scharfe Seiten und verborgene Radien
bleiben negative Kontrollen.

Ein zusätzlicher scharfer Randfall zeigt eine separate Renderergrenze:
Selbst sein geometrisch exaktes natives Referenz-SVG besteht global, verfehlt
aber im MuPDF-Raster zwei lokale Seitenprüfungen; librsvg besteht dieselben
Prüfungen. Eine Ablehnung dieses Falls wird weder durch eine großzügigere
Grenze noch durch die große Elternfläche ersetzt. Der folgende
[Renderer-Seitennachweis](next_arbeitspaket_2026-11-11_clipped_side_renderer.md)
ist deshalb das nächste P0-Paket.
Zusätzlich bleibt ein separater Zusatzfall ohne geprüften Zwischenstand
am Fünf-Sekunden-Limit; seine exakten Kontrollen bestehen mit beiden
Renderern. Die Registrierungsgrenze wird im selben Folgepaket ausdrücklich
vom Rendererfehler getrennt weitergeführt. Die übergeordnete Kompositionsaufgabe und
die unabhängige reale Gesamtabnahme bleiben offen; HC0010 und Rail bleiben
`sealed_unrun` ohne Konvertierungsversuch. Vorhandene Katalog-Testausgaben
werden durch die neuen Prüfungen nicht überschrieben.

Reproduktion in frischen Ausgabeordnern:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_clipped_rectangular_parent.py -q
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --prepare .tmp/clipped-new --seed 718293
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-new --output .tmp/clipped-cli-new --require-all
.venv/Scripts/python.exe -m tools.evaluate_clipped_rectangular_parent --inputs .tmp/clipped-new --output .tmp/clipped-cli-new --audit .tmp/clipped-audit-new.json --require-all
```

Für die separate Zusatzkohorte `--seed 391827` und für die gekoppelte
Kohorte `--seed 718293 --variations` verwenden. Die Zusatzkohorte enthält
den dokumentierten negativen Rendererfall; dort `--require-all` weglassen,
aber alle Versuche einschließlich Ablehnungen im Bericht behalten.
Der neue CI-Job prüft die vorab erklärte Hauptkohorte, Negativkontrollen
und tatsächliche CLI-Ausgaben mit beiden Renderern. Er wurde lokal
vorbereitet; ein GitHub-Lauf wurde hier nicht gestartet.
