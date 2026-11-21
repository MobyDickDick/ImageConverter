# Arbeitspakete für eine gemeinsame Suchsteuerung

Stand: 21. November 2026. Die drei folgenden Umbauten erweitern die Korrektur der
wiederholten roten Rechtecke auf die übrigen produktiven Suchfamilien. Ihre
Umsetzung ist offen. Bereits korrigierte Seed-Verbindungen und die erweiterte
Vorlagenausrichtung sind im
[Untersuchungsbericht](../artifacts/evaluation/search_routes_2026-11-21/README.md)
getrennt dokumentiert.

Die Bestandsaufnahme umfasst 60 Einstiegsfunktionen, darunter gemeinsame Kerne
und bedingte Legacy-Einstiege. 19 Spezialfits besitzen eigene Optimierungsschleifen.
Das [Inventar mit Funktionen und Dateien](../artifacts/evaluation/search_routes_2026-11-21/manifest.json)
ist die Ausgangsliste für die Umstellung; es ist kein Laufzeitnachweis für alle
Bildvarianten.

Die Reihenfolge innerhalb dieses Vorhabens ist **AP 1 → AP 2 → AP 3**.
Die Budgetsteuerung wird mit dem bestehenden
[Vorhaben für adaptive Formmodelle](next_arbeitspakete_2026-11-21_adaptive_formmodelle.md)
abgestimmt, damit nicht zwei voneinander unabhängige Suchbudgets entstehen.

## AP 1 · Gemeinsame Suchsteuerung

**Kennung:** SEARCH-ROUTES-01. **Status:** Offen.

Ein Suchkontext pro Bild führt den vollständigen 64-Bit-Seed, die ursprüngliche
Deadline, das Renderbudget, den Kandidatenspeicher und das Versuchsprotokoll.
Er wird von CLI beziehungsweise Worker an alle Unterfits weitergegeben.
Verschiedene Modelle erhalten daraus reproduzierbare, benannte Zufallsfolgen.
Ein Modellwechsel eröffnet keine neue Profilzeit.

Jeder tatsächliche Renderkandidat erhält eine inhaltsgebundene Identität.
Rastercache und modellabhängige Bewertung bleiben getrennt. Zwischenstufen
werden als `intermediate`, vollständige Bildprüfungen als `full_scene`
gekennzeichnet. Beide verwenden denselben Kontext; nur die vollständige Prüfung
kann einen Konvertierungserfolg bestätigen.

**Abnahme:**

- Gleicher Seed, gleiche Eingaben und gleicher Arbeitsumfang reproduzieren die
  tatsächliche Kandidatenfolge. Andere Seeds erzeugen bei schlechten Fits
  nachweislich andere zulässige Geometrien, sofern Alternativen verfügbar sind.
- Das Protokoll enthält echte Renderzahlen, Fortschritt und konkrete Stopgründe.
  Ein Seed in Metadaten zählt nicht als Sucharbeit.
- Ein bereits gerenderter Kandidat wird aus dem Cache bedient. Modellwechsel,
  Neustarts und Zwischenstufen bleiben innerhalb des gemeinsamen Budgets.
- Die Weitergabe wird über frische GUI-Konvertierung, Vorlagenworker, CLI,
  Batch sowie Katalog-/Workbench- und Plan-B-Einstiege geprüft.

## AP 2 · Weitere Modelle nach schlechten Entwürfen prüfen

**Kennung:** SEARCH-ROUTES-02. **Status:** Offen. **Abhängigkeit:** AP 1.

Die Modellaufrufe liefern eindeutige Ergebniszustände: `passed`, `draft`,
`exhausted` oder `unsupported`. Der Dispatcher beendet die Suche nicht allein,
weil ein Modell ein Ergebnis ungleich `None` zurückgibt.

