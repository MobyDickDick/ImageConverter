# GUI: besseren Zwischenstand erhalten und Strichelung prüfen

Die zweite Nutzerreklamation betrifft den normalen Upload-/GUI-Lauf, nicht
nur die Plan-B-Workbench. Untersucht wurden die gespeicherten GUI-Jobs
`b5014d1577134a9e881075086e9b7bc2` und
`5495b01e9f7a4f368084e984ffd499a1`.
Die ursprünglichen Jobdateien und Nutzeränderungen an Katalog/SVGs bleiben
unverändert.

## Schlechteres Endergebnis

Der erste Job enthält 2.807 protokollierte Render-Versuche. Zwischenstand
1148 aus der Phase „Suche“ hat einen normalisierten Bildfehler von 0,000704
und besteht die Bildprüfung (Kantenwert 0,88645). Das angezeigte Endergebnis
aus „Vektoraufbau“ hat dagegen einen Fehler von 0,004192 und verfehlt mit
Kantenwert 0,63586 die Grenze 0,72.

Die Ursachen lagen zwischen den Phasen:

- Der Preview-Publisher begann im neuen Wiederherstellungsprozess mit einem
  unendlich schlechten Ausgangswert. Damit konnte dessen erster schlechter
  Entwurf den besseren Preview der ersten Suche überschreiben.
- Der GUI-Preview-Endpunkt bevorzugte `recovery.svg`, sobald diese Datei
  existierte, unabhängig vom besseren Preview der vorherigen Suche.
- Die abschliessende Ergebnisübernahme verglich reguläre Ausgabe und
  Wiederherstellung, berücksichtigte aber den besten protokollierten
  Render-Versuch nicht.

Jetzt übernimmt ein neuer Publisher den unabhängig neu gerenderten
Bestwert der vorherigen Phase. Die GUI zeigt den so über die Phasen
erhaltenen Preview. Vor der Wiederherstellung, nach deren Ende und bei
deren Abbruch wird auch der beste bestätigte Journaleintrag berücksichtigt.
Die Auswahl rendert die Kandidaten erneut und prüft explizite
Beschreibungsbedingungen. Ein bloss beobachteter Zwischenstand wird dadurch
nicht als vollständig bestätigtes Modell ausgegeben.

Eine Wiederholung der Ergebnisübernahme auf einer Kopie des konkreten
Nutzerjobs stellt den Zwischenstand mit Fehler 0,000704 wieder her.
Die Originaldateien des Nutzerjobs werden dabei nicht überschrieben.

## „Sprühstrahlen“ und „gestrichelte Linien“

Die Änderung wurde gespeichert und an den Konverter weitergegeben.
Der erste genannte Job enthält wörtlich „graue gestricelte Linien“.
Diese Schreibweise wurde durch die bisherige enge Musterprüfung nicht
als Strichelung erkannt. Die Erkennung unterstützt nun die begrenzte
Schreibvariante sowie „graue gestrichelte Linien“, „Linien sind
gestrichelt“ und „Sprühstrahlen bestehen aus gestrichelten Linien“.
Verneinte Strichelung wird nicht positiv interpretiert.

Der Konverter interpretiert Freitext über begrenzte Modell- und
Eigenschaftsmuster. Die beiden korrekt erkannten Formulierungen können
dieselbe Liniengruppe bezeichnen und müssen deshalb nicht unterschiedliche
Geometrie erzeugen. Der eigentliche Fehler war, dass die geforderte
Strichelung bei der späteren allgemeinen Wiederherstellung nicht als
verbindliche Ausgabeprüfung erhalten blieb.

Für eine erkannte Luftbefeuchterbeschreibung mit expliziter Strahlenzahl
wird diese Vorgabe jetzt auch bei Sample- und Wiederherstellungsergebnissen
geprüft. Gezählt werden passende native gerade Pfade/Linien mit positiver
Strichelung und tatsächlicher Lücke. Der gestrichelte rechte Rechteckrahmen
zählt nicht als Sprühstrahl. Unsichtbare, strichlose oder durch ein überlanges
Muster effektiv durchgezogene Strahlen erfüllen die Prüfung nicht.
Dies ergänzt die bestehende Prüfung; es ist kein allgemeiner vollständiger
Semantikprüfer für beliebige SVGs.

Die GUI nennt bei einer Verletzung die geforderte und bestätigte Zahl.
Sie fordert dann nicht dazu auf, eine korrekte Beschreibung an die
unvollständige Konvertierung anzupassen. Bestehende Ergebnisse erhalten
die neue Beschreibungs-Prüfversion 5.

## Tatsächlicher GUI-Suchpfad und Zeitbudget

Auch mit korrigierter Ergebniswahl konnte die GUI zunächst innerhalb ihrer
120 Sekunden die vollständige Strichelung nicht einpassen. Der normale
GUI-Pfad unterscheidet sich von den früheren Workbench-Läufen:

- Er aktivierte zusätzlich eine Isolation pro Renderer. Der gesamte
  CLI-Prozessbaum wird bereits von der GUI mit Zeitlimit überwacht und
  beendet. Die zusätzliche Isolation wird daher nicht mehr standardmässig
  erzwungen; eine explizite Umgebungsvorgabe bleibt erhalten.
- Die Vorschaujournalisierung öffnete, prüfte und schloss für jeden
  einzelnen Render-Versuch beide Journaldateien erneut. Die lokale
  Vergleichsprobe mit 30 Kandidaten benötigte ohne Vorschau rund
  2,99 ms/Render und mit Vorschau 16,88 ms/Render. Mit über die Phase
  geöffneten Journaldateien sinkt dieser Wert auf 4,64 ms/Render.
  Jeder vollständige Datensatz wird weiterhin vor seinem Indexeintrag
  geflusht; Versuche werden nicht ausgelassen oder gesammelt verzögert.
  Die gemessene Beschleunigung ist eine lokale Probe, keine allgemeine
  Leistungsgarantie.

## Abnahme und Grenzen

Der tatsächliche `Jobs.upload`-/`Jobs.start`-/`Jobs.run`-Pfad wurde mit dem
unveränderten Nutzer-Raster und Text einschliesslich „gestricelte“ unter
Profil `normal`, Seed 0 wiederholt. Für diesen Test wurden lediglich
Kataloglesen und Projektpromotion abgeschaltet, damit keine Nutzer- oder
Projektartefakte überschrieben werden. Renderer, Vorschau, Journale,
primäre Konvertierung, Wiederherstellung und Ergebnisübernahme blieben aktiv.

Der abschliessende Lauf benötigt **63,2 Sekunden** und liefert eine native
SVG mit **15 gestrichelten Geraden**. Die gespeicherte Ausgabe besteht die
Bild- und explizite Strichelungsprüfung:

| Gespeichertes Endergebnis | MuPDF | unabhängiges librsvg |
| --- | ---: | ---: |
| Normalisierter Bildfehler | 0,000316 | 0,000331 |
| Vordergrund-IoU | 0,99229 | 0,99268 |
| Kantenwert | 0,92896 | 0,92785 |

Die Wiederherstellung übernimmt in diesem Lauf den erhaltenen generierten
Kandidaten nach einer Render-Prüfung. Ihr Bericht behauptet keine vollständige
Modellbestätigung (`model_confirmed=false`). Die bestandene Pixel- und
Strichelungsprüfung ist keine allgemeine Konvertierungsabnahme und keine
Abnahme der 17 Plan-B-Varianten.

[Lokale Belege, Resultat und Testprotokolle](../artifacts/evaluation/gui_final_selection_2026-11-15/README.md).
