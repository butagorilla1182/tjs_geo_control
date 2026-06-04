from skyfield.api import load, EarthSatellite
import csv

tle_path = "tjs_clean.tle"
out_path = "tjs_geo.csv"

ts = load.timescale()
t = ts.now()
rows = []

with open(tle_path, encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

for i in range(0, len(lines), 3):
    name = lines[i]
    line1 = lines[i+1]
    line2 = lines[i+2]
    sat = EarthSatellite(line1, line2, name, ts)
    geocentric = sat.at(t)
    subpoint = geocentric.subpoint()
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    alt_km = subpoint.elevation.km
    norad = line1[2:7].strip()
    rows.append({"name": name, "norad": norad, "lat": round(lat, 4), "lon": round(lon, 4), "alt_km": round(alt_km, 1)})

rows.sort(key=lambda r: r["lon"])

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "norad", "lat", "lon", "alt_km"])
    writer.writeheader()
    writer.writerows(rows)

print("saved", out_path)
print("count", len(rows))
for r in rows:
    print(r["name"], r["norad"], r["lon"])
