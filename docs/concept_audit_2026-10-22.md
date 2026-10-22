# Welche früheren Konzepte inzwischen greifen

Geprüfter Ausgangsstand: `26cbde874` auf `main`, 22. Oktober 2026.
Arbeitsbranch: `codex/concept-audit-real-scenes-2026-10-22`.
Grundlage sind die im Repository erhaltenen Anforderungen, Konzepte, Runtime,
Tests und Messartefakte. Nicht im Repository dokumentierte frühere Gespräche
sind damit nicht vollständig rekonstruiert.

Die Vermutung stimmt teilweise: Seit der ursprünglichen Zielprüfung sind
mehrere Kernideen produktiv angeschlossen. **Es greifen noch nicht alle
Konzepte.** Einige alte Häkchen bescheinigten lediglich eine Spezifikation;
andere Untersuchungen endeten ohne belegten Zusatznutzen. Ein Schema, ein
erzeugter Bericht und eine echte Produktionsabnahme sind verschiedene Belege.

| Früher vorgeschlagene Idee | Heutiger Befund | Konkreter Beleg und verbleibende Lücke |
| --- | --- | --- |
| Nur Bild + eigenständige Beschreibung; keine gespeicherten Bildparameter als Laufzeitwissen | Im regulären `semantic-only`-Pfad umgesetzt und begrenzt geprüft | [Ursprüngliches Ziel](umsetzungscheck_bild_semantik_2026-05-15.md), produktive Rasterregistrierungen und Worker-Lesewächter. Der aktuelle Runtime-ID-Scanner findet null Katalogkennungen. Das beweist keine beliebige Generalisierung; der historische `standard`-Pfad bleibt ein anderer Umfang. |
| Grundformen erkennen und zu einer vollständigen Szene zusammensetzen | Greift für begrenzte Zusammensetzungen | [Szenenfusion](next_arbeitspaket_2026-10-20_scene_fusion.md), [Sichtbarkeit](next_arbeitspaket_2026-10-21_scene_visibility.md), [Verlaufspanels](next_arbeitspaket_2026-10-22_gradient_scene.md). Ein bis drei Kreise/Rechtecke, bestimmte Konturen, Überdeckungen und Verläufe; keine allgemeine Zerlegung beliebiger Symbole. |
| Gleichbedeutende Beschreibungen führen zu demselben fachlichen Ergebnis | Im dokumentierten Wortschatz nachgewiesen | [Sprachrobustheit](next_arbeitspaket_2026-10-22_semantic_robustness.md): zehn bekannte reale Familien; insgesamt 119/120 positive und 90/90 negative Versuche des endgültigen Codes. Kein Nachweis freien Sprachverständnisses. |
| Iterativ rendern, vergleichen und verbessern; bei Erfolg oder Stagnation stoppen | Produktiv umgesetzt | [Adaptive Suche](adaptive_conversion_search_2026-10-18.md), Scheduler und überwachte Budgets. Fehlende Ausgangsobjekte oder Topologien werden durch mehr Parameteriteration allein nicht ergänzt. |
| Mehrere Bots und alternative Suchwege kooperieren lassen | Technisch angeschlossen; Zusatznutzen bleibt teilweise unklar | [Komponentenversuch](next_arbeitspaket_2026-10-18_component_value.md): 375 echte Versuche rechtfertigen keine pauschale Entfernung oder allgemeine Nutzenbehauptung. `COMPONENT-VALUE-02` verlangt aktiv schwierige Fälle und neue Prüffamilien. |
| Kleines neuronales Netz zur Elementerkennung | Zweimal erprobt; produktive Abnahme nicht erreicht | [Erster Versuch](next_arbeitspaket_2026-10-19_neural_elements.md): kein zusätzlicher Erfolg. [Realer Folgeversuch](next_arbeitspaket_2026-10-19_neural_real_regions.md): analytisch 71/90, mit Netz 72/90; kein belastbarer End-to-End-Vorteil. Das Netz bleibt optional. |
| Gemeinsamer ImageDetector für beliebige neue Formen | Teilbausteine vorhanden, Gesamtziel offen | [ImageDetector-Plan](image_detector_development_branch.md): analytische Erkenner und Kandidatenverträge existieren. Freie Kurven, allgemeine Szenenwahl, Text/OCR und kalibrierte Unsicherheit sind nicht als durchgängiges Produkt abgenommen. |
| V1: Primitive-Inventar messbar machen | Schema-/Messgrundlage erfüllt | Die [vier historischen Referenzen](primitive_inventory_v1_baseline_2026-05-14.md) sind eine kleine Baseline. Ihre Zahlen sind keine aktuelle allgemeine Detektorquote. Neuere echte Szenenprüfungen haben einen eigenen begrenzten Umfang. |
| V2: quadratische/kubische Bézierkurven aus dem Raster mit Fehlerschranken fitten | Vollständiger Nachweis fehlt | [Strategie](v2_bezier_detection_strategy_2026-05-14.md) vorhanden. `_closed_catmull_rom_to_bezier_path` erzeugt Bézierpfade, erfüllt allein aber nicht den geforderten adaptiven Fit, die drei Fehlergrenzen und den Vergleich mit einer Polyline-Baseline. V2 wieder offen. |
| V3: Füllungen und allgemeine lineare/radiale Verläufe | Produktive Teilumfänge; ursprüngliche Abnahme offen | Native lineare Verläufe funktionieren in mehreren Registrierungen. Der allgemeine V3-Vertrag mit Stop-Auswahl, radialen Modellen und unabhängigem DeltaE-Vergleich zur Flat-Fill-Baseline ist dadurch nicht vollständig abgenommen. V3 wieder offen. |
| V4: Überdeckungsgraph und verdeckte Fortsetzungen | Begrenzte Tiefenrollen greifen; allgemeiner Vertrag offen | Native Sichtbarkeitsmodelle prüfen bestimmte Reihenfolgen. Ein allgemeiner beobachteter Layer-Graph mit `continues_behind` und realer Griff-/Verbindungsabnahme ist damit nicht belegt. V4 wieder offen. |
| V5: allgemeine semantische Szene als Objekte, Relationen und Constraints | Schema und begrenzte produktive Verträge; vollständiger Vertrag offen | Geometry-IR, typisierte Szenenbezüge und SVG-Zusicherungen sind produktiv. Nicht alle im V5-Schema beschriebenen Szenen sind durchgängige CLI-Eingaben mit nachgewiesener Rekonstruktion. V5 wieder offen. |
| V6: gemeinsame Mehrzieloptimierung mit Semantik, Pareto-Auswahl und Konvergenznachweisen | Teilprinzipien greifen; vollständige spezifizierte Abnahme fehlt | Rasterfit, lokale Qualitätsverluste und harte Semantikbedingungen existieren. Die ursprüngliche allgemeine Mehrziel-/Pareto-Abnahme ist nicht durch das Konzeptpapier nachgewiesen. V6 wieder offen. |
| V7: Text → SVG → Raster → Rückerkennung und Rückwärts-Training | Bisher nur JSON-Vergleich, kein vollständiger Kreislauf | `tools/evaluate_semantic_roundtrip.py` liest zwei JSON-Dateien und vergleicht IDs/Relationsschlüssel. Es startet weder Konverter noch Rastererkennung oder Training. V7 wieder offen. |
| V8: nicht eindeutige Rekonstruktion ausdrücklich dokumentieren | Grenzfallkatalog vorhanden | [Katalog](v8_non_invertibility_edge_case_catalog_2026-05-14.md) mit acht Fehlerarten. Seine Existenz belegt keine automatische Erkennung aller dieser Fehler im Produktionspfad. |
| Generalisierung durch Ablation und unbekannte reale Familien beweisen | Noch nicht vollständig erfüllt | IDO-19/IDO-21 verwenden weiterhin als `contract_fixture` gekennzeichnete Ersatzwerte. Neuere echte Abnahmen ersetzen diese offenen Gesamtaufgaben nicht. |
| Praktischen Nutzen, Arbeitsersparnis und kleinere Architektur belegen | Offen | `BENCHMARK-PRACTICAL-01`, `ARCH-RUNTIME-CONTEXT-01` und die Roadmap verlangen externe Verfahren, menschliche Zeitmessung bzw. die Ablösung globaler Runtime-Bindings. Zwei produktive Aufrufe von `_syncRemainingRuntimeBindings` bestehen weiterhin. |

