# Geometrische Klassen des gesamten Bildkatalogs

1787 Katalogbilder: 1781 geometrisch zugeordnet,
0 zu klären, 6 reserviert.
1781 Zuordnungen sind durch Sichtprüfung der Quellbilder ergänzt.
0 Zuordnungen sind noch automatische Vorschläge aus Beschreibungen.

| Klasse | Bilder | Vorhandenes SVG mit Rasterpass | Historisch archiviert |
| --- | ---: | ---: | ---: |
| Kreis/Ellipse mit Text und optionalen Anschlüssen | 184 | 17 | 51 |
| Kreis mit Dreieck / Pumpe / Kompressor | 122 | 18 | 21 |
| Kreis mit Linien, Kreuz, Balken oder Pfeil | 139 | 26 | 44 |
| Kreis mit Spirale oder gebogenen Innenlinien | 36 | 12 | 18 |
| Kreis/Kugel mit radialem Verlauf | 24 | 6 | 6 |
| Kreis/Ellipse, Füllung, Kontur oder Verlauf | 9 | 1 | 3 |
| Ventil / Dreiecksflügel mit Stellglied | 100 | 10 | 3 |
| Rechteck mit Linien, Kreuz, Zeichen oder Anschluss | 405 | 49 | 41 |
| Rechteck/Quadrat mit Kontur, Füllung oder Verlauf | 116 | 20 | 0 |
| Panel/Röhre mit Kurven oder räumlichem Effekt | 84 | 0 | 0 |
| Pfeile, Linien, Dreiecke und Verzweigungen | 248 | 164 | 168 |
| Achsendiagramm / Stufen / Sinus | 20 | 4 | 3 |
| Mehrere geometrische Formen / Überdeckung / Verschachtelung | 42 | 5 | 4 |
| Geometrisches Piktogramm / Button / Flagge / Haken | 107 | 13 | 13 |
| Kurviges Piktogramm / Flamme / Glocke / Tropfen / Werkzeug | 120 | 4 | 4 |
| Foto / dichtes oder organisches Motiv | 25 | 0 | 0 |
| Reservierter Prüfbestand | 6 | 0 | 0 |

## Einordnung

Die Klassen gruppieren Geometrie und Komposition, nicht Bildnummern. Zu jeder
Zuordnung stehen vorhandene native Modelle und deren Grenzen in der Gesamtliste.
Die Modelle decken Teile der Klasse ab; die Mitgliedschaft beweist weder einen
passenden vollständigen Modellvertrag noch eine erfolgreiche Konvertierung.
Ein Pixel-Fehlschlag ist kein Nachweis grundsätzlicher Nichtkonvertierbarkeit.
Die 1781 Sichtzuordnungen werden eigens markiert. Sie beruhen
auf den sichtbaren Formen jedes einzelnen Bildes einschließlich der Größenvarianten.
Die beobachteten Unterformen und Anbauten stehen bei der jeweiligen Zuordnung.
Die verbleibenden 0 beschreibungsbasierten Vorschläge
sind noch nicht an den Originalbildern geprüft.

Die Qualitätszahlen stammen aus dem vorhandenen Snapshot
`2026-11-14T12:30:47.960334+00:00` und werden nur bei identischen
Bildbytes und Beschreibungen übernommen. Es wurde keine neue Konvertierung
oder Rastermessung durchgeführt. Archiv und Rasterpass überlappen.
Reservierte Bilder bleiben ohne neue geometrische Zuordnung.

Beschreibungsprobleme: `{"reference_or_vague": 135, "missing": 1, "placeholder": 189}`.
Platzhalter mit Vorschlagslisten (Kreis/Ellipse/Rechteck/Polygon) zählen nicht als
Beobachtung dieser Formen. Sichtzuordnungen sind an die Bildbytes gebunden;
der damalige Beschreibungshash bleibt als Herkunft dokumentiert. Eine reine
Textkorrektur verwirft eine bildunabhängig geprüfte Zuordnung nicht. Veränderte
Bildbytes verwerfen sie. Die Zuordnung ist keine menschliche fachliche Freigabe.

## Dateien und Wiederholung

- [Durchsuchbare Gesamtliste](index.html), mit Originalbildern und Klassenauswahl.
- [Alle Zuordnungen als CSV](classes.csv).
- [Vollständige Zuordnungen und Herkunft als JSON](manifest.json).
- [Bilanz und Prüfsummen](summary.json).

Im Projektverzeichnis: `.venv/Scripts/python.exe -m tools.build_catalog_classes`.
Die Konvertierungsqualität im lokalen Webserver zeigt dieselben Klassen.

## Vollständige Sichtprüfung

- [Bilanz und Vollständigkeitsprüfungen](review_summary.json).
- [Geänderte Klassenzuordnungen als CSV](review_changes.csv).
- [Quelldateien und Zellen der geprüften Kontaktbögen](review_manifest.json).
