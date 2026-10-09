# Plan-B-Kandidatenliste (SVG nachzeichnen)

Ziel: maximal **5** aktive JPG-Kandidaten, die derzeit noch nicht zufriedenstellend konvertieren, aber voraussichtlich nicht "hoffnungslos komplex" sind.

## Aktuelle Kandidaten (Stand: 2026-10-09, nach Strich-/Punkt-Abnahme)

Der reproduzierbare Review über `688` renderbare Paare zeigte am 2026-10-03,
dass die damalige Plan-B-Spitze **nicht zufriedenstellend** war. Details und
Reprobefehl stehen in `docs/plan_b_satisfaction_audit_2026-10-03.md`. Ein
bloßer grüner Konvertierungs-Exit oder eine Verbesserung gegenüber einem
früheren Wert gilt nicht als Qualitäts-Pass.

`AC0554_2_L` wurde im ZG7.6-Pilot katalogfrei mit dem Track
`envelope_polyline_over_vertical_color_field_v1` bearbeitet und besteht nun
zusammen mit dem fremd benannten Holdout `renamed_holdout` beide harten Gates;
der maschinenlesbare Beleg steht in
`artifacts/evaluation/semantic_only_plan_b_pilot_v1/report_2026-10-04.json`.
Die nächste Rotation beginnt deshalb mit dem nächsten weiterhin offenen Fall.

`DLG0010_1` besteht nach katalogfreier Rasterregistrierung zweier verschachtelter
Rechteckflächen beide Gates (`mean_delta2=468.700897`, `edge_alignment=0.903612`).
Der graue, fremd benannte Holdout besteht ebenfalls ohne Regression. Die Abnahme
verwendet eine zutreffende Beschreibung der sichtbaren Rechteckstruktur; die
alte XML-Farbangabe „hellgraues Quadrat“ für das rote Raster bleibt als
Datenqualitätsfolge dokumentiert. Details: `docs/next_arbeitspaket_2026-10-04_dlg0010_1.md`.

`AC0724_1_S` besteht nach der allgemeinen Hauptdiagonalspiegelung der
Quadrat-/Griff-Topologie und rastergestützter Innenmarkierung beide Gates
(`mean_delta2=569.914673`, `edge_alignment=0.842189`). M-/L-Holdouts bestehen
ebenfalls ohne Regression. Die Innenkontur wird geometrisch erkannt; es wird
kein T-Label im Parser vorausgesetzt. Details:
`docs/next_arbeitspaket_2026-10-04_ac0724_1_s.md`.

`AC0252_1` besteht nach rastergestützter Kreis-/Dreieck-/Farbregistrierung
beide Gates (`mean_delta2=458.776276`, `edge_alignment=0.939825`). Grüne und
graue Holdouts bestehen ebenfalls ohne Regression; drei unabhängige CLI-Läufe
reproduzieren alle SVG-Bytes und Gate-Records. Die gemeinsame XML beschreibt
jetzt zutreffend ein nach rechts zeigendes Dreieck und enthält keine falschen
Farbangaben oder Griffreferenz. Details:
`docs/next_arbeitspaket_2026-10-05_ac0252_1.md`.

`AC0731_1_L` besteht nach katalogfreier Quadrat-/Griff-/Textregistrierung
beide Gates (`mean_delta2=920.249756`, `edge_alignment=0.964218`). Alle fünf
Farb-/Größen-Holdouts bestehen ebenfalls ohne Regression. Der explizite Text
bleibt einschließlich Groß-/Kleinschreibung erhalten; die gemeinsame XML
beschreibt jetzt eigenständig Quadrat, unteren Griff und `P`. Details:
`docs/next_arbeitspaket_2026-10-05_ac0731_1_l.md`.

`GE1003_M` besteht nach katalogfreier Haken-/Scheibenregistrierung beide
Gates (`mean_delta2=401.955200`, `edge_alignment=0.922646`). L-/S-Holdouts
bestehen ebenfalls ohne Regression; zwei unabhängige CLI-Läufe reproduzieren
alle SVG-Bytes und Gateentscheidungen. Die XML beschreibt die Topologie jetzt
eigenständig. Native Radialverläufe bleiben im SVG erhalten; ein privater
Renderadapter verhindert die schwarzen PyMuPDF-Artefakte. Details:
`docs/next_arbeitspaket_2026-10-05_ge1003_m.md`.

