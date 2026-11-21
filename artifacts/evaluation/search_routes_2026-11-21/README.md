# Untersuchung aller produktiven Suchfamilien

Die vorige Korrektur hat **nicht sämtliche Suchpfade** auf ein einheitliches
Verfahren umgestellt. Diese Untersuchung erfasst die aktuellen produktiven
Einstiege und beschreibt die konkrete Erweiterung. Statische Erfassung und
ausgeführte Verhaltenstests werden ausdrücklich getrennt.

`tools/audit_search_routes.py` erzeugt `manifest.json` aus Funktionen,
Importverweisen und den drei produktiven Mode-Runnern. Die dynamische
`scene_reconstruction_fitters()`-Liste wird dabei mit erfasst. Der Test
`test_route_inventory_covers_every_registered_scene_fitter` prüft zusätzlich,
dass alle 39 dort registrierten Fit-Funktionen im Manifest stehen.

Das Ergebnis enthält **60 Einstiegsfunktionen**, darunter die gemeinsamen
Suchkerne und zwei ausdrücklich bedingte Legacy-Einstiege. Es sind keine 60
voneinander unabhängigen Algorithmen. Mehrere Einstiege teilen einen Kern.
**19 Fit-Einstiege erreichen keinen der erfassten gemeinsamen Suchkerne** und
besitzen eigene Anpassungs-/Messschleifen. `fit_dot_panel` wurde aus dem
produktiven Inventar ausgeschlossen: Es wird nur vom historischen
`_fit_symbol_element_by_element`-Hilfspfad benutzt, nicht vom aktuellen
`runNonCompositeIterationImpl` oder dessen Modellregistry.

Die Referenzanalyse ersetzt keine Laufzeitabdeckung aller Bilder: injizierte
Callbacks, textabhängige Zweige, Modelle mit mehreren internen Stufen und
Legacy-Schalter müssen zusätzlich über Verhaltenstests geprüft werden.
Deshalb steht im statischen Manifest bei jedem Eintrag `behavior_verified=false`.

## Gefundene Lücken und bereits ausgeführte Änderungen

