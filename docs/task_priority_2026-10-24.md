# Aufgaben nach absteigender Wichtigkeit (24.10.2026)

Basis: [verbindliche Schwächenprüfung](weakness_review_2026-10-23.md) und alle **52 offenen Checkboxen** in [open_tasks.md](open_tasks.md) am Ausgangscommit `0927496bb`.

Die Reihenfolge zwischen den sechs Gruppen ist verbindlich. Innerhalb einer Gruppe gilt die hier angegebene Arbeitsreihenfolge; Quellenprüfungen erfolgen vor Verwendung der betroffenen Bilder. Reproduzierte neue Regressionen rücken sofort vor. Bereits erledigte Teilpakete werden nicht erneut aufgelistet.

Die 52 Checkboxen enthalten auch Arbeitsregeln und Sitzungsabläufe. Diese bleiben unten sichtbar, sind jedoch keine zusätzlichen Produktfunktionen. IDO-19/IDO-21 dienen bei Rang 3 weiterhin als Nachweisrahmen; sie haben keine eigene offene Checkbox in dieser Momentaufnahme.

## 1 / P0: Struktursuche und gemeinsame Komposition

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 1 | SEARCH-STRUCTURE-01 (P0, begonnen) | [Zeile 20](open_tasks.md) |
| 2 | GENERAL-SCENE-COMPOSITION-09 | [Zeile 114](open_tasks.md) |

## 2 / P1: Vollständige produktive Semantikabnahme

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 3 | SEMANTIC-COMPLETENESS-02 (P1) | [Zeile 21](open_tasks.md) |
| 4 | V5 – Semantische Textrepräsentation + Bedingungen einführen | [Zeile 899](open_tasks.md) |
| 5 | V6 – Iterativen Nachzeichnungsalgorithmus auf Semantik umstellen | [Zeile 905](open_tasks.md) |

## 3 / P1: Unabhängige reale Übertragung und praktischer Nutzen

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 6 | GENERAL-SCENE-REAL-05 | [Zeile 106](open_tasks.md) |
| 7 | IDO-P4 – Zielqualität am Holdout beweisen | [Zeile 850](open_tasks.md) |
| 8 | BENCHMARK-PRACTICAL-01 | [Zeile 65](open_tasks.md) |

## 4 / P2: Fehlende Operatoren und gemeinsame Fehlerursachen

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 9 | V2 – Bezierkurven-Erkennung ergänzen | [Zeile 881](open_tasks.md) |
| 10 | V3 – Farbfüllungen und Verläufe robust modellieren | [Zeile 887](open_tasks.md) |
| 11 | V4 – Überdeckungen/Z-Order explizit erkennen | [Zeile 893](open_tasks.md) |
| 12 | PB-LEARN-INVENTORY | [Zeile 91](open_tasks.md) |
| 13 | PB-POOL-2026-10-07 | [Zeile 712](open_tasks.md) |
| 14 | CATALOG-SOURCE-REVIEW | [Zeile 120](open_tasks.md) |
| 15 | GE0305-TOOLS-SOURCE | [Zeile 219](open_tasks.md) |
| 16 | GE0306-TOOLS-SOURCE | [Zeile 299](open_tasks.md) |
| 17 | GE0022-BELL-SOURCE | [Zeile 348](open_tasks.md) |
| 18 | AC0411-PB-GREY | [Zeile 161](open_tasks.md) |
| 19 | AC0424-PB-GREY | [Zeile 172](open_tasks.md) |
| 20 | GE9033-PB-GREY | [Zeile 183](open_tasks.md) |
| 21 | AC0414-PB-GREY | [Zeile 196](open_tasks.md) |
| 22 | AC0421-PB-GREY | [Zeile 309](open_tasks.md) |
| 23 | AC0721-PB-GREY | [Zeile 468](open_tasks.md) |
| 24 | AC0413-PB-GREY | [Zeile 495](open_tasks.md) |
| 25 | GE9023-PB-STRESS | [Zeile 526](open_tasks.md) |

## 5 / P2: Komponenten- und Netzversuche

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 26 | COMPONENT-VALUE-02 | [Zeile 69](open_tasks.md) |
| 27 | NEURAL-ELEMENTS-01 | [Zeile 83](open_tasks.md) |
| 28 | V7 – Rückwärts-Training (Text → SVG → Raster → Rücktransformation) | [Zeile 911](open_tasks.md) |

## 6 / P3: Runtime, Kompatibilität und Test-/Betriebsrestarbeiten

