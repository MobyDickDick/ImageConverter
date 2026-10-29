# Quadrat-Kelle und kleines Klappengelenk: vorlagengestützte Nachzeichnung

Die Originalpixel von `AC0501_S_sia.jpg` und die ausdrücklich bereitgestellte
Inkscape-Vorlage führen zu einer nativen SVG mit Quadrat, beiden Diagonalen,
mittigem Stiel, rundem Gelenk und schräger Klappenlinie. Die Vorlage bleibt
bytegleich erhalten; die neue Ausgabe liegt im regulären SVG-Ausgabeordner.

`checks.json` enthält Quell-/Vorlagen-/Ausgabehashes, beide strengen
Rendererprüfungen, den echten GUI-Auftrag und die Prüfbefehle. MuPDF und
librsvg bestehen die unveränderten Gates. Die neue Vorlage wird im GUI-Auftrag
mit einer Prüfung und ohne Verformung übernommen. Der generische
Optimierungsversuch auf der ursprünglichen Inkscape-Vorlage bleibt separat
als negativer Qualitätsfall sichtbar (Foreground-IoU 0,725352).

Neun SIA-Bildbeschreibungen pro Katalog werden eigenständig ersetzt;
die anderen Rechteckvarianten bleiben erhalten. Keine Erhöhung der
Katalogerfolgszahl und kein Nachweis allgemeiner automatischer Erkennung.
Rohdaten und Vorschauen bleiben lokal unter `.tmp/ac0501-work/`.

[Umsetzung, GUI-Ursachen und Grenzen](../../../docs/ac0501_sia_redraw_and_gui_2026-10-29.md).
