# Nächstes Arbeitspaket – generische Kellen-/Badge-Beschreibungsparameter Run VG (2026-07-04)

Run VG reagiert auf den gemeldeten SE0012-Fehlerfall als generische
Beschreibungslücke: Beschreibungen wie Kreis/Kelle mit `T`-Text und durch
Drehung links liegendem horizontalem Griff wurden bisher nicht als
parametrisierbares Semantic-Badge erkannt. Dadurch fiel der Lauf auf eine
bildnahe, aber topologisch unvollständige Fallback-Rekonstruktion ohne Griff
zurück.

## 1) Umsetzung

- Die freie Semantic-Badge-Beschreibungsanalyse erkennt nun `T`/Temperatur-Text
  explizit und versteht auch `waagrecht` formulierte Drehbeschreibungen wie
  `nach rechts gredreht` als linken Kreis-Connector, sofern Kreis/Kelle und
  horizontaler Text beschrieben sind.
- Für Semantic-Badge-Beschreibungen ohne AC08-Rezept erzeugt der Runtime-Pfad
  nun katalogfreie generische Kreis-/Text-/Connector-Parameter aus den erkannten
  Beschreibungselementen, statt sofort in den Sample-/Element-Fallback zu
  kippen.
- Der neue Pfad bleibt bild-ID-frei: Er hängt an Beschreibungselementen wie
  `Kreis + Buchstabe` und `waagrechter Strich links vom Kreis`, nicht an
  `SE0012`.
- Ein Detailtest sichert die gedrehte T-Kelle mit linkem horizontalem Connector
  als freie Beschreibung ab.

## 2) Perception-Lerneffekt

Der Lerneffekt ist `generalisiert`: Die reine Bilddetektion war nicht der
Hauptfehler. Der Fehler lag in der Beschreibung-zu-IR/Parameter-Fusion: Der
beschriebene Griff wurde zwar im Raster sichtbar, aber der freie SE-Pfad bekam
keine generischen Semantic-Badge-Parameter. Run VG erweitert daher den
beschreibungsgesteuerten Badge-Pfad, damit vergleichbare Kreis-/Kellen-Symbole
mit Text und horizontalem Connector nicht mehr ohne parametrisierten Connector
starten.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_family_rules_helpers.py` läuft grün mit `16 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0012-after3 --start SE0012 --end SE0012 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; SE0012 nutzt nun `mode=semantic_badge`, `label=T` und die Elemente `circle,arm,text`. Die isolierte Metrik sinkt gegenüber dem dokumentierten Ausgangswert `Mean-Delta²=2663.792969` auf `Mean-Delta²=1690.029541`.

## 4) Ergebnis / nächster Schritt

SE0012 ist weiterhin nicht perfekt; die Warnung zur lokal konzentrierten
Restabweichung bleibt bestehen. Der grobe Topologiefehler ist aber reduziert:
Der linke Griff wird nun aus der Beschreibung abgeleitet und in die
parametrisierte SVG-Erzeugung übernommen. Der nächste Schritt sollte nicht noch
feinere Mikronudges sein, sondern die generische Beschreibung-Bild-Fusion für
Badge-Primitive weiter ausbauen und die offene Qualitätsdefinition aus dem
Form-Decoupling-Plan konkretisieren.

Aktueller Aufgabenstand: `PLAN_B_KANDIDATEN.md` enthält weiterhin 5 aktive
Plan-B-Kandidaten. Der Refactoring-Taskplan enthält aktuell 38 offene
Checkbox-Aufgaben.