| Rang | Aufgabe / Arbeitsregel | Quelle |
| --- | --- | --- |
| 29 | ARCH-RUNTIME-CONTEXT-01 | [Zeile 70](open_tasks.md) |
| 30 | SEARCH-DEADLINE-COMPAT | [Zeile 79](open_tasks.md) |
| 31 | ARCHIVE-WINDOWS-IO | [Zeile 471](open_tasks.md) |
| 32 | ARCHIVE-DRIFT-2026-10-10 | [Zeile 472](open_tasks.md) |
| 33 | Spalten verwenden: `Planned` → `Running` → `Review` → `Done` / `Blocked`. | [Zeile 3182](open_tasks.md) |
| 34 | Pro Session mindestens einen Block vollständig bis `Review` abschließen. | [Zeile 3183](open_tasks.md) |
| 35 | TB1 – Stabilisieren/Beheben von `blocking_conversion`-Tests | [Zeile 3710](open_tasks.md) |
| 36 | TB1-Sammelaufgabe – `blocking_conversion`-Tests wieder eingrünen | [Zeile 3727](open_tasks.md) |
| 37 | TB2 – Nicht ausführbarer Test (Umgebungsabhängigkeit) wieder aktivieren | [Zeile 3751](open_tasks.md) |
| 38 | TB3 – Nicht-blocking-Batterie vollständig abschließen (ohne Hänger/Timeout) | [Zeile 3757](open_tasks.md) |
| 39 | FP-R1: Kein Commit ohne dokumentiertes Testsignal (Befehl + Exit-Code + Kurzfazit). | [Zeile 3936](open_tasks.md) |
| 40 | FP-R2: Kein „gefühlt besser“ ohne Metrikvergleich (`vorher`/`nachher`). | [Zeile 3937](open_tasks.md) |
| 41 | FP-R3: Kein Vollbereichslauf ohne Timeout-Guard und Batch-Plan. | [Zeile 3938](open_tasks.md) |
| 42 | FP-R4: Jeder Arbeitstag endet mit einem 5-Zeilen-Log (Getestet, Ergebnis, Blocker, nächster Schritt, morgiger Startbefehl). | [Zeile 3939](open_tasks.md) |
| 43 | FP-D1-1: Baseline-Toolchain fixieren (`PYENV_VERSION=3.10.20`) und in Session-Log eintragen. | [Zeile 3943](open_tasks.md) |
| 44 | FP-D1-2: Baseline-Run ausführen (`pytest -q -rs` + TB-A3-Kurzlauf) und Logs unter `artifacts/converted_images/reports/` mit Datumspräfix ablegen. | [Zeile 3944](open_tasks.md) |
| 45 | FP-D1-3: Mini-Scorecard anlegen/aktualisieren (Anzahl Varianten, `semantic_ok`, `semantic_mismatch`, Timeout-Anteil, mittlere Laufzeit). | [Zeile 3945](open_tasks.md) |
| 46 | FP-D1-EXIT: Baseline vollständig reproduzierbar: gleiche Kommandos, vollständige Artefakte, keine manuelle Nacharbeit. | [Zeile 3946](open_tasks.md) |
| 47 | FP-D2-1: Baseline-Runs identisch wiederholen und auf Drift prüfen. | [Zeile 3950](open_tasks.md) |
| 48 | FP-D2-2: Abweichungen (wenn vorhanden) als konkrete Aufgaben in `docs/open_tasks.md` erfassen. | [Zeile 3951](open_tasks.md) |
| 49 | FP-D2-EXIT: Zwei aufeinanderfolgende Baseline-Läufe konsistent dokumentiert. | [Zeile 3952](open_tasks.md) |
| 50 | QR-2026-05-30-2: `AC0838_M.jpg` erneut konvertieren bzw. per Plan B verbessern, weil das vorhandene SVG-Paar die Review-Grenze überschreitet (`normalized_mse=0.04729276` > `0.045945679012345676`). | [Zeile 4433](open_tasks.md) |
| 51 | QR-2026-05-30-3: `AC0881_M.jpg` erneut konvertieren oder das fehlende SVG-Artefakt rekonstruieren, weil beim Review kein passendes SVG in den geprüften Konvertierungs-/Baseline-Pfaden gefunden wurde. | [Zeile 4434](open_tasks.md) |
| 52 | QR-2026-05-30-4: `AC0835_S.jpg` nach der nächsten AC08-/Plan-B-Rotation erneut beobachten, weil der Messwert knapp unterhalb der Review-Grenze liegt (`normalized_mse=0.04467485`). | [Zeile 4435](open_tasks.md) |

## Bearbeitung des höchsten Rangs

Branch: `codex/search-structure-island-groups-2026-10-24`.

Der jüngste abgegrenzte Lieferumfang von SEARCH-STRUCTURE-01 kombiniert mehrere
gleichfarbige Instanzen mit jeweils mehreren sichtbaren Inseln. Begrenzte
Gruppierungshypothesen teilen sich das bestehende Bild-/96-Zustände-Budget mit
der Edit-Suche. Zwölf unveränderte synthetische CLI-Fälle mit Rundung und hellen
Konturen verbessern sich von 0/12 auf 12/12.
[Umsetzung und Grenzen](next_arbeitspaket_2026-10-24_island_groups.md).
Die Gesamtaufgabe bleibt bis zur breiteren Komposition und unabhängigen realen Abnahme offen.
