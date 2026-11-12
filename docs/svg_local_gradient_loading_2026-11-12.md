# Lokale SVG-Verlaufsverweise öffnen, 12.11.2026

`AC0213_L.svg` wurde beim Öffnen in der Workbench mit „Das Sample muss
ausschliesslich eigenständige SVG-Formen enthalten“ abgewiesen. Die Datei
enthält einen lokalen `xlink:href="#swatch11"` am Verlauf `linearGradient12`.
`prepare_sample` hatte pauschal jedes `href` untersagt, auch Verweise auf
Definitionen innerhalb derselben SVG-Datei.

Die Ladeprüfung erlaubt jetzt lokale Verweise zwischen eindeutigen Verläufen
desselben Typs. Externe Ressourcen, unbekannte Ziele, Zyklen, widersprüchliche
Verweise und Ketten mit mehr als 64 Verweisen bleiben abgewiesen. Unterstützt
werden `href` sowie `xlink:href`. Die Quell-SVG wurde nicht verändert.

Der lokale Server auf Port 8766 wurde nach Prüfung auf inaktive Aufträge
neu gestartet. Der echte POST auf `/api/workbench/inspect` mit `AC0213_L.svg`
liefert HTTP 200 und eine Vorschau mit 47 × 61 Pixeln. Die native librsvg-
Darstellung der Vorschau zeigt beide grauen Ventildreiecke und den Motor-Kreis.
Die geringfügige Höhenrundung entspricht dem bestehenden Vorschauverhalten.

Die 57 gezielten Tests für Sample-Import, Workbench und Verlaufsreferenzen
bestehen, einschliesslich HTTP-Regression mit dieser Originaldatei, tatsächlicher
Verlaufsdarstellung und negativer Ressourcen-/Zyklus-/Tiefenkontrollen.
Die HTTP- und Prozessabbruchtests benötigen unter Windows die Ausführung
ausserhalb der Sandbox.

## Getrennte offene Rasterabweichung

Beim zusätzlichen Vergleich wurde festgestellt, dass der interne MuPDF-basierte
Rasterweg die Dreiecksfüllungen dieser Datei schwarz darstellt. Die vorhandene
Verlaufsanpassung unterstützt den zusammengesetzten Pfad mit V-Kommandos und
seiner Verlaufstransformation nicht. Browser-/librsvg-Vorschau und Ladeprüfung
sind davon getrennt. Die Korrektur der Ladeprüfung behebt diesen Rasterfehler
nicht; eine Plan-B-Abnahme für AC0213 darf daher nicht auf dem fehlerhaften
internen Prüfraster beruhen. Native und interne Raster liegen als lokale
Diagnose unter `artifacts/evaluation/ac0213_local_gradient_2026-11-12/`.
