# GUI: vollständiges Zeitbudget und sichtbarer Vektorentwurf

Der gespeicherte AC0070_L-Auftrag endete zuvor nach 2,4 Sekunden ohne Vorschau:
Die Pfeilerkennung scheiterte; die Rasterkopie in einer SVG-Hülle wurde abgelehnt.
Die unveränderte Benutzereingabe wurde mit neutralem Dateinamen erneut ausgeführt.

## Ergebnis des vollständigen Laufs

- Profil: gründlich, 240 Sekunden gemeinsames Suchbudget.
- Gesamtdauer einschließlich Abschlussprüfung: 240,8 Sekunden.
- Erster Versuch fehlgeschlagen; verbleibende Zeit für native Struktursuche und Parameteroptimierung verwendet.
- 77.320 Rasterauswertungen in der Wiederherstellung; 27 veröffentlichte Verbesserungen.
- Ergebnis: drei native Rechtecke und zwei Dreiecke, ohne eingebettetes Rasterbild oder Konturpfade.
- Pixelprüfung bestanden: MSE 0,0001523242, Vordergrund-IoU 0,9986413, Kantenausrichtung 0,8930339.
- Weiterhin **Entwurf**: Die Eingabe verlangt links eine Spitze nach unten und rechts nach oben; das Original zeigt die umgekehrten Richtungen. Die Beschreibung wird nicht stillschweigend korrigiert und der Entwurf nicht als semantisch bestanden ausgegeben.

Die vollständige Eingabe, der Seed und die Messwerte stehen in `summary.json`.
Die lokalen Dateien `source.png`, `result.svg` und `comparison.png` sowie der rohe
GUI-Auftrag unter `jobs/` sind entsprechend der Repository-Regeln nicht versioniert.

## Prüfung

Die neuen Tests prüfen den elementweisen Aufbau am echten Raster mit neutralem
Namen, generische Struktursuche, die gemeinsame Deadline, Vorschauaktualisierungen,
Behalten eines besseren bisherigen Vektors, Abbrechen und die Wiederherstellung
bei Prozessabbruch zwischen SVG- und Berichtsschreiben. Die strikte normale
Pfeilerkennung weist die widersprüchliche Eingabe weiterhin zurück.

Die GUI-Suite besteht einschließlich der vier lokalen HTTP-/Prozessprüfungen;
diese vier benötigen außerhalb der Sandbox lokale Socket- und Prozessrechte.
Zusätzlich bestehen die Pfeil-/Such-/Initialisierungs-, Struktur-/Kompositions-/
Gruppen-/Deadline- und JavaScript-Prüfungen. Siehe `checks.json`.

Die laufende Webserverinstanz muss für den geänderten Python-Code neu gestartet
und die Browseransicht neu geladen werden. Bestehende fehlgeschlagene Aufträge
bleiben als Diagnose erhalten; ein erneuter Start erzeugt einen neuen Auftrag.
