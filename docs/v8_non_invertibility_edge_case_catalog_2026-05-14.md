# V8 – Grenzfallkatalog für Nicht-Invertierbarkeit (v1)

Datum: 2026-05-14

## Ziel
Explizit dokumentieren, wann die Rücktransformation (Raster/semantische Beschreibung → eindeutige SVG-Szene) prinzipiell mehrdeutig oder nicht invertierbar ist.

## Failure-Mode-Katalog (v1)

| ID | Failure-Mode | Kurzbeschreibung | Warum nicht invertierbar? | Empfohlene Zusatzbedingungen |
|---|---|---|---|---|
| FM-01 | Vollständige Verdeckung eines Verbindungselements | Griff/Steg liegt komplett hinter Vordergrundobjekt | Geometrie und Existenz sind aus Rasterdaten nicht beobachtbar | Pflicht-Constraint `continues_behind` + Minimalform (z. B. Linie/Bogen) |
| FM-02 | Symmetrie-Mehrdeutigkeit | Spiegel- oder Rotationslösung erzeugt nahezu identisches Raster | Mehrere Parameterbelegungen mit gleicher Fehlerfunktion | Ankerpunkt + Orientierungsregel (links/rechts, oben/unten) |
| FM-03 | Topologie-Kollision bei dünnen Strukturen | Dünne Linien/Brücken kollabieren bei Rasterisierung | Konnektivität geht verloren (verbunden vs. getrennt unklar) | Mindeststrichbreite + Topologie-Constraint im Semantiklayer |
| FM-04 | Text-vs.-Geometrie-Verwechslung | Einzelzeichen ähneln primitiven Formen | Gleiche Pixel können als Glyphen oder Shapes erklärt werden | OCR-Confidence + erlaubtes Label-Vokabular |
| FM-05 | Gradient-/Flat-Fill-Äquivalenz | Weiche Verläufe sind bei Auflösung/Kompression kaum trennbar | Mehrere Farbmodelle sind visuell äquivalent | Mindest-DeltaE-Schwelle + fester Gradient-Model-Selektor |
| FM-06 | Alias-/Quantisierungsartefakte | Treppeneffekte verändern lokale Kantenlage | Subpixel-Geometrie nicht eindeutig rekonstruierbar | Supersampling-Rendervergleich + Geometrie-Regularisierung |
| FM-07 | Mehrfachobjekte mit identischer Farbe/Layer | Grenzen zwischen benachbarten Objekten verschwinden | Objektzahl und Segmentgrenzen sind mehrdeutig | Objektanzahl-Constraint oder Separationsanker |
| FM-08 | Unbeobachtbarer Start-/Endpunkt bei offenen Pfaden | Pfadenden liegen außerhalb/unter Verdeckung | Unklare Parametrisierung derselben sichtbaren Teilkurve | Sichtbarkeitsmaske + explizite Endpunktconstraints |

## Zuordnungsvorlage für Fehlschläge
Jeder neue Fehlschlag soll mindestens enthalten:

1. `failure_mode_id` (aus FM-01..FM-08)
2. `scene_id`/Referenzdatei
3. Kurze Evidenz (welche Beobachtung die Mehrdeutigkeit zeigt)
4. Gewählte Zusatzbedingung(en)
5. Ergebnis nach Constraint-Anwendung (`resolved`/`unresolved`)

## Mini-JSON-Schema für Gap-Reports

```json
{
  "scene_id": "ACxxxx_variant",
  "failure_mode_id": "FM-01",
  "evidence": "connector fully hidden behind circle",
  "recommended_constraints": ["continues_behind", "connector_min_length"],
  "resolution_status": "resolved"
}
```

## Abnahmekriterium (V8)
V8 gilt als erfüllt, wenn jeder neu dokumentierte Rücktransformations-Fehlschlag einem bekannten Failure-Mode (FM-01..FM-08) zugeordnet ist oder als neuer FM mit Begründung ergänzt wird.
