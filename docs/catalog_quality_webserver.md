# Vollständige Konvertierungsqualität im lokalen Webserver

Aufruf: `startWebServer.cmd`, dann **Konvertierungsqualität** oder
[direkt die Qualitätsliste](http://127.0.0.1:8766/catalog).
Die Oberfläche zeigt die letzte vollständige Liste aller 1.787 Katalogbitmaps.
Suchen über Dateinamen und Beschreibungen, Qualitäts-/Archivfilter,
MSE-Sortierung, Seitenauswahl und „Alle“ wirken auf den gesamten Bestand.
Original und ausgewähltes SVG sind unmittelbar vergleichbar; jeder gespeicherte
Kandidat zeigt die Befunde beider Renderer. CSV und JSON enthalten alle Zeilen,
unabhängig vom aktuellen Ansichtsfilter.

**Qualitätsliste aktualisieren** startet einen eigenen Prüfprozess.
Er misst bereits gespeicherte SVGs gegen die Originalbitmap mit MuPDF und
librsvg. Unveränderte, hashgebundene Paarprüfungen können wiederverwendet werden;
**Alle Paarprüfungen neu messen** erzwingt die Neumessung. Quellen,
Beschreibungen, Konvertierungsausgaben und Erfolgsarchiv werden nicht verändert.
Reservierte Prüffamilien bleiben gesperrt und werden nicht gerendert.
Während der aktiven Messung verwendet der Prüflauf die vorhandene zeitlich
begrenzte System-/Ausführungs-Wachhalteanforderung. Der Bildschirm darf weiterhin
abschalten; der eigene Handle wird bei Abschluss, Fehler und Prozessabbruch
freigegeben. Nicht verfügbare Windows-Anforderungen stehen sichtbar im Protokoll.

Die Anzeige meldet abgeschlossene Bilder, Gesamtzahl, neue Paarprüfungen
und wiederverwendete Messungen. **Prüfung abbrechen** beendet den Prüfprozess
einschließlich seiner Unterprozesse. Auch beim Serverende wird abgebrochen.
Die letzte vollständige Liste bleibt während Prüfung, Fehler und Abbruch
sichtbar und exportierbar. Eine abgebrochene Teilprüfung wird nicht als
vollständige neue Liste veröffentlicht. Ein neuer Versuch ist danach möglich.

Jeder Versuch verwendet einen eigenen Ordner unter
`artifacts/gui/catalog-quality/<id>/`. Erst nach erfolgreichem Prozessende
und vorhandenem vollständigem Manifest ersetzt ein atomarer `current.json`-
Verweis den veröffentlichten Stand. Alte fertige Berichte bleiben erhalten.
Ohne eigenen fertigen Webbericht dient `artifacts/catalog_inventory` als
Ausgangsstand. Serverneustart markiert einen unterbrochenen Auftrag als
`interrupted` und übernimmt keine unfertige Ausgabe.

## Bedeutung der Qualität

- Rastergates erfüllt/verfehlt: bestehende strenge Plan-B-Pixel-/Größen-/
  Vektorgates mit beiden Renderern, ohne pauschale Grenzlockerung.
- Historisch archiviert: separat ausgewiesene frühere Abnahme mit Prüfsummen,
  Beschreibungsgleichheit und vorhandenem oder fehlendem Beleg.
- Kein SVG, Messfehler, Quellkonflikt und reserviert bleiben eigene Zustände.
- MSE ist der schlechteste Wert beider Renderer; Kanten und Vordergrund-IoU
  verwenden jeweils den schlechteren Wert. Fehlende Werte bleiben leer.

Rasterpass und Archivmitgliedschaft überlappen und dürfen nicht addiert werden.
Eine vollständige neue Objekt-/Semantikabnahme ist damit nicht erbracht.
Das Werkzeug startet keine neue autonome Konvertierung aller Bilder.

## Prüfung

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_catalog_quality_server.py tests/test_catalog_inventory.py tests/test_catalog_inventory_html.py tests/test_image_converter_gui.py
```

56 Regressionen bestehen: echter CLI-Prüfprozess mit anschließender
Cachewiederverwendung, Prozessbaumabbruch, unveränderte frühere Liste,
fehlgeschlagene Veröffentlichung, Neustart, vollständige Exporte und lokale
HTTP-Routen. Unter Windows benötigt dieser Integrationstest normale lokale
Socket- und Prozessbaumrechte; die eingeschränkte Sandbox verweigert beides.
Die Prüfung außerhalb der Sandbox besteht ohne Überspringungen.
Der Browserablauf wurde zusätzlich am tatsächlichen Katalog gestartet,
abgebrochen und erneut gestartet; Suchfilter und bisherige Liste blieben nutzbar.

Der erste vollständige Versuch scheiterte nach 1.102 Bildern an einer
Windows-Dateisperre beim atomaren Austausch der gelesenen Fortschrittsdatei.
Die alte vollständige Liste blieb erhalten. Der Fortschrittskanal wiederholt
solche Austauschversuche jetzt kurz und lässt einen dauerhaft blockierten
UI-Tick aus, statt die Messung zu verlieren. Zwei zusätzliche Regressionen
prüfen kurze und anhaltende Sperren einschließlich späterer Erholung.

Die Anzeige wendet auch nachträglich hinzugekommene Reservierungen auf ältere
Berichte an: Messkandidaten und Assetzugriffe solcher Bilder werden gesperrt,
ohne alte Messungen zu wiederholen. Gruppen-/Gesamtzähler bleiben konsistent.
Zwei zusätzliche Regressionen prüfen die Freigabe der Wachhalteanforderung
bei Erfolg und Fehler; eine weitere prüft nachträgliche Reservierungen.

Der abschließende lokale Serverabruf bestätigt 1.787 Zeilen, 348 historische
strenge Rasterpässe und 379 Archivaufnahmen. Die aktuelle Reservierungsliste
umfasst sechs Bitmaps aus vier Familien. Der letzte vollständige Messstand
bleibt vom 07.11.2026; die zuletzt gestartete Neumessung wurde abgebrochen und
nicht erneut gestartet. Eine frische vollständige Qualitätsmessung wird damit
nicht behauptet. [Lokaler Prüfbeleg](../artifacts/evaluation/catalog_quality_web_v1/README.md).

CI um die lokalen Serverregressionen ergänzt, kein GitHub-Lauf gestartet.
