# ImageConverter CLI

Die primäre CLI wird als Python-Modul gestartet:

```bash
python -m src.imageCompositeConverter --help
```

## Häufige Aufrufe

### Tatsächlichen Komponentenbeitrag messen

`--disable-search-bot fine_coordinates` schaltet genau diesen Bot im adaptiven
Portfolio ab. Der Schalter ist für mehrere Bots wiederholbar; die sechs Namen
stehen in `--help`. `--no-component-observation` deaktiviert die zusätzlichen
Detailzähler. Der überwachte Worker dokumentiert die tatsächlich angewendeten
Schalter in `reports/<name>_components.jsonl`. Qualitätsprüfungen bleiben aktiv.

`python -m tools.run_component_value --output-dir .tmp/component-study --work-dir .tmp/component-study-work`
startet echte gepaarte Konvertierungen mit unabhängiger SVG-Prüfung statt einer
Bewertung mit Ersatzscores. Protokoll, Grenzen und Abnahme:
[COMPONENT-VALUE-01](next_arbeitspaket_2026-10-18_component_value.md).

### Durchgängiges Bildbudget

Die reguläre `semantic-only`-CLI führt Bildversuche einschließlich der finalen
Qualitätsmessung in überwachten Prozessen aus. Prozessstart und Wiederholungen
zählen zum Bildbudget: normalerweise 60 Sekunden, bei spätem gemessenem
Fortschritt höchstens 120 Sekunden. Blockierte Renderkinder werden mit beendet;
vollständig geprüfte Zwischenstände können erhalten bleiben. Rankings und
Übersichten verwenden bereits gemessene Werte und PNGs.

`--isolate-conversion` ist in diesem Pfad voreingestellt.
`--no-isolate-conversion` aktiviert den bisherigen direkten Entwicklungsablauf.
Der historische `standard`-Kompatibilitätsmodus hat weiterhin keine neue harte
Prozessgarantie. Geltungsbereich, Bereinigungszeit und Nachweise:
[Überwachte Bildbudgets](next_arbeitspaket_2026-10-18_search_deadline.md).

`reports/<name>_timing.jsonl` trennt Prozessstart, Workerbereitschaft, laufende
Aufsicht und Prozessabbau durch monotone Zeit, UTC-Zeit und Prozess-CPU-Zeit.
Die Zeitaufsicht benötigt einen laufenden und eingeplanten Hauptprozess;
Standby oder blockierende Betriebssystem-/Dateioperationen können die
verstrichene Gesamtzeit über das Budget hinaus verlängern. Nach Wiederaufnahme
wird das abgelaufene Budget geprüft. Diagnose und nachgewiesene Standbyfälle:
[Zeitüberlauf-Audit](next_arbeitspaket_2026-10-22_deadline_overrun_audit.md).

### Alternative Suchwege und Fortschritt

`--search-mode portfolio --search-policy adaptive` ist voreingestellt. Unterstützte analytische Modelle
probieren bei verfehlter lokaler Pixelprüfung zusätzliche Suchwege aus. Die
Kurztextregistrierung vergleicht außerdem normale/fette Schrift und gemeinsame/
einzeln positionierte Zeichen. `--search-mode legacy` deaktiviert die zusätzlichen
Parametersuchen für eine Ablation.

Ein früh zufriedenstellender, semantisch geprüfter Fit beendet die angeschlossene
Suche. Stagnation führt zum Suchwegwechsel und zum Ende weiterer ergebnisloser
Arbeit. Deutlicher später Fortschritt erlaubt zusätzliche Zeit: standardmäßig
60 Sekunden regulär, höchstens 120 Sekunden aktive Bildzeit über angeschlossene
Modelle und Wiederholungen. `--search-seconds` und `--search-max-seconds` passen
die Grenzen an. `--search-policy fixed` verwendet den bisherigen festen Ablauf.
Im adaptiven Modus teilen sechs Such-Bots ihre Verbesserungen und deaktivieren
erfolglose Arbeiter. Bereits geprüfte Parameter und deaktivierte Bots bleiben
für Wiederholungen desselben Bild-/Modellstarts erhalten. Das gemeinsame Budget
wird dadurch nicht erhöht. Ablauf und Grenzen:
[Kooperatives Bot-Modell](bot_conversion_search_2026-10-18.md).

```powershell
python -m src.imageCompositeConverter EINGABE --descriptions-path BESCHREIBUNGEN.xml --output-dir AUSGABE --start ERSTES --end LETZTES --search-seed 42 --search-budget 384
```

