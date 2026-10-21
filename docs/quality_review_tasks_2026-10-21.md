# Praktische Aufgaben aus der Projekteinschätzung (2026-10-21)

Die Einschätzung begründet vier neue Aufgaben und präzisiert das offene Paket
GENERAL-SCENE-REAL-05. Der verbindliche Checkbox-Status steht ausschließlich in
[open_tasks.md](open_tasks.md). Die folgenden Abschnitte definieren Umfang,
Reihenfolge und Abnahme; sie dokumentieren keine bereits erzielten Ergebnisse.

## Ziel und Reihenfolge

Zuerst den Nutzen auf unbekannten realen Symbolfamilien und die Ursachen
fehlgeschlagener Konvertierungen messen. Danach belegte Sprach- und
Rekonstruktionsfehler beheben. Die größere Produktbereinigung folgt gemäß
[Roadmap](product_roadmap.md) nach der Qualitätsphase. Eine wissenschaftliche
Neuheitsbehauptung ist kein Entwicklungsziel; entscheidend sind brauchbare,
bearbeitbare SVGs und eingesparte Arbeit.

Vorhandene Qualitätsgrenzen, gute archivierte Ausgaben und die Trennung von
Raster-/Beschreibungsquellen und Bewertungsreferenzen bleiben verbindlich.
Ein negatives oder unklares Experiment darf als abgeschlossene Untersuchung
dokumentiert werden; es ist keine positive Fähigkeitsabnahme.

## BENCHMARK-PRACTICAL-01 – Nutzen gegenüber bestehenden Verfahren messen

**Priorität:** zuerst das Protokoll und den Prüfbestand einfrieren; an IDO-19,
IDO-21 und BENCHMARK-ANYTIME-01 anschließen, deren Nachweisrahmen wiederverwenden.

**Praktische Folge der Kritik:** Archivzahlen und interne Vorher-/Nachher-Läufe
belegen noch keinen Vorteil gegenüber verfügbaren Werkzeugen oder Nachzeichnen.

**Aufgabe:**

- Mindestens 20 unabhängig abgegrenzte reale Symbolfamilien vor den Änderungen
  auswählen und annotieren, darunter mindestens fünf außerhalb des bisherigen
  Kreis-/Rechteckszenenvertrags. Entwicklungsfälle und gesperrte Prüffamilien
  einschließlich Quellen, Beschreibungen und Hashes festlegen. Bereits zur
  Entwicklung verwendete Familien ausdrücklich als bekannt kennzeichnen;
  Größen, Farben, Seeds und Umformulierungen zählen nicht als neue Familien.
- Den eingefrorenen Converter mit mindestens zwei bestehenden Verfahren
  vergleichen: einem Kontur-Vektorisierer und einem Verfahren, das strukturierte
  SVGs erzeugt. Versionen, Einstellungen, Hardware und verfügbare Eingaben
  festhalten. Beschreibungszugriff, Vorverarbeitung und Ressourcenunterschiede
  offen ausweisen; deren Einfluss begrenzt die Vergleichsaussage.
- Einstellungen ausschließlich auf Entwicklungsdaten festlegen. Für alle
  Versuche echte CLI-/Werkzeugausgaben speichern; Qualitätsreferenzen bleiben
  für die Konvertierung unzugänglich. Identische Quellen, vorab festgelegte
  Zeitgrenzen und dieselben unabhängigen Qualitätsprüfungen verwenden.
- Vollständige Akzeptanz, fehlende/falsche Objekte, Beschriftung, Beziehungen,
  Pixel-/Kantenqualität, native Elemente/Pfadkomplexität sowie Median und p95
  der gesamten Laufzeit berichten. Fehlende Ausgaben und nicht unterstützte
  Formen bleiben im Nenner; Renderbarkeit ist keine Qualitätsfreigabe.
- An einer vorab ausgewählten Teilmenge von mindestens zehn Familien die
  aktive Zeit bis zur gleichen fachlichen Abnahme messen: Ausgabe korrigieren
  bzw. von Hand nachzeichnen. Dieselben Bearbeiter, wechselnde Reihenfolge und
  gleiche Zielkriterien verwenden; Prüfen, Beschreibung erstellen und Korrigieren
  zeitlich getrennt ausweisen. Personen- und Übungseffekte dokumentieren.