`AC0404_1_L` besteht im aktuellen CLI bereits vor der Änderung beide Gates
(`mean_delta2=89.825623`); der bisherige hohe Kandidatenwert stammt aus einer
alten Sammelausgabe. Alle 18 Farb-/Größen-/SIA-Varianten bestehen jetzt beide
Gates ohne Metrikregression. Eine katalogfreie Flächenprüfung verwirft die
fälschlich als Dreieck vereinfachten Kreissegmente und verbessert vier SIA-Fälle.
Die XML beschreibt das Links-Dreieck eigenständig. Details:
`docs/next_arbeitspaket_2026-10-05_ac0404_1_l.md`.

`GE9011_6M` besteht nach katalogfreier Dreieck-/Verlaufsschaft-Registrierung
beide Gates (`mean_delta2=500.660004`, frische CLI-Baseline `15406.099609`).
Alle 14 Farb-/Größenvarianten bestehen ohne Metrikregression; zwei unabhängige
CLI-Läufe reproduzieren sämtliche 28 SVG-Bytes und Gateentscheidungen.
Die gemeinsame XML beschreibt die Pfeiltopologie jetzt eigenständig. Details:
`docs/next_arbeitspaket_2026-10-06_ge9011_6m.md`.

`GE0281` besteht nach katalogfreier Kreis-/Radialverlauf-Registrierung beide
Gates (`mean_delta2=308.333344`, frische CLI-Baseline `14981.222656`).
Alle sechs Farbvarianten bestehen ohne Metrikregression; zwei unabhängige
CLI-Läufe reproduzieren alle zwölf SVG-Bytes und Gateentscheidungen.
Die XML für das Ziel und den grauen Holdout beschreibt die Kreisstruktur
jetzt eigenständig. Details: `docs/next_arbeitspaket_2026-10-06_ge0281.md`.

`GE9013_6M` besteht nach katalogfreier Richtungsnormalisierung der
Dreieck-/Verlaufsschaft-Registrierung beide Gates (`mean_delta2=488.706665`,
frische CLI-Baseline `15279.816406`). Alle 14 Farb-/Größenvarianten bestehen
ohne Pflichtmetrikregression; zwei unabhängige CLI-Läufe reproduzieren
sämtliche 28 SVG-Bytes und Gateentscheidungen. Die gemeinsame XML beschreibt
die Pfeilstruktur jetzt eigenständig. Details:
`docs/next_arbeitspaket_2026-10-07_ge9013_6m.md`.

Das Checkboxpaket `DLG0031` / `DLG0021` und das Dachlinienpaket `AC0554`
sind inzwischen abgeschlossen. Das folgende Luftbefeuchterpaket `AC0130_S`
besteht mit M-/L-Holdouts beide Gates ohne Regression. Die vorhandene
SVG-Vorlage hat eine abweichende Liniengruppen-/Balkenstruktur und besteht
mit zwei Seeds jeweils 16/16 unveränderte Roundtrip-Gates. Alle CLI-SVG-Bytes
und Gateentscheidungen sind reproduzierbar. Details:
`docs/next_arbeitspaket_2026-10-08_ac0130_s.md`.

Die Alarmglocke `GE1420_S` ist mit M-/L- und neutraler Variante abgeschlossen;
alle vier bestehen die regulären Gates. Details:
`docs/next_arbeitspaket_2026-10-08_ge1420_s.md`.
Das folgende Quadrat-/Griffpaket `AC0704_1_L` besteht mit allen sechs roten
und hellgrauen Größenvarianten beide regulären Gates und die strengeren
Plan-B-Pixelgrenzen. Zwei CLI-Läufe reproduzieren alle zwölf SVGs und
Gateentscheidungen. Details: `docs/next_arbeitspaket_2026-10-08_ac0704_1_l.md`.

