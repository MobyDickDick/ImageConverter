# SEARCH-STRUCTURE-01: verbundene Restbildkomponenten aufteilen

Basis: `628da4bd0218eaa80caa2217564562bb1da1ed60` auf `main`.
Branch: `codex/search-structure-component-splits-2026-10-23`.
Auswahl: höchstes offenes P0-Paket aus `open_tasks.md` und der
[Schwächenprüfung](weakness_review_2026-10-23.md).

## Verhalten

Nach den drei bisherigen Segmentierungen und der begrenzten Edit-Agenda kann
die Suche nun eine zusammenhängende Restbildkomponente in getrennte native
Rechtecke zerlegen. Das schließt die gemeinsame Ursache der drei bisher
gescheiterten `edit_00` bis `edit_02`: Antialiasing verbindet die Ränder zweier
tatsächlich getrennter Rechtecke bei allen bisherigen Restbildschwellwerten.

Die neue Hypothese schätzt den einfarbigen Kern und dessen Deckung gegenüber
dem örtlichen Elternverlauf aus dem Raster. Eine Deckung von mindestens 0,9
liefert mögliche getrennte Kerne. Die Kerne müssen rechteckig und ausreichend
groß sein; pro Komponente werden höchstens acht Teile vorgeschlagen. Die
Kanten werden aus der beobachteten Deckung geschätzt. Wenn beide Nachbarn zu
demselben Pixel beitragen, ist ihre Einzelkante daraus nicht eindeutig
bestimmt: Eine symmetrische Startschätzung wird anschließend gemeinsam am
Originalraster registriert. Referenzgeometrie und Dateinamen liefern keine
Runtime-Parameter.

Diese Deckungsschwelle gehört ausschließlich zur Vorschlagserzeugung.
Anzahl, native Formklassen, vollständiges Containment, geforderte Anordnung,
Trennung und alle bisherigen lokalen sowie globalen Rastergates gelten weiter.
Ein durchgehender Balken darf nicht als zwei getrennte Rechtecke gelten.
Zusätzliche Objekte, Textur und falsche Anordnungen bleiben Negativkontrollen.
Konturen und andere Formklassen verwenden die bestehende konservative Erkennung.

Split-Vorschläge teilen den vorhandenen fortsetzbaren Edit-Job, das Bildbudget,
den Rendercache und die bild-/vertragsgebundene negative Evidenz. Sie werden als
`operator=split` bzw. `split_edit` protokolliert. Die zweite Edit-Agenda verwendet
nur den Rest des gemeinsamen 96-Zustände-Limits; die 32-Kandidaten-Grenze bleibt.
Auch bei Annahme, Abbruch oder Deadline enthält die Abschlusstelemetrie die
bereits besuchten Zustände. Eine kontrollierte doppelte Detektorinstanz belegt
Split plus Remove mit echter Registrierung und unveränderten Gates.

Beim Aufbau der Komponentenlisten greift die Instanzgrenze bereits während
der Sammlung, damit ein verrauschtes Raster nicht unbegrenzt vollständige
Bildmasken im Speicher hält. Ein eigener Gegenversuch sichert das.

## Nachweise

Die zwölf neuen synthetischen Entwicklungsfälle und die acht bekannten
Operatorfälle wurden vor der Runtime-Änderung mit Eingaben, Objektmarkierungen
und Prüfsummen eingefroren. Die echte überwachte `semantic-only`-CLI verwendet
vorher und nachher fünf Sekunden Gesamtbudget und Suchseed 17. Die unabhängige
Nachprüfung zählt native SVG-Objekte, prüft ihre Geometrie und Zeichenreihenfolge
und rendert Objektregionen sowie das gesamte Raster erneut. Beide
Referenzvektor-Zugriffswächter müssen leer bleiben.