Ein schlechter Entwurf bleibt als bisher bester gültiger Stand erhalten.
Weitere zur Beschreibung passende Modelle werden im verbleibenden Budget
geprüft. Suchzweige dürfen vorübergehend schlechter werden; die gespeicherte
beste Version wird nur durch eine besser bewertete gültige Version ersetzt.
Die bestehenden Form-, Beschreibungs-, Pixel- und Modellprüfungen bleiben
verbindlich.

**Abnahme:**

- Ein schlechtes erstes Modell blockiert ein erfolgreiches zweites nicht.
- Ein guter früher Stand überlebt schlechtere spätere Suchzweige, Abbruch und
  Zeitlimit.
- Eine bestandene maskierte Zwischenprüfung wird nicht als vollständiger Erfolg
  veröffentlicht. Ein unlösbarer Fall bleibt korrekt ungenügend.
- Nicht unterstützte Beschreibungen erhalten keine erfundene Ersatzform.
  Identische gute Endergebnisse bei verschiedenen Seeds bleiben zulässig.

## AP 3 · Modellspezifische Adapter

**Kennung:** SEARCH-ROUTES-03. **Status:** Offen. **Abhängigkeit:** AP 1 und AP 2.

Jede Suchfamilie beschreibt ihre erlaubten Parameter, Grenzen, gekoppelten
Grössen, Farbzuordnungen und Modellprüfungen. Koordinaten, Winkel und Farben
erhalten passende Schrittweiten. Analytische Messungen bleiben erste
Hypothesen; zusätzliche Starts untersuchen zulässige Alternativen derselben
beschriebenen Konstruktion.

| Familie | Umstellung und verbindliche Grenzen |
| --- | --- |
| 19 eigene Spezialfits | Die als `custom_fitter` erfassten Funktionen schrittweise an gemeinsame Registrierung und Suchplanung anschliessen. Bestehende Teil-, Verbindungs- und Modellprüfungen übernehmen. |
| Analytische Registrierung | Parameterrollen und Zwischenstufen ausdrücklich kennzeichnen. Deaktivierte Portfolio-Worker nicht pauschal für maskierte Verluste freischalten. |
| Semantische und Composite-Suche | Zulässige Parameter- beziehungsweise Konturhypothesen über den gemeinsamen Kontext vergleichen. Eine zufällige Reihenfolge derselben erschöpften Liste reicht nicht aus. |
| SVG-Bauteile | Mehrere plausible Lokalisierungen pro Bauteil gemeinsam am Gesamtbild prüfen. Donorformen und -farben, explizite Platzierungen und vorgegebene Ebenenbeziehungen bleiben verbindlich. |

**Abnahme:**

- Pro migriertem Modell: ein unabhängiger Positivfall, ein schlechter Start mit
  nachgewiesener Suche anderer Geometrien und ein unmöglicher Negativfall.
- Vergleiche verwenden feste Ausgangsdaten, mehrere Seeds, unveränderte
  Qualitätsgrenzen und gleiche Zeit-/Renderbudgets.
- Bauteiltests enthalten mehrdeutige lokale Treffer, feste Positionen und
  vorgegebene Überdeckungen. Unzulässige Änderungen an Donoren werden abgelehnt.
- Das Inventar kennzeichnet je Einstieg die erfolgte Umstellung und die
  zugehörigen Verhaltenstests. Ein statisch erfasster Pfad gilt erst nach diesen
  Tests als abgenommen.

Stillgelegte Struktur-/Raster-Nachsuchen und automatischer Donortransfer werden
für die beschreibungsgetriebene Konvertierung nicht wieder aktiviert. Die
Beschreibung bestimmt weiterhin die vollständige erlaubte Elementliste.

## Nachführung

Die drei offenen Kennungen stehen auch in der [Aufgabenliste](open_tasks.md).
Bei Umsetzung werden dort und hier Status und Prüfbelege aktualisiert.
Der Untersuchungsbericht bleibt der Nachweis des Ausgangsbefunds; neue Abnahmen
werden als neue Prüfstände ergänzt.
