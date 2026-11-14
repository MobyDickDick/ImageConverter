# Vollständige Konvertierungsqualität im lokalen Webserver

Aufruf: `startWebServer.cmd`, dann **Konvertierungsqualität** oder
[direkt die Qualitätsliste](http://127.0.0.1:8766/catalog).
Nach einer Codeänderung muss der bisherige Server beendet und neu gestartet
werden. Die statischen Webseiten werden von der Festplatte geladen, während
Python-Code bis zum Neustart im laufenden Prozess verbleibt. Eine fehlende
Hintergrunddienst-API wird mit einem konkreten Neustarthinweis angezeigt;
die vorhandene Katalog- und Fortschrittsanzeige aktualisiert sich weiter.
Unter Windows bindet der Server seinen Port exklusiv. Läuft derselbe
ImageConverter-Server bereits, öffnet ein erneuter Start dessen Oberfläche
und endet erfolgreich. Mit `--no-browser` wird nur die Adresse ausgegeben.
Projekt und Datenverzeichnis müssen übereinstimmen; andere Dienste auf
demselben Port werden nicht übernommen. Der zweite Aufruf liest oder verändert
keine gespeicherten Aufträge und startet keinen zusätzlichen Serverprozess.
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
Die reine Qualitätsprüfung startet keine Konvertierung. Der separat startbare
Hintergrunddienst führt neue Versuche aus.

## Hintergrundkonvertierung

In der Katalogansicht startet **Hintergrunddienst starten** einen Durchlauf.
Zuerst wird die Qualitätsliste aktualisiert. Anschließend wird unter den
Katalogbildern mit **Rastergates verfehlt** jeweils der kleinste MSE des
schlechteren Renderers gewählt; bei Gleichstand entscheidet der Dateiname.
Bestandene und reservierte Bilder, Quellkonflikte, fehlende oder ungültige
Messwerte und Bilder ohne Beschreibung werden ausgeschlossen.

Der Dienst verwendet den gewöhnlichen Konvertierungsweg mit dem ausgewählten
Suchprofil und einem frischen Suchseed. Laufende manuelle Konvertierungen oder
Workbench-Läufe werden abgewartet. Nach jedem Versuch wird die Rangliste neu
ausgewertet. Nach drei erfolglosen Versuchen innerhalb einer Runde wird ein
Bild zurückgestellt. Sobald alle verbleibenden bewertbaren offenen Bilder
ebenfalls drei Fehlversuche haben, werden sämtliche Markierungen und
Fehlversuchszähler aufgehoben; die nächste Runde beginnt automatisch.
Bestandene Bilder scheiden sofort aus der Auswahl aus. Der Dienst wiederholt
die Runden bis zum Stopp oder bis keine bewertbaren offenen Bilder übrig sind.
Rundennummer und Fehlversuchszähler bleiben bei Stopp und Serverneustart
erhalten; ein manueller Start setzt die aktuelle Runde fort. Ein abgebrochener
Versuch zählt nicht als Fehlversuch.

Jeder neue SVG-Kandidat bleibt unter
`artifacts/converted_images/catalog_background_svgs/<job-id>/<bildname>.svg`
erhalten, auch bei weiterhin ungenügender Qualität. Vorhandene Kandidaten
bleiben erhalten. Nach jedem Versuch wird die vollständige Qualitätsliste
mit Cachewiederverwendung aktualisiert. Nur die bestehende Prüfung mit beiden
Renderern entscheidet über **Rastergates erfüllt**.

Die Oberfläche fragt den Status alle 1,5 Sekunden ab und zeigt aktuelles Bild,
MSE, Konvertierungsdauer, Live-Protokoll, Rundennummer, Versuch 1–3 und
zurückgestellte Bilder. Die letzten 200 Versuchsergebnisse seit dem Start
bleiben in der Anzeige; die vollständigen Auftragsprotokolle bleiben gespeichert. Die Zähler und
Katalogzeilen aktualisieren sich nach jedem vollständigen Prüfbericht.
Die Dienstkarte zeigt auch während der vorbereitenden Qualitätsprüfung die
Anzahl geprüfter Bilder, Gesamtzahl, neue und wiederverwendete Paarprüfungen,
Laufzeit, Fortschrittsbalken und das zugehörige Live-Prüfprotokoll.

**Nächstes Bild** zeigt Dateiname, Originalbild, MSE, Runde und Versuchsnummer.
Während einer Qualitätsprüfung ist die Auswahl vorläufig. Während einer
Konvertierung wird die voraussichtliche Auswahl unter der Annahme angezeigt,
dass das aktuelle Bild weiter offen bleibt; ein Erfolg kann sie ändern.
**Letzter Konvertierungsversuch** bleibt unabhängig davon sichtbar und zeigt
Original und erzeugtes SVG nebeneinander. Das SVG erscheint bereits vor
Abschluss der Nachprüfung mit der Kennzeichnung **SVG-Prüfung läuft**.
Erfolg wird ausschließlich anhand der Messung dieses Kandidaten mit beiden
Renderern bestätigt. Ein älteres bestandenes SVG desselben Bildes genügt
dafür nicht. Fehlendes SVG, offene bzw. unterbrochene Prüfung und fehlgeschlagene
Rasterprüfung bleiben unterscheidbar. Das letzte Ergebnis bleibt auch nach
einem Dienst- oder Serverneustart sichtbar.
Eine bereits laufende ältere Serverinstanz kann die neue Webseite anhand
der vorhandenen Katalog- und Auftrags-APIs mit denselben Vorschauen versorgen.
Damit muss eine parallel laufende Konvertierung oder Workbench-Prüfung für
die Anzeige nicht unterbrochen werden.
**Hintergrunddienst stoppen** beendet auch die aktive Konvertierung bzw.
Qualitätsprüfung samt Unterprozessen; es startet danach kein weiteres Bild.
Bereits vollständige Berichte und gespeicherte Versuche bleiben erhalten.
Der Dienst läuft unabhängig vom Browserfenster. Serverende stoppt den Dienst;
nach einem Neustart wird er als unterbrochen angezeigt und startet erst manuell.

Status: `GET /api/catalog/conversion`; Start und Stopp:
`POST /api/catalog/conversion/start` mit optionalem `profile`
(`quick`, `normal`, `thorough`) bzw. `POST /api/catalog/conversion/stop`.
Es gelten dieselben lokalen Host-/Origin- und Headerprüfungen wie für die GUI.

## Prüfung

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_catalog_background_conversion.py tests/test_catalog_quality_server.py tests/test_catalog_inventory.py tests/test_catalog_inventory_html.py tests/test_image_converter_gui.py tests/test_category_collection.py
node --test tests/test_catalog_poll.js
```

Die Dienstregressionen prüfen Auswahlreihenfolge, Ausschluss bestandener und
reservierter Bilder, drei Fehlversuche pro Runde, Zurückstellung, Rundenwechsel,
Fortsetzung nach Stopp und Neustart, Live-Protokoll, unveränderte
alte Kandidaten sowie Stopp während Wartezeit, Konvertierung und echter Prüfung.
Ein vollständiger Berichtslauf erzeugt mit einem eingespeisten SVG-Kandidaten
einen neuen Rasterpass durch die unveränderten MuPDF-/librsvg-Prüfprozesse.

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