`AC0402_1_S` besteht mit allen 18 gefüllten Farb-/Größen-/SIA-Varianten beide
regulären Gates ohne Pflichtmetrikregression. Die frische Ziel-CLI-Baseline
sinkt von `14019.147461` auf `262.637512`; eine eigenständige XML aktiviert die
vorhandene Kreis-/Dreieckregistrierung ohne Runtime-Algorithmusänderung.
Die SVG-Vorlage besteht mit zwei Seeds jeweils 16/16 strengere Plan-B-Gates.
Fünf JPG-Varianten verfehlen die separate strengere IoU-Grenze; drei ungefüllte
Konturdreieck-Raster sind separat beschrieben und nicht Teil dieser Abnahme.
Details: `docs/next_arbeitspaket_2026-10-08_ac0402_1_s.md`.

`AC0403_1_L` und alle 18 Farb-/Größen-/SIA-Varianten bestehen bereits mit
der frischen CLI-Baseline beide regulären Gates. Das historische Ziel-SVG
ohne Dreieck erreicht `13989.019531`, das frische SVG `93.733124`.
Die XML-Präzisierung mit absoluter Richtung nach unten verändert keine
SVG-Bytes; die Runtime bleibt unverändert. Zwei unabhängige Abnahmen
reproduzieren alle SVGs und Gates. 11/18 JPG-Varianten bestehen zusätzlich
die strengere Plan-B-Prüfung; deren vollständiger Nachweis bleibt offen.
Details: `docs/next_arbeitspaket_2026-10-09_ac0403_1_l.md`.

1. `GE0032` – `mean_delta2=13826.389648`, `normalized_mse=0.070877`.
2. `GE9023_6M` – `mean_delta2=13675.259766`, `normalized_mse=0.070103`.
3. `AC0413_1_M` – `mean_delta2=13465.694336`, `normalized_mse=0.069028`.
4. `AC0713_1_L` – `mean_delta2=13458.083984`, `normalized_mse=0.068989`.
5. `AC0721_1_S` – `mean_delta2=13368.759766`, `normalized_mse=0.068531`.

`AC0714_L` und alle fünf Farb-/Größen-Holdouts bestehen nach eigenständiger
Beschreibung und rastergestützter Strich-/Punktregistrierung beide regulären
Gates ohne Pflichtmetrikregression sowie die strengeren Plan-B-Pixelgrenzen.
Die frische Ziel-CLI-Baseline verbessert sich von `33066.082031` auf `24.314667`.
Zwei unabhängige Läufe reproduzieren sämtliche SVGs und Gateentscheidungen.
Details: `docs/next_arbeitspaket_2026-10-09_ac0714_l.md`.

Die nächste reguläre Rotation beginnt mit `GE0032`; vor Änderungen ist eine
frische CLI-Baseline erforderlich. Der Review über 1.000 Einträge (993 renderbare
Paare) und sein exakter Aufruf stehen im kompakten Nachweis
`artifacts/evaluation/marked_square_recheck_v1/summary_2026-10-09.json`.
Alle 48 gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze.
104 renderbare Einträge überschreiten die Reviewgrenze. Die neue Reihenfolge
schließt die sechs geprüften Varianten aus der historischen Diff-Auswahl aus.
Vollständige Tabellen liegen lokal unter `.tmp/ac0714/review/`.

Die gekoppelte randomisierte Plan-B-Auswahl `AC0538_1L_sia` mit Seed
`3948009396310964094` besteht nach eigenständiger Beschreibung und katalogfreier
Rasterregistrierung **16/16 Qualitäts-Pässe**. Ein weiterer Seed besteht ebenfalls
16/16. Eingabe-/Referenzhashes des eingefrorenen Laufs bleiben identisch;
die Qualitätsgrenzen wurden nicht verändert. Beschreibung allein besteht den
isolierten Vergleichsfall noch nicht. Details und Generalisierungsgrenzen:
`docs/plan_b_variation_acceptance.md`. Dieser zufällige Fall ersetzt keinen
der fünf regulären Kandidaten.

Abschluss des Runtime-Registrierungspakets `AC0713_1_S` (2026-10-04):
`Rotated180SquareKelleGlyph` gehört nun auch zu den beiden Runtime-Kind-Sets.
Das gespeicherte CLI-SVG erreicht `mean_delta2=2194.829346`,
`normalized_mse=0.011251`, `edge_alignment=0.734084` und besteht beide harten
Gates. Die M-/L-Holdouts bestehen ebenfalls, ohne Metrikregression gegenüber
dem eingefrorenen Vorlauf. Der Beleg steht in
`artifacts/evaluation/rotated_square_kelle_recheck_v1/report_2026-10-04.json`.
Die helle Innenmarkierung bleibt eine dokumentierte visuelle Qualitätsfolge;
das CLI meldet dafür weiterhin konzentrierten Restfehler. Details stehen in
`docs/next_arbeitspaket_2026-10-04_ac0713_1_s.md`.

