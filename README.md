# Dis Jahrgangsbaum

Gib di Jahrgang i und lueg, wele Baum d Stadt Bärn im glyche Jahr gsetzt het: Art, Quartier,
Alter, Charte und es Plakat zum Teile («Ich bi e Winterlinde vo 1987, Länggass»).

Live (sobald GitHub Pages aktiviert ist): https://richardcervenka111-create.github.io/jahrgangsbaum/

## Warum

Bern hat einen öffentlichen Baumkataster mit Pflanzjahr und Standort jedes Stadtbaums. Als
Geoportal-Ebene schaut ihn niemand an. Als «mein Baum» wird er zu einem Spaziergang, einem
Geschenk für einen Geburtstag, einem Grund, einen Baum zu giessen. Nichts wird gesendet.

## Daten

`data/trees.json`: 24 025 Bäume, 539 Arten, Pflanzjahre 1820–2026, aus dem Baumkataster der
Stadt Bern (Geoportal-Export vom 25.09.2026, Stand der Daten 21.09.2026, File-Geodatabase, LV95).
Nutzungsbedingungen: freie Nutzung, **Quellenangabe «Geodaten Stadt Bern» ist Pflicht** und steht
auf Seite und Plakat. Der Kataster enthält kein Quartier; die Seite leitet es aus der Lage ab
(nächstes Quartierzentrum, «öppe»). Bei alten Bäumen ist das Pflanzjahr im Kataster geschätzt
(Häufungen 1905, 1925, 1945, 1965, 1985); die Seite sagt das dazu.

## Daten neu einspielen (bei Bedarf)

1. Baumkataster der Stadt Bern herunterladen (opendata.swiss → «Baumkataster» Stadt Bern, oder
   map.bern.ch Geoportal → Baumkataster → Export). Bevorzugt **GeoJSON** oder CSV; eine File-Geodatabase (.gdb) lässt sich mit `pyogrio` lesen (siehe Git-History dieses Repos).
2. `python3 scripts/convert_trees.py export.geojson --out data/trees.json`
   Der Konverter erkennt Spalten nach Stichwort (Pflanzjahr, Baumart, Latein, Strasse, Quartier)
   und rechnet LV95/LV03 nach WGS84 um. Er druckt, was er erkannt hat; bei einer falschen
   Spalte die Stichwortliste in `KEYS` anpassen.
3. `data/trees.json` committen. Ohne die Datei zeigt die Seite Beispieldaten mit Hinweis.

## Technik

Eine Datei, Bärndütsch mit hochdeutscher Zeile, Plakat als SVG → PNG im Browser (1080 × 1350).
Keine Karte eingebettet, dafür ein Link auf OpenStreetMap. Lizenz CC0; Baumdaten: Stadt Bern OGD,
Nutzungsbedingungen der Stadt beachten (Quellenangabe steht auf Seite und Plakat).
