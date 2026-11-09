#!/usr/bin/env python3
"""Draw the images of the profile README (assets/*.svg), each in a light and a
dark version, from scripts/profile.json.

Text is drawn as outlines of Source Serif 4 and Source Sans 3 (scripts/fonts,
SIL Open Font License), so the images look the same on every machine. The
backgrounds are transparent and the colours follow the light and dark GitHub
themes; README.md picks the version with <picture> and prefers-color-scheme.

    python scripts/profile_art.py            # numbers and skills
    python scripts/profile_art.py --banner   # also the banner (numpy, matplotlib)
"""
import functools
import json
import math
import os
import sys
from html import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
DATA = os.path.join(HERE, "profile.json")
WIDTH = 860

THEMES = {
    "dark": dict(fg="#e6edf3", muted="#9198a1", faint="#6b737e", border="#3d444d", link="#4493f8",
                 dot="#334051", grat="#151b23", home="#e3b341",
                 sats=["#79b8e0", "#6cc4a4", "#e0a964", "#c99ad6", "#ec8f7d"]),
    "light": dict(fg="#1f2328", muted="#59636e", faint="#818b98", border="#d1d9e0", link="#0969da",
                  dot="#c3ccd6", grat="#eff2f5", home="#bf8700",
                  sats=["#2f73a8", "#25856a", "#b26a16", "#8a55a0", "#b9533f"]),
}

FONTS = {
    "name": ("SourceSerif4.ttf", dict(wght=600, opsz=60)),
    "num": ("SourceSerif4.ttf", dict(wght=560, opsz=36)),
    "txt": ("SourceSans3.ttf", dict(wght=400)),
    "txtm": ("SourceSans3.ttf", dict(wght=500)),
    "txtb": ("SourceSans3.ttf", dict(wght=600)),
}


# Text as outlines -------------------------------------------------------------

@functools.lru_cache(None)
def font(key):
    path, axes = FONTS[key]
    return instancer.instantiateVariableFont(TTFont(os.path.join(HERE, "fonts", path)), axes)


def width(key, text, size):
    f = font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c)) or cmap[ord("?")]][0] for c in text) * size / upm