| Suchfamilie | Befund | Stand nach dieser Untersuchung |
| --- | --- | --- |
| Allgemeine Geometry-IR-Anpassung | Feste Startfarbe, deterministischer Einzelstart, Hintergrunddominanz | Vorige Korrektur mit gemessener Farbe, mehreren Starts, Vordergrund-/Kantenbewertung und echten Renderhashes bleibt aktiv. |
| Gemeinsame analytische Registrierung (`_register`, `_register_steps`) | `allow_portfolio=False` schaltete auch die Seed-Reihenfolge aus; `proposal_rng` ignorierte Legacy-Konfiguration | Seed ist jetzt unabhängig von der Freigabe später Portfolio-Worker und vom Suchmodus. Modellverlust, semantische Prüfung und Zwischenstufen bleiben erhalten. Mehrere echte Neustarts sind dadurch noch nicht für jede Stufe nachgewiesen. |
| Eigenständige Spezialfits | 19 Einstiege haben eigene lokale Raster-/Geometrieschleifen, zum Teil eigene Zeit-/Renderzähler und feste Prüfreihenfolgen | Vollständig inventarisiert; noch nicht alle auf einen gemeinsamen Suchvertrag migriert. |
| Vorlagen / aktuelles SVG | `refine` übergab den gewählten Seed nicht an `align_sample`; feste lokale Reihenfolge; ein Kontrastschutz verhinderte den notwendigen Wechsel roter Flächen zu hellem Grau | Seed wird übergeben, acht korrelierte Platzierungs-/Skalierungsproben ergänzen schlechte Fits, die lokale Reihenfolge ist reproduzierbar vom Seed abhängig. Chromatische gefüllte Flächen werden vor Geometrieänderungen anhand eigener Renderabdeckung farblich kalibriert. Dunkle Text-/Konturdetails behalten ihren Kontrastschutz. Jeder neue Kandidat wird vor dem Rendern an der Beschreibung geprüft. Kreise, Quadrate und Rauten werden nur gemeinsam in beiden Achsen skaliert. Bericht enthält tatsächliche Renderfolge, Prüfzahl und Stopgrund. |
| Semantische Elementoptimierung / alte globale Parametersuche | `Action.STOCHASTIC_RUN_SEED` stammte aus einem getrennten RNG; bei `--deterministic-order` immer 0, unabhängig vom GUI-/CLI-Suchseed | Der konfigurierte vollständige 64-Bit-Seed wird jetzt auch hier verwendet. Deterministische Dateireihenfolge überschreibt den Geometrie-Seed nicht mehr. Ohne Suchkonfiguration bleiben die bisherigen Bibliotheks-/Umgebungsregeln erhalten. Das ist ein Weitergabenachweis, kein Nachweis unterschiedlicher sinnvoller Modellhypothesen in sämtlichen Unteroptimierern. |
| Duale Pfeile | Primärer `fit_arrow_pair` verwendet den gemeinsamen analytischen Kern; bei Nicht-Erkennung existiert ein anderer Detektorpfad | Im Inventar erfasst. Für den Detektorpfad sind eine explizite Unterscheidung zwischen `unsupported` und `draft` und ein eigener Negativtest nötig. Die Raster-SVG-Sperre bleibt bestehen. |
| Composite-Modus | Feste Folge von Kontur-Epsilonwerten, eigener Plateauabbruch; keine allgemeine gemeinsame Neustartverwaltung | Erfasst; Änderungen müssen zulässige Konturhypothesen betreffen. Eine zufällige Epsilon-Reihenfolge allein wäre kein ausreichender Suchraumgewinn. |
| Explizite SVG-Bauteile | Eigene mehrskalige Lokalisierung und anschliessende Platzierungs-/Ebenensuche; bestes lokales Match wird früh festgelegt | Erfasst. Künftig mehrere gute Lokalisierungen pro Bauteil gemeinsam vergleichen. Donorgeometrie und -farben, explizite Platzierungen und vorgegebene Ebenenbeziehungen müssen unverändert verbindlich bleiben. |
| Automatischer Donortransfer | Nur bei deaktiviertem `semantic_only` an den Batchlauf angeschlossen | Als bedingter Legacy-Pfad erfasst. Für die aktuelle beschreibungsgetriebene Konvertierung nicht wieder aktivieren. |
| GUI-Erholung / native Struktur-Nachsuche | Recovery ist ein expliziter No-op; die alten Struktur-/Fallback-Module werden produktiv nicht zur Fortsetzung aufgerufen | Kein zu erweiternder aktiver Suchpfad. Nicht als neue zweite Rasterrekonstruktion wieder einschalten. |

CLI, GUI-Einzelkonvertierung, Katalogdienst und Workbench/Plan-B bilden nicht
jeweils eine eigene Modellimplementierung. Die GUI startet bei frischer
Konvertierung den CLI-Worker; Plan-B verwendet dieselbe CLI im
`semantic-only`-Modus. Vorlagen sind ein eigener Worker-Einstieg. Ein Audit nur
der CLI-Option `--search-seed` hätte die gefundenen Unterpfade übersehen.

## Konkreter gemeinsamer Suchvertrag

Die Erweiterung sollte einen gemeinsamen **Suchkontext** besitzen, während jedes
Modell seine erlaubten Parameter und Prüfungen liefert:

```text
SearchContext:
  seed, input_hash, description_assertions, deadline, render_budget
  scope = full_scene | intermediate
  render_cache, trial_journal, incumbent, exploration_branches

ModelSpec:
  parameters, parameter_roles, bounds, valid_geometry
  initial_hypotheses, propose_restart, render, local_loss
  validate_model, paint_bindings, locked_parameters

SearchOutcome:
  status = passed | draft | exhausted | unsupported
  best_candidate, actual_render_count, geometry_trace, stop_reason
```

