# Gleichfarbige Instanzen mit mehreren Sichtbarkeitsinseln

`summary.json` erhält den kontrollierten echten CLI-Vergleich **0/12 → 12/12**
auf unveränderten Eingaben mit Seed `731529`. Der endgültige Code besteht
**11/12** mit Zusatzseed `418267`, **12/12** mit drei gleichfarbigen Kreisen und
Seed `392841` sowie **17/17** an genau einer gekoppelten Plan-B-Vorlage mit
Seed `962731`. Alle Fälle bleiben im Nenner. Suchseed 17 und ein gemeinsames
Fünf-Sekunden-Budget gelten pro Bild.

Die verbleibende Ablehnung `islands_3_06` bei Seed `418267` betrifft eine gültige
schmale gerundete Brücke mit nur vier statt fünf beobachteten Seitensamples.
Die Grenze bleibt unverändert und ist als Negativkontrolle abgesichert.
Frühere Entwicklungsstände und ihre Fehlversuche bleiben separat unter
`development_attempts` erhalten. Der Baseline-Code stammt aus `40c84e83e`;
SHA-256-Werte binden Ausgangsmodul, endgültiges Modul, Generator und Eingaben.

Je endgültigem CLI-Fall bleiben Eingabe-/Ausgabehashes, native Objektprüfung,
lokale und globale Rastermessungen, Rückgabecode und unabhängige Zeitaufsicht
erhalten. Referenz-SVG-Zugriffe der Konvertierungsworker wurden gesperrt.
`checks.json` dokumentiert Befehle, Exit-Codes und den Codebezug der Tests.
Der breite Lauf vor der letzten Radiuskorrektur und die betroffenen Prüfungen
am endgültigen Code werden getrennt berichtet und nicht addiert.

Wiederholung mit automatischer Entfernung der generierten Raster-/Vektordaten:

```powershell
python -m tools.run_seeded_scene_check evaluate_island_groups --seed 731529 --rounded --outlines
python -m tools.run_seeded_scene_check evaluate_island_groups --seed 392841 --children 4 --rounded --outlines
python -m tools.run_seeded_scene_check evaluate_island_groups --seed 962731 --rounded --outlines --variations
```

Seed `418267` mit `--rounded --outlines` reproduziert **11/12**; wegen der
vollständigen Abnahmeanforderung endet dieser Wrapperlauf erwartungsgemäß
mit Exit 1. Alle Seeds bleiben zusätzlich im versionierten Testjournal.
Dies ist synthetische Entwicklung, keine neue unabhängige reale Familienabnahme.
Details: [Arbeitspaket](../../../docs/next_arbeitspaket_2026-10-24_island_groups.md).