## Neue direkte Gegenprobe

Der V7-Vergleicher erhält als Referenz einen Kreis mit ID `a`, Radius 10.
Der Kandidat enthält mit derselben ID ein Rechteck mit Breite 900 sowie ein
zusätzliches Textobjekt. Trotzdem meldet er `passed=true`: Er erfasst das
Zusatzobjekt zwar, berücksichtigt es aber ebenso wenig wie Geometrie und Typ
in seiner Pass-Entscheidung. Das ist ein reproduzierbarer Beleg für die
Begrenzung des Werkzeugs, keine Aussage über die unabhängigen Produktionsgates.

Die Eingaben und der vollständige Rückgabewert stehen in
`artifacts/evaluation/mixed_gradient_scene_v1/concept-probes.json`.
Die sechs Vision-Aufgaben V2 bis V7 sind deshalb mit konkreter Restabnahme
wieder geöffnet. Historische Konzepte und Messungen bleiben erhalten.

## Nächste dokumentierte Arbeit

Gemäß [Roadmap](product_roadmap.md) und dem offenen Paket
[GENERAL-SCENE-REAL-05](quality_review_tasks_2026-10-21.md#general-scene-real-05--übertragung-statt-weiterer-einzelfallpfade)
folgt die Übertragung vorhandener Primitive auf neue reale Zusammensetzungen.
Der separate Branch bearbeitet eine Verlaufsscheibe mit einem bzw. zwei
eingeschlossenen Rechtecken über denselben Raster-/Szenenweg. Umfang,
Vorher-/Nachher-Ergebnisse und Grenzen stehen im
[Arbeitspaket](next_arbeitspaket_2026-10-22_mixed_gradient_scene.md).

Die 379 archivierten Paare des Ausgangsstands sind weder 379 unabhängige
Familien noch eine aktuelle Erfolgsquote über alle 1.785 Katalogbilder.
Erfolgreiche Varianten, neue Zusammensetzungen und ein praktisch belegter
Gesamtnutzen werden weiterhin getrennt ausgewiesen.
