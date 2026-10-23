# Roadmap: Konvertierungsqualität, danach Produkt (2026-10-09)

Aktuelle Gewichtung vom 23.10.2026: [Struktursuche und Komposition zuerst](weakness_review_2026-10-23.md).
SEARCH-STRUCTURE-01 ist mit alternativen Restbildzerlegungen im bestehenden
Verlaufsszenenweg begonnen. Danach vollständige Semantikabnahme und unabhängige
reale Übertragung; neue Netze und größere Produktbereinigung folgen später.
Der begrenzte synthetische Entwicklungsschritt schließt GENERAL-SCENE-REAL-05
und GENERAL-SCENE-COMPOSITION-09 nicht ab.

Die vom Nutzer vorgegebene Reihenfolge gilt für die nächsten Arbeitspakete.
Die konkrete nächste Aufgabe und ihr Abschluss stehen in `open_tasks.md`
und `../PLAN_B_KANDIDATEN.md`.

Vorheriger Fokus am 22.10.2026: `GENERAL-SCENE-REAL-05` bleibt offen.
Die [eingefrorene Folgeprüfung](next_arbeitspaket_2026-10-22_real_scene_transfer.md)
ergibt 0/2 für Kreuz- und Vierfelderkompositionen bei unverändertem Algorithmus.
Als Nächstes folgt GENERAL-SCENE-COMPOSITION-09: vorhandene Rundungs-/Überdeckungs-
und Kinderanzahlfähigkeiten gemeinsam anschließen und vor Entwicklung andere
reale Prüffamilien sperren. Die zwei jetzt offengelegten Fälle sind Entwicklung.
Der [gemischte Szenenschritt](next_arbeitspaket_2026-10-22_mixed_gradient_scene.md)
verbessert zwei nach negativem Erstversuch bekannte Originale; die unabhängige
Übertragung auf zwei weitere reale Familien fehlt weiterhin. Der
[Konzeptaudit](concept_audit_2026-10-22.md) präzisiert die früheren Vision-Häkchen.
Die unten genannten Kandidaten und Zwischenzahlen beschreiben historische
Pakete; maßgeblich für die aktuelle Auswahl ist `open_tasks.md`.

## 1. Möglichst viele gute Konvertierungen

Den Katalog von ungefähr 1.700 Bildern schrittweise erschließen. Pro Familie
zuerst einen frischen CLI-Vorlauf messen, danach Beschreibung und allgemeine
Rastererkennung verbessern. Farb-, Größen- und unabhängige Geometrievarianten
prüfen; gespeicherte gute Ergebnisse durch Regressionstests schützen.
Qualitätsgrenzen beibehalten und die tatsächlich geprüften SVGs speichern.

Die Konvertierung verwendet Rasterbild und eigenständige Beschreibung.
Formparameter entstehen aus diesen Eingaben. Die Katalogbilanz soll gute,
weiter verbesserbare und wegen ihrer Komplexität zurückgestellte Bilder
ausweisen. Vollständige Abdeckung aller Bilder ist kein Abschlusskriterium.
Der offene zufällige Plan-B-Pool bleibt eine eigene, weiter sichtbare Aufgabe.

