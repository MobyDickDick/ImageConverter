# SEARCH-ROUTES-01 · Gemeinsamer Bildkontext

Umgesetzt am 21. November 2026. Infrastruktur und repräsentative öffentliche
Einstiege sind geprüft. Die vollständige Verhaltensmigration der einzelnen
Modelle gehört weiterhin zu SEARCH-ROUTES-03. Keine allgemeine Verbesserung der
Katalogquote oder Laufzeit und keine Abnahme sämtlicher 60 Inventareinträge.

## Verhalten

- Ein `ImageSearch` je Bild enthält den vollständigen vorzeichenlosen
  64-Bit-Seed, aktive Bildzeit, ursprüngliche Zeitgrenzen, gemeinsamen
  Renderzähler, Kandidatenspeicher und Versuchsprotokoll. Modellwechsel und
  Wiederaufnahme starten diese Ressourcen nicht neu. Benannte Zufallsfolgen
  lesen den Bildseed; auch die Workbench akzeptiert jetzt `2**64-1`.
- Zentrale Renderer zählen tatsächliche SVG-Kandidaten einschließlich
  Initialisierung, Masken, Glyphenprüfungen und Nachprüfungen/PNG-Export.
  Verschachtelte private Renderadapter zählen einen äußeren Kandidaten einmal.
  Cachetreffer erzeugen kein neues Rendering. Backend/Farbraum, Größe und
  kanonisierter SVG-Inhalt bestimmen den Rastercache; Modellverlust und
  Formprüfung bleiben getrennt. Pixelcache: höchstens 8.192 Einträge/32 MiB;
  Messwertspeicher: 256 Einträge.
- `candidate_rendered`, `candidate_cache_hit`, `candidate_measured` und
  `candidate_skipped` protokollieren Arbeit, Fehler, Fortschritt und Stopgrund.
  `candidate_evaluations` und `renderings` zählen echte Renderkandidaten;
  frühere lokale Modellzähler stehen als `model_evaluations` bereit. Der
  Aufsichtsprozess erhält Renderstände auch vor dem abschließenden Handoff.
- `intermediate` und `full_scene` bleiben getrennt. Nur vollständige
  Form-/Beschreibungs-/Pixelprüfung gegen gebundene Originalpixel erzeugt einen
  an exakte SVG-Bytes und Originalpixel gebundenen Erfolgsnachweis. Eine
  Maskenprüfung bestätigt keine Konvertierung. Qualitätsgrenzen bleiben gleich.
- Beim Verwerfen einer optionalen Vorlage übernimmt die Beschreibungskonvertierung
  den bisherigen Kontext als JSON einschließlich Rastercache, Zähler, Seed und
  Restzeit. Originaldateihash und Einstellungen werden geprüft. Die Rückgabe
  enthält echte Renderstände und Raster, sodass ein vorhandener Entwurf auch
  am Renderlimit ohne weiteres Budget geprüft werden kann. Unpassende Vorlagen
  werden vor dem ersten Rendering zurückgewiesen. Die Ausrichtung nutzt die
  ursprüngliche Bilddeadline; die frühere Reservierung für eine entfernte
  zweite Rasterrekonstruktion entfällt.
- Die generische IR-Ausgabe übernimmt das tatsächlich vermessene, auf die
  Zeichenfläche begrenzte SVG. Ein Neuaufbau aus unbeschränkten Parametern
  konnte zuvor SVG und vermessene Pixel auseinanderlaufen lassen.
- Die abschließende Bauteilprüfung nutzt denselben RGB-Renderer wie die
  Platzierung. Dadurch wird ein bereits vermessener Kandidat aus dem Cache
  geprüft, statt ihn erneut durch die BGR-/RGB-Adapter zu rendern.

## Budgetbedienung

`--search-budget N` ist die harte gemeinsame Grenze tatsächlicher Renderkandidaten
je Bild, auch in `legacy`/`fixed`. Erlaubt sind 32 bis 10.000. CLI-Standard:
**4.096**. Der bisherige Standard 384 bezeichnete zusätzliche Vorschläge je
Modell; Initialisierungen und semantische Renderings kamen hinzu. Diese
Standards sind deshalb kein Vergleich bei gleichem Aufwand. Explizite Grenzen
werden nicht erhöht. Lokale Modellkontingente bleiben der gemeinsamen Grenze
und Bilddeadline untergeordnet. Direkte `search_configuration`-, Vorlagen- und
Bauteilaufrufe behalten ohne andere Konfiguration die Grenze 384.