| Kohorte | Vorher | Endstand |
| --- | --- | --- |
| Zwölf neue Entwicklungsfälle: zwei/drei benachbarte Rechtecke, beide Anordnungen, beide Verlaufsachsen, drei Farbpaletten | 3/12 | 12/12 |
| Acht bekannte Operatorfälle, einschließlich der drei bisherigen Fehler | 5/8 | 8/8 |
| Gemeinsamer unveränderter Vergleichsbestand | 8/20 | 20/20 |
| Zwölf nach dem ersten Code-Freeze erzeugte synthetische Fälle, anderer Seed | kein Elternvergleich | 12/12 |
| Gekoppelter Plan-B-Repro: Original und 16 Größen-/Verschiebungsvarianten | erster Entwicklungsversuch 1/17 | 17/17 |
| Neun bekannte Restbildfälle | früherer Stand 7/9 | 7/9 |

Der Plan-B-Erstversuch deckte einen zusätzlichen Sprachfehler auf: Die bereits
in anderen Szenenwegen unterstützte Aussage zum vergrößerten/verkleinerten und
verschobenen gesamten Motiv wurde hier abgelehnt. Der geschlossene Parser
verarbeitet jetzt genau diese vorhandene Grammatik. Zusätzliche Objekt-,
Relations- oder Negationsaussagen bleiben Ablehnungsgründe. Der negative
Erstversuch ist gespeichert; seine Varianten sind anschließend Entwicklung.
Auch die zwölf zusätzlichen synthetischen Fälle sind keine unabhängigen realen
Familien und wurden nach der letzten Speicherbegrenzung erneut geprüft.

Die zwei kontrastarmen Restbildfälle bleiben negativ im Nenner. Der neue Split
ändert weder ihre Qualitätsgrenzen noch die übrigen erfolgreichen Szenenwege.
Alle **379** gespeicherten Archivpaare bestehen ihre bisherige absolute
Pixelprüfung; **758** Bild-/SVG-Prüfsummen sind unverändert. Das ist eine Prüfung
der gespeicherten Paare, keine erneute Konvertierung aller Archiveingaben.

Eingaben, tatsächliche SVGs, Berichte, Workerlogs, Zugriffsbelege und
Verifikationsresultate stehen unter
[`artifacts/evaluation/component_splits_v1/`](../artifacts/evaluation/component_splits_v1/README.md).
`checks.json` und die Testprotokolle enthalten die abschließenden Prüfungen.
**372/372 Tests** aus den betroffenen Szenen-, Scheduler-, Such- und
Deadline-Modulen bestehen, darunter alle **32 neuen Tests**. Syntaxprüfung,
CLI-Hilfe und die Runtime-ID-Prüfung (null Katalog-IDs) bestehen ebenfalls.
Die reduzierte Evidenz wurde ausschließlich aus den für Git ausgewählten
Dateien in einen neuen Ordner kopiert und dort vollständig unabhängig erneut
geprüft. Die vollständige historische Gesamtsuite wurde nicht erneut ausgeführt;
ihre früher dokumentierten Zeitmessungsfehler werden nicht als behoben behauptet.
Die neue CI-Aufgabe wiederholt synthetische Szenen durch die überwachte CLI
und deren unabhängigen Nachprüfer.

## Restumfang und Algorithmusflexibilität

Dieses P0-Teilpaket ist umgesetzt. SEARCH-STRUCTURE-01 bleibt insgesamt offen
für breitere Komposition und unabhängige reale Abnahme. GENERAL-SCENE-COMPOSITION-09
verknüpft anschließend Rundung, Überdeckung und weitere Schichten. Vor deren
realer Entwicklung müssen andere reale Familien unabhängig markiert und
gesperrt werden. Bekannte GE0018/GE0307 bleiben Entwicklung; das Erfolgsarchiv
wächst durch synthetische Prüfungen nicht.

Der Algorithmus ist damit strukturell flexibler: Er variiert nicht nur Zahlen
einer vorgegebenen Geometrie, sondern Segmentierungen, Instanzvorrat und native
Formklassen, kombiniert Add/Remove/Replace und nun Split und vermeidet bekannte
Ablehnungen im selben Bildkontext. Das ist weiterhin eine begrenzte Suche über
vorhandene Operatoren. Beliebige neue Formen, freie Algorithmen oder verlässlich
gelöste neue reale Kompositionen sind damit nicht nachgewiesen.
