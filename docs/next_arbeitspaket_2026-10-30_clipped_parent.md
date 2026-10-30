# P0: Am Bildrand angeschnittene Verlaufskreise

Abgegrenzter Teil von **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[Prioritätenliste](task_priority_2026-10-24.md). Ausgangscommit `7e6124bea`.
Anlass sind die drei ausdrücklich offenen Randfehler `probe_08`, `probe_12`
und `probe_13` aus der [Überdeckungsgruppen-Abnahme](next_arbeitspaket_2026-10-28_overlap_groups.md).

## Ursache und Umsetzung

Die ursprüngliche Kreisschätzung behandelte die gerade Schnittkante am
Bildrahmen als Bestandteil der Kreisgrenze. Außerdem verlangte die
Registrierung auch vom äußeren Kreis eine vollständig innerhalb des Bildes
liegende Geometrie. Bereits geringfügig angeschnittene Varianten wurden so
zurückgewiesen.

Bei einer den Rahmen berührenden Vordergrundkontur werden nun die
Rahmenpunkte einschließlich eines Pixels Abstand von der Kreisschätzung
ausgeschlossen. Mindestens 24 verbleibende Konturpunkte, mindestens ein
halber beobachteter Kreisbogen, der bisherige Residualgrenzwert von 0,85 Pixeln
und ein innerhalb des Bildes liegender Mittelpunkt sind erforderlich.
Der Radius bleibt auf die kleinere Bilddimension begrenzt. Eine Ellipse,
zu kurze Bögen und eine vollständig verdeckte Kreisgrenze liefern keine
zulässige Ersatzgeometrie.

Die sichtbare Bogenlänge ergibt sich analytisch aus den Schnittwinkeln des
Kreises mit den vier Bildkanten. Randfarbbeleg und Konturbreite verwenden
diese sichtbare Länge. Damit wird eine helle Kontur durch das Abschneiden
anderer Kreisteile nicht künstlich dünner geschätzt. Vollständige Kreise
behalten ihre bisherige Schätzung und den vollen Umfang.

Nur das äußere Elternobjekt darf über den Bildrahmen reichen. Kinder,
native Eltern-Kind-Einschließung, Inventar, Rundung, helle Konturen,
beobachtete Zeichenreihenfolge und lokale/globale Rastergates bleiben
verbindlich. Bildbudget von fünf Sekunden, Strukturbudget von 96 Zuständen,
Renderer und Qualitätsgrenzen wurden nicht erhöht oder ausgetauscht.

## Nachweise und Grenzen

Die ursprünglichen 17 Varianten mit Seed `853197` wurden vor der
Runtime-Änderung erneut erzeugt und ihre Rasterbytes gesichert. Die drei
Randfälle bestehen in einer eigenen vollständigen Vorherprüfung **0/3**.
Die finale Variantenkohorte und die zusätzliche synthetische Entwicklungskohorte
werden im [Evidenzbericht](../artifacts/evaluation/clipped_parent_v1/README.md)
mit Einzelentscheidungen, Eingabe-/Runtimehashes und Prüfbefehlen ausgewiesen.
Die Zusatzkohorte mit Seed `618293` enthält zwölf Fälle an allen vier Kanten
und vier Ecken, einschließlich stärkerer Verschiebungen. Der Generator
verwendet eigene SVG-Geometrie und Objektmarkierungen, keinen Produktionsdetektor.

Ein erster vollständiger Vorherlauf meldete 13/17 positive Entscheidungen,
drei fehlende Ausgaben an den bekannten Randfällen und einen äußeren
Prozess-Timeout bei `probe_11`. Wegen fehlender Zugriffsevidenz dieses Timeouts
scheiterte die vollständige unabhängige Nachprüfung. Dieser Lauf ist keine
vollständig geprüfte 13/17-Baseline und bleibt als negativer Vorversuch erhalten.
Die gepaarte Aussage ist deshalb ausdrücklich **0/3 → 3/3** auf denselben
drei Rastereingaben; der historische 14/17-Wert wird nicht umgeschrieben.

Die finale Runtime besteht **17/17** gekoppelte Varianten und **12/12**
zusätzliche Kanten-/Eckfälle. Alle Produktionsdateihashes stimmen über beide
Kohorten mit dem geprüften Stand überein. Die größte unabhängig gemessene
Abweichung einer Objektgrenze beträgt 0,2341 Pixel. Ein explorativer
17/17-Lauf während einer kleinen Änderung am Gültigkeitszweig ersetzt nicht
diese anschließende Abnahme mit durchgehend gleichem Runtimehash.

