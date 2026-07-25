from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta, timezone
import csv

tle_path = "tjs_clean.tle"
out_path = "tjs_geo.csv"

ts = load.timescale()
t = ts.now()
rows = []


def parse_tle_epoch(line1):
    # TLE 1行目のエポック部分：YYDDD.DDDDDDDD
    raw = line1[18:32].strip()

    yy = int(raw[:2])
    day = float(raw[2:])

    # NORADの年表記
    year = 2000 + yy if yy < 57 else 1900 + yy

    epoch_dt = (
        datetime(year, 1, 1, tzinfo=timezone.utc)
        + timedelta(days=day - 1)
    )

    return {
        "epoch_raw": raw,
        "epoch_day": f"{year}年{int(day)}日目",
        "epoch_utc": epoch_dt.strftime("%Y/%m/%d %H:%M:%S UTC"),
        "epoch_iso": epoch_dt.isoformat().replace("+00:00", "Z"),
    }


with open(tle_path, encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]


for i in range(0, len(lines), 3):
    name = lines[i]
    line1 = lines[i + 1]
    line2 = lines[i + 2]

    sat = EarthSatellite(line1, line2, name, ts)

    geocentric = sat.at(t)
    subpoint = geocentric.subpoint()

    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    alt_km = subpoint.elevation.km

    norad = line1[2:7].strip()

    epoch = parse_tle_epoch(line1)

    rows.append({
        "name": name,
        "norad": norad,
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "alt_km": round(alt_km, 1),

        "epoch_raw": epoch["epoch_raw"],
        "epoch_day": epoch["epoch_day"],
        "epoch_utc": epoch["epoch_utc"],
        "epoch_iso": epoch["epoch_iso"],
    })


rows.sort(key=lambda r: r["lon"])


with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "name",
            "norad",
            "lat",
            "lon",
            "alt_km",
            "epoch_raw",
            "epoch_day",
            "epoch_utc",
            "epoch_iso",
        ],
    )

    writer.writeheader()
    writer.writerows(rows)


print("saved", out_path)
print("count", len(rows))

for r in rows:
    print(
        r["name"],
        r["norad"],
        r["lon"],
        r["epoch_day"],
        r["epoch_utc"],
    )