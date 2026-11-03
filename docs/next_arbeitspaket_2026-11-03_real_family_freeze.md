# Reale Kompositionsfamilien vor weiterer Entwicklung reservieren

Branch `codex/freeze-real-composition-families-2026-11-03`, Ausgangscommit
`147e86405`. Begrenztes Vorbereitungspaket zum ausdrücklich dokumentierten
[nächsten Schritt](next_arbeitspaket_2026-10-31_proposal_reuse.md#sitzungslog--status-review)
der P0-Struktursuche: andere reale Familien markieren und vor weiterer
Kompositionsentwicklung sperren. Status: **Review**.

## Lieferumfang

Zwei weitere reale Kandidatenfamilien sind anhand vergrößerter Originalpixel
markiert und gesperrt. Es wurde kein Converter, Detektor oder Referenz-SVG auf
ihnen ausgeführt beziehungsweise betrachtet. Der produktive Code unter `src/`
ist vollständig hashgleich zum Ausgangsstand.

| Familie | Fixierte sichtbare Inhalte | Grenze der späteren Abnahme |
| --- | --- | --- |
| HC0010, Heizkörper | Neun gerundete, schattierte Glieder, angeschnittene äußere Glieder und zwei dahinterliegende Verbinder; elf Objektmarkierungen und 18 Tiefenrelationen | Mehr Objekte als im heutigen begrenzten Suchweg; Rundung, verdeckte Verbinder und schwache Graukanten zusätzlich zu Boxen prüfen |
| Rail, Metallschiene | Fünf abgeschrägte Langlöcher, strukturierter Untergrund, obere Rille und untere Kanten; acht Regionsmarkierungen und neun Relationen | Löcher sind keine gerundeten Rechtecke; Textur, Abschrägungen und Randhelligkeit benötigen eigene unabhängige Prüfungen |

Originalbytes, verlustfrei dekodierte neutrale PNGs, eigenständige
Beschreibungen, sichtbare Boxen, Lochpolygone, Unsicherheiten, Relationen,
Familien-/Nachfahrenregeln, Quellenaudit und Runtimehashes stehen im
[versiegelten Reservebestand](../artifacts/evaluation/real_composition_holdout_freeze_v1/README.md).
Alle bekannten Dateien und spätere Skalierungen, Ausschnitte, Umfärbungen oder
Umbenennungen gehören jeweils zu derselben Familie. Umbenannte identische
Originalbytes oder gemeinsam verwendete Nachfahren zählen nicht als zwei
Familien und werden vom Vorbereiter zurückgewiesen.

Die implementierende Instanz hat die Originalpixel markiert; ein unabhängiger
menschlicher Annotationsaudit fehlt. Beide Bilder waren bereits im historischen
Katalog. Die am Ausgangscommit festgeschriebene Namens-/Historienprüfung fand
keine gezielte Verwendung von HC0010. Die Rail-Treffer sind nach Prüfung
gewöhnliche englische Bezeichnungen im anderen Panelmodul. Das schließt
unbenannte Verwandte oder frühere Katalog-Batchläufe nicht aus.

## Sperre und Nachprüfung

`tools.freeze_real_composition_holdouts` erzeugt ausschließlich Prüfdatensätze,
ohne Converterimport oder Konvertierung. Bestehende Zielordner werden nicht
überschrieben. Der schreibfreie Nachprüfer kontrolliert Inventar, Prüfsummen,
Original-/PNG-Pixelgleichheit, Beschreibungen, gültige Markierungen und den
Status `sealed_unrun`. Optional prüft er den aktuellen produktiven Quellstand.
Fehlende Dateien, zusätzliche Versuchsdateien und vorgetäuschte Erfolgsangaben
scheitern. Die normale `evaluate_real_scene.prepare_real`-Vorbereitung weist
gesperrte Annotationen vor jeder Dateierzeugung zurück.

Vor Freigabe sind Runtime-Stand, Bildbudget, Seeds und unveränderte Qualitätsgates
festzulegen. Alle sechs dokumentierten Lücken des unabhängigen Prüfers müssen
geschlossen sein. Erst dann erfolgt der vorab geplante CLI-Versuch ohne
Nachstimmung anhand seiner Ergebnisse. Anschließend bleibt die ganze
offengelegte Familie Entwicklungsmaterial.

**Keine positive Transferabnahme:** Es gab null Konvertierungsversuche;
`accepted` bleibt `null`. Beide Kandidaten reichen über die heutige
Verlaufskreis-/Rechteckgrammatik hinaus. Ihre Reservierung belegt daher noch
keine Übertragung bereits unterstützter Primitive über denselben Szenenweg.
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und GENERAL-SCENE-REAL-05
bleiben offen. Es gibt keine neue Runtimefähigkeit und keinen Kataloggewinn.

## Prüfung

- Szenen-/Evidenzregressionen: **55/55**, Exit 0, ohne Überspringung; darin
  enthalten sind **26 neue** Sperr-/Integritätsprüfungen einschließlich einer
  Gegenprobe für die bisherige ungesperrte Vorbereitung.
- Separates Kernprofil: **42/42**, Exit 0, ohne Überspringung.
- Schreibfreie Freezeprüfung mit aktuellem Runtimevergleich, Python-Syntax und
  Diffprüfung: jeweils Exit 0.
- Lokale Umgebung: Python **3.10.11**; keine Behauptung der historischen
  3.10.20-Toolchain. Keine vollständige Standardsuite oder Archiv-Neukonvertierung.

Befehle, Exitcodes und Berichtshashes:
[`checks.json`](../artifacts/evaluation/real_composition_holdout_freeze_v1/checks.json).
Rohberichte liegen lokal unter `.tmp/composition-freeze/`.

## Sitzungslog

- Getestet: Freeze-/Sperrprüfung, bestehende reale/gemischte/Restbild-Evidenz und Kernprofil.
- Ergebnis: 55/55 plus separat 42/42; zwei ungetestete Familien reserviert, keine Qualitätsquote.
- Grenzen: Kandidaten außerhalb heutiger Grammatik; vollständige unabhängige Prüfer und menschlicher Annotationsaudit fehlen.
- Nächster Schritt: generische Kompositionsentwicklung mit synthetischen/bekannten Entwicklungsfällen; Reserve erst mit vollständigem unabhängigen Prüfer offenlegen.
- Startbefehl: `.venv/Scripts/python.exe -m tools.freeze_real_composition_holdouts --verify artifacts/evaluation/real_composition_holdout_freeze_v1/freeze/manifest.json --check-current-runtime`.
