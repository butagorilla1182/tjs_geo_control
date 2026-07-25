from pathlib import Path
from datetime import datetime, timedelta, timezone
import csv

from skyfield.api import load, EarthSatellite, wgs84


tle_path = Path("geo.tle")

out_csv = Path("tjs_geo.csv")
out_clean_tle = Path("tjs_clean.tle")
out_tjs_tle = Path("tjs.tle")

satcat_files = [
    Path("satcat_geo.csv"),
    Path("satcat_gpz.csv"),
]


def is_tjs(name: str) -> bool:
    upper = name.upper()

    return (
        upper.startswith("TJS-")
        or upper.startswith("TJS ")
        or "TONGXIN JISHU SHIYAN" in upper
    )


def parse_tle_epoch(line1: str):
    raw = line1[18:32].strip()

    yy = int(raw[:2])
    day = float(raw[2:])

    year = 2000 + yy if yy < 57 else 1900 + yy

    epoch_dt = (
        datetime(year, 1, 1, tzinfo=timezone.utc)
        + timedelta(days=day - 1)
    )

    return {
        "epoch_raw": raw,
        "epoch_day": f"{year}年{int(day):03d}日目",
        "epoch_utc": epoch_dt.strftime("%Y/%m/%d %H:%M:%S UTC"),
        "epoch_iso": epoch_dt.isoformat().replace("+00:00", "Z"),
        "epoch_dt": epoch_dt,
    }


# -------------------------
# SATCAT読み込み
# -------------------------

satcat = {}

for satcat_path in satcat_files:

    if not satcat_path.exists():
        print("SATCAT file not found:", satcat_path)
        continue

    with satcat_path.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:

        for row in csv.DictReader(f):

            norad = str(
                row.get("NORAD_CAT_ID", "")
            ).strip()

            if not norad:
                continue

            satcat[norad] = {
                "launch_date": str(
                    row.get("LAUNCH_DATE", "")
                ).strip(),

                "launch_site": str(
                    row.get("LAUNCH_SITE", "")
                ).strip(),
            }


print("SATCAT records loaded:", len(satcat))


# -------------------------
# 更新前のTJS一覧
# -------------------------

old_norad = set()

if out_csv.exists():
    try:
        with out_csv.open(
            encoding="utf-8"
        ) as f:

            for row in csv.DictReader(f):
                if row.get("norad"):
                    old_norad.add(
                        row["norad"]
                    )

    except Exception as e:
        print(
            "Could not read old CSV:",
            e
        )


ts = load.timescale()
t = ts.now()


lines = [
    line.strip()
    for line in tle_path.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()
    if line.strip()
]


# -------------------------
# NORAD IDごとに最新TLEだけ採用
# -------------------------

satellites = {}

i = 0

while i < len(lines) - 2:

    name = lines[i]
    line1 = lines[i + 1]
    line2 = lines[i + 2]

    if not (
        line1.startswith("1 ")
        and line2.startswith("2 ")
    ):
        i += 1
        continue

    if is_tjs(name):

        try:
            norad = line1[2:7].strip()
            epoch = parse_tle_epoch(line1)

            candidate = {
                "name": name,
                "norad": norad,
                "line1": line1,
                "line2": line2,
                "epoch": epoch,
            }

            current = satellites.get(
                norad
            )

            # GEOとGPZに重複した場合、
            # エポックが新しい方を採用
            if (
                current is None
                or epoch["epoch_dt"]
                > current["epoch"]["epoch_dt"]
            ):
                satellites[norad] = candidate

        except Exception as e:
            print(
                "TLE parse skip:",
                name,
                e
            )

    i += 3


# -------------------------
# 座標計算 + SATCAT結合
# -------------------------

rows = []
tle_output = []


for item in satellites.values():

    try:
        name = item["name"]
        norad = item["norad"]
        line1 = item["line1"]
        line2 = item["line2"]
        epoch = item["epoch"]

        sat = EarthSatellite(
            line1,
            line2,
            name,
            ts
        )

        geocentric = sat.at(t)
        subpoint = wgs84.subpoint(
            geocentric
        )

        satcat_info = satcat.get(
            norad,
            {}
        )

        rows.append({
            "name": name,
            "norad": norad,

            "lat": round(
                subpoint.latitude.degrees,
                4
            ),

            "lon": round(
                subpoint.longitude.degrees,
                4
            ),

            "alt_km": round(
                subpoint.elevation.km,
                1
            ),

            "launch_date":
                satcat_info.get(
                    "launch_date",
                    ""
                ),

            "launch_site":
                satcat_info.get(
                    "launch_site",
                    ""
                ),

            "epoch_raw":
                epoch["epoch_raw"],

            "epoch_day":
                epoch["epoch_day"],

            "epoch_utc":
                epoch["epoch_utc"],

            "epoch_iso":
                epoch["epoch_iso"],
        })

        tle_output.extend([
            name,
            line1,
            line2
        ])

    except Exception as e:
        print(
            "Satellite calculation skip:",
            item["name"],
            e
        )


rows.sort(
    key=lambda r: r["lon"]
)


# -------------------------
# CSV保存
# -------------------------

with out_csv.open(
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "name",
            "norad",
            "lat",
            "lon",
            "alt_km",
            "launch_date",
            "launch_site",
            "epoch_raw",
            "epoch_day",
            "epoch_utc",
            "epoch_iso",
        ]
    )

    writer.writeheader()
    writer.writerows(rows)


# -------------------------
# TJS TLE保存
# -------------------------

tle_text = "\n".join(
    tle_output
) + "\n"

out_clean_tle.write_text(
    tle_text,
    encoding="utf-8"
)

out_tjs_tle.write_text(
    tle_text,
    encoding="utf-8"
)


# -------------------------
# ログ
# -------------------------

new_rows = [
    r for r in rows
    if r["norad"] not in old_norad
]


print("saved:", out_csv)
print("TJS count:", len(rows))


if new_rows:

    print("")
    print(
        "=== NEW TJS SATELLITES ==="
    )

    for r in new_rows:
        print(
            "NEW:",
            r["name"],
            "NORAD:",
            r["norad"],
            "Launch:",
            r["launch_date"],
            "Site:",
            r["launch_site"],
        )

else:
    print(
        "No new TJS satellites."
    )


print("")
print("=== CURRENT TJS ===")

for r in rows:
    print(
        r["name"],
        r["norad"],
        "Launch:",
        r["launch_date"],
        "Site:",
        r["launch_site"],
        "Epoch:",
        r["epoch_utc"],
    )