# Nächstes Arbeitspaket – Plan-B GE1001_M Triage Run SO (2026-06-24)

Run SO arbeitet nach der abgeschlossenen IDO-Zielqualitätsstrecke wieder die reguläre Plan-B-Rotation aus `PLAN_B_KANDIDATEN.md` ab. Der aktuelle erste Kandidat ist `GE1001_M`.

## Änderungen

- `GE1001_M.jpg` wurde im echten Non-Composite-Pfad mit der vorhandenen Beschreibung erneut ausgeführt.
- Die Beschreibung lautet `Hintergrund GE1000, Vordergrund grüner Haken mit feiner grauer Umrandung` und wird weiterhin als unzureichend für eine sichere beschreibungsgetriebene Geometrie bewertet.
- Der Lauf fällt deshalb kontrolliert auf den elementweisen Raster-Fallback zurück und bleibt qualitativ unverändert bei `Mean-Delta²=18208.144531` beziehungsweise `Fehler/Pixel=0.073663`.
- Der PF8-Lerneffekt aus der aktiven Rotation bleibt für `GE1001_M` gültig: Kreis-/Linien-Kandidaten sind als `generalisiert` dokumentiert, aber die aktuelle Textbeschreibung liefert noch keinen ausreichend konkreten Haken-/Umrandungs-IR-Vertrag.

## Artefakte

- `artifacts/converted_images/reports/GE1001_M_plan_b_runSO_2026-06-24.log`

## Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ge1001-runso --start GE1001_M --end GE1001_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün und erzeugt den dokumentierten Fallback-Lauf.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py` läuft grün.
- `python tools/check_no_new_image_id_hardcoding.py` meldet weiterhin `0` Runtime-ID-Vorkommen.

## Ergebnis

Das nächste Plan-B-Arbeitspaket ist als Triage abgeschlossen, aber nicht als Qualitätsverbesserung gelöst: `GE1001_M` bleibt in der Rotation, weil die damalige Beschreibung zwar den grünen Haken benannte, aber noch keine katalogfreie Haken-/Kontur-Geometrie erzeugte. Run SP schärft die Beschreibung danach katalogfrei nach; der nächste konkrete Umsetzungsschritt ist ein generischer `hook/checkmark`-Primitive-Contract mit grauer Outline oder die Rotation auf `GE9021_7M` als kleineres Linien-Arbeitspaket.
