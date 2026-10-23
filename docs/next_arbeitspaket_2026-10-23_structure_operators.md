# SEARCH-STRUCTURE-01: begrenzte native Strukturoperatoren

Basis: `dd832bd22` auf `main` nach dem Scheduler-Merge.
Branch: `codex/search-structure-operators-isolated-2026-10-23`.
Die P0-Reihenfolge aus der [Schwächenprüfung](weakness_review_2026-10-23.md)
bleibt maßgeblich. Dieses Paket ergänzt Add/Remove/Replace im vorhandenen
Restbildszenenweg. Die übergeordnete Aufgabe bleibt für die unabhängige reale
Übertragung und die breitere Komposition offen.

## Verhalten und Grenzen

Ein Restbildvorschlag wird nicht mehr allein wegen einer falschen Objektzahl
verworfen. Die drei vorhandenen Zerlegungen liefern einen gemeinsamen Vorrat
beobachteter Instanzen. Eine begrenzte Agenda kann eine fehlende Instanz
hinzufügen, einen überzähligen Detektorvorschlag entfernen oder eine Instanz
durch eine andere beobachtete Geometrie/Farbe bzw. native Formklasse ersetzen.
Die Agenda verwendet höchstens 32 Kandidaten und 96 verschiedene Zustände.
Auch unvollständige Zwischenzustände werden untersucht, aber nur eine Szene
mit der vollständigen verlangten Klassenanzahl darf in die Registrierung.

Der unterstützte Vertrag besteht aus einem axialen Verlaufskreis mit bis zu
acht getrennten, einfarbig gefüllten Kreis-/Rechteckkindern. Die bestehende
Rechtecksprache bleibt erhalten. Gemischte Kinder verwenden ausdrücklich
„Der äußere Kreis hat einen … Farbverlauf“ und „Die inneren Formen liegen
innerhalb des äußeren Kreises und getrennt voneinander“. Diese Sprache
erweitert den geschlossenen Vertrag; unbekannte Aussagen werden weiterhin
zurückgewiesen. Kinder benötigen getrennte achsenparallele Begrenzungsboxen.
Überdeckung, Rundung, freie Kurven und beliebige Schichten sind hier nicht
freigeschaltet. Referenz-SVGs oder Kataloggeometrien sind keine Runtime-Quelle.

Die Edit-Agenda ist eine weitere fortsetzbare Arbeitseinheit des vorhandenen
Schedulers. Sie teilt dessen Bildbudget, Rendercache und Zeitaufsicht mit den
drei ursprünglichen Zerlegungen. Doppelte Szenen werden unabhängig von der
Reihenfolge ihrer getrennten Kinder erkannt. `scene_hypothesis` protokolliert
zusätzlich `inventory_rejected`, `previously_rejected` und die ausgeführten
Edits. `structure_search_finished` unterscheidet Annahme, ausgeschöpfte Agenda,
Kandidaten-/Zustandsgrenze, Abbruch und Zeitlimit.

Vollständig abgelehnte Registrierungen bleiben innerhalb derselben
`ImageSearch` als negative Evidenz erhalten. Ihr Schlüssel enthält das Raster,
den vollständigen hier unterstützten Vertrag und den konkreten Geometrie-/
Farbvorschlag. Andere Bilder oder andere Verträge beginnen unabhängig.
Zeitabbrüche und geschlossene pausierte Fits werden nicht als fachliche
Ablehnung gespeichert. Die Evidenz wird nicht auf Platte als Bildvorlage
gespeichert und nicht zwischen Konvertierungen übertragen.

Remove entfernt einen Vorschlag, keine Prüfpflicht: Zusätzlich zu allen
endgültigen Objekten werden die Rasterregionen aller erkannten Vorschläge
unter denselben lokalen Grenzen geprüft. Dadurch kann ein kleines zusätzliches
Rasterobjekt nicht hinter dem Mittelwert des großen Elternkreises verschwinden.
Ungeeignete nicht native Komponenten bleiben konservative Ablehnungsgründe.
Containment, Klassenanzahl, Trennung sowie vollständige lokale und globale
Rastergates bleiben verbindlich.

## Echte CLI-Gegenprobe

Vor der Runtime-Änderung wurden acht synthetische Entwicklungseingaben mit
Objektmarkierungen und Prüfsummen festgelegt und durch die echte überwachte
CLI geprüft: **0/8** bestanden. Derselbe Bestand erreicht anschließend
**5/8** unter demselben Fünfsekundenbudget und Seed 17:

- `edit_03` benötigt Add: Keine einzelne der drei Zerlegungen enthält alle
  drei Rechtecke. Zwei dunkle Nachbarn und ein helleres drittes Rechteck werden
  erst aus mehreren Zerlegungen vollständig zusammengesetzt.
