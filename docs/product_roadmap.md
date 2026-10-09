# Roadmap: Konvertierungsqualität, danach Produkt (2026-10-09)

Die vom Nutzer vorgegebene Reihenfolge gilt für die nächsten Arbeitspakete.
Die konkrete nächste Aufgabe und ihr Abschluss stehen in `open_tasks.md`
und `../PLAN_B_KANDIDATEN.md`.

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

Das aktuelle Paket `GE0032` trennt das Abwärtspfeil-Grundbild von den drei
Kreisscheiben mit Rundbalken und sichert beide Rastertopologien durch
allgemeine Registrierung und native Verlaufsdarstellung. Alle vier Fälle
bestehen die regulären und strengeren Plan-B-Gates. Der nächste reguläre
Kandidat ist nach dem erneuerten Review `GE9023_6M`.

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