Der vollständige betroffene Regressionsblock besteht **294 Tests**, mit
**drei Fehlern und einer regulären Überspringung**, Exit 1. Alle **30 neuen
Prüfungen bestehen** innerhalb dieses Blocks; sie sind keine zusätzlichen
30 Versuche. Das Kernprofil besteht **42/42**, Exit 0. Die drei Fehler sind
die alten Vier-Gruppen-Fälle mit Rundung und Kontur, Indizes 0/1/3. Ein
gesonderter Lauf mit dem unveränderten Produktionsmodul aus `7e6124bea`
reproduziert exakt dieselben drei Fehler: **15/18 bestanden**, Exit 1.
Die frühere Einzelwiederholung des ersten Falls bestand; die feste
Fünf-Sekunden-Grenze bleibt dabei unverändert.

Bereits der erste, parallel zu anderen Konvertierungen ausgeführte
Gruppentest bestand 42/45 Fälle mit denselben drei Fehlern. Auch die finale
serielle Ausführung bleibt damit keine grüne Gesamtregression. Ein
zusätzlicher Versuch mit OpenCV explizit auf einem Thread und begrenztem
OpenBLAS/OMP reproduzierte die drei Fehler und wurde danach beendet; er
liefert keine vollständige neue Testabnahme. Die Laufzeitschwankungen bleiben
beim bestehenden Runtime-/Teststabilitätspaket. Die CI erhält keine daraus
abgeleitete Lockerung oder Sonderbehandlung der fehlschlagenden Tests.

Die Negativkontrollen prüfen fehlende/zusätzliche Kinder, falsche Verlaufsachse,
fehlende/dunkle Elternkontur, eine deutlich beschädigte kleine Kinderfüllung,
angeschnittene Kinder trotz passender Elterngeometrie, Ellipsen, unzureichende
Bögen und erschöpfte Budgets. Die Pixelgates bleiben quantitative Grenzen:
Eine kleine weiße Störung nur auf der großen Elternfläche blieb in einer
Entwicklungskontrolle innerhalb dieser Grenzen. Die produktive vollständige
Semantikabnahme bleibt **SEMANTIC-COMPLETENESS-02**.

Dies ist eine synthetische Kompositionserweiterung. **SEARCH-STRUCTURE-01**,
die unabhängige reale Familienabnahme und die übrigen Kompositionsgrenzen
bleiben offen. Es wurden keine Archivpaare neu konvertiert oder verändert.
Für neue reale Abnahmen müssen weiterhin vor der Entwicklung neue Familien
gesperrt werden. Die vollständige Standardsuite ist nicht Teil dieser Abnahme.

## Reproduktion

Neue, noch nicht vorhandene Zielordner verwenden:

```powershell
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --prepare .tmp/clipped-variants --seed 853197 --groups 2 --rounded --outlines --variations
.venv/Scripts/python.exe -m tools.evaluate_mixed_overlap --inputs .tmp/clipped-variants --output .tmp/clipped-variants-cli --require-all
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 618293 --groups 2 --rounded --outlines --clipped-parent
.venv/Scripts/python.exe -m pytest tests/test_clipped_gradient_parent.py tests/test_overlap_groups.py -q
```

Der CI-Job `clipped-gradient-parent` führt die neuen Regressionen, die
zusätzliche Zwölferkohorte und genau diese gekoppelte 17er-Variantenkohorte
aus. Lokal wurde die vorhandene Python-3.10.11-Umgebung verwendet; die
historische `.python-version`-Vorgabe 3.10.20 wurde damit nicht nachgewiesen.

## Sitzungslog / Status: Review

- Getestet: gepaarte Randfälle, vollständige 17er-Variantenkohorte, zwölf zusätzliche Kanten-/Eckfälle, 298 Regressionen, unveränderte Basis und Kernprofil.
- Ergebnis: 0/3 → 3/3; Varianten 17/17, Zusatzfälle 12/12; 30/30 neue Prüfungen, Kernprofil 42/42; breiter Block 294 bestanden/3 Basisfehler/1 übersprungen.
- Grenzen: bestehende Vier-Gruppen-Zeitlimitfehler, reale Gesamt-Abnahme, vollständige Semantikabnahme und weitere Komposition bleiben offen.
- Nächster Schritt: vor weiterer realer Kompositionsentwicklung neue Familien sperren; bestehende P0-Struktursuche fortsetzen.
- Startbefehl: `.venv/Scripts/python.exe -m pytest tests/test_clipped_gradient_parent.py -q`.