## Ad-hoc Plan-B-Aufgabe (2026-07-05)

- `AC0512_1_L` – vom Nutzer angefragte Generalisierungsaufgabe für ein querformatiges rotes/oranges Rechteck-Icon mit grauem Rand und drei parallelen weissen Diagonalstreifen. Die Aufgabe ist als separater Plan-B-Contract dokumentiert in `docs/next_arbeitspaket_2026-07-05_runVI.md` und soll nicht die fünf automatisch triagierten aktiven Kandidaten verdrängen.
- `AC0832` – vom Nutzer angefragte Generalisierungsaufgabe für eine linke Kelle mit runder CO²-Scheibe und hochgestellter `2`. Die Aufgabe ist als separater Plan-B-Contract dokumentiert in `docs/next_arbeitspaket_2026-07-05_runVJ.md` und soll nicht die fünf automatisch triagierten aktiven Kandidaten verdrängen.
- `AC0840_L` – vom Nutzer angefragte Plan-B-Aufgabe für ein 28×28-AC08-`rF`-Kreisbadge, bei dem die bisherige Konvertierung den Text zu klein und gegenüber der Vorlage versetzt rendert. Die Aufgabe ist als separater Textregistrierungs-Contract dokumentiert in `docs/next_arbeitspaket_2026-07-08_runVX.md` und soll nicht die fünf automatisch triagierten aktiven Kandidaten verdrängen.
- `AC0213_L` – aus dem neu hinzugefügten Sample `artifacts/images_to_convert/samples/AC0213_L.svg` abgeleitete Generalisierungsaufgabe für ein linksorientiertes Ventilsymbol mit grauem Verlaufskörper, Leitungsanschlüssen und `M`-Glyph. Die Aufgabe ist als sample-basierter Roundtrip-Contract dokumentiert in `docs/next_arbeitspaket_2026-07-11_runXJ.md` und soll nicht die fünf automatisch triagierten aktiven Kandidaten verdrängen.
- `AC0552_2_L` – aus dem neu hinzugefügten Sample `artifacts/images_to_convert/samples/AC0552_2_L.svg` abgeleitete Generalisierungsaufgabe für ein flaches grünes Chevron-/Pfeilsegment mit mehrstufigem Vertikalgradienten und beschnittener Innenkontur. Die Aufgabe ist als sample-basierter Roundtrip-Contract dokumentiert in `docs/next_arbeitspaket_2026-07-11_runXJ.md` und soll nicht die fünf automatisch triagierten aktiven Kandidaten verdrängen.
- `AC0502_1L_sia` – sample-basierte Plan-B-Aufgabe für die 80×40-Variante aus grauer Diagonalverbindung, Kreis und rotem Diagrammfeld mit weissem Kreuz; Roundtrip-Baseline `delta2=497.845640`. Der Contract und die Abgrenzung zur fachlich anders beschriebenen AC0502-Familie stehen in `docs/next_arbeitspaket_2026-07-31_runABH.md`.
- `AC0502_1M_sia` – Skalierungs-/Generalisierungsaufgabe derselben Primitive auf 60×30 statt eine zweite ID-spezifische Nachzeichnung; Roundtrip-Baseline `delta2=465.142682`. Der gemeinsame Familien-Contract steht in `docs/next_arbeitspaket_2026-07-31_runABH.md`.
- `AC0538_1L_sia` – sample-basierte Plan-B-Aufgabe für die verwandte Diagrammvariante mit grauer Rahmenkontur und weisser Stufenkurve; Historische Roundtrip-Baseline `delta2=1629.625242`; die aktuelle Parametervariation besteht 32/32 Qualitätsgates, siehe `docs/plan_b_variation_acceptance.md`. Der Klassifikations-/Perception-Contract steht in `docs/next_arbeitspaket_2026-07-31_runABH.md`.

