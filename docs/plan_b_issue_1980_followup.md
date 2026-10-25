# Folgeaufgaben zu Plan-B-Issue #1980 (25.10.2026)

Das [GitHub-Issue #1980](https://github.com/MobyDickDick/ImageConverter/issues/1980)
verbindet den technischen Abbruch der Variantenvorbereitung mit einer noch
fehlenden Qualitätsabnahme. [PR #2067](https://github.com/MobyDickDick/ImageConverter/pull/2067)
enthält die technische Reparatur und ist zum Dokumentationsstand noch nicht
gemergt. Im Branch schließen Originalseed und Zusatzseed jeweils alle 17
CLI-Fälle ab; die alten Qualitätsprüfungen bestehen nur 3/17 bzw. 2/17 Fälle.
Diese Zahlen beschreiben die bisherige Prüfkette und keine validierte
Rekonstruktion der sichtbaren Quelle.

Die folgenden drei Aufgaben sind offen und in dieser Reihenfolge zu bearbeiten.
Sie konkretisieren die Quellenprüfung und gemeinsame Fehleranalyse innerhalb
der [bestehenden Prioritätsgruppe 4/P2](task_priority_2026-10-24.md).
Die Quellenprüfung ist Voraussetzung für jede neue Abnahme dieses Bildes.

## 1. PB-1980-REFERENCE: Referenzrasterisierung korrigieren und visuell abgleichen

**Befund:** `artifacts/samples/z_201.svg` enthält einen referenzierten rosa
Farbverlauf. Das bisherige Prüfraster zeigt einen weitgehend schwarzen Streifen.
Die Ursache der Abweichung ist noch zu isolieren; Gradientverweise und
Stildeklarationen gehören zur Prüfung, sind aber noch keine bewiesene Ursache.

- [ ] Das unveränderte SVG in einem unabhängigen SVG-fähigen Browser oder
  Renderer ansehen und mit dem Raster der Prüfkette vergleichen. Quelle,
  SHA-256, Renderer und Version, Abmessungen sowie Vergleichsbilder sichern.
- [ ] Den kleinsten reproduzierbaren Fehler isolieren und die allgemeine
  Rasterisierung korrigieren. Keine Sonderbehandlung nach Katalogname und
  keine manuelle Ersatzgrafik als vermeintliche Rendererreparatur einführen.
- [ ] **Abnahme:** Form, rosa Farbtöne, Verlaufsrichtung, Lage und Beschnitt
  stimmen bei Original und transformierten Kontrollen mit der unabhängig
  dargestellten Quelle überein. Einen fachlichen Regressionstest und anders
  benannte, unabhängige Gradienten-/Transformationskontrollen ergänzen;
  bestehende Renderfälle bleiben korrekt.

## 2. PB-1980-DESCRIPTION: Eigenständige, zutreffende Bildbeschreibung hinterlegen

**Abhängigkeit:** PB-1980-REFERENCE liefert die geprüfte visuelle Grundlage.
Die bisherige allgemeine Aufzählung gerader, gebogener und T-förmiger Rohre
beschreibt die konkrete Quelle nicht ausreichend.

- [ ] Die tatsächliche Form, Orientierung, Füllung, Verlaufsrichtung und
  gegebenenfalls vorhandene Konturen anhand der geprüften Quelle beschreiben.
  Keine nur für die Bildfamilie typischen, im Bild nicht vorhandenen Objekte
  verlangen und keine numerischen SVG-Koordinaten als Nachzeichnungsanleitung
  in die Beschreibung übernehmen.
- [ ] Die eigenständige Beschreibung in der maßgeblichen Katalogbeschreibung
  hinterlegen und verwendete Sidecars auf Widersprüche prüfen. Auswahl über
  `select_task` und den expliziten Replay müssen dieselben Bildaussagen liefern.
- [ ] **Abnahme:** Sichtbare Quelle und sämtliche Beschreibungsaussagen passen
  zusammen. Eine neue Replay-Version bewahrt Beschreibung, Beschreibungs- und
  Rasterhash, Seed sowie Budget; gekoppelte Varianten erhalten die Bildaussagen.
  Der bisherige Fehlerbeleg bleibt unverändert als Historie erhalten.

## 3. PB-1980-QUALITY: Verbleibende Fehler reproduzieren und allgemein beheben

**Abhängigkeiten:** PB-1980-REFERENCE und PB-1980-DESCRIPTION sind abgenommen;
die technische Duplikatreparatur aus PR #2067 ist im verwendeten Stand enthalten.

- [ ] Mit den korrigierten Eingaben und dem vollständigen Originalseed
  `347146220485913939`, 64 Iterationen und 60 Sekunden je CLI-Fall einen neuen
  Ausgangslauf sichern. Neue Referenzwerte ausdrücklich von den alten
  3/17- und 2/17-Messungen trennen; sie sind keine direkt vergleichbare Baseline.
- [ ] Verbleibende Fehler nach Ursache zuordnen und mindestens zwei überprüfbare
  Lösungshypothesen unter protokolliertem Budget vergleichen. Änderungen an
  Beschreibung, Renderer und Konvertierungsalgorithmus getrennt nachweisen.
- [ ] Allgemeine Korrekturen aus Raster und Beschreibung umsetzen; keine
  Dateinamenpfade oder Referenz-SVG-Vorlagen in der Konvertierung verwenden.
- [ ] **Abnahme:** Original plus alle 16 tatsächlich verschiedenen Varianten
  bestehen über die echte CLI die unveränderten Qualitäts- und Komplexitätsgates.
  Die Bildaussagen werden zusätzlich visuell bzw. objektbezogen geprüft.
  Zusatzseed `817263`, unabhängige Formen/Farben/Anordnungen und fachliche
  Negativkontrollen ergänzen. Referenz-SVG-Zugriffe bleiben gesperrt; Laufzeit,
  Suchbudget, Renderzahlen und bestehende Regressionen sind nachzuweisen.

Ein vollständig ausgeführter Prozess, ein reparierter Renderer oder eine
korrigierte Beschreibung allein schließen die Qualitätsaufgabe nicht ab.
Bleiben Fälle erfolglos, werden sie mit Ursache und Belegen offen ausgewiesen.

## Umgang mit dem GitHub-Issue

#1980 wird als gemeinsamer Nachweis und Aufgabenanker behalten und auf die
drei oben genannten offenen Schritte ausgerichtet. Die ursprüngliche
automatisch erzeugte Evidenz bleibt erhalten; ihre Checkliste und Messwerte
sind historisch. Löschen würde die Reproduktionsdaten und Querverweise
verlieren, ohne einen Fehler zu beheben. Das Issue wird erst nach Abnahme der
drei Aufgaben und Übernahme der zugehörigen Änderungen geschlossen.

Die [bisherigen Replays und technischen Nachweise](../artifacts/evaluation/raster_variations_issue_v1/README.md)
bleiben gültige Belege für den damaligen Ausführungsfehler. Neue Referenz- und
Qualitätsnachweise ersetzen diese Historie nicht.