- `edit_04` bis `edit_07` prüfen verschiedene Kreis-/Rechteckkombinationen mit
  zwei bzw. drei Kindern und beiden Verlaufsachsen.
- `edit_00` bis `edit_02` bleiben im Nenner. Die verfügbaren Zerlegungen liefern
  dort keinen vollständig verwendbaren Instanzvorrat. Das Paket löst keine
  allgemeine Aufspaltung zusammenhängender Komponenten.

Die unabhängigen Nachprüfer zählen native SVG-Objekte, vergleichen ihre
Geometrie und Zeichenreihenfolge und prüfen jede Objektregion sowie das
gesamte Raster. Die Worker haben keinen Referenz-SVG-Zugriff. Add ist in der
CLI nachgewiesen. Remove eines doppelten Detektorvorschlags und Replace einer
falsch klassifizierten Instanz sind kontrollierte Detektorfehler mit echter
Registrierung und denselben unabhängigen Gates; das sind keine neuen realen
CLI-Familiengewinne.

Die neun bekannten Restbild-CLI-Fälle bleiben bei **7/9**. Die beiden bekannten
kontrastarmen Fälle werden weiterhin abgelehnt. Alle 379 gespeicherten
Archivpaare bestehen ihre bisherige absolute Pixelprüfung; ihre 758
Quellbild-/SVG-Prüfsummen stimmen weiterhin mit dem Archivindex überein.
Diese Archivprüfung ist keine erneute Konvertierung aller 379 Eingaben.

Reproduzierbare Eingaben, Vorher-/Nachher-Ausgaben, Workerlogs, Prüf- und
Zugriffsbelege stehen unter
[`artifacts/evaluation/structure_operators_v1/`](../artifacts/evaluation/structure_operators_v1/README.md).
Die finalen Testresultate stehen dort in `checks.json` und `full-suite.log`:
**3.931 bestanden, 30 übersprungen, zwei fehlgeschlagen** nach 70 Minuten und
38 Sekunden. Alle 19 neuen Tests bestehen auch in diesem vollständigen Lauf.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung und Whitespace-Prüfung bestehen.
Es gibt ausdrücklich keine grüne Gesamtsuite; die beiden folgenden
unveränderten, zeitabhängigen Tests bleiben negative Beobachtungen.

Die 78 gezielten Struktur-/Restbild-/Mischszenentests bestehen auch im isolierten
Worktree. Ein im breiten Lauf auffälliger unveränderter Test,
`test_observation_changes_neither_candidates_nor_measurement_budget`, besteht
einzeln und im vollständigen Komponentenmodul (28/28). Ein separater
200-facher Versuch reproduziert unterschiedliche Kandidaten/Budgets bereits
mit dem ursprünglichen `ImageSearch` aus `dd832bd22` in 3/200 Fällen. Der
entsprechende Versuch mit dem neuen Stand beobachtet 0/200 Abweichungen; daraus
wird keine Verbesserung abgeleitet. Die tatsächlichen Laufzeiten bestimmen
die Fortschrittsraten des vorhandenen Bot-Schedulers, während der Test gleiche
Kandidaten und Messbudgets erwartet. Bot-, Scheduler-, Portfolio- und Testcode
sind gegenüber der Basis unverändert. Probe und Rohabweichungen sind erhalten;
die Wiederholungen ersetzen keinen grünen vollständigen Erstlauf.

Auch `test_blocked_real_inference_is_inside_the_process_deadline` fällt im
breiten Lauf auf: Sein Zwei-Sekunden-Budget endet nach 2,016 Sekunden, bevor
der Worker den Inferenzmarker schreibt oder seine Bereitschaft meldet. Die
Zeitspur belegt den Abbruch und vollständigen Prozessabbau; der breite Lauf
belegt an dieser Stelle keine tatsächlich betretene blockierte Inferenz.
Die gezielte Wiederholung besteht in 2,37 Sekunden einschließlich Testaufbau.
Deadline-, Netz- und Testcode sind gegenüber `dd832bd22` unverändert.
Zeitspur, Deadlinebericht und Wiederholungslog stehen unter
`structure_operators_v1/neural-deadline/`.

## Restumfang

SEARCH-STRUCTURE-01 wird nicht als vollständig erledigt markiert. Die Operatoren
arbeiten im beschriebenen geschlossenen Szenenvertrag. Eine unabhängige reale
Abnahme benötigt vor der weiteren Entwicklung neue gesperrte und unabhängig
markierte Familien. GE0018/GE0307 und die hier verwendeten synthetischen Fälle
bleiben Entwicklung. GENERAL-SCENE-COMPOSITION-09 umfasst anschließend die
gemeinsame Rundungs-/Überdeckungs- und Schichtenkomposition.
