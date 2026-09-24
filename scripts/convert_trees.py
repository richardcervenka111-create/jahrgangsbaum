#!/usr/bin/env python3
"""Convert an export of the Stadt Bern Baumkataster into data/trees.json for the page.

Accepts GeoJSON (.geojson/.json) or CSV (.csv, ; or , separated) as exported from
opendata.swiss / map.bern.ch. Field names differ between exports, so columns are detected
by keyword (case-insensitive):
  year     : pflanzjahr, jahr, planted, baumalter? (no), year
  species  : baumart, art, deutsch, name_de
  latin    : latein, lateinisch, botanisch, scientific, art_lat
  street   : strasse, standort, adresse, lage
  quarter  : quartier, stadtteil, kreis
  x/y      : e/n or x/y (LV95 or LV03) or lon/lat; GeoJSON geometry wins.
Output: compact JSON {source, fetched, fields:{species:[],latin:[],street:[],quarter:[]},
        trees:[[year, speciesIdx, latinIdx, streetIdx, quarterIdx, lat, lon], ...]}
Usage: python3 scripts/convert_trees.py export.geojson [--out data/trees.json]
"""
import csv, json, math, sys, argparse
from datetime import date

def lv95_to_wgs84(e, n):
    # swisstopo approximate formulas (accuracy ~1 m), accepts LV95 (2.6M/1.2M) or LV03
    if e > 2_000_000: e -= 2_000_000
    if n > 1_000_000: n -= 1_000_000
    y = (e - 600_000) / 1_000_000
    x = (n - 200_000) / 1_000_000
    lon = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    lat = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return lat * 100 / 36, lon * 100 / 36

KEYS = {
    'year': ['pflanzjahr', 'pflanz_jahr', 'planted', 'jahr', 'year'],
    'species': ['baumart_de', 'baumart', 'art_de', 'deutsch', 'name_de', 'art', 'gattung_de'],
    'latin': ['baumart_lat', 'latein', 'lateinisch', 'botanisch', 'scientific', 'art_lat', 'name_lat'],
    'street': ['strasse', 'standort', 'adresse', 'lage', 'street'],
    'quarter': ['quartier', 'stadtteil', 'kreis', 'gebiet'],
}

def pick(cols, kind):
    low = {c.lower(): c for c in cols}
    for k in KEYS[kind]:
        for lc, orig in low.items():
            if k in lc:
                return orig
    return None

def rows_from_file(path):
    if path.lower().endswith('.csv'):
        with open(path, encoding='utf-8-sig', newline='') as f:
            sample = f.read(4096); f.seek(0)
            delim = ';' if sample.count(';') > sample.count(',') else ','
            for r in csv.DictReader(f, delimiter=delim):
                yield r, None
    else:
        with open(path, encoding='utf-8') as f:
            g = json.load(f)
        feats = g.get('features', g if isinstance(g, list) else [])
        for ft in feats:
            props = ft.get('properties', ft.get('attributes', {})) or {}
            geom = ft.get('geometry')
            yield props, geom

def to_float(v):
    try: return float(str(v).replace(',', '.'))
    except Exception: return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--out', default='data/trees.json')
    a = ap.parse_args()
    rows = list(rows_from_file(a.src))
    if not rows: sys.exit('no rows')
    cols = list(rows[0][0].keys())
    f = {k: pick(cols, k) for k in KEYS}
    print('columns:', cols); print('detected:', f)
    if not f['year']: sys.exit('no planting-year column found; rename it to PFLANZJAHR')
    xcol = next((c for c in cols if c.lower() in ('e', 'x', 'lon', 'longitude', 'east', 'ost', 'x_lv95', 'e_lv95')), None)
    ycol = next((c for c in cols if c.lower() in ('n', 'y', 'lat', 'latitude', 'north', 'nord', 'y_lv95', 'n_lv95')), None)
    idx = {k: {} for k in ('species', 'latin', 'street', 'quarter')}
    lists = {k: [] for k in idx}
    def ix(kind, val):
        val = (str(val).strip() if val is not None else '') or ''
        if val.lower() in ('nan', 'none', 'null'): val = ''
        if val not in idx[kind]:
            idx[kind][val] = len(lists[kind]); lists[kind].append(val)
        return idx[kind][val]
    trees = []; skipped = 0
    for props, geom in rows:
        y = to_float(props.get(f['year']))
        if y is None or y < 1600 or y > date.today().year: skipped += 1; continue
        lat = lon = None
        if geom and geom.get('type') == 'Point':
            gx, gy = geom['coordinates'][:2]
            if abs(gx) <= 180 and abs(gy) <= 90: lon, lat = gx, gy
            else: lat, lon = lv95_to_wgs84(gx, gy)
        elif xcol and ycol:
            gx, gy = to_float(props.get(xcol)), to_float(props.get(ycol))
            if gx is not None and gy is not None:
                if abs(gx) <= 180 and abs(gy) <= 90: lon, lat = gx, gy
                else: lat, lon = lv95_to_wgs84(gx, gy)
        if lat is None: skipped += 1; continue
        trees.append([int(y), ix('species', props.get(f['species'])) if f['species'] else 0,
                      ix('latin', props.get(f['latin'])) if f['latin'] else 0,
                      ix('street', props.get(f['street'])) if f['street'] else 0,
                      ix('quarter', props.get(f['quarter'])) if f['quarter'] else 0,
                      round(lat, 5), round(lon, 5)])
    for k in idx:
        if not lists[k]: lists[k] = ['']
    years = sorted(set(tr[0] for tr in trees))
    out = {'source': 'Stadt Bern, Baumkataster (Open Government Data)', 'fetched': date.today().isoformat(),
           'fields': lists, 'trees': trees}
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    print(f'wrote {a.out}: {len(trees)} trees, {skipped} skipped, years {years[0]}–{years[-1]}, {len(lists["species"])} species')

if __name__ == '__main__':
    main()
