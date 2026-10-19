# Neuronale Elementerkennung und messbarer Komponentenbeitrag

Stand 19. Oktober 2026: Der erste integrierte Nachweisrahmen für die sechs
Such-Bots ist umgesetzt und mit 375 echten Konvertierungen unabhängig geprüft.
Die konkrete Entscheidung ist die Beibehaltung des vollständigen Portfolios;
eine allgemeine Gleichwertigkeit oder Entbehrlichkeit ist nicht nachgewiesen.
Umfang, Kontrollen, Unsicherheit und Grenzen stehen unter
[COMPONENT-VALUE-01](next_arbeitspaket_2026-10-18_component_value.md).
Der erste [neuronale Versuch](next_arbeitspaket_2026-10-19_neural_elements.md)
ist optional umgesetzt und mit 84 echten CLI-Versuchen untersucht. Er zeigt
keinen zusätzlichen Erfolg und bleibt außerhalb des Standardpfads.
Die produktive Netzabnahme bleibt offen; vorhandene Erkenner werden erhalten.

Auch das [reale Folgeexperiment NEURAL-ELEMENTS-REAL-02](next_arbeitspaket_2026-10-19_neural_real_regions.md)
ist inzwischen abgeschlossen: neun reale Trainingsfamilien, sechs bisherige
Entwicklungsfamilien, zehn neue Abnahmefamilien und 180 echte CLI-Versuche.
Bessere Regionsabdeckung führt noch nicht zu belastbarem End-to-End-Nutzen;
die analytische Standardkonvertierung bleibt erhalten.

## Kleines neuronales Netz als zusätzlicher Erkennungs-Bot

Ein kleines Faltungsnetz (CNN) ist ein sinnvoller Versuch für die Erkennung
von Grundformen und Textbereichen. Ein Klassifikator für Bildausschnitte kann
beispielsweise Kreis, Rechteck, Dreieck, Linie, Textbereich oder unbekannt
vorschlagen. Die vorhandene Bildanalyse könnte die Ausschnitte liefern.
Mehrere Elemente in einem Gesamtbild erfordern zusätzlich Positionen und
Instanztrennung; eine einzige Klassenangabe für das ganze Bild genügt nicht.
Eine spätere kleine Detektion oder Segmentierung wäre dafür gesondert zu prüfen.

Die projektbezogene Hypothese lautet: Zusätzliche Erkennungsvorschläge könnten
unvollständige analytische Starts ergänzen und erfolglose Suche vermeiden.
Ein Nutzen ist damit noch nicht nachgewiesen. Gerade bei einfachen geometrischen
Konturen kann die vorhandene analytische Erkennung günstiger oder genauer sein.
Ein Textbereichsdetektor ersetzt außerdem keine Zeichenerkennung.

Geplanter Vergleich:

1. Vorhandene Erkennung als unveränderte Basis erfassen. Als erstes begrenztes
   Ziel Grundform-/Textbereichsklassen und deren Positionen festlegen.
2. Synthetische SVG-Szenen offline mit Klassen und Instanzpositionen erzeugen;
   Orientierung, Farbe, Strichbreite, Auflösung, Überlagerung, Hintergrund,
   Antialiasing und JPEG-Störungen variieren. Reale Bilder unabhängig markieren.
3. Ganze Symbol-/Quellfamilien vor jeder Augmentation auf Training, Entwicklung
   und gesperrten Holdout aufteilen. Größenvarianten oder gerenderte Abwandlungen
   derselben Vorlage dürfen nicht auf beiden Seiten stehen. Synthetische und
   reale Ergebnisse getrennt ausweisen. Kein Training auf dem Abnahme-Holdout.
4. Ein kleines selbst trainiertes CNN und, sofern das Laufzeit-/Größenbudget es
   erlaubt, ein kleines vortrainiertes Modell vergleichen. Die Architektur ist
   eine zu prüfende Wahl; ein großes Modell wird nicht vorausgesetzt.
5. Klassen-, Positions- und Instanzfehler, Recall kleiner Elemente, unbekannte
   Formen sowie die Zuverlässigkeit der Konfidenzen messen. Besonders
   fehlerhafte hochsichere Vorhersagen und übersehene Zusatzobjekte ausweisen.
6. Einen optionalen Erkennungs-Bot tatsächlich an die Szenenkandidatenbildung
   anschließen. Er liefert Klasse, Position und Konfidenz. Unbekannte oder
   unsichere Fälle erlauben weiterhin analytische Alternativen. Eine fehlende
   Netzerkennung darf allein keine vorhandene Form verwerfen.