def text(key, s, size, x, y, fill, anchor="start", tracking=0.0):
    f = font(key)
    cmap, hmtx, glyphs = f.getBestCmap(), f["hmtx"], f.getGlyphSet()
    scale = size / f["head"].unitsPerEm
    w = width(key, s, size) + tracking * max(len(s) - 1, 0)
    x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
    pen = SVGPathPen(glyphs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    for c in s:
        g = cmap.get(ord(c)) or cmap[ord("?")]
        glyphs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[g][0] * scale + tracking
    return '<path d="%s" fill="%s"/>' % (pen.getCommands(), fill)


def wrap(key, s, size, maxw):
    lines, cur = [], ""
    for word in s.split(" "):
        t = cur + " " + word if cur else word
        if width(key, t, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + [cur] if cur else lines


def svg(w, h, body, label):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
            'aria-label="%s"><title>%s</title>%s</svg>\n' % (w, h, w, h, escape(label), escape(label), body))


def write(name, content):
    path = os.path.join(ASSETS, name)
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == content:
                return
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", os.path.relpath(path))


# Numbers ----------------------------------------------------------------------

def metrics(d, mode):
    t = THEMES[mode]
    s = d["scholar"]
    items = [("{:,}".format(s["citations"]), "citations"), (str(s["h_index"]), "h-index"),
             (str(s["i10_index"]), "i10-index"), (d["papers"], "papers"), (str(d["repositories"]), "repositories")]
    h, cw = 78, WIDTH / len(items)
    b = []
    for i, (value, label) in enumerate(items):
        cx = cw * i + cw / 2
        if i:
            b.append('<rect x="%.1f" y="16" width="1" height="%d" fill="%s"/>' % (cw * i, h - 32, t["border"]))
        b.append(text("num", value, 32, cx, 42, t["fg"], "middle"))
        b.append(text("txt", label, 14, cx, 63, t["muted"], "middle"))
    return svg(WIDTH, h, "".join(b), ", ".join("%s %s" % (l, v) for v, l in items))


def skills(d, mode):
    t = THEMES[mode]
    colw, gap, lh = 404, 52, 21
    groups = d["skills"]
    half = (len(groups) + 1) // 2
    cols, heights = [[], []], [0, 0]
    for k, (head, items) in enumerate(groups):
        c = 0 if k < half else 1
        x, y = c * (colw + gap), heights[c]
        cols[c].append('<rect x="%d" y="%d" width="%d" height="1" fill="%s"/>' % (x, y, colw, t["border"]))
        cols[c].append(text("txtb", head, 15.5, x, y + 26, t["fg"]))
        lines = wrap("txt", ", ".join(items), 14.5, colw)
        for j, line in enumerate(lines):
            cols[c].append(text("txt", line, 14.5, x, y + 49 + j * lh, t["muted"]))
        heights[c] = y + 49 + (len(lines) - 1) * lh + 24
    label = "Technical skills. " + " ".join("%s: %s." % (h, ", ".join(i)) for h, i in groups)
    return svg(WIDTH, max(heights) - 10, "".join(cols[0] + cols[1]), label)


def github(d, mode):
    t, g = THEMES[mode], d["github"]
    h = 128
    b = ['<rect x="0.5" y="0.5" width="%d" height="%d" rx="6" fill="none" stroke="%s"/>' % (WIDTH - 1, h - 1, t["border"])]
    cells = [("{:,}".format(g["commits"]), "commits in 12 months"), (str(g["stars"]), "stars"),
             (str(g["repos"]), "public repositories"), (str(g["followers"]), "followers")]
    x = 26
    for value, label in cells:
        b.append(text("num", value, 28, x, 64, t["fg"]))
        b.append(text("txt", label, 13, x, 86, t["muted"]))
        x += max(width("num", value, 28), width("txt", label, 13)) + 34
    x0, bw = 486, 348
    b.append(text("txtb", "Languages", 14, x0, 34, t["fg"]))
    b.append('<clipPath id="bar"><rect x="%d" y="46" width="%d" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">' % (x0, bw))
    xx = x0
    for name, pct, color in g["languages"]:
        b.append('<rect x="%.1f" y="46" width="%.1f" height="8" fill="%s"/>' % (xx, bw * pct / 100 + 0.6, color))
        xx += bw * pct / 100
    b.append("</g>")
    for k, (name, pct, color) in enumerate(g["languages"][:6]):
        cx, cy = x0 + (k % 3) * 118, 80 + (k // 3) * 22
        b.append('<circle cx="%d" cy="%.1f" r="5" fill="%s"/>' % (cx + 5, cy - 4.5, color))
        b.append(text("txtm", name, 13, cx + 16, cy, t["fg"]))
        b.append(text("txt", "%.1f%%" % pct, 13, cx + 22 + width("txtm", name, 13), cy, t["muted"]))
    label = "GitHub: %s commits in 12 months, %s stars, %s public repositories, %s followers" % tuple(v for v, _ in cells)
    return svg(WIDTH, h, "".join(b), label)


# Banner -----------------------------------------------------------------------
# Equal Earth map centred on the Pacific (Viet Nam, Texas and the Middle East all
# in view), land as dots, ground tracks of five satellites for one orbit each
# (circular orbits, no nodal drift), and the regions of the work.

LON0 = 160.0
SATELLITES = [  # label, inclination (deg), period (min), ascending node (deg E), seconds per orbit
    ("SMAP", 98.1, 98.5, 205.0, 34),
    ("SWOT", 77.6, 102.8, 120.0, 38),
    ("NISAR", 98.4, 99.7, 300.0, 36),
    ("Landsat 9", 98.2, 98.9, 60.0, 33),
    ("Sentinel-1", 98.2, 98.6, 255.0, 35),
]
REGIONS = [  # label, lon, lat, home, label offset
    ("US croplands and floods", -98.0, 40.5, False, (9, -7)),
    ("Temple, Texas", -97.34, 31.10, True, (9, 13)),
    ("Eastern Sahara and Levant", 31.0, 30.0, False, (9, -8)),
    ("Viet Nam", 106.5, 16.0, False, (9, 4)),
]
NAME_BOX = (452, 214, 336, 104)


def banner(mode, cache={}):
    import numpy as np
    from matplotlib.path import Path

    A1, A2, A3, A4, M = 1.340264, -0.081106, 0.000893, 0.003796, math.sqrt(3) / 2

    def equal_earth(lon, lat):
        lam = np.radians(((np.asarray(lon, float) - LON0 + 180) % 360) - 180)
        th = np.arcsin(M * np.sin(np.radians(np.asarray(lat, float))))
        t2, t6 = th * th, th ** 6
        return (lam * np.cos(th) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2))),
                th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2)))

    xmax, ymax = 2.70662848, 1.31736276
    sc = (WIDTH - 8) / (2 * xmax)
    h = int(round(2 * ymax * sc)) + 8

    def proj(lon, lat):
        x, y = equal_earth(lon, lat)
        return WIDTH / 2 + x * sc, h / 2 - y * sc

    def line(xs, ys):
        return "M" + "L".join("%.1f %.1f" % p for p in zip(xs, ys))

    if "dots" not in cache:
        step = 4.2
        gx, gy = np.meshgrid(np.arange(step / 2, WIDTH, step), np.arange(step / 2, h, step))
        pts = np.c_[gx.ravel(), gy.ravel()]
        inside = np.zeros(len(pts), bool)
        with open(os.path.join(HERE, "data", "ne_110m_land.geojson"), encoding="utf-8") as f:
            features = json.load(f)["features"]
        for feat in features:
            g = feat["geometry"]
            for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
                ring = np.asarray(poly[0], float)
                rel = ((ring[:, 0] - LON0 + 180) % 360) - 180
                parts = [rel] if rel.max() - rel.min() < 300 else \
                    [np.where(rel * s < 0, s * 179.99, rel) for s in (1, -1)]   # rings cut by the map edge
                for p in parts:
                    x, y = proj(p + LON0, ring[:, 1])
                    inside |= Path(np.c_[x, y]).contains_points(pts)
        cache["dots"] = pts[inside]
    t = THEMES[mode]
    dots = "".join("M%.1f %.1fh0" % (x, y) for x, y in cache["dots"])
    grat = []
    for lat in range(-60, 90, 30):
        lons = np.linspace(LON0 - 179.9, LON0 + 179.9, 120)
        grat.append(line(*proj(lons, np.full_like(lons, lat))))
    lats = np.linspace(-90, 90, 121)
    for side in (-179.999, 179.999):
        grat.append(line(*proj(np.full_like(lats, LON0 + side), lats)))

    tracks, sats = [], []
    we = 360.0 / 86164.0
    for k, (label, inc, period, node, dur) in enumerate(SATELLITES):
        c = t["sats"][k]
        u = np.linspace(0, 2 * math.pi, 800)
        i = math.radians(inc)
        lat = np.degrees(np.arcsin(np.sin(i) * np.sin(u)))
        lon = node + np.degrees(np.unwrap(np.arctan2(math.cos(i) * np.sin(u), np.cos(u)))) - we * u / (2 * math.pi) * period * 60
        rel = ((lon - LON0 + 180) % 360) - 180
        x, y = proj(lon, lat)
        d = "".join(("M" if j == 0 or abs(rel[j] - rel[j - 1]) > 180 else "L") + "%.1f,%.1f" % (x[j], y[j])
                    for j in range(len(u)))
        tracks.append('<path id="t%d" d="%s" fill="none" stroke="%s" stroke-width="0.9" stroke-opacity="0.28"/>' % (k, d, c))
        begin = 7 * k + 3
        for g in range(1, 11):   # fading tail
            sats.append('<circle r="%.2f" fill="%s" fill-opacity="%.2f"><animateMotion dur="%ds" repeatCount="indefinite" '
                        'begin="-%.2fs"><mpath href="#t%d"/></animateMotion></circle>'
                        % (2.8 - 0.17 * g, c, 0.55 * (1 - g / 11), dur, begin - 0.16 * g, k))
        sats.append('<g><circle r="3" fill="%s"/><circle r="7" fill="none" stroke="%s" stroke-opacity="0.45"/>%s'
                    '<animateMotion dur="%ds" repeatCount="indefinite" begin="-%ds"><mpath href="#t%d"/></animateMotion></g>'
                    % (c, c, text("txtm", label, 11.5, 10, 4, c), dur, begin, k))

    marks = []
    for label, lon, lat, home, (dx, dy) in REGIONS:
        x, y = (float(v) for v in proj(lon, lat))
        c = t["home"] if home else t["fg"]
        marks.append('<circle cx="%.1f" cy="%.1f" r="2.8" fill="%s"/>' % (x, y, c))
        marks.append('<circle cx="%.1f" cy="%.1f" r="3" fill="none" stroke="%s" stroke-width="1">'
                     '<animate attributeName="r" values="3;14" dur="3.4s" repeatCount="indefinite"/>'
                     '<animate attributeName="stroke-opacity" values="0.7;0" dur="3.4s" repeatCount="indefinite"/></circle>'
                     % (x, y, c))
        marks.append(text("txt", label, 12, x + dx, y + dy, t["muted"]))

    bx, by, bw, bh = NAME_BOX
    words = [text("name", "Duc Tran", 54, bx, by + 50, t["fg"], tracking=-0.4),
             text("txt", "Hydrologist and Earth system scientist", 16, bx + 1, by + 78, t["fg"]),
             text("txt", "USDA Agricultural Research Service, Temple, Texas", 14, bx + 1, by + 98, t["muted"]),
             text("txt", "Ground tracks of SMAP, SWOT, NISAR, Landsat 9 and Sentinel-1, one orbit each",
                  11, WIDTH - 10, h - 8, t["faint"], "end")]
    body = ('<defs><filter id="soft" x="-30%%" y="-60%%" width="160%%" height="220%%"><feGaussianBlur stdDeviation="14"/></filter>'
            '<mask id="quiet" maskUnits="userSpaceOnUse" x="0" y="0" width="%d" height="%d"><rect width="%d" height="%d" fill="#fff"/>'
            '<rect x="%d" y="%d" width="%d" height="%d" rx="18" fill="#000" filter="url(#soft)"/>'
            '<rect x="%d" y="%d" width="420" height="24" fill="#000" filter="url(#soft)"/></mask></defs>'
            % (WIDTH, h, WIDTH, h, bx - 18, by - 6, bw + 36, bh + 18, WIDTH - 420, h - 24)
            + '<g mask="url(#quiet)"><path d="%s" fill="none" stroke="%s" stroke-width="0.8"/>' % ("".join(grat), t["grat"])
            + '<path d="%s" stroke="%s" stroke-width="2.1" stroke-linecap="round"/>' % (dots, t["dot"])
            + "".join(tracks) + "".join(sats) + "</g>" + "".join(marks) + "".join(words))
    return svg(WIDTH, h, body, "Duc Tran, hydrologist and Earth system scientist. Satellite ground tracks over the Earth")


# ------------------------------------------------------------------------------

def draw(d, with_banner=False):
    os.makedirs(ASSETS, exist_ok=True)
    for mode in THEMES:
        write("metrics-%s.svg" % mode, metrics(d, mode))
        write("skills-%s.svg" % mode, skills(d, mode))
        write("github-%s.svg" % mode, github(d, mode))
        if with_banner:
            write("banner-%s.svg" % mode, banner(mode))


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    draw(load(), with_banner="--banner" in sys.argv)
