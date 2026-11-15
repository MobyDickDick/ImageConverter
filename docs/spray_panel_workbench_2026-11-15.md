# Plan-B-Luftbefeuchter: Diagnose und Korrektur der zwei fehlgeschlagenen Fälle

Untersucht wurde `C:\Users\marku\Desktop\plan-b-workbench.zip`.
Der Export enthält zwei abgeschlossene Fehlläufe (`original`, `probe_01`)
und einen begonnenen, abgebrochenen dritten Fall. Er enthält keine zwei
vollständig ausgeführten 17er-Batterien. Der Seed ist `3935970335737749794`.

## Ursachen

- Die bildspezifische, inzwischen korrigierte Beschreibung sagt
  „Queranschlüsse“. Der Sprühpanel-Fitter verlangte jedoch wörtlich „Düsen“.
  Damit wurde das passende Modell übersprungen und die generische Suche
  rekonstruierte unvollständige Rechteck-/Linienkompositionen. Die pauschale
  Ersetzung von `ue` durch `ü` hätte zusätzlich das Wort „Quer“ beschädigt.
- Die Prüfung für gestrichelte Strahlen verstand „gestrichelte hellgraue
  Linien“, aber nicht „gestrichelte graue Sprühstrahlen“.
- Die Referenz-SVG benutzt für ihre Sprühstrahlen gerade `path`-Elemente.
  MuPDF ignoriert deren Strichelung. Der private Renderweg korrigierte bislang
  nur native Rechtecke und Linien. Die exportierten Eingaberaster zeigten
  deshalb durchgezogene Strahlen, obwohl SVG und Beschreibung gestrichelte
  Strahlen vorgeben. Der anfängliche Kodierungsverdacht war dagegen ein
  Diagnose-Lesefehler; die UTF-8-Texte im ZIP sind korrekt.
- Bei der verkleinerten, verschobenen Variante verzerrte der dunkle Gehäuserand
  die Schwelle für Düsen. Eine schwache, auf zwei Pixelzeilen verteilte Düse
  verschwand aus der Erkennung: vier statt fünf Düsen. Bei `probe_02` wurden
  anfangs sogar nur drei ungleichmässig verteilte Gruppen beobachtet.
- Gehäuse und Innenrahmen wurden vor den Düsen und Sprühstrahlen angepasst.
  Nach deren Anpassung blieb für die Variante ein schlechter Kompromiss zurück:
  Hintergrundfehler 0,002371 und Rahmenfehler 0,002136 überschritten die
  unveränderte lokale Grenze 0,002. Die generische Erholungssuche verlor danach
  wieder Teile der zuvor erkannten Struktur.
- Das ursprüngliche Gesamtlimit betrug 60 Sekunden. Die Workbench reserviert
  davon nur 55 Prozent, also 33 Sekunden, für die erste Modellsuche. Ein
  vollständiger Suchlauf mit allen 15 einzeln angepassten Strichmustern kann
  dieses Budget überschreiten. Mehr Zeit allein behob den Strukturfehler nicht.

## Änderungen

Der Fitter akzeptiert jetzt auch Queranschlüsse und graue gestrichelte
Sprühstrahlen sowie die entsprechenden `ue`-Schreibungen. Explizite
Gegenaussagen bleiben ausgeschlossen. Nur der Gehäuseinnenbereich bestimmt
die Düsenschwelle; die Prüfung gleichmässiger Abstände bleibt erhalten.

Wenn nach dem vollständigen Einpassen ausschliesslich Gehäuse oder Rahmen die
Detailprüfung verfehlen, werden diese beiden Teile nochmals gegen die nun
eingepassten Vordergrundteile optimiert. Die Detailgrenze wird nicht angehoben.
Unvollständige oder vom Zeitlimit abgebrochene Ergebnisse gelten weiterhin
nicht als erfolgreich.