**Abnahme:** Ein reproduzierbarer Bericht mit Eingabemanifest, Befehlen,
Ausgaben, unabhängigen Prüfergebnissen, Familienaggregation und gemessener
Nacharbeit beantwortet, für welche Bildarten das Projekt Arbeit spart.
Abnahmearchiv, aktuelle Katalog-Erfolgsquote und neue Prüfergebnisse getrennt
ausweisen. Ein fehlender Vorteil schließt die Messaufgabe ebenfalls ab und
führt zu einer begründeten Eingrenzung des Einsatzbereichs. Die hier genannten
Mindestzahlen sind ein praktischer Untersuchungsumfang, kein automatischer
Nachweis statistischer Überlegenheit.

## GENERAL-SCENE-REAL-05 – Übertragung statt weiterer Einzelfallpfade

**Status:** bestehende offene Aufgabe; keine zusätzliche Doppelaufgabe.

**Praktische Folge der Kritik:** Weitere Größen-/Farbvarianten und synthetische
Szenen belegen allein keine Übertragung auf neue reale Zusammensetzungen.

**Präzisierung der Abnahme:**

- Den bestehenden Kreis-/Rechteckumfang, sichtbare Überdeckungen und eindeutige
  Farb-/Lagebezüge an unabhängig annotierten, vor Entwicklung gesperrten realen
  Familien prüfen. Gemeinsame Daten mit BENCHMARK-PRACTICAL-01 sind möglich,
  müssen aber denselben Entwicklungs-/Prüfstatus behalten.
- Mindestens zwei neue reale Familien mit anderen Kombinationen bereits
  unterstützter Primitive durch denselben Szenenweg bearbeiten. Raster und
  Beschreibung liefern Geometrie und Beziehungen; keine neue Familienkennung,
  bildspezifische Konfiguration oder zusätzliche vollständige Symbolvorlage
  darf diese beiden Erfolge herbeiführen.
- Tatsächlichen Runtime-Pfad, erkannte Instanzen und Auswahlentscheidung neben
  den unabhängigen Objekt-/Regionsprüfungen belegen. Benötigt eine Familie eine
  neue Formklasse oder bleibt die Rekonstruktion unzureichend, den offenen
  Umfang benennen und die Übertragungsabnahme nicht als bestanden markieren.
- Historische Spezialpfade erst ersetzen, wenn der gemeinsame Pfad deren
  reale Regressionen unter denselben Qualitätsgrenzen besteht. Eine größere
  Zahl unterstützter Katalogvarianten separat vom Familiengewinn berichten.

## SEMANTIC-ROBUSTNESS-01 – Gleiche Bedeutung robust verarbeiten

**Priorität:** zusammen mit GENERAL-SCENE-REAL-05; zuerst messen, dann die
beobachteten Parser-/Dispatchfehler beheben. IDO-19/IDO-21 mit echten
Produktionskonvertierungen ergänzen.

**Praktische Folge der Kritik:** Einzelne Schlüsselwörter und Satzformen
können die Modellwahl verändern, obwohl das Raster und die Bedeutung gleich
bleiben. Ein spezifiziertes Beschreibungsschema allein belegt keine robuste CLI.

**Aufgabe und Abnahme:** Für mindestens zehn reale Familien je fünf unabhängig
formulierte, bedeutungsgleiche Beschreibungen vor der Implementierung festlegen
(Synonyme, Reihenfolge, Adjektive, explizite und verneinte Textangaben).
Je Familie mindestens drei gezielte Widerspruchs-/Mehrdeutigkeitsfälle ergänzen,
die eine überprüfbare Objektanzahl, Beziehung oder Beschriftung betreffen.
Mit unveränderten Rastern, neutralen Dateinamen und festen Suchseeds echte
CLI-Vorher-/Nachher-Läufe ausführen. Semantisch gleiche Beschreibungen müssen
denselben fachlichen Objekt-/Beziehungsvertrag und dieselbe Qualitätsabnahme
erreichen; Bytegleichheit ist dafür kein allgemeines Kriterium. Widersprüche
und unaufgelöste Referenzen dürfen keinen stillen vollständigen Erfolg erhalten.
Unterstütztes Vokabular und Grenzen dokumentieren. Entwicklungsformulierungen
und neue gesperrte Prüfformulierungen trennen; eine reine Wortlisten-Erweiterung
auf den bereits bekannten Prüfsätzen genügt nicht zur Abnahme.