## Frische öffentliche Einstiege

`python -m tools.evaluate_shared_search_context --output .tmp/NEUER_ORDNER`
erzeugt neue Eingaben und führt echte Worker aus. Alle verwenden den Seed
`18446744073709551615`. Renderereignisse werden mit den abschließenden
Kontextzählern verglichen. [Messwerte](summary.json),
[Dateihashes und statisches Inventar](manifest.json), [Rohprotokolle](journals/).

| Einstieg | Abnahme |
| --- | --- |
| CLI/Batch, zwei getrennte Bilder | Je 32/32 Renderings; beide `render_limit`, beide ungenügend. Das zweite Bild erhält einen eigenen Kontext. |
| Frische GUI-Konvertierung | Vollständiger Pixel-/Modellpass; Zähler und Seed aus dem echten Worker. |
| GUI-Vorlagenworker | Passendes SVG; ein Rendering, vollständige Prüfung, keine neue Konstruktion. |
| GUI-Hintergrundkonvertierung | Frischer Beschreibungspfad ohne Startvorlage; vollständiger Pass. |
| SVG-Bauteilworker | Unveränderte Donorgeometrie/-farbe/-position; gemeinsame Zählung der Teilprüfungen und abschließender Cachetreffer, vollständiger Pass. |
| Workbench → Plan B → CLI | Neuer Originalfall mit vollständigem Pass und maximalem Seed. Keine Ausführung der 16 Varianten oder allgemeine Plan-B-Abnahme. |

Verhaltenstests prüfen Seed-Wiederholung und andere zulässige Geometrien bei
anderen Seeds, Modellwechsel, Cachekopien, Backend-/Größentrennung, Masken ohne
Erfolgsfreigabe, Renderfehler, Deadline, Worker-/JSON-Übergabe und Nachprüfungen
nach Rückkehr der Modellpipeline.

## Prüfung und Grenzen

Die gezielte Abnahme samt Kernprofil und Aufsichtsprüfungen steht unter
`checks/`: 42 Kerntests bestanden; der gezielte Lauf bestand zunächst 153 Tests.
Nach Erweiterung um die Kernprüfungen bestanden 194 Tests bei einem
Zwei-Sekunden-Bauteiltimeout. Der anschließend korrigierte doppelte Renderaufruf
wurde mit 53 bestandenen Bauteil-/Kontext-/Formmodelltests nachgeprüft.
Die 29 Kontext-/Aufsichtsprüfungen bestanden ebenfalls; der separat mit dem
Ausgangscode reproduzierte Ventiltest wurde bei diesem Aufsichtslauf explizit
nicht ausgeführt (`1 deselected`, keine Änderung am Teststatus).
Der breitere frühe Prüflauf bleibt ebenfalls erhalten: 317 bestanden,
71 fehlgeschlagen, sechs Aufräumfehler. Er ist **kein grüner Gesamtstand** und
stammt vor den abschließenden Korrekturen für sehr kurze Vorlagendeadlines und
der CLI-Standardgrenze. Keine vollständige abschließende Wiederholung.

Mit unverändertem Ausgangscode separat reproduziert: veraltete Erwartung
direkter SVG-Kindknoten trotz Canvas-Gruppe, Ventilfehler
`logical_object_count:diagonal:1:0` und drei weitere GUI-Descriptionsfälle.
Ausgangsprotokolle sind beigefügt. Die übrigen Fehler werden damit nicht
pauschal als bereits vorhanden eingestuft. Windows-Prozessabbruch-/HTTP-Tests
bleiben außerhalb der begrenzten Paketabnahme teilweise rot. Keine Tests
ummarkiert und keine Form-/Pixelgates abgeschwächt.

Im statischen Inventar bleibt `behavior_verified=false`. Zentrale Rendergrenzen
erfassen eigene Spezialfits; neue Suchgeometrien und Positiv-/Negativverträge
jedes Modells bleiben AP 3. **SEARCH-ROUTES-02** ist als nächstes offen:
Fortsetzung nach schlechten Entwürfen, eindeutige Ergebniszustände und Erhalt
des besten Standes. Die neue CI-Stufe ist eingerichtet, noch nicht auf GitHub
ausgeführt. Den Webserver nach Abschluss laufender Aufträge neu starten;
laufende Aufträge wurden hier nicht unterbrochen.