Ohne expliziten Seed wird pro Aufruf ein neuer erzeugt. `--deterministic-order`
allein fixiert nur die Dateireihenfolge; für die neue Suche zusätzlich
`--search-seed` angeben. Zeitabhängige Abbrüche können je nach Rechner und Last
an anderer Stelle eintreten. Das Vorschlagsbudget gilt je Modell: im festen
Modus als Grenze, im adaptiven Modus als Basis mit höchstens vierfacher
Verlängerung bei spätem Fortschritt. Identische SVGs werden innerhalb eines Fits aus
einem Rendercache bewertet. `[Search]` und `AUSGABE/search/progress.jsonl`
zeigen Suchweg, Vorschläge, tatsächliche Renderprüfungen und Fehlerwerte.

Geprüfte Kurztextvarianten liegen unter `AUSGABE/search/validated/` mit ihren
Semantik- und Pixelstatus. Nur `--execution-mode standard` darf erfolgreiche
Strategien anhand von `strategy_memory.json` für spätere Suchen priorisieren.
`semantic-only` liest keine gespeicherte Erfahrung. Fertige SVGs werden durch
die neue Suche nicht als Vorlagen geladen. Grenzen und Lernprozess:
[Plan-B-Nachbearbeitung](plan_b_learning_workflow.md),
[UML-Diagramme](conversion_search_uml.md).
Regeln, Zeit-/Prozessgrenzen und Nachweise:
[Adaptive Suche](adaptive_conversion_search_2026-10-18.md).

### Katalogbereich konvertieren

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

### Einzelne Bereiche annotieren

```bash
python -m src.imageCompositeConverter \
  --mode annotate \
  --output-dir artifacts/annotated_images \
  --start AC0811 \
  --end AC0814
```

### Nachvollziehen, warum eine Konvertierung schlecht ist

Mit `--debug-trace` schreibt der Konverter zusaetzlich eine maschinenlesbare
JSONL-Ablaufspur nach `reports/conversion_debug_trace.jsonl`:

```bash
python -m src.imageCompositeConverter artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/debug-conversion \
  --start AC0811_L --end AC0811_L \
  --deterministic-order --debug-trace
```

Jede Zeile ist ein eigenstaendiges JSON-Objekt. Die Spur dokumentiert unter
anderem die tatsaechlich ausgewaehlten Dateien, Zufallsseed und Budgets,
inkrementell wiederverwendete Ergebnisse, Qualitaetsschwellen, den erkannten
Strategiemodus und die Zahl der Geometrieelemente. Fuer Template-Transfers
werden Anzahl der Spender, Annahme/Ablehnung, gewaehlter Spender, Rotation,
Skalierung und der Fehler vor/nach dem Transfer festgehalten. So ist sichtbar,
ob ein Bild neu analysiert, nur aus dem Cache uebernommen oder mangels einer
kompatiblen Verbesserung nicht von einer anderen Variante abgeleitet wurde.

Ein eigener Zielpfad kann direkt hinter der Option angegeben werden:

```bash
python -m src.imageCompositeConverter ... --debug-trace artifacts/test-evidence/my-run.jsonl
```

## Artefakt- und Log-Pfade

`artifacts/converted_images/` ist für erzeugte Bild-/SVG-/CSV- und Review-Artefakte reserviert. Neue Laufzeitlogs sollen nicht mehr unter `artifacts/converted_images/` abgelegt werden, damit synchronisierte Arbeitskopien wie `myCloud/imageConverter/artifacts/converted_image(s)` keine Logdateien enthalten. Für neue Nachweise bitte stattdessen `artifacts/test-evidence/*.log` verwenden und die zugehörige Zusammenfassung als Markdown daneben ablegen.

### Ein einzelnes Bild konvertieren und als Regression einfrieren

Für das schrittweise Abarbeiten einzelner Bilder gibt es einen dedizierten Wrapper,
der exakt eine Varianten-ID startet, deterministische Reihenfolge erzwingt und
Batch-Einzelfehler als Fehlercode zurückgibt:

```bash
python -m tools.convert_one_image AC0800_L \
  --input-dir artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/one-image-conversions \
  --iterations 64
```

Wenn die Konvertierung visuell abgenommen ist, kann derselbe Lauf die erzeugte
SVG-Datei zusammen mit dem Quellbild in die geschützte Satisfactory-Baseline
kopieren:

```bash
python -m tools.convert_one_image AC0800_L --freeze-baseline
```

`--freeze-baseline` ergänzt `artifacts/regression_baseline/satisfactory/variants.txt`
im Append-Modus. Dadurch prüft `./tools/run_satisfactory_regression_battery.sh`
bei späteren Änderungen automatisch, dass die neu konvertierte Version für alle
bereits eingefrorenen Varianten die gespeicherte `mean_delta2`-Qualität nicht
verschlechtert.
