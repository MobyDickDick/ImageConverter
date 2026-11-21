# Arbeitspakete für die adaptive SVG-Konvertierung

Ziel ist, mehr Katalogbilder bei gleicher oder kürzerer Laufzeit erfolgreich zu vektorisieren. Die erkannten und beschriebenen Formen begrenzen die zulässigen Modelle. Der Konverter rendert Varianten dieser Modelle und bestimmt Geometrie, Farbe und Verläufe für jedes Original neu.

## AP 0 · Kreis und Pfeil für GE0037_S rekonstruieren

**Status** · Im Prüflauf umgesetzt und verifiziert. Die Katalogausgabe steht noch aus.

- Die aktuelle Bildbeschreibung führt zum vorhandenen Pfeilmodell. Die Prüfung verlangt einen Kreis mit Farbverlauf und einen zusammenhängenden Pfeil in der beschriebenen Richtung.
- Der Konverter passt Kreismittelpunkt, Radius, Randbreite und Verlaufsfarben an. Rechteckiger Schaft und dreieckige Spitze haben eigene Abmessungen und bilden eine gemeinsame SVG-Kontur.
- Beim erneuten Rendern des alten und neuen SVG sank der RGB-RMSE pro Kanal von 38,1 auf 7,7. Der neue Lauf bestand die Qualitätsprüfung nach 2,8 Sekunden Suchzeit. 51 bestehende Pfeiltests und der neue Regressionstest bestanden.
- Der neue Export liegt im lokalen, temporären [Prüflauf](../.tmp/ge0037-check/verified/converted_svgs/GE0037_S.svg). Die Katalogausgabe kann nach Sichtprüfung übernommen werden.

## AP 1 · Mehrere passende Formmodelle früh vergleichen

**Status** · Umgesetzt am 21.11.2026: früher Modellvergleich mit gemeinsamer Rendergrenze, produktiv für die Kreis-Pfeil-Familie. Die feste Stichprobe und Ausgangsmessung wurden vor der Runtimeänderung gesichert. [Umsetzung, Messungen und Grenzen](../artifacts/evaluation/adaptive_form_models_v1/README.md).

- Aus Beschreibung und erkannten Konturen wenige zulässige Modelle ableiten. Für einen Pfeil im Kreis kommen beispielsweise flache Füllung und horizontaler Farbverlauf als Varianten derselben Geometrie infrage, soweit die Beschreibung beide zulässt.
- Jeden Kandidaten mit einem kleinen Renderbudget an das Original anpassen. Die bestehenden Fitters und Suchverfahren als Ausgangspunkt verwenden.
- Pro Kandidat Modell, Zahl der Renderings, Laufzeit und Prüfergebnis protokollieren.
- **Abnahme** · Ein früher gültiger Kandidat beendet den Vergleich erst bei ausreichender Qualität oder ausgeschöpftem Budget. Ein späterer Kandidat kann gewinnen, wenn er die Formvorgaben erfüllt und das Original besser trifft.

**Ergebnis** · Der Fitter vergleicht einen Verlauf mit zwei Farbstopps mit einem Verlauf mit zusätzlichem Mittelstopp. Beide werden aus Originalpixeln geschätzt; die Beschreibung verlangt einen Verlauf, deshalb ist eine flache Füllung hier kein zulässiger Kandidat. Anfangsproben und feste Verfeinerung teilen höchstens 417 tatsächliche Renderings beziehungsweise die kleinere konfigurierte Grenze und die bestehende Bilddeadline. Jeder Versuch protokolliert Modell, Phase, Renderings, Zeit, Fehler und Form-/Pixelprüfung. Nur ein semantisch gültiger Fit kann gewinnen; ein bereits bestandener Pixelvertrag wird bei der Auswahl erhalten. Die strengere bestehende Qualitätsmarke erlaubt einen frühen Abschluss, ein bloßer Pixelpass nicht.

Der zusätzliche Verlauf gewinnt bei GE0037_S und GE0039_L im seriellen Vergleich sowie in einer unabhängigen synthetischen Gegenprobe. Die Kreis-Pfeil-Erfolgsquote bleibt bei 5/7; die zusätzliche Suche kostet derzeit mehr Zeit. Das ist eine funktionale Abnahme von AP 1, kein Nachweis für das Laufzeit-/Katalogziel von AP 4. Weitere Formfamilien sind noch nicht an den wiederverwendbaren Modellvergleich angeschlossen. AP 2 ist das nächste Umsetzungspaket.

