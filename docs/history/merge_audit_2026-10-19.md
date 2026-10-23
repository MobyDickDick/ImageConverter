# Prüfung des wiedergefundenen Komponenten-Branches

Geprüfter Stand: `08c3d78db`, Merge von
`archive/component-value-before-slim-258c372db` nach `213e72cf6`.
Der Arbeitsbaum war vor dieser Untersuchung sauber.

## Befund

Der Merge verändert **keinen Runtime-Code, kein Werkzeug, keinen Test, keine
Workflow-Datei und keine Dokumentation**. Er fügt ausschließlich 2.734 Dateien
unter `artifacts/evaluation/` hinzu: 815.056 Textzeilen und 62.991.380 Bytes
unkomprimierter Dateiinhalte (rund 60,1 MiB). Es gibt daher keinen durch diesen
Merge begründeten Runtime-Rückbau.

| Wiederaufgenommener Ordner | Dateien | Bytes |
| --- | ---: | ---: |
| component_activation_probe_v1 | 1.186 | 25.983.801 |
| component_control_render_delay_v1 | 107 | 6.133.209 |
| component_control_timing_probe_v1 | 85 | 832.772 |
| component_retention_activation_probe_v1 | 88 | 1.743.960 |
| component_retention_v1 | 85 | 1.705.699 |
| component_value_v1 | 1.183 | 26.591.939 |

## Wenig sinnvolle Änderungen und Entscheidungen

1. **Alle generierten Rohdaten dauerhaft versionieren.** Der vorherige Abschluss
   hatte bewusst kompakte Manifeste, Prüfzahlen und Zusammenfassungen erhalten.
   `.gitignore` und die Komponenten-Dokumentation sehen Rohdaten lokal bzw. als
   CI-Artefakte vor. Der Recovery-Merge bringt gerade diese ausgeschlossenen
   Daten zurück. Ignore-Regeln wirken auf bereits versionierte Dateien nicht.
   Empfehlung: Bei einer gesonderten Repository-Bereinigung aus dem Index nehmen,
   dabei Originaldaten lokal oder in einem dauerhaften Nachweisarchiv erhalten.
   Diese Untersuchung entfernt keine wiedergefundenen Belege.
2. **Vorversuche als zusätzliche bestandene Abnahmen interpretieren.** Die
   Activation-Probe stammt noch vor der vollständigen Konstruktorabschaltung;
   Timing-/Render-Delay-Probes enthalten abgewiesene Kontrollen. Die damalige
   Suchmodulkopie ist ein historischer Nachweis, keine einzuspielende Runtime.
   Die definitive Abnahme und die negativen Vorversuche müssen unterscheidbar
   bleiben. Die vorhandene Abschlussdokumentation tut dies bereits.
3. **Bots wegen ähnlich guter kleiner Stichproben entfernen.** Der getrennte
   Abnahmebestand hatte keine Bot-Vorschläge erzeugt; gleiche Ergebnisse belegen
   dort keine Entbehrlichkeit seltener Fähigkeiten. Alle sechs Bots bleiben
   begründet erhalten. Ein Wiederherstellen älterer Schaltpunkte oder Entfernen
   von Bots wäre durch diese Daten nicht gerechtfertigt.
4. **Die auffällige Batchdauer als Konvertierungszeit oder Normalfall auslegen.**
   Die dokumentierten Unterbrechungen bis 22.587,672 Sekunden sind keine
   nachgewiesene typische Bildlaufzeit. Bilddeadline und CLI-Batchdauer bleiben
   getrennte Messgrößen; diese Untersuchung behauptet keine geklärte Ursache.

## Erneute unabhängige Prüfung

Beide vollständigen Messbestände wurden am 19. Oktober erneut mit den
vorhandenen Verifikatoren geprüft:

- Hauptmatrix: 348 Versuche, 343 SVGs, 230 unabhängige Freigaben.
- Getrennter Abnahmebestand: 27 Versuche, 27 SVGs, 27 Freigaben.
- Kein beobachteter Vorschlag eines abgeschalteten Bots; ein unbeobachteter
  Startabbruch bleibt im Hauptbestand ausdrücklich enthalten.
- Alle 377 archivierten Original-/SVG-Paare stimmen mit ihren Hashes überein.

```powershell
git diff 213e72cf6 08c3d78db --shortstat
git diff 213e72cf6 08c3d78db -- src tools tests docs .github .gitignore
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir artifacts/evaluation/component_value_v1
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir artifacts/evaluation/component_retention_v1
```

Es wurden **keine funktionalen Regressionen durch diesen Recovery-Merge
nachgewiesen**. Diese Aussage bezieht sich auf seine tatsächlich hinzugefügten
Dateien und die erneute Belegprüfung, nicht auf eine vollständige Konvertierung
des Katalogs. Das nächste dokumentierte Architekturpaket ist
[NEURAL-ELEMENTS-01](next_arbeitspaket_2026-10-19_neural_elements.md).
