# Freie Grundformensuche: Prüfung am 21./22. November 2026

Die freie Suche verwendet dieselbe allgemeine Implementierung für bis zu zehn
beschriebene Grundformen. Produktionscode enthält weder Bildnamen noch eine
vorgegebene Ventilgeometrie. AC0204_L dient hier als gemeldeter Prüffall.
Die bestehende Beschreibung wurde nicht verändert.

## Bestandener echter GUI-Worker

Der frische Lauf `21b1699f82dc415e9193aa551db421b0` startet mit Profil `explore10`,
Seed 42 und ohne SVG-Wiederverwendung. Er erzeugt 11.275 Renderkandidaten mit
9.357 unterschiedlichen Geometrien und 844 Neustarts nach der Initialpopulation.
Die aktive Suche endet nach 181,2 Sekunden mit `satisfactory`; der gesamte
GUI-Lauf benötigt 208,8 Sekunden einschliesslich Initialisierung und Abschluss.

| Prüfung am gespeicherten SVG | Ergebnis | Grenze |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0,00468449 | höchstens 0,01 |
| Vordergrundfehler | 0,01301903 | höchstens 0,04 |
| Vordergrund-IoU | 0,90192644 | mindestens 0,85 |
| Kantenübereinstimmung | 0,72858727 | mindestens 0,72 |
| Vollständiges Inventar und Verbindungen | bestanden | verbindlich |
| Ursprüngliche 65 × 50 Pixel | eingehalten | verbindlich |

Kreis, Griff und zwei Dreiecke besitzen native SVG-Elemente. Beide
Dreiecksspitzen und das freie Griffende haben identische ausgegebene Koordinaten.
Die reguläre Projektablage speichert
`artifacts/converted_images/converted_svgs/AC0204_L.svg`. Die Grenzen wurden nicht
gelockert. Das Ergebnis ist eine bestandene Annäherung, keine pixelidentische Kopie.

Der erneute Worker-Lauf mit Profil `explore5` lädt denselben Checkpoint,
verifiziert ihn mit einem Rendering und endet nach 3,1 Sekunden. Die bereits
gleich gute Projektversion bleibt erhalten. Auch ein echter HTTP-Start im
neuen Webserver auf Port 8767 bestätigt diese Fortsetzung nach 3,0 Sekunden.
Die Zusammenfassung steht in `summary.json`; rohe Aufträge und Suchjournale
bleiben lokal und sind über `run_gui.py` reproduzierbar.

Die zuletzt ergänzte Auswahl wirksamer Parameter wurde zusätzlich mit Seed
2026 direkt am JPEG geprüft: 20.216 Renderkandidaten, 18.492 verschiedene
Geometrien, 1.474 Neustarts, 172,9 Sekunden, vollständige Verbindungen und
bestandene Pixelprüfung. Dieser direkte JPEG-Decodierpfad ist nicht mit dem
PIL/PNG-Import der GUI pixelidentisch. Seine Population wird deshalb korrekt
getrennt gespeichert; Dateinamen allein reichen nicht zum Wiederverwenden.

## Fehlversuche und Grenzen

Ein früherer voller Fünf-Minuten-Lauf liefert zwar einen pixelähnlichen Stand,
verfehlt aber die gemeinsame Spitze. Die vollständige Prüfung veröffentlicht
ihn nicht als bestandene Konvertierung. Der strenge Vergleich führte zur
Erhaltung eigener gültiger Suchzweige. Ein früher 48-Sekunden-Versuch hatte noch
eine gröbere Verbindungstoleranz und zählt hier nicht als abschliessende Abnahme.

Ein unabhängiges synthetisches Bild mit Kreis und Rechteck bleibt in den
zusätzlichen Versuchen ungenügend. Das dokumentiert eine reale Grenze und wird
nicht durch einen bildspezifischen Fitter ersetzt. Eine allgemeine höhere
Erfolgsquote über den Katalog ist mit diesen Messungen nicht belegt.

## Tests

Die fokussierte Suite für neue Suche, beide GUI-Profile, Checkpoint-Fortsetzung,
Vorschaujournal und CLI-Helfer besteht mit **67 Tests**. Eine grössere Suite für
Sprache, Formrepräsentation, bisherige Beschreibungsregistrierung, gemeinsamen
Suchkontext, Suchrouten und Ventilprüfungen besteht mit **171 Tests**, bei vier
gesondert dokumentierten bestehenden Fehlern. Weitere Such- und Deadline-Tests
liefern 75 bestandene Prüfungen neben acht reproduzierten Bestandsfehlern.

Die Bestandsfehler wurden mit den betroffenen Modulen aus `git show HEAD:…`
in einem separaten Prozess erneut geprüft. Vier Fälle betreffen ungebundene
Referenzkontexte beziehungsweise alte Ventil-GUI-Erwartungen; acht weitere
betreffen GUI-Fixtures ohne Beschreibung und einen vorhandenen
3-Wege-Ventil-/Diagonalzählfehler. Der JavaScript-Bestand hat unverändert
10 bestandene und drei fehlgeschlagene Tests, auch mit unverändertem
`HEAD:web/app.js`. Diese Fehler werden nicht als behoben angegeben.

Neue Prüfungen belegen insbesondere:

- reproduzierbare echte SVG-Folgen bei gleichem Seed und festem Arbeitsumfang;
- andere Geometriefolgen bei anderen Seeds und eine räumlich breite Startpopulation;
- Fortsetzung statt Wiederholung, getrennte Speicher je Seed beziehungsweise Bildpixeln;
- erneute Prüfung gespeicherter Erfolgskennzeichen und Umgang mit beschädigtem JSON;
- unveränderte Inventar- und Verbindungsprüfung am ausgegebenen SVG;
- tatsächliche Renderzählung, Zeitende und beide weitergereichten GUI-Zeitbudgets;
- explizite Ablehnung nicht unterstützter Angaben vor dem GUI-Start.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_primitive_evolution.py tests/test_image_converter_gui.py::test_free_search_profiles_reach_cli_with_durable_memory_and_skip_samples tests/test_image_converter_gui.py::test_free_search_rejects_unsupported_claim_before_launch tests/test_image_converter_gui.py::test_free_search_completion_does_not_rescan_every_rendered_attempt tests/test_gui_preview.py tests/detailtests/test_cli_helpers.py -q
.venv/Scripts/python.exe artifacts/evaluation/primitive_evolution_2026-11-21/run_gui.py --profile explore10 --publish
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
git diff --check
```

[Bedienung, Speicherformat und begrenzter Sprachumfang](../../../docs/free_primitive_search_2026-11-22.md).