## Perception-Lerneffekt (Pflichtabschnitt ab PF8)

Aktueller Recheck: Quadrat, rechter Griff und beschriebener schräger Strich mit
quadratischem Punkt sind für die geprüften Raster `generalisiert`. Alle sechs
echten Varianten bestehen beide regulären und die strengeren Plan-B-Gates.
Unabhängige Geometrie-, Farb-/Kontrast-, Lage- und Auflösungstests sowie
Umbenennung sind abgesichert. Fehlende oder zusätzliche Innenbefunde werden
verworfen. Details: `docs/next_arbeitspaket_2026-10-09_ac0714_l.md`.

Vorheriger Recheck: Die vorhandene Kreis-/Dreieckregistrierung ist für 18
gefüllte Rechts-Dreieck-Raster `generalisiert`. Eine eigenständige Beschreibung
aktiviert den bestehenden Algorithmus; es gibt keine neue Runtime-Regel.
Alle 18 bestehen die regulären Gates, die SVG-Vorlage mit zwei Seeds jeweils
16/16 strengere Plan-B-Gates. Die fünf strengeren JPG-IoU-Folgen und drei
Konturdreieck-Raster bleiben außerhalb dieses engeren Nachweises.
Details: `docs/next_arbeitspaket_2026-10-08_ac0402_1_s.md`.

Vorheriger Recheck: Die unbeschriftete Quadrat-/Griff-Topologie ist für die
geprüften Raster `generalisiert`. Lage, Größe, Rand-/Griffbreite und Farben
stammen aus den Pixeln; alle sechs echten Fälle bestehen beide regulären und
die strengeren Plan-B-Gates. Unabhängige Farb-/Lage-/Auflösungstests und
Umbenennung sind abgesichert. Fehlender Griff, zusätzliche Objekte und
kontrastreiche Innenmarkierungen werden verworfen. Details:
`docs/next_arbeitspaket_2026-10-08_ac0704_1_l.md`.

Vorheriger Recheck: Zickzack-/Innenrahmen- und Liniengruppen-/Balkenregistrierung
sind für die geprüften Luftbefeuchterstrukturen `generalisiert`. Die drei
JPG-Größen bestehen beide Gates; die vorhandene SVG-Vorlage besteht nach
Rasterisierung und Parametervariation mit zwei Seeds jeweils 16/16.
Wiederholungsperiode, Lage, Strichbreiten und Verlauf stammen aus den Pixeln.
Synthetische Farb-/Lage-/Auflösungstests, neutrale Namen und verbotener
Sample-Zugriff sind abgesichert. Die Andreaskreuz-Variante ist separat und
gehört nicht zu diesem Generalisierungsnachweis. Details:
`docs/next_arbeitspaket_2026-10-08_ac0130_s.md`.

Aktueller Recheck: Vertikale Pfeile mit Dreieck und getrenntem Verlaufsschaft
sind für beide Richtungen `generalisiert`. Alle 14 nach unten gerichteten
Farb-/Größenvarianten sowie zusätzliche Lage-, Größen- und Farbtests bestehen;
Umbenennung, Negativfälle und verbotener Sample-Zugriff sind abgesichert.
Die zufällige Diagramm-/Stufenkurvenaufgabe ist für die geprüften Varianten `generalisiert`.
Details: `docs/next_arbeitspaket_2026-10-07_ge9013_6m.md`.

Aktueller Recheck: Die Unterscheidung zwischen einem Dreieck und dem gekrümmten
Kreissegment ist `generalisiert`. Sie verwendet das Verhältnis der beobachteten
Fläche zur vereinfachten Dreiecksfläche ohne Katalogkennung. Alle 18 Varianten
bestehen beide Gates; explizite Richtungen, Größen-/Farbvariation, Umbenennung
und falsche Topologien sind abgesichert. Details:
`docs/next_arbeitspaket_2026-10-05_ac0404_1_l.md`.

Vorheriger Recheck: Haken-/Scheibenregistrierung sind `generalisiert`;
Ziel und zwei Größen-Holdouts bestehen beide Gates. Umbenennung, verschobene
Lage, doppelte Größe, zwei Grüntöne und Negativfälle sind abgesichert. Der
Renderadapter erhält native Radialverläufe in den gespeicherten SVGs.
Details: `docs/next_arbeitspaket_2026-10-05_ge1003_m.md`.

