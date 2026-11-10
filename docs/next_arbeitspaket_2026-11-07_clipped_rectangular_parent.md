# Nächstes P0-Paket: angeschnittene äußere Verlaufsrechtecke

**SEARCH-STRUCTURE-CLIPPED-RECTANGULAR-PARENT**, Status **Planned**.
Fortsetzung von SEARCH-STRUCTURE-01 nach der
[Korrektur des Rundungsrenderers](next_arbeitspaket_2026-11-06_rounded_renderer.md).

## Ziel und Lieferumfang

Die bestehende gemeinsame Komposition soll angeschnittene äußere Rechtecke
anhand sichtbarer Seiten und Ecken rekonstruieren. Gemischte Kinder,
Überdeckungsgruppen, Einzelobjekte, Verlauf, helle Konturen und optional
beobachtete Rundungen bleiben im selben Such- und Qualitätsvertrag.

1. Vor Runtimeänderungen neue unabhängige librsvg-Raster mit Objekt-, Radius-,
   Tiefen- und Zugehörigkeitsmarkierungen sichern. Bildkanten, unterschiedliche
   Schnittrichtungen und Subpixellagen getrennt abdecken; bisherige Eingaben
   und ihre Prüfsummen erhalten.
2. Bildrandabschnitte von tatsächlich sichtbaren Elternseiten trennen.
   Fehlende Grenzen oder Radien ohne ausreichende unabhängige Beobachtung
   konservativ ablehnen. Kein Rückschluss aus Generator- oder Referenzdaten.
3. Elternhypothesen mit der vorhandenen begrenzten Strukturagenda und
   gemeinsamen Registrierung verbinden. Keine Sonderbehandlung nach Bildnamen,
   Familien oder Seeds; fünf Sekunden Bildbudget und 96 Zustände beibehalten.
4. Echte CLI vor/nach der Änderung, separate Zusatz- und Variantenkohorten,
   unabhängige native Objekt-/Relationsprüfung und beide Rasterrenderer
   verwenden. Sichtbare Ecken, Seiten und Restbild lokal prüfen; verdeckte
   Ecken nicht als positive Beobachtung zählen. Keine Qualitätsgrenze lockern.
5. Vollständig sichtbare scharfe/gerundete Eltern, angeschnittene Elternkreise,
   dünne Konturen und negative Evidenz als Regression mitprüfen.

HC0010 und Rail bleiben `sealed_unrun` ohne Konvertierungsversuch. Dieses
synthetische Teilpaket ersetzt weder SEARCH-STRUCTURE-01 noch die offene
unabhängige reale Gesamtabnahme.

## Start

```powershell
.venv/Scripts/python.exe -m pytest tests/test_rectangular_gradient_parent.py tests/test_rounded_gradient_parent.py tests/test_clipped_gradient_parent.py tests/detailtests/test_rounded_renderer.py -q
```
