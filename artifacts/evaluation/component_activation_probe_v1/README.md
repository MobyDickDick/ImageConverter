# Voruntersuchung: gemeinsame Initialisierung, abgeschaltete Suchausführung

Diese vorherige Matrix ist als Audit-Beleg erhalten. Abgeschaltete Bots
erzeugten keine Vorschläge, ihre Startobjekte wurden aber noch angelegt.
Die definitive Matrix unter `../component_value_v1` schaltet auch diese
Initialisierung ab und wurde vollständig neu ausgeführt. Die damalige
Suchmodulquelle liegt als `imageCompositeConverterSearchBots.py` bei.

## Damaliger Bericht

`checks.json` bestätigt 348 vollständige Versuche, 345 gespeicherte SVGs,
231 unabhängige Freigaben und unveränderte Hashes aller 377 Archivpaare.
Kein abgeschalteter Bot hat Vorschläge erzeugt.

- 324 produktive Konvertierungen: neun Raster-/Beschreibungsfälle, zwölf
  Varianten und drei Seeds, jeweils fünf Sekunden einschließlich Workerstart.
- 24 abschließende Kontrollversuche: zwei Fälle, vier Varianten und drei Seeds.
  Fester Ablauf, Vorschlagsbasis 32, gleiches 15-Sekunden-Budget je Kontrollarm.
  Die beiden Renderer-Zugänge liefern dieselben SVGs; ohne beide scheitern die
  Fälle. Zwei Sekunden Zusatzwartezeit vor dem ersten Renderaufruf jedes Workers
  erhalten die SVGs bei höherem Aufwand.
- `sources/`, `manifest.json`: eingefrorene Raster, Texte und Objekt-Orakel.
- `outputs/`, `telemetry/`: tatsächlich erzeugte SVGs, Rendererereignisse und
  beobachtete Runtime-Schalter. Quellen und Ausgaben sind per SHA-256 gebunden.
- `report.json`: sämtliche Versuche einschließlich dreier fehlender Ausgaben,
  Einzelmetriken, Zeit-/Speicherbeobachtungen und vorsichtige Paarvergleiche.

Das vollständige Portfolio besteht 18/27 Produktionsfälle. Ohne alle Bots,
ohne Feinregistrierung beziehungsweise mit Geometrie plus Neustarts sind es
jeweils 17/27. Das ist keine allgemeine Rangliste: Alle produktiven Einstufungen
bleiben wegen geringer Familienabdeckung und unsicherer Zeitdaten unklar.
Die konkrete Entscheidung lautet Beibehaltung aller sechs Bots. Der unabhängige
zusätzliche Bestand steht unter `../component_retention_v1`.

Der vollständige Repository-Testlauf lief parallel. Darüber hinaus zeigen
einzelne CLI-Batches sehr lange Unterbrechungen, unter anderem 21.805,641 und
7.732,516 Sekunden im Zusatzaufwand-Arm. Die Rohzeiten werden erhalten. Daraus
lässt sich weder eine allgemeine Laufzeitverbesserung noch eine Garantie für
die CLI-Gesamtdauer ableiten. Gemessene Bildzeiten und Batchzeiten sind getrennt.

Zwei unzureichende Kontrollentwürfe bleiben mit ihren Rohdaten erhalten:
`../component_control_timing_probe_v1` und
`../component_control_render_delay_v1`. Ihre Fehlbefunde werden nicht als
bestandene Kontrollabnahme gezählt. Die Wiederaufnahme nach dem Fehler der
Zwischenbericht-Paarbildung hat alle gespeicherten Produktionsausgaben erneut
geprüft. Runtime-Quellen und Qualitätsgrenzen blieben gleich; der ergänzte
Reporter-Hash ist im Hauptbericht vermerkt.

Reproduktion mit frischen Ordnern und unabhängige Nachprüfung:

```powershell
.venv/Scripts/python.exe -m tools.run_component_value --output-dir .tmp/component-replay --work-dir .tmp/component-replay-work
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir artifacts/evaluation/component_value_v1
```
