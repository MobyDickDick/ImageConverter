# AP 1 – Isolierter Konvertierungskern

Ausgangsstand: ace79edf61f3fa6bd8c2b63de0f5a1a4ff7fdc5f.
Grundlage: AP0_Architekturanalyse_ImageConverter.md, Abschnitt 8.

## Schnittstelle

```python
import cv2
from src.exploratory import convert

image = cv2.imread("bild.png")
result = convert(image, description="", seconds=300)
print(result.stop_reason, result.evaluated, result.quality, result.errors)
if result.best is not None:
    from pathlib import Path
    Path("draft.svg").write_text(result.best.svg, encoding="utf-8")
```

Synchron, ohne Worker, ohne CLI/GUI-Änderung. BGR uint8. Adapter verwenden
das bestehende In-process-Rendering und die bestehende Vollbildbewertung.
Ein Kandidatenanbieter erhält Bild und Beschreibung und liefert SVG-Kandidaten.
Mehrere Anbieter werden abwechselnd abgefragt; Fehlschläge bleiben lokal.
Der kleine rasterbasierte Startanbieter liefert Rechteck und Ellipse bzw.
eine einfarbige Fläche bei tatsächlich einfarbigem Raster. Er ist nur eine
Baseline, kein vollständiger Hypothesengenerator. Die Beschreibung blockiert
diesen Anbieter nicht; sie wird in AP 1 noch nicht interpretiert.

## Ergebnisvertrag

Der beste gemessene native Vektorentwurf bleibt erhalten, auch bei ungenügender
Pixelqualität. Pixel-Freigabe und semantische Freigabe sind getrennt; released
bleibt in AP 1 immer False. Ausgabe erfolgt bewusst durch den Aufrufer.
Kandidaten mit eingebetteten Rasterbildern oder nicht unterstützten SVG-Elementen
werden abgelehnt. Nur einfache selbstenthaltene SVG-Grundformen sind vorgesehen.
Die Qualitätsmetrik bevorzugt zuerst bestandene Pixelgrenzen, dann den
vorhandenen Vektor-Score.

Die Zeitgrenze ist kooperativ, kein hartes Prozesslimit. Ein laufender Renderer
oder Anbieter kann überziehen; ein bereits ausgewerteter Entwurf bleibt erhalten.
Das Kandidatenlimit zählt auch Duplikate. Keine künstliche Wartezeit bei
erschöpften Quellen. Fehler, Zeit, Kandidaten, Render-Aufrufe und Bewertungen
werden getrennt erfasst. Renderings zählt Aufrufe, auch fehlgeschlagene.

## Abnahme und Grenzen

Tests: python -m pytest tests/test_exploratory_ap1.py -q

Die Tests decken optionale Beschreibung, Anbieterfehler, konkurrierende
Kandidaten, Duplikate, Budget, Entwurfserhalt, Rasterpayload-Ablehnung,
fehlende semantische Freigabe sowie die bestehenden Renderer/Metriken ab.
**Erfolgreiche Testabnahme, am 28. November 2026 durch den Anwender gemeldet:**
Unter Windows mit Python **3.10.11** bestanden alle **neun Tests in 12,25 Sekunden**,
einschliesslich des realen Renderings und der Qualitätsmessung. Damit ist die
AP-1-Testabnahme für diese Umgebung bestätigt. Diese historische Ausführung
wurde vom Anwender berichtet; ein zugehöriger CI-Link oder ein Testprotokoll
liegt dieser Meldung nicht bei. Sie wurde im Rahmen von AP 2 nicht lokal wiederholt.
Der Workflow `Exploratory acceptance` prüft AP 1 und AP 2 künftig gemeinsam auf
GitHub Actions unter Windows und Linux mit Python 3.10.11 und sichert JUnit-Berichte.

AP 2 ergänzt die variable Szenenrepräsentation; siehe
[AP2_Flexible_geometrische_Repraesentation.md](AP2_Flexible_geometrische_Repraesentation.md).
AP 3–8 bleiben offen: insbesondere Wahrnehmung, Mutationen,
echte 300-Sekunden-Exploration, semantische Hinweise, persistente Diagnose,
Generalisierung und CLI/GUI-Integration. AP 0 ist nicht vollständig abgenommen.
Keine Legacy-Datei geändert.
