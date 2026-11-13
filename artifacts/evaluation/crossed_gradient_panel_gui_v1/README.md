# GUI-Nachprüfung mit unveränderter Benutzereingabe

Der ursprüngliche Nachweis für AC0110_L verwendete eine sprachlich bereinigte
Katalogbeschreibung. Der lokale GUI-Auftrag behielt dagegen den ursprünglichen
Benutzertext einschließlich `Minnus-Zeichen` und `horizonalen` bei. Der neue
Form-Fit erkannte diese Schreibvarianten noch nicht und kehrte sofort zurück;
der generische Fallback speicherte wieder den fehlerhaften Entwurf. Ein
Serverneustart hätte diese Ursache nicht behoben.

Die Gegenprobe auf dem tatsächlich hochgeladenen GUI-PNG ergibt vor der
Korrektur: ursprünglicher Text → kein Fit; ausschließlich `Minnus`/`horizonal`
berichtigt → erfolgreicher Fit. Die gemeinsame Sprach-Normalisierung erkennt
jetzt diese begrenzten Schreibvarianten sowie `vertial`. Der Form-Fit verwendet
diese Normalisierung intern. Gespeicherte Benutzereingaben, Negationen und
zitierte Beschriftungen bleiben erhalten; keine Beschreibung wird durch den
Katalogtext ersetzt. Bildnamen und Referenz-SVGs werden nicht zur Lösung genutzt.

Die Regression enthält den vollständigen ursprünglichen Text als Fixture.
Ein echter GUI-Worker-Test lädt die JPEG-Bytes unter neutralem Namen, bereitet
sie über `Jobs.upload` auf und startet über `Jobs.start` denselben überwachten
Konverterprozess wie die Oberfläche. Der Test verlangt native Diagonalen,
Minus, Modellbestätigung und den GUI-Status `quality=passed`.

Zusätzlich wurde über die HTTP-API des bereits laufenden lokalen Servers ein
neuer Versuch mit der unveränderten Beschreibung des gescheiterten Auftrags
gestartet. Alte Versuche bleiben erhalten. Der neue Auftrag
`dc337b38746243288b8157d49d1c881a` meldet nach 32,1 Sekunden:
`SVG erstellt. Qualitätsprüfung bestanden.` Ein erneutes Auslesen über die API
bestätigt `done`, `passed` und `satisfactory=true`. MuPDF und unabhängig librsvg
bestehen ebenfalls. `summary.json` dokumentiert identische Quellpixel und
Beschreibungsprüfsummen vor und nach der Korrektur.

Die 42 gezielten Sprach-, Modell- und echten GUI-Worker-Tests bestehen.
Weitere Prüfungen und die bekannte unabhängige Gesamttestabweichung werden in
`checks.json` ausdrücklich ausgewiesen. Der Browser zeigt den neuen Auftrag
nach dem Neuladen der Seite automatisch als neuesten Eintrag; der Server muss
für die Konverterkorrektur nicht neu gestartet werden.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_description_language.py tests/test_crossed_gradient_panel_runtime.py tests/test_image_converter_gui.py::test_unedited_user_description_converts_through_real_gui_worker
```