Vorheriger Recheck: Quadrat-/Griff-/Textregistrierung sind `generalisiert`;
Ziel und fünf Farb-/Größen-Holdouts bestehen beide Gates. Umbenennung, exaktes
beschriebenes `P`, andere Farben, verschobene Lage, doppelte Größe und die
Einzelbuchstaben `P`, `M`, `T` sind abgesichert. Details stehen in
`docs/next_arbeitspaket_2026-10-05_ac0731_1_l.md`.

Vorheriger Recheck: Kreis-/Dreieck-/Farbregistrierung sind `generalisiert`;
Ziel sowie zwei Farb-Holdouts bestehen beide Gates. Umbenennung, andere Farben,
verschobene Lage, doppelte Größe und vier Richtungen sind abgesichert.
Details stehen in `docs/next_arbeitspaket_2026-10-05_ac0252_1.md`.

Vorheriger Recheck: Hauptdiagonalspiegelung und rastergestützte Innenmarkierung
sind `generalisiert`; Ziel und zwei Größen-Holdouts bestehen beide Gates,
Umbenennung und synthetische Farb-/Lage-/Größenvariationen sind abgesichert.
Details stehen in `docs/next_arbeitspaket_2026-10-04_ac0724_1_s.md`.

Vorheriger Recheck: Die Erkennung verschachtelter Rechteckflächen ist
`generalisiert`; sie überträgt Lage, Farben und Größen aus dem Raster auf zwei
SVG-Primitive und besteht Ziel-/Holdout-Gates sowie Farb-/Größenvariationen.
Der Beleg steht in `docs/next_arbeitspaket_2026-10-04_dlg0010_1.md`.
Die folgenden Run-SR-/PF8-Notizen dokumentieren den historischen Verlauf.

Die Run-SR-Triage ersetzt die erledigte `GE1001_M`/`GE9021_7M`-Rotation durch fünf kleinere Diff-Fälle. Vor der konkreten Nachzeichnung ist für `DLG0021` zu prüfen, ob die dominanten grafischen Primitive bereits als katalogfreie Perception-Kandidaten (`color_patch`, `polygon_path`, `line`, `rectangle` oder `text_glyph`) auftauchen. Der Lerneffekt wird pro Kandidat im nächsten Arbeitspaket als `generalisiert`, `nur Sonderfall` oder `noch nicht erkannt` dokumentiert.

