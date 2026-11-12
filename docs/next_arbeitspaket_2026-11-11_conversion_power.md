# CONVERSION-POWER-01: aktive Konvertierung vor automatischem Standby schützen

Implementierungsumfang vom 11.11.2026 abgeschlossen. Das
[jüngste Katalogaudit](catalog_search_followup_2026-11-11.md#priorisierte-konsequenzen)
priorisiert diese Betriebsaufgabe vor weiteren langen Katalogläufen. Die dort
belegten 155 Standbyminuten sind keine geleistete Optimierungsarbeit.

## Umsetzung

Eine aktive `convertRange`-Berechnung hält unter Windows einen eigenen
`PowerCreateRequest`-Handle mit `PowerRequestSystemRequired` und
`PowerRequestExecutionRequired`. Dadurch sind sowohl die reguläre CLI und ihr
GUI-Aufruf als auch der historische Bereichsmodus angeschlossen. Einzelne
`ImageDeadline.run`-Aufrufe schützen auch Prozessstart und Aufsicht unabhängig
vom Bereichseinstieg. Jeder Aufruf besitzt seinen Handle; verschachtelte und
gleichzeitige Aufrufe können die fremde Anforderung nicht freigeben.

Es gibt keine Displayanforderung: Der Bildschirm kann abschalten.
Anforderungen werden direkt nach der Arbeit mit `PowerClearRequest` und
`CloseHandle` freigegeben, einschließlich Fehler, Timeout, `KeyboardInterrupt`
und `SystemExit`. Teilweise fehlgeschlagene Einrichtung wird vor Fortsetzung
aufgeräumt. Der Prozess besitzt die Handles; auch bei Prozessbeendigung bleibt
kein unabhängiger Hintergrunddienst zurück. API-Fehler werden sichtbar als
`unavailable` protokolliert; die Konvertierung läuft dann ohne diese Absicherung.
Andere Betriebssysteme melden im Bildtiming `unsupported` und laden keine
Windows-Bibliothek. Energiepläne und globale Einstellungen bleiben unverändert.

Die Bildaufsicht markiert Beobachtungslücken ab fünf Sekunden im vorhandenen
Timingdatensatz. Dauer, UTC-Uhrdifferenz und CPU-Zunahme **der Aufsicht** stehen
separat im Datensatz und in `observation_interruptions` des Deadlineberichts.
Eine Lücke allein unterscheidet weder Standby noch Prozessplanung oder I/O;
`cause` bleibt deshalb `undetermined`. Es wird keine vermeintlich exakte aktive
Workerzeit daraus berechnet. Das verstrichene Bildbudget bleibt angerechnet.

Nach einer Unterbrechung gilt weiterhin die bestehende kontrollierte Behandlung:
Abgelaufene Worker samt Rendernachkommen beenden, verspätete ungeprüfte Ausgabe
verwerfen, ausschließlich quellen-/SVG-gebundene geprüfte Zwischenstände retten
und mit weiteren Eingaben fortfahren. Eine automatische Wiederholung mit neuem
Budget wurde nicht eingeführt. Der separate Katalogrunner behandelt fehlgeschlagene
Versuche bei `--resume` weiterhin als erneut einzuplanen; seine Regressionen
prüfen dieses Verhalten.

## Prüfung und Grenzen

- 54/54 gezielte Tests: Ressourcenlebensdauer, Teilfehler, Abbruch, fehlende
  Plattformunterstützung, Timing, echte Prozessaufsicht, geprüfte
  Zwischenstandsrettung, vorhandene Produktions-CLI und Katalogfortsetzung.
- 42/42 Kerntests, keine Überspringungen.
- Native Windows-API-Prüfung außerhalb der Sandbox: Erfolg und kontrollierter
  Abbruch jeweils `acquired` → `released`, offene Handles jeweils
  **153 → 154 → 153**, keine Freigabefehler. In der Sandbox verweigert Windows
  den API-Aufruf mit Fehler 5; die sichtbare Degradierung ist dort erwartbar.
- Neuer CI-Job für Ubuntu/Windows mit Lifecycle-/Timingtests und Plattformprobe;
  noch kein GitHub-Lauf dieses neuen Jobs.

Reproduktionsbefehle und maschinenlesbarer nativer Nachweis stehen im
[Evidenzverzeichnis](../artifacts/evaluation/conversion_power_v1/README.md).
Das ist eine API-/Lebensdauerabnahme, **kein** tatsächlicher Standbyversuch und
keine Akkulaufzeit- oder vollständige Katalogabnahme.

Die Windows-Richtlinie hat Vorrang: Laut
[Microsofts PowerSetRequest-Vertrag](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest)
können die System-/Ausführungsanforderungen bei Modern Standby im Akkubetrieb
fünf Minuten nach dem Sleep-Timeout enden. Bewusst ausgelöster Standby beendet
sie ebenfalls. Die API-Zusage ist daher keine Garantie gegen jede Unterbrechung.
[PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest)
und [REASON_CONTEXT](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-reason_context)
bestimmen den verwendeten nativen Handle- und Strukturvertrag.

## Nächstes dokumentiertes Paket

Punkt 2 des jüngsten Audits ist mit
[CONVERSION-PERSISTENCE-01](next_arbeitspaket_2026-11-12_conversion_persistence.md)
umgesetzt: unmittelbare Zustände, unveränderliche Laufrevisionen und gemeinsam
gebundene SVG-Metriken/Freigaben. Als Nächstes folgt die dort konkretisierte
Strukturerweiterung des tatsächlich benutzten Fallbackpfads
(FALLBACK-STRUCTURE-01). Sie bleibt offen.

SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 und reale Qualitätsabnahmen
werden durch dieses Betriebspaket nicht abgeschlossen.
