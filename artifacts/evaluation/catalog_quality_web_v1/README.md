# Vollständige Qualitätsliste mit abbrechbarer Neumessung

[Bedienung, Fehlerbehandlung und Grenzen](../../../docs/catalog_quality_webserver.md).
[Projektstand und Entfernung zur breiten Abdeckung](../../../docs/project_status_2026-11-13.md).

`checks.json` bindet die finalen Quellen an die ausgeführten lokalen
Regressionsprofile und den abschließenden HTTP-Abruf des Webservers.
56 Server-/GUI-/Inventarregressionen bestehen ohne Überspringungen. Der echte
kleine CLI-Prüfprozess und seine Cachewiederverwendung sind dabei unabhängig
vom weiterhin unvollständigen großen Katalogprüflauf abgenommen.

Die Browserprüfung startete die tatsächliche Neumessung, bestätigte Suche,
Einzelbefunde und Abbruch bei erhaltener vollständiger Liste. Der erste lange
Versuch scheiterte an einer Windows-Dateisperre der Fortschrittsdatei nach
1.102 Bildern; Wiederholung/Best-Effort-Publikation ist jetzt separat geprüft.
Der spätere Lauf wurde abgebrochen. Es wird kein neuer vollständiger
Katalogmessstand oder Konvertierungsbenchmark behauptet.

Ein zwischenzeitlicher Integrationstest enthält eine 25-minütige
Systemunterbrechung und eine daraufhin abgelaufene Achtsekunden-Startwartezeit.
Er bleibt als fehlgeschlagener Versuch ausgewiesen. Der vollständige finale
Integrationslauf mit temporärem vorhandenen Wachschutz besteht 56/56 in
41,84 Sekunden; die native Anforderung meldet `acquired` und anschließend
`released`, ohne Freigabefehler. Das ist keine allgemeine Standbygarantie.

Der zuletzt geprüfte Server liefert 1.787 Einträge, 348 Rasterpässe,
379 historische Archivaufnahmen und sechs aktuell reservierte Bitmaps.
Letzte vollständige Messung: 07.11.2026, ergänzt um aktuelle Reservierungsregeln.
Exporte und Listenfilter starten keine Konvertierung. Keine Reserveversuche,
Modellfreigaben oder Archivpromotionen; keine GitHub-CI gestartet.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_catalog_quality_server.py tests/test_catalog_inventory.py tests/test_catalog_inventory_html.py tests/test_image_converter_gui.py
```

Der lokale Server läuft über `startWebServer.cmd`, Oberfläche `/catalog`.
Große Laufbelege bleiben unverändert unter `artifacts/gui/catalog-quality/`.