1. Der Kontext wird am Bild-/Worker-Einstieg erzeugt und über alle Unterfits
   weitergegeben. Kein Unterfit bekommt eine neue Profilzeit. Benannte
   RNG-Teilströme hängen von Seed und Modellinhalt ab, nicht vom Dateinamen oder
   von der Reihenfolge fremder Modellaufrufe.
2. Das Modell deklariert Geometrie-, Farb-, Winkel- und andere Parameter getrennt.
   Pixelkoordinaten, normierte Grössen, Winkel und Farbkanäle dürfen nicht alle
   mit derselben Zufallsschrittweite behandelt werden. Feste Platzierungen,
   Donorfarben, explizite Beziehungen und gemeinsame Seitenlängen sind gesperrt
   oder gekoppelt.
3. Analytische Messungen bleiben gute erste Hypothesen. Bei schlechtem Fit
   werden mehrere zulässige Startpunkte lokal weitergeführt. Der Suchzweig darf
   vorübergehend schlechter sein; der gespeicherte beste gültige Stand bleibt
   erhalten. Nur eine Umordnung derselben erschöpften Prüfliste genügt nicht.
4. Alle tatsächlichen Renderkandidaten werden gemeinsam dedupliziert und
   protokolliert. Rastercache und modellabhängige Bewertung sind getrennt:
   derselbe Rasterentwurf kann in mehreren Stufen verschiedene Verluste haben.
   Der Renderhash enthält echte Kandidaten, niemals bloss den Seed.
5. Zwischenstufen arbeiten weiterhin mit ihren Masken-/Bauteilverlusten. Eine
   dort bestandene Prüfung darf keinen kompletten Erfolg auslösen. Nur das
   vollständige SVG mit voller Beschreibung, Modellprüfung und Pixel-/Kontur-
   sowie gegebenenfalls lokalen Überdeckungsprüfungen erhält `passed`.
6. Die Dispatch-Schicht darf **nicht allein bei `result is not None` aufhören**.
   Im aktuellen Non-Composite-Pfad können Spezialfits ein Ergebnis liefern,
   obwohl `validated_result(...)` keine Freigabe erteilt hat; danach erfolgt
   trotzdem ein früher Return. `draft` muss als bester Entwurf aufgehoben werden,
   während weitere zur Beschreibung passende Modelle innerhalb des verbleibenden
   Budgets geprüft werden. `unsupported` darf keine künstliche Ersatzform liefern.

## Umstellung der übrigen Pfade

Die drei übergreifenden Umbauten sind als offene, aufeinander aufbauende
[Arbeitspakete mit Abnahmekriterien](../../../docs/next_arbeitspakete_2026-11-21_gemeinsame_suchsteuerung.md)
und als `SEARCH-ROUTES-01` bis `SEARCH-ROUTES-03` in der
[Aufgabenliste](../../../docs/open_tasks.md) festgehalten.

