# Wiederhergestellte Beschreibungskorrekturen

19 explizite Benutzereingaben aus dem lokalen GUI-Verlauf wurden wiederhergestellt,
jeweils die jüngste Eingabe pro Datei nach der letzten gepflegten XML-Änderung.
Dateiname und normalisierte Bildpunkte mussten mit dem Katalogoriginal
übereinstimmen. Beide XML-Tabellen wurden bildspezifisch geändert; andere Varianten
und die ursprünglichen GUI-Aufträge bleiben erhalten.

`summary.json` nennt die Aufträge, Bilder und Prüfsummen beider Tabellen vor/nach
der Wiederherstellung. `tests/test_description_persistence.py` und die realen
JavaScript-Abläufe prüfen die zukünftige automatische Speicherung.
