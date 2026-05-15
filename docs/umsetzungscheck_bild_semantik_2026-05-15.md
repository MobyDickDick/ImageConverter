# Umsetzungscheck zur Zieldefinition (2026-05-15)

## Zielbild (aus Anforderung)

Eingabe:
1. JPEG-Datei
2. Sprachliche (ggf. formalisierte) Bildbeschreibung

Verarbeitung:
1. Bildelemente aus Beschreibung ableiten/suchen
2. Elemente mit den beschriebenen Bedingungen nachzeichnen
3. Ergebnis gegen Vorlage vergleichen
4. Iterativ verbessern bis
   - optimale/gute Lösung erreicht ist, **oder**
   - erkannt wird, dass keine gute Lösung erreichbar ist

Wichtige Negativbedingung:
- Im ImageConverter sollen **keine bildspezifischen Angaben dauerhaft hinterlegt** sein.

Schlechte Lösung:
- Fehlermass schlechter als definierte „gute“ Lösungen
- oder Dimensions-/Seitenverhältnis-Mismatch zur Vorlage

## Ist-Stand-Abgleich

### 1) Eingabe: JPEG + sprachliche Beschreibung

**Teilweise erfüllt.**
- JPEG als Eingabe ist Standardfall im aktuellen Workflow.
- Beschreibungen werden über einen separaten Beschreibungspfad übergeben (z. B. XML), also grundsätzlich als zweiter Input-Kanal unterstützt.
- Zusätzlich existiert bereits ein formalisiertes semantisches Beschreibungsmodell (JSON-Schema v1).

Bewertung: **gut vorbereitet**, aber noch kein einheitlicher „JPEG + Beschreibung“-Contract als klarer API-Standard dokumentiert.

### 2) Keine Ablage bildspezifischer Angaben im Converter

**Nicht erfüllt (kritische Lücke).**
- Der aktuelle Stand nutzt weiterhin dateiname-/familienbezogene Pfade und Heuristiken (u. a. AC08-Familien, Preservationsets, Beschreibungsfragmente in Report-Artefakten).
- Damit besteht mindestens indirekte Kopplung an konkrete Bildklassen statt rein beschreibungsgetriebener, allgemein gültiger Inferenz.

Bewertung: **Hauptabweichung zur Zielvorgabe**.

### 3) Beschreibung → Bildelemente + Bedingungen

**Teilweise erfüllt.**
- Die V5-Spezifikation definiert Objekte, Relationen und Constraints als formale Semantikschicht.
- V6 definiert die Nutzung dieser Semantik in einer mehrzieligen Optimierung.
- In der dokumentierten Praxis gibt es jedoch noch signifikanten Altpfad-Anteil über heuristische/legacy-nahe Optimierung und testspezifische Variantensteuerung.

Bewertung: **architektonisch vorhanden**, aber noch nicht vollständig als alleiniger Hauptpfad durchgezogen.

### 4) Iterativer Vergleich gegen Vorlage bis optimal / nicht erreichbar

**Weitgehend erfüllt, aber Schwellwert-Policy unvollständig.**
- Iterativer Optimierungs- und Vergleichsprozess mit Konvergenz-/Stagnationskriterien ist vorhanden.
- „Nicht erreichbar“ wird teilweise über Timeouts/Budgets/Stagnation erkannt.
- Eine einheitliche, explizit versionierte „Good-enough“-Policy (pro Klasse/gesamt), gegen die Fehlermass formal geprüft wird, ist aktuell noch nicht stringent als Gate standardisiert.

Bewertung: **funktional weit**, aber Governance der Abbruch-/Qualitätsschwellen noch zu schärfen.

### 5) Dimensions-/Seitenverhältnis-Konsistenz als harte Qualitätsbedingung

**Teilweise erfüllt.**
- Canvas- und Größenangaben sind im Semantikmodell vorgesehen.
- Ein explizites globales Hard-Fail-Kriterium „Dimensionen passen nicht zur Vorlage ⇒ schlechte Lösung“ ist als durchgehendes Gate noch nicht klar zentralisiert.

Bewertung: **konzeptionell vorhanden, operativ zu härten**.

## Priorisierte Aufgaben zur Zielannäherung

## P0 – Zwingend (Architektur- und Qualitätskern)

1. **Input-Contract v1 fixieren**
   - Einheitliches Inputformat: `{image_path, semantic_description}`
   - Adapter für bestehende XML-Beschreibungen auf V5-JSON
   - Klare Fehlermeldung bei fehlender/inkonsistenter Beschreibung

2. **Bildspezifische Wissensentkopplung**
   - Inventur aller dateiname-/familienabhängigen Heuristiken
   - Kennzeichnung „deprecated: image-bound logic"
   - Ersatz durch beschreibungs- und constraint-getriebete Logik

3. **Good-Solution-Gate v1**
   - Versionierte Schwellwerte für `error_per_pixel`, `semantic_score`, `dimension_match`
   - Statusmodell: `good`, `suboptimal`, `not_reachable`
   - Einheitliche Entscheidung in Pipeline + Report

4. **Dimension-Hard-Constraint**
   - Harte Regel: Abweichung bei Breite/Höhe/Seitenverhältnis über Toleranz => `suboptimal` oder `not_reachable`
   - Explizite Aufnahme in die globale Zielfunktion und den Final-Validator

## P1 – Hoch (Operationalisierung)

5. **Semantik-first Execution-Mode**
   - Feature-Flag „semantic-only“ (ohne bildspezifische Legacy-Helfer)
   - Vergleichsläufe gegen bisherigen Mischmodus

6. **Nicht-Erreichbarkeit robust machen**
   - Einheitliche Gründe: `stagnation`, `budget_exceeded`, `dimension_violation`, `semantic_conflict`
   - Reproduzierbare Exit-/Report-Codes

7. **Benchmark-Set ohne Sonderwissen**
   - Repräsentatives Sample-Set mit nur Beschreibung + JPEG
   - Nachweis, dass Ergebnisse ohne bildspezifische Hinterlegung stabil bleiben

## P2 – Mittel (Nachvollziehbarkeit und Wartung)

8. **Dokumentierte Metrik-Hierarchie**
   - Primär: semantische Korrektheit + Dimensionstreue
   - Sekundär: Pixel-/Farbfehler

9. **Taskboard-Verankerung**
   - Aufgaben in `docs/open_tasks.md` mit klaren Akzeptanzkriterien und Exit-Bedingungen

## Akzeptanzkriterien für „zielkonform“ (Definition of Done)

- Converter akzeptiert als Pflichtinput genau: JPEG + Beschreibung (formalisiert zulässig).
- Keine dateiname-/bildspezifische Regel mehr auf dem Hauptpfad.
- Ergebnisstatus ist deterministisch einer der drei Zustände: `good`, `suboptimal`, `not_reachable`.
- Dimensions-/Seitenverhältnisprüfung ist hartes Qualitätskriterium.
- Alle Entscheidungen werden mit Metriken und Grund im Report ausgewiesen.