| Priorität | Konkreter Umbau | Verbindliche Abnahme |
| --- | --- | --- |
| 1 | Ergebniszustände und gemeinsamen Kontext an den produktiven Dispatch anbinden; frühe Returns bei blossen Entwürfen ersetzen | Ein schlechtes erstes Modell blockiert ein besseres zweites nicht. Ein früher guter Stand überlebt schlechtere spätere Zweige. Alle Arbeit bleibt im selben Budget. |
| 2 | Die 19 eigenen Fit-Schleifen über `ModelSpec` an `_register_steps`/Scheduler anbinden; vorhandene Messungen als erste Hypothese übernehmen | Pro Modell ein unabhängiger Positivfall, ein gültiger schlechter Start mit nachgewiesenen anderen Geometrien und ein unmöglicher Negativfall. Bisherige Modell-/Teilprüfungen bleiben verbindlich. |
| 3 | Analytische Kernstufen mit explizitem `scope` und Parameterrollen ausstatten; blockierte Portfolio-Stufen nicht pauschal öffnen | Maskierte Zwischenfits erhalten Seed/Deduplizierung, können aber keinen vollständigen Erfolg melden. Vollständige Fits erhalten echte alternative Startzweige. |
| 4 | Semantische Element-Hooks und Composite-Hypothesen an Kontext und Journal anbinden | Tatsächlich unterschiedliche zulässige Geometrien bei begrenztem Arbeitsumfang; keine Variation erst nach erfolgreicher Prüfung. Gleicher Seed und gleiche Arbeitsmenge reproduzieren die Folge. |
| 5 | SVG-Bauteile: Top-k-Matches und mehrere erlaubte Ebenenfolgen gemeinsam durchsuchen | Mehrdeutige lokale Platzierung wird am Gesamtbild gelöst. Explizite Platzierung und Ebenen bleiben fest. Donorfarben/-formen werden nicht verändert. |
| 6 | Alle produktiven Einstiege in einer gemeinsamen Testmatrix absichern | GUI frisch, GUI Vorlage, CLI einzeln, Batch, Katalog-/Workbench-Worker und Plan-B reichen denselben Seed weiter. Jeder aktive Suchpfad weist tatsächliche Renderarbeit oder einen konkreten Grund ohne Sucharbeit aus. |

Die Inventarliste im Manifest benennt für jeden Einstieg Datei und Funktion.
Die dort als `custom_fitter` klassifizierten Funktionen sind die konkrete
Migrationsliste für Priorität 2. Eine Umstellung durch zufälliges Ändern
beliebiger SVG-Knoten würde diesen Vertrag verletzen.

## Verhaltenstests und Grenzen dieses Prüfstands

Bereits ausgeführt:

- 40 Tests für den neuen Pfadvertrag, Vorlagenausrichtung, bestehende Seed-
  Weitergabe und das Zweiwegventil bestanden.
- 167 Tests für CLI, alten RNG, Beschreibungssprache, SVG-Bauteile und
  Konvertierungspersistenz bestanden.
- 32 Tests für die gemeinsame Suchplanung, Suchbots, den alten RNG und die
  vorige allgemeine Beschreibungsregistrierung bestanden.
- Bild-ID-Nullprüfung und Whitespace-Prüfung der hier geänderten Dateien bestanden.

Der neue Testblock prüft den vollen Seed bis `2^64-1`, Portfolio und Legacy,
Seed trotz `allow_portfolio=False`, tatsächlich verschiedene Geometrien bei
Vorlagen-Fehlversuchen, identische Wiedergabe mit gleichem Seed, Weitergabe über
die öffentliche Vorlagenfunktion und die Korrektur einer falschen roten
Flächenfarbe. Das Laufzeitbudget wird dabei nicht verlängert.

**Nicht behauptet:** Jeder der 60 statisch erfassten Einstiege sei schon mit
mehreren Seeds und allen Bildvarianten durchgetestet oder vollständig migriert.
Die Untersuchung benennt insbesondere die 19 eigenen Optimierer und die noch
ausstehenden Ergebnis-/Dispatcher-, Composite- und Bauteiladapter. Die
beschriebene Gesamtarchitektur ist ein konkreter Erweiterungsplan, keine bereits
vollständig ausgeführte Umstellung.

```powershell
.venv/Scripts/python.exe tools/audit_search_routes.py
.venv/Scripts/python.exe -m pytest tests/test_search_route_contracts.py tests/test_sample_alignment.py tests/test_seed_search_effect.py tests/test_two_way_valve_description.py -q
.venv/Scripts/python.exe -m pytest tests/detailtests/test_cli_helpers.py tests/detailtests/test_conversion_random_helpers.py tests/test_description_language.py tests/test_svg_components.py tests/test_conversion_persistence.py -q
.venv/Scripts/python.exe -m pytest tests/detailtests/test_conversion_random_helpers.py tests/test_conversion_search_scheduler.py tests/test_conversion_search_bots.py tests/test_description_registration_search.py -q
```