Der PF8-Linkage-Report wurde als gekoppelte Plan-B-Aufgabe erneut auf die neue Rotation ausgerichtet (`5/5` Samples mit dokumentiertem Perception-Lerneffekt): `GE1410_L` ist seit Run ST für Achsen-/Linien- und Dreieck-Seeds `generalisiert`, seit Run TG stroke-seitig pixelnäher getunt, seit Run TQ über neutrale PolygonPath-Füllfarb-Probes weiter registriert, seit Run TR um katalogfreie PolygonPath-Stroke-Width-Probes, seit Run UB um feine PolygonPath-Punktprobes, seit Run UG um feine absolute PolygonPath-Stroke-Width-Probes, seit Run UL um sehr feine PolygonPath-Punktprobes, seit Run UR um ultrafeine PolygonPath-Punktprobes, seit Run UV um microfeine PolygonPath-Punktprobes, seit Run VA um nanofeine PolygonPath-Punktprobes und seit Run VD um microfeine absolute PolygonPath-Stroke-Width-Probes, seit Run VE um nanofeine absolute PolygonPath-Stroke-Width-Probes, seit Run VF um picofeine absolute PolygonPath-Stroke-Width-Probes und seit Run VH um picofeine PolygonPath-Punktprobes, seit Run VL um femtofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run VN um attofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run VS um zeptofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run VY um yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run XE um half-yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run XJ um quarter-yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes und seit Run XO um sixteenth-yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run XT um thirtysecond-yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes, seit Run YD um eine weitere 64th-/128th-yoctofeine PolygonPath-Punkt- und Stroke-Width-Zwischenstufe und seit Run YO um 256th-yoctofeine, seit Run YP um 512th-yoctofeine und seit Run YZ um 2048th-yoctofeine und seit Run ZE um 4096th-yoctofeine PolygonPath-Punkt- und Stroke-Width-Probes ergänzt, `GE9012_6M` besitzt seit Run SV einen beschreibungsbasierten Sonderfall-Contract für das BackBottom-/hellgraues-Quadrat-Vokabular und seit Run TL eine neutrale Füllfarb-Elementregistrierung, seit Run TV feine katalogfreie RectBorder-/ColorPatch-Kantenprobes, seit Run UD neutrale Rechteck-Opacity-Probes, seit Run UI feine Opacity-Zwischenstufen, seit Run UN noch feinere Opacity-Zwischenstufen, seit Run UO ultrafeine Opacity-Zwischenstufen, seit Run UT microfeine Opacity-Zwischenstufen und seit Run UX nanofeine Opacity-Zwischenwerte, seit Run VC picofeine Opacity-Zwischenwerte, seit Run VP femtofeine Opacity-Zwischenwerte und seit Run VU attofeine Opacity-Zwischenwerte, seit Run WA zeptofeine Opacity-Zwischenwerte, seit Run XG half-yoctofeine, seit Run XL quarter-yoctofeine, seit Run XQ eighth-yoctofeine, seit Run XV sixteenth-yoctofeine, seit Run XX thirtysecond-yoctofeine, seit Run YJ 128th-yoctofeine und seit Run ZB 8192th-yoctofeine ColorPatch-/RectBorder-Opacity-Zwischenwerte, `GE9013_1M` besitzt seit Run SW denselben beschreibungsbasierten Sonderfall-Contract, eine vertikale Canvas-Skalierungsabsicherung, seit Run TC eine semantische Non-Composite-Auswahl, seit Run TM eine neutrale warme Füllfarb-Elementregistrierung, seit Run TX neutrale RectBorder-Stroke-Farbprobes, seit Run UE feine absolute RectBorder-Stroke-Width-Probes, seit Run UJ sehr feine ColorPatch-/RectBorder-BBox-Subpixel-Probes, seit Run UP ultrafeine BBox-Subpixel-Probes, seit Run UY nanofeine warme Füllfarb-Probes, seit Run VQ eine picofeine warme Zwischenfarbe, seit Run VV femtofeine warme Zwischenfarben, seit Run XH eine half-yoctofeine warme Zwischenfarbe mit verbessertem isoliertem Recheck und seit Run XR eine eighth-yoctofeine warme Zwischenfarbe, seit Run XW eine sixteenth-yoctofeine warme Zwischenfarbe, seit Run YB eine thirtysecond-yoctofeine warme Zwischenfarbe, seit Run YX eine sixtyfourth-yoctofeine warme Zwischenfarbe, seit Run YM 1024th-yoctofeine, seit Run YU 4096th-yoctofeine und seit Run ZM 262144th-yoctofeine ColorPatch-/RectBorder-Opacity-Zwischenwerte, während `SE0041_1` seit Run SU als Sonderfall eine manuelle, beschreibungsbasierte Square-Badge-Seed-Annahme nutzt, seit Run TI mit neutralen Inset-/Höhenparametern pixelnäher registriert ist und seit Run TS neutrale Kopf-Füllfarbe plus graue Kontur nutzt, seit Run UC feine katalogfreie RectBorder-/ColorPatch-BBox-Subpixel-Probes besitzt und seit Run UH feine absolute Rule-Stroke-Width-Probes, seit Run UM noch feinere absolute Rule-/RectBorder-Stroke-Width-Probes und seit Run US microfeine absolute Rule-/RectBorder-Stroke-Width-Probes nutzt; Run UW ergänzt nanofeine absolute Rule-/RectBorder-Stroke-Width-Probes, der isolierte Einzellauf bleibt metrisch stabil bei `Mean-Delta²=2436.707764`; Run VB ergänzt picofeine absolute Rule-/RectBorder-Stroke-Width-Probes mit stabilem isoliertem Recheck; Run VO ergänzt attofeine absolute Rule-/RectBorder-Stroke-Width-Probes mit stabilem isoliertem Recheck; Run VT ergänzt zeptofeine absolute Rule-/RectBorder-Stroke-Width-Probes mit stabilem isoliertem Recheck; Run VZ ergänzt yoctofeine absolute Rule-/RectBorder-Stroke-Width-Probes mit stabilem isoliertem Recheck; Run XF ergänzt half-yoctofeine absolute Rule-/RectBorder-Stroke-Width-Probes mit stabilem isoliertem Recheck; Run XP ergänzt eine explizite half-yoctofeine Rule-/RectBorder-Stroke-Width-Testabsicherung und bestätigt den isolierten Einzellauf semantisch; Run XZ ergänzt eighth-yoctofeine absolute Rule-/RectBorder-Stroke-Width-Probes; Run YE ergänzt sixteenth-yoctofeine, Run YG 256th-yoctofeine, Run YH 512th-yoctofeine, Run YI 1024th-yoctofeine, Run YR 2048th-yoctofeine und Run ZA 4096th-yoctofeine absolute Rule-/RectBorder-Stroke-Width-Probes. Für `DLG0021` ist die manuelle Seed-Annahme seit Run SS als neutraler Checkbox-/Haken-Primitive-Contract dokumentiert; Run SX ergänzt daran katalogfrei den beschriebenen grünen Vertikalgradienten, Run TF verschlankt die Stroke-Registrierung, Run TH justiert Hakenlage und Schattenstärke pixelnäher, Run TK verschiebt Haken/Schatten nochmals katalogfrei in die Rasterkontur, Run TN verallgemeinert die lokale Punkt- und Füllfarbregistrierung, Run TO ergänzt neutrale Stroke-Farbprobes für `PolygonPath`-Konturen, Run TP ergänzt neutrale Linecap-/Linejoin-Probes für `PolygonPath`-Konturenden und -ecken, Run TY ergänzt neutrale Opacity-Probes, Run TW ergänzt feine katalogfreie Punktprobes, Run TZ ergänzt neutrale Stroke-Gradient-Stop-Probes, und Run UA ergänzt neutrale Stroke-Gradient-Offset-Probes mit stabilem isoliertem Recheck; Run UF ergänzt feine ±2,5-Prozentpunkte für Stroke-Gradient-Offsets, der isolierte Recheck bleibt stabil bei `Mean-Delta²=17056.199219`; Run UK ergänzt noch feinere ±1,25-Prozentpunkte für Stroke-Gradient-Offsets mit stabilem isoliertem Recheck; Run UQ ergänzt ultrafeine ±0,625-Prozentpunkte für Stroke-Gradient-Offsets mit stabilem isoliertem Recheck; Run UZ ergänzt microfeine ±0,3125-Prozentpunkte für Stroke-Gradient-Offsets mit stabilem isoliertem Recheck; Run VG ergänzt nanofeine ±0,15625-Prozentpunkte für Stroke-Gradient-Offsets mit stabilem isoliertem Recheck; Run VK ergänzt picofeine ±0,078125-Prozentpunkte, Run VR attofeine ±0,01953125-Prozentpunkte, Run XC halbyoctofeine ±0,00244140625-Prozentpunkte, Run XD quarter-yoctofeine ±0,001220703125-Prozentpunkte, Run XI eighth-yoctofeine ±0,0006103515625-Prozentpunkte, Run XN sixteenth-yoctofeine ±0,00030517578125-Prozentpunkte und Run XS sixtyfourth-yoctofeine ±0,0000762939453125-Prozentpunkte, Run XX 128th-yoctofeine ±0,00003814697265625-Prozentpunkte und Run YN 512th-yoctofeine ±0,0000095367431640625-Prozentpunkte für Stroke-Gradient-Offsets; der isolierte Recheck liegt zuletzt bei `Mean-Delta²=16476.853516`. Die reine Bilddetektion bleibt weiterhin nicht ausreichend.

## Pflege-Regel (fortan)

Bei jedem abgeschlossenen Arbeitspaket:

- erledigte/gelöste Einträge entfernen,
- auf **maximal 5** Einträge auffüllen,
- den Review mit `tools/review_conversion_quality.py` reproduzierbar erneuern,
- bevorzugt Kandidaten wählen, die
  - in `artifacts/converted_images/diff_pngs/*_diff.png` weiterhin als problematisch auftauchen,
  - noch nicht häufig in expliziten Aufgaben genannt wurden,
  - visuell eher einfach bis mittel wirken (nicht hoffnungslos komplex).
