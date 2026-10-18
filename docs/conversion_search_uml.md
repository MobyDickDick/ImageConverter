# Bildkonvertierung und Lernschleife als UML

Stand: 2026-10-18. Die Diagramme skizzieren Verantwortlichkeiten und Abläufe;
sie behaupten keine automatische Unterstützung beliebiger Bildtopologien.
Die Mermaid-Blöcke sind direkt renderbare Sequenz-, Klassen- und Zustandsdiagramme.
Die Modellschleife zeigt Alternativen innerhalb angeschlossener Registrierungen.
Der Runtime-Dispatcher beendet einige Spezialpfade weiterhin früh; ein gemeinsamer
Vergleich aller unterstützten Formfamilien ist noch nicht umgesetzt.

Die drei Parametersuchwege sind ein heutiger Teilbaustein. Ein gemeinsames
60-Sekunden-Limit und eine erweiterbare Struktursuche sind als Ziel in der
[Verfahrensprüfung](conversion_search_review_2026-10-18.md) beschrieben und noch
nicht allgemein implementiert. `mermaid-diagram.png` im Projektstamm zeigt den
älteren Stand dieses Sequenzdiagramms.

## Konvertierung und alternative Suche: Sequenzdiagramm

```mermaid
sequenceDiagram
    actor User as Nutzer
    participant CLI
    participant Runtime
    participant Model as Beschreibungs- und Rastermodelle
    participant Search as Suchportfolio
    participant Renderer
    participant Gate as Lokale Prüfung
    participant Store as Sucharchiv
    User->>CLI: Raster + Beschreibung + Budget + optionaler Seed
    CLI->>Runtime: Konvertierung mit Suchkonfiguration
    Runtime->>Model: Passende Modelle aus Beschreibung und Raster bilden
    loop Unterstützte Modellhypothesen
        Model->>Search: Analytischer Start und bisherige Registrierung
        opt Restfehler und Portfolio aktiviert
            loop Drei Parametersuchwege innerhalb desselben Modells
                Search->>Renderer: Neue gültige Parameter rendern
                Renderer-->>Search: Raster
                Search->>Search: Verlust und Fehler prüfen, Dubletten vermeiden
                Search-->>CLI: Fortschritt, Prüfzahl, bester Fehler
                Search->>Store: Auch gescheiterte Versuche sichern
            end
        end
        Search-->>Model: Bester nicht verschlechterter Fit
        Model->>Gate: Kreis, Schriftkontur und zusätzliche Rasteranteile prüfen
        opt Lokale Semantik besteht
            Gate->>Store: Variante + getrenntes Pixelgate speichern
            opt Standardmodus und strenger Pixelpass
                Gate->>Store: Erfolgreiche Modellart zählen
            end
        end
    end
    Runtime-->>CLI: Beste zulässige Ausgabe
    CLI-->>User: SVG und Berichte
    Note over Store,CLI: semantic-only liest keine gespeicherten Vorlagen oder Strategiestatistik
    Note over Search,Runtime: Heutiger Teilbaustein: kein gemeinsames Zeitlimit und keine allgemeine Struktursuche
```

## Verantwortlichkeiten: vereinfachtes Klassendiagramm

Die Kästen repräsentieren überwiegend Python-Module, keine zusätzlich
implementierten objektorientierten Klassen.

```mermaid
classDiagram
    class CLI {
        parseArgsImpl()
        runMainImpl()
    }
    class SearchPortfolio {
        search_configuration()
        explore_parameters()
        ranked_models()
        store_validated_variant()
        progress()
    }
    class AnalyticRegistration {
        _register()
    }
    class ShortLabelDisk {
        fit_short_label_disk()
    }
    class Runtime {
        runNonCompositeIterationImpl()
        semanticBadgeRuntime()
    }
    class Evidence {
        progress_jsonl
        provisional_attempts
        validated_variants
        strategy_memory_json
    }
    CLI --> SearchPortfolio : Konfiguration
    CLI --> Runtime : Konvertierung
    Runtime --> ShortLabelDisk : passendes Modell
    ShortLabelDisk --> AnalyticRegistration : vier Textmodelle
    AnalyticRegistration --> SearchPortfolio : alternative Suchwege
    ShortLabelDisk --> SearchPortfolio : geprüfte Variante sichern
    SearchPortfolio --> Evidence : Belege und Statistik
```

`_register` wird auch von weiteren analytischen Formregistrierungen verwendet.
Andere Optimierer und frühe Spezialpfade sind noch nicht vollständig an das
Portfolio angebunden. Die ursprüngliche Pipeline besitzt weiterhin eigene
Parser-, Perception-, Geometry-IR-, Raster- und Qualitätsmodule.

## Fehlernachbearbeitung: Zustandsdiagramm

Dieser Prozess verbindet die vorhandene automatische Fehlererfassung mit der
dokumentierten Entwicklungsarbeit. Ursachenanalyse und Codekorrektur sind noch
keine unbeaufsichtigte Runtime-Funktion.

```mermaid
stateDiagram-v2
    [*] --> Gescheitert
    Gescheitert --> Erfasst: Fehlerbericht und Eingaben sichern
    Erfasst --> Reproduziert: Hashes, Seed, Budget und Code festhalten
    Reproduziert --> Ursache: Lokale und globale Prüfungen
    Ursache --> TechnischeReparatur: Ausführung defekt
    Ursache --> Hypothesen: Beschreibung oder Rekonstruktion falsch
    TechnischeReparatur --> Reproduziert
    Hypothesen --> Vergleich: Unterschiedliche Ansätze mit Budget
    Vergleich --> Hypothesen: Keine hinreichende Verbesserung
    Vergleich --> Abnahme: Allgemeine Korrektur
    Abnahme --> Hypothesen: Original, Varianten oder Regressionen verfehlt
    Abnahme --> Gesichert: Original, 16 Varianten, Holdouts und Bestand bestehen
    Gesichert --> [*]: Erkenntnis, Varianten und Regressionstest erhalten
```

Vorgehen, Befehle und Grenzen stehen im
[Nachbearbeitungsprozess](plan_b_learning_workflow.md).
