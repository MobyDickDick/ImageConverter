# Nächstes Arbeitspaket – Spezialfallabbau für freie Badge-Beschreibungen Run VH (2026-07-04)

Run VH korrigiert die Kritik an Run VG: Der SE0012-Fix war zwar bild-ID-frei,
aber noch zu phrasenhaft. Dadurch wäre der nächste ähnlich formulierte
Kellen-/Badge-Fall wieder mit einer neuen Einzelphrase nachgezogen worden. Der
Schwerpunkt liegt deshalb auf Spezialfallabbau im Prozess: Label-, Drehungs- und
Connector-Erkennung werden als kleine generische Beschreibungskonzepte
modelliert.

## 1) Umsetzung

- Freie Badge-Beschreibungen nutzen nun gemeinsame Textnormalisierung und
  allgemeine Prädikate für Token- und Drehungs-Erkennung statt lokaler
  Einzelketten für jeden beobachteten Satz.
- Die Drehungserkennung ist richtungs-/verb-basiert und akzeptiert korrekte wie
  häufig fehlerhafte Schreibungen von `gedreht`, ohne an eine konkrete Bild-ID
  oder einen konkreten SE0012-Satz gekoppelt zu sein.
- Badge-Labels werden generisch aus kurzen Anführungszeichen-Labels und aus
  semantischen Schlüsselwörtern abgeleitet. Dadurch funktioniert nicht nur `T`,
  sondern z. B. auch ein neutrales `"x"` ohne neue Spezialregel.
- Der generische Beschreibung-zu-Badge-Parameterpfad wird zusätzlich direkt
  getestet: ein beliebiger Kreis/Text/Links-Connector erzeugt Text- und
  Arm-Parameter auch ohne AC08-Rezept.

## 2) Warum der Prozess bisher harzt

Der Engpass ist nicht nur Pixeloptimierung, sondern die falsche Abstraktionsebene:
Zu viele Verbesserungen wurden als nachträgliche lokale Heuristik oder als immer
feineres Antialiasing-Tuning formuliert. Wenn die Topologie aus Beschreibung und
Bild nicht zuerst stabil in eine neutrale IR/Parametermenge überführt wird,
optimiert der anschließende iterative Prozess nur eine falsche Form. Dann wirkt
jedes Bild wie ein Spezialfall.

Run VH geht deshalb eine Ebene höher: Nicht `SE0012` wird gelernt, sondern die
wiederverwendbaren Konzepte `Badge/Kelle`, `kurzes Textlabel`, `horizontaler
Connector` und `Drehung nach Richtung`. Das verhindert Spezialfälle nicht
vollständig, reduziert aber den Mechanismus, der neue Spezialfälle erzeugt.

## 3) Sicherung

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_family_rules_helpers.py tests/detailtests/test_semantic_badge_runtime_helpers.py` läuft grün mit `20 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` läuft grün und bestätigt weiterhin `0` Runtime-ID-Vorkommen.
- `PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-se0012-runVH --start SE0012 --end SE0012 --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order` läuft grün; SE0012 bleibt auf dem generischen `semantic_badge`-Pfad mit `label=T`, `circle,arm,text` und `Mean-Delta²=1690.029541`.

## 4) Ergebnis / nächster Schritt

Spezialfall-Wachstum wird nicht durch weitere Micro-Probes verhindert, sondern
durch harte Architekturregeln: neue Korrekturen müssen als Beschreibungskonzept,
IR-Primitive, Parameterfamilie oder Optimiererfähigkeit formuliert werden. Neue
Bild-ID- oder Satzform-Sonderzweige sollen nur noch als Testfälle auftreten.
Der nächste sinnvolle Schritt ist eine CI-/Review-Regel, die genau diese
Abstraktionsebene für neue Qualitätsfixes erzwingt.

Aktueller Aufgabenstand bleibt: `PLAN_B_KANDIDATEN.md` enthält 5 aktive
Plan-B-Kandidaten; der Refactoring-Taskplan enthält 38 offene Checkbox-Aufgaben.
