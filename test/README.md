# Bildtest Workers AI (LOP 127, Schritt 1)

Die Bilder erzeugt der Workflow **Bildtest** (`automat/bildgen.py --vergleich test/`):
je Modell ein Unterordner mit denselben 5 Motiven, Übersicht in `vergleich.json`.
Ein erneuter Lauf erzeugt nur fehlende Bilder (z. B. nach leerem Tageskontingent).
Prüfen nach 06 §10.3: dokumentarisch, fotorealistisch, 4:5, keine Schrift, keine Logos,
keine Tracht, kein Kitsch, keine erkennbaren Gesichter; freie Fläche für den Bildtext
(laut Dateiname, wie im Pool).

| Datei | Motiv |
|---|---|
| 01_landstrasse-herbst_text-oben.jpg | Landstraße im Herbst |
| 02_wirtshaus_text-oben.jpg | Wirtshaus (Gaststube, leer) |
| 03_dorfplatz_text-oben.jpg | Dorfplatz |
| 04_see_text-oben.jpg | See |
| 05_neutral_text-mitte.jpg | neutrales Motiv für Themenmeldungen |