## COMPONENT-VALUE-02 – Such-Bots auf tatsächlich ausgeführter Arbeit prüfen

**Priorität:** nach Auswahl aussagekräftiger Entwicklungsfälle; den vorhandenen
Komponentenmodus nutzen. COMPONENT-VALUE-01 bleibt als abgeschlossene
Untersuchung mit unklarer Beitragsbewertung erhalten.

**Praktische Folge der Kritik:** Gleiche Akzeptanz mit/ohne Bots und ein
Prüfbestand ohne Bot-Vorschläge rechtfertigen weder einen Nutzenanspruch noch
die Entfernung aller Bots.

**Aufgabe:** Einen auf Entwicklungsdaten festgelegten Bestand schwieriger
Registrierungen und neue gesperrte reale Prüffamilien verwenden. Für jede zu
bewertende Strategie tatsächliche Initialisierung, Vorschläge, Messungen und
übernommene Verbesserungen beobachten. Vollständiges Portfolio, alle Bots aus
und anhand der Entwicklungsdaten begründete kleinere Portfolios bei gleichem
Gesamtbudget mit mindestens drei Seeds vergleichen. Budget, Familienumfang,
praktisch relevante Gewinn-/Verlustgrenzen und Unsicherheitsauswertung vor dem
Prüflauf festlegen. Aktive Fälle und Fälle mit bereits ausreichendem Initialfit
getrennt berichten; Familien, nicht Seeds, sind die unabhängigen Einheiten.

**Abnahme:** Unabhängige SVG-Prüfungen und Gesamtaufwand begründen eine konkrete
Beibehaltungs-, Vereinfachungs- oder weitere Untersuchungsentscheidung.
Erzeugt ein Bot keine Vorschläge oder reicht die Evidenz nicht, bleibt dessen
Beitrag unklar. Vereinfachungen benötigen seltene Fähigkeitsfälle und
Archivregressionen; aus fehlender Signifikanz folgt keine Gleichwertigkeit.
Weitere CNN-Arbeit bleibt bei NEURAL-ELEMENTS-01: ohne neuen begründeten
Kandidaten und neue gesperrte Familien kein bloßes Wiederholen der negativen
Experimente und keine Standardaktivierung.

## ARCH-RUNTIME-CONTEXT-01 – Eine globale Abhängigkeit vollständig ablösen

**Priorität:** Produktbereinigung nach der Qualitätsphase gemäß Roadmap.
Kein vollständiger Architekturumbau als Voraussetzung für weitere Konvertierungen.

**Praktische Folge der Kritik:** Dateiaufteilung allein beseitigt die Kopplung
durch globale Zustände und das Nachreichen ganzer Modulnamensräume nicht.

**Aufgabe:** Die produktiven Aufrufer von `_syncRemainingRuntimeBindings` und
der Namespace-Übernahme in `imageCompositeConverter.py` inventarisieren.
Eine begrenzte Rendering- oder Reporting-Grenze auswählen, ihre tatsächlich
benötigten Abhängigkeiten explizit als Argumente bzw. typisierten Kontext
übergeben und die zugehörige globale Synchronisierung für diesen Pfad entfernen.
Öffentliche Kompatibilitätsfunktionen erhalten. Abhängigkeiten für zwei
Konvertierungskontexte unabhängig halten; keine Ersatz-Service-Locator-Struktur
oder weitere bloße Dateiextraktion als Abschluss ausgeben.

**Abnahme:** Der gewählte produktive Pfad arbeitet ohne die abgelösten globalen
Bindings. Zwei aufeinanderfolgende Konvertierungen mit verschiedenen
Render-/Ausgabekontexten beeinflussen sich nicht. Repräsentative echte
CLI-Vorher-/Nachher-Ausgaben und die betroffenen Archivregressionen behalten
Qualität und Schnittstellen. Entfernte globale Bindings, verbleibende Kopplung
und gemessener Laufzeiteinfluss sind dokumentiert; Zeilen- oder Dateianzahl
allein ist kein Erfolgskriterium.