Der private Renderer materialisiert nun auch gestrichelte Pfade, die aus genau
einem geraden Segment bestehen: `M`/`m` mit explizitem oder implizitem `L`/`l`
sowie `H`/`h` und `V`/`v`. Transformationen, Richtung, Phase und geerbte
Strichattribute bleiben erhalten. Kurven, mehrere Segmente, geschlossene Pfade
und sonstige nicht unterstützte Formen werden nicht umgedeutet. Gespeicherte
SVGs werden durch diese Renderkorrektur nicht verändert.

## Nachprüfung

Frische Workbench-Eingaben wurden aus der exportierten SVG und demselben Seed
erzeugt. Der Konverter erhielt nur Raster und Beschreibung; der vorhandene
SVG-Zugriffsschutz blieb aktiv. Die Ausgabe wurde unabhängig erneut gerendert.
Die folgende Tabelle zeigt die MuPDF-Messung, ohne Änderung der Abnahmegrenzen:

| Fall | Vorher Kantenwert | Jetzt Kantenwert | Vorher Vordergrund-IoU | Jetzt Vordergrund-IoU | Ergebnis |
| --- | ---: | ---: | ---: | ---: | --- |
| original | 0,7016 | 0,9745 | 0,9406 | 0,9949 | bestanden |
| probe_01 | 0,7551 | 0,8888 | 0,7793 | 0,8909 | bestanden |

Die Wiederholung nutzte ein Gesamtlimit von **240 Sekunden je Fall**;
tatsächlich benötigte der abschliessende Lauf **36,656 bzw. 45,031 Sekunden**.
Es bestehen jeweils alle 28 lokalen Detailprüfungen. Die Variante benötigte
zwei zusätzliche Anpassungsstufen für Gehäuse und Rahmen. Beide Ausgaben
enthalten drei Rechtecke, fünf Düsenpolygone und 15 gestrichelte Geraden,
keine eingebetteten Raster. Es gab keine Referenz-SVG-Zugriffe des Konverters.

Auch librsvg besteht die unveränderte globale Abnahme: Kantenwert 0,9727 und
IoU 0,9935 für das Original, Kantenwert 0,8884 und IoU 0,8908 für die Variante.
Die Variante ist weiterhin deutlich ungenauer als das Original. Bestehende
Grenzen zu bestehen bedeutet keine pixelidentische Rekonstruktion.

Auf dem unveränderten exportierten Raster von `probe_01` besteht zusätzlich
ein direkter Fit sämtliche Detailprüfungen und die globale Abnahme
(Kantenwert 0,8912, IoU 0,8964). Die geänderte Referenzrasterung ist also
nicht die einzige Ursache des verbesserten Ergebnisses.

135 gezielte Renderer-, Sprühpanel- und Workbench-Regressionen bestehen.
Ein zusätzlicher vollständiger Fit der verschobenen Variante besteht ebenfalls
(136 Prüfungen insgesamt). Die HTTP-/Windows-Prozessprüfungen benötigen eine
Ausführung ausserhalb der Sandbox; der erste Sandboxlauf scheiterte an
Socketrechten bzw. Prozessabbruchrechten, der abschliessende Lauf besteht.

## Verwendung und Grenzen

Für einen neuen Versuch den Webserver neu starten, die Plan-B-Aufgabe mit
derselben SVG neu vorbereiten und das Zeitlimit auf 240 Sekunden je Fall
setzen. Alte Berichte und Eingaberaster werden dabei nicht überschrieben.
Der Standardwert 60 Sekunden und die Zeitverteilung sind unverändert.

Die Abnahme gilt für das Original und die erste Variante. Die dritte Variante
hat einen Regressionstest für die vollständige anfängliche Teileerkennung,
aber keine vollständige Konvertierungsabnahme. Die gesamte 17er-Serie wurde
nicht ausgeführt oder als akzeptierte Plan-B-Aufgabe freigegeben.

[Lokale Ergebnisse, Berichte und Reproduktion](../artifacts/evaluation/spray_panel_workbench_fix_2026-11-15/README.md).
