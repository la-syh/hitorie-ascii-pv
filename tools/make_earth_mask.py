#!/usr/bin/env python3
"""Regenerate assets/earth_mask.txt from Natural Earth (public domain).

Only needed if you want to rebuild the bundled land mask; the PV renderer
reads the committed text file and never touches the network.

    python3 tools/make_earth_mask.py ne_110m_land.geojson assets/earth_mask.txt

Download the GeoJSON from
https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson
"""
import json
import sys

from PIL import Image, ImageDraw

W, H = 360, 180  # 1 degree per cell, equirectangular


def main(src: str, dst: str) -> None:
    gj = json.load(open(src, encoding="utf-8"))
    ss = 4
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)

    def proj(lon, lat):
        return ((lon + 180) / 360 * W * ss, (90 - lat) / 180 * H * ss)

    for feat in gj["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            outer, *holes = poly
            d.polygon([proj(*p[:2]) for p in outer], fill=255)
            for h in holes:
                d.polygon([proj(*p[:2]) for p in h], fill=0)
    im = im.resize((W, H), Image.BOX)
    px = im.load()
    rows = ["".join("#" if px[x, y] >= 96 else "." for x in range(W)) for y in range(H)]
    header = ("# Earth land mask, 360x180 equirectangular (1 deg/cell), '#' = land.\n"
              "# Derived from Natural Earth ne_110m_land (public domain) by tools/make_earth_mask.py\n")
    open(dst, "w", encoding="utf-8").write(header + "\n".join(rows) + "\n")
    print(f"wrote {dst}: {sum(r.count('#') for r in rows)} land cells")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