Das Paket `GE9023` sichert alle 14 U-Bogen-/Verlaufsschaftvarianten
mit eigenständiger Beschreibung, allgemeiner Rasterregistrierung und nativer
Verlaufsmaske durch die regulären und strengeren Plan-B-JPG-Gates. Die zusätzliche
synthetische Stressprüfung bleibt mit 12/17 Fällen als Folgeaufgabe offen.
Das anschließende Paket `AC0413` sichert neun Kreis-/Linienvarianten durch beide
regulären Gates und ein unabhängiges SVG mit zwei Seeds durch jeweils 17/17
strenge CLI-Prüfungen. Die drei grauen JPG-IoU-Fälle bleiben separat offen.
Das folgende Paket `AC0713` sichert alle sechs Varianten mit oberem Griff,
Strich und Punkt. `AC0721` sichert jetzt sechs Quadrat-/Untergriff-/T-Varianten
durch beide regulären Gates und ein unabhängiges SVG mit zwei Seeds durch
jeweils 17/17 strenge CLI-Prüfungen. Ein großer grauer JPG-IoU-Fall bleibt offen.
Die separate Erfolgsübersicht enthält inzwischen 329 Bild-/SVG-Paare und wird
im erweiterten Profil vollständig erneut konvertiert.
Das Paket `GE9021` sichert alle 14 Bogen-/Verlaufsschaftvarianten
und ein unabhängiges SVG mit 17/17 strengen CLI-Prüfungen.
Das Paket `SE0081` aktiviert die vorhandene Quadrat-/Textregistrierung
mit einer eigenständigen Beschreibung. Ziel und unabhängiger Holdout bestehen
beide regulären Gates; die unabhängige CLI-Vorlage besteht reproduzierbar 17/17.
Das Paket `GE0300` ergänzt eine allgemeine Registrierung für Kreuz,
Rechteckfläche und Verlaufsscheibe. Ziel und zwei unabhängige CLI-Läufe mit
jeweils 17/17 Fällen bestehen die unveränderten Gates. Das neueste Paket
`b_heating1` registriert
verschachtelte aufrechte Flammen auf einer Verlaufsscheibe. Ziel und zwei
unabhängige CLI-Läufe mit jeweils 17/17 Fällen bestehen die unveränderten
Gates. Das folgende Paket `AC0414` sichert neun Kreis-/Sehnen-/T-Varianten
mit allgemeiner Richtungsnormalisierung durch beide regulären Gates und eine
unabhängige Vorlage durch zwei CLI-Läufe mit jeweils 17/17 Fällen. Die drei
grauen JPG-IoU-Fälle bleiben als zusätzlicher strenger Folgepunkt offen.
Der nächste reguläre Kandidat ist jetzt `GE9033_6M`.
Die geprüfte Batchfähigkeit und die weiterhin begrenzte Motivabdeckung sind in
`project_status_2026-10-10.md` beschrieben. Eine frische Gesamtquote des
autonomen Kataloglaufs ist noch nicht belegt.

## 2. Verständliches, kleineres Produkt

Nach der Qualitätsphase den produktiven Einstieg und die benötigten Algorithmen
abgrenzen. Erprobte generische Primitive und Registrierung zusammenführen,
duplizierte Abläufe und abgelöste Heuristiken entfernen, Namen und Schnittstellen
vereinfachen und einen nachvollziehbaren Ablauf von Eingabe bis Qualitätsurteil
dokumentieren. Historische Abnahmewerkzeuge und Belege separat einordnen.
Die gewonnene Konvertierungsqualität bleibt durch dieselben Abnahmen geschützt.

Die Git-Basis dieses Pakets enthält **43.376 physische Python-Zeilen unter `src/`**
in 171 Dateien, ohne externe Bibliotheken; zusätzlich 50.710 Zeilen Tests und
15.224 Zeilen Werkzeuge. Gezählt sind auch Leerzeilen und Kommentare; externe Bibliotheken sind ausgeschlossen.
Eine kleinere Zeilenzahl ist ein Fortschrittsmaß; Verständlichkeit, Wartbarkeit
und erhaltene Qualität entscheiden über den Produktabschluss.

## Möglicher Entwicklungszweig: ImageDetector

Als mittel- bis langfristige Option ist ein vorgeschalteter
[ImageDetector](image_detector_development_branch.md) vorgesehen. Er soll
Grundformen erkennen, ihre Masse und Stilmerkmale aus dem Raster schätzen und
dem Konverter über die gemeinsame Geometry-IR bessere Ausgangsdaten liefern.
Erste Kandidaten sind Kreise/Ringe, Linien, Rechtecke und einfache Vielecke;
Beziehungen und Überdeckungen, Bézierkurven sowie Text bilden spätere
Ausbaustufen. Exakte Schriftarterkennung bleibt eine zusätzliche Option.

Der Zweig knüpft an vorhandene Perception-First-Bausteine an. Sein Nutzen ist
an unabhängigen Bildern durch Vergleiche mit und ohne Detector nachzuweisen.
Er ist als mögliche Weiterentwicklung dokumentiert und ändert weder die
bisherige Prioritätenfolge noch die nächste reguläre Aufgabe. Eine Umsetzung
oder ein Termin ist damit noch nicht festgelegt.