7. Echte CLI-Konvertierungen mit/ohne Netz bei gleichem Gesamtbudget vergleichen.
   Modellinitialisierung, Bildvorbereitung, Inferenz, Speicher und Abhängigkeiten
   mitrechnen; Kaltstart und Batchbetrieb getrennt ausweisen. Training bleibt
   offline. Runtime liest weder Trainingsvorlagen noch Referenz-SVGs.

**Abnahme:** Auf eingefrorenen realen, bisher unbekannten Familien entsteht
entweder eine belastbar höhere Rate vollständig akzeptierter Konvertierungen
bei gleichem Budget oder eine vorab definierte relevante Zeitersparnis bei
gleichwertiger Qualität. Objekt-, Text-, Pixel- und Komplexitätsprüfungen
bleiben unabhängig und unverändert. Mehrere Trainings-/Such-Seeds und die
Messunsicherheit gehören zum Bericht. Ein allein guter Trainingswert oder eine
höhere Klassifikationsgenauigkeit genügt nicht. Ohne Nutzen bleibt der Versuch
außerhalb des Standardpfads und wird als negatives Ergebnis dokumentiert.

Methodische Grundlagen: Das offizielle
[TensorFlow-CNN-Beispiel](https://www.tensorflow.org/tutorials/images/cnn)
zeigt ein kleines Faltungsnetz zur Bildklassifikation. Das
[TensorFlow-Klassifikationsbeispiel](https://www.tensorflow.org/tutorials/images/classification)
behandelt auch Überanpassung bei kleinen Datensätzen. Die
[PyTorch-Anleitung zur Objektdetektion](https://docs.pytorch.org/tutorials/intermediate/torchvision_tutorial)
zeigt die Anpassung eines vortrainierten Detektors an einen kleinen Datensatz.
Diese Beispiele belegen keine Eignung für unseren Symbolkatalog; diese muss
der obige Vergleich erst nachweisen.

## Komponentenbeitrag als Teil der Software

Ziel ist eine in Konverter, Bot-Scheduler und CI integrierte Messmöglichkeit
für den tatsächlichen Nutzen von Komponenten. Ein aufrufbarer Reporter ohne
Anschluss an echte Konvertierungen erfüllt die Aufgabe nicht.

Im Bestand existieren Telemetrie und ein Ablations-Berichtsvertrag.
`tools/build_holdout_ablation_matrix.py` leitet seine Bildmerkmale jedoch aus
Beschreibungstermen ab und verwendet Ersatzbewertungen. Das ist kein Nachweis
des Beitrags produktiver Komponenten. Diese Grenze und die offenen Aufgaben
IDO-19/IDO-21 sind bereits im Rekonstruktionsaudit dokumentiert.

Die Umsetzung soll folgende zusammengehörige Teile erhalten:

- **Echte Schaltpunkte:** Eine kleine Komponentenregistrierung dokumentiert
  Kennung, Version, Voraussetzungen und Schalter für Erkenner, Modellgeneratoren,
  Such-Bots, Caches und Nachbearbeitung. Abhängige Varianten dürfen nur in
  gültigen Kombinationen laufen. Qualitätsprüfungen bilden den festen Maßstab;
  das Abschalten einer Prüfung zählt nie als Qualitätsgewinn.
- **Leichte Laufzeitbeobachtung:** Je Bild werden Aufwand, Vorschläge,
  Verbesserungen, Ablehnungen und Ergebnisherkunft erfasst. Geteilte Arbeit und
  Cachetreffer müssen eindeutig zugeordnet werden. Der Zusatzaufwand der
  Beobachtung selbst wird gemessen und begrenzt. Eine seltene Nutzung oder
  fehlende Siegerrolle belegt noch keine Nutzlosigkeit: Auch Fehlversuche,
  Validierung und Rückfallpfade können wichtig sein.
- **Gepaarte Gegenproben:** Ein integrierter Evaluationsmodus startet echte
  Produktionskonvertierungen mit und ohne einen Baustein. Eingaben,
  Quellstand, Einstellungen, Seeds, Grenzwerte, Hardware und Zeitbudgets sind
  vergleichbar. Caches und Strategievergangenheit sind isoliert; Reihenfolge
  und Kalt-/Warmläufe werden kontrolliert. Messungen entstehen aus tatsächlichen
  Ausgaben und Laufzeiten. Die normale Konvertierung muss keine vollständige
  Ablationsserie mitbezahlen.
- **Wechselwirkungen:** Zusätzlich zu Einzelabschaltungen ausgewählte Paare
  und schrittweiser Wiederaufbau prüfen. Zwei gleichwertige Ersatzverfahren
  können einzeln entbehrlich erscheinen, obwohl das Entfernen beider schadet.
  Kooperierende Bots können ihren Nutzen erst gemeinsam entfalten. Für große
  Mengen wird ein begrenzter, dokumentierter Versuchsplan statt aller
  möglichen Kombinationen verwendet.
- **Entscheidungsbericht:** Vollständig akzeptierte Konvertierungen,
  Objekt-/Textfehler, Laufzeit einschließlich Median/p95, Speicher und
  Renderaufwand vergleichen. Ergebnisse nach Familie und Schwierigkeit
  aufschlüsseln, damit seltene notwendige Fähigkeiten nicht im Mittelwert
  verschwinden. Vorher festgelegte Relevanz- und Gleichwertigkeitsgrenzen,
  Wiederholungen und Unsicherheitsintervalle bestimmen die Aussage.

Der Bericht unterscheidet **nützlich**, **schädlich**, **im untersuchten Bereich
gleichwertig** und **noch unklar**. Eine statistisch nicht nachgewiesene Wirkung
bedeutet nicht automatisch Gleichwertigkeit. Die Einstufung gilt für die
getestete Konfiguration und Datenabdeckung, nicht für beliebige Eingaben.
Fehlerbehandlung, Dateiintegrität, Zeitlimits und andere Schutzfunktionen
benötigen zusätzlich eigene Ausfall-/Wiederherstellungsszenarien.

## Abnahme der integrierten Beitragsmessung

1. Ein dokumentierter CLI-/CI-Lauf führt echte Konvertierungen mit/ohne
   Komponenten aus und enthält Quell-/Konfigurationskennungen, Eingabehashes,
   Seeds, beobachtete Schalterzustände, SVG-Ausgaben und unabhängig gemessene
   Qualitäts-/Kostenunterschiede. Ein deaktivierter Baustein wird nachweislich
   nicht ausgeführt. Ausgedachte Scores erfüllen diese Abnahme nicht.
2. Auf echten Raster-/Beschreibungsfällen erkennt das Verfahren kontrolliert
   einen hilfreichen Baustein, einen reinen Zusatzaufwand ohne Qualitätsnutzen
   sowie zwei sich ersetzende Bausteine. Seltene nützliche Fälle und absichtlich
   unzureichende Daten müssen eine vorsichtige Einstufung auslösen. Solche
   Kontrollfälle sind getrennt von Aussagen über produktive Module auszuweisen.
3. Die sechs Such-Bots dienen als erstes produktives Untersuchungsfeld;
   danach folgen Erkennung und Nachbearbeitung. Die Erzeugung einer Rangliste
   allein reicht nicht: Mindestens eine daraus abgeleitete konkrete
   Vereinfachung oder begründete Beibehaltung wird auf Entwicklung und einem
   getrennten Abnahmebestand überprüft. Adaptive Bot-Zuteilung nutzt nur zuvor
   bestätigte Erkenntnisse; der Abnahme-Holdout trainiert keinen Scheduler.
4. Der Messmodus ist mit den tatsächlichen Runtime-Schaltern verbunden, läuft
   regelmäßig in der Regression/CI und zeigt seinen eigenen Aufwand. Normale
   Läufe liefern die leichte Beobachtung; aufwendige Gegenproben laufen gezielt.
5. Vor einer dauerhaften Deaktivierung oder Entfernung folgt ein eigener
   Bestandsschutzlauf einschließlich seltener Familien und notwendiger
   Rückfall-/Fehlerpfade. Schwache Evidenz führt zu weiteren Messungen, nicht
   zu automatischer Codeentfernung. Entwicklungs-/Validierungs- und finale
   Abnahmedaten bleiben auch bei wiederholten Auswahlentscheidungen getrennt.

Empfohlene Reihenfolge: zuerst echte Komponenten-Gegenproben aufbauen, dann
die neuronale Erkennung daran messen. So entscheidet derselbe Nachweis über
vorhandene Software und neue Erweiterungen. Der erste Komponenten-Nachweisrahmen
ist für die sechs Bots abgenommen; breitere reale Familien, weitere Komponenten
und die positive Prüfung seltener Fähigkeiten bleiben Folgearbeit.
NEURAL-ELEMENTS-01 bleibt bis zur tatsächlichen End-to-End-Abnahme offen.
