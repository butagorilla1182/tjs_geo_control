import csv
rows = list(csv.DictReader(open("tjs_geo.csv", encoding="utf-8")))
parts = []
parts.append("<html><head><meta charset=\"utf-8\"><title>TJS GEO</title></head><body>")
parts.append("<h1>TJS GEO longitude map</h1>")
parts.append("<p>CelesTrak GEO TLEから抽出したTJSの経度表示</p>")
parts.append("<svg width=\"1200\" height=\"420\" style=\"background:#001428;border:1px solid #999\">")
parts.append("<line x1=\"0\" y1=\"210\" x2=\"1200\" y2=\"210\" stroke=\"gray\"/>")
for r in rows:
    lon = float(r["lon"])
    lat = float(r["lat"])
    x = (lon + 180) / 360 * 1200
    y = 210 - lat * 4
    parts.append("<circle cx=\"{:.1f}\" cy=\"{:.1f}\" r=\"6\" fill=\"orange\"><title>{} lon {}</title></circle><text x=\"{:.1f}\" y=\"{:.1f}\" fill=\"white\" font-size=\"12\">{}</text>".format(x, y, r["name"], r["lon"], x+8, y+4, r["name"]))
parts.append("</svg>")
parts.append("<table border=\"1\"><tr><th>Name</th><th>NORAD</th><th>Lat</th><th>Lon</th><th>Alt km</th></tr>")
for r in rows:
    parts.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(r["name"], r["norad"], r["lat"], r["lon"], r["alt_km"]))
parts.append("</table></body></html>")
open("tjs_geo.html", "w", encoding="utf-8").write("\n".join(parts))
print("saved tjs_geo.html")