## AP 2 · Suchbudget nach Qualität und Fortschritt verteilen

**Status** · Offen. Baut auf AP 1 auf.

Im Formmodellvergleich des Kreis-Pfeil-Pfads wird die Auswahl jetzt durch die
bereits gemessenen Versuche gesteuert. Suchstände und negative Messungen bleiben
zwischen den Suchrunden erhalten. Konturen, Vordergrundflächen, Pixelfehler und
Fortschritt bestimmen die nächsten Runden; stagnierende Nachbarschaften werden
verlassen. Die allgemeine Wirkung auf weitere Formfamilien bleibt offen.
[Verhalten, Nachweise und Grenzen](search_attempt_memory_2026-11-21.md).

- Den gerenderten Kandidaten anhand von Farbfehler, Kantenabweichung und Übereinstimmung der einzelnen Formen bewerten. Die Formprüfung muss falsche Richtungen, fehlende Teile und zusätzliche Objekte erkennen können.
- Das restliche Budget auf aussichtsreiche Kandidaten verteilen. Bei Stagnation Modell oder Suchverfahren wechseln und bei bestandener Qualitätsprüfung früh beenden.
- **Abnahme** · Ein belegbar besserer gültiger Kandidat ersetzt den bisherigen. Die Suche bleibt im vorgegebenen Zeit- und Renderbudget. Ein Ergebnis unterhalb der Qualitätsanforderungen bleibt als fehlgeschlagener Versuch erkennbar.

## AP 3 · Suchreihenfolge aus verifizierten Läufen lernen

**Status** · Offen. Baut auf AP 1 und AP 2 auf.

- Je Formfamilie und Strategie die Zahl der Versuche, die bestandenen Prüfungen und den Aufwand speichern. Beim nächsten ähnlichen Bild wirksame Strategien früher ausprobieren und einen kleinen Teil des Budgets für Alternativen reservieren.
- Das Gedächtnis steuert die Reihenfolge. Geometrie und Farben stammen bei jedem Lauf aus dem jeweiligen Original. Für Vergleichsläufe eine feste Suchreihenfolge ohne Historie vorsehen.
- Auch Fehlversuche berücksichtigen: Bei unveränderten Bildpixeln und unveränderter Beschreibung sollen spätere Konvertierungsstarts bereits erfolglose Suchbereiche erkennen. Identische und lediglich geringfügig veränderte Fehlversuche dürfen nicht durch einen neuen Seed als neue Erkenntnis zählen. Dieses dauerhafte Gedächtnis ist noch nicht umgesetzt; der aktuelle Formmodellvergleich merkt sich Versuche innerhalb eines Vergleichslaufs.
- **Abnahme** · Auf zuvor ungesehenen Bildern erreicht die gelernte Reihenfolge bei gleichem Budget mehr bestandene Konvertierungen oder benötigt bei mindestens gleicher Erfolgsquote weniger Zeit.

## AP 4 · Wirkung auf den Katalog messen

**Status** · Baseline und erster Vergleich für AP 1 erfasst: elf feste Katalogeinträge in vier Gruppen, davon zehn im analytischen Messpfad; die explizite Bauteilkomposition ist als außerhalb dieses Messpfads ausgewiesen. Verwandte Kreis-Pfeil-Motive bleiben gemeinsam in der Entwicklungsgruppe. Eine unabhängige Katalogabnahme und der Nachweis gleicher oder kürzerer Laufzeit bleiben offen. [Hashgebundene Stichprobe](../artifacts/evaluation/adaptive_form_models_v1/manifest.json), [Messwerte](../artifacts/evaluation/adaptive_form_models_v1/summary.json).

- Eine feste Stichprobe aus gelungenen und gescheiterten Katalogkonvertierungen zusammenstellen. Bilder nach Formfamilien gruppieren und Varianten desselben Motivs gemeinsam der Entwicklung oder Prüfung zuordnen.
- Ausgangsversion und neue Suche mit denselben Eingaben, Formprüfungen und Laufzeitbudgets vergleichen. Anteil bestandener Konvertierungen, Laufzeit, Renderanzahl und häufigste Fehlerursachen erfassen.
- **Abnahme** · Die Prüfmenge zeigt mehr bestandene Konvertierungen bei gleicher oder kürzerer Laufzeit. Das Ergebnis für GE0037_S dient als Einzelregression. Der bisher geschätzte Anteil von etwa einem Drittel wird über die gemessene Baseline überprüft.
