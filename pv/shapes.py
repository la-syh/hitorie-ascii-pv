"""Reusable ASCII motifs: globe, picture frame, figure, clock, phone, room...

All shapes are drawn in "square units" (see ``Canvas.X/Y``) so circles stay
round on the non-square character grid.  Everything here is a pure function
of its arguments (no hidden state), so any frame can be rendered on its own.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from .canvas import Canvas
from .glyphs import ROOT

# ----------------------------------------------------------------------- SDF


def sd_circle(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def sd_capsule(X, Y, ax, ay, bx, by, r):
    pax, pay = X - ax, Y - ay
    bax, bay = bx - ax, by - ay
    h = np.clip((pax * bax + pay * bay) / (bax * bax + bay * bay + 1e-9), 0, 1)
    return np.hypot(pax - bax * h, pay - bay * h) - r


def sd_box(X, Y, cx, cy, hw, hh, r=0.0):
    qx = np.abs(X - cx) - hw + r
    qy = np.abs(Y - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_poly(X, Y, pts):
    """Signed distance to a convex/concave polygon (list of (x,y))."""
    pts = np.asarray(pts, np.float32)
    d = np.full(X.shape, np.inf, np.float32)
    s = np.ones(X.shape, np.float32)
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[i - 1]
        ex, ey = bx - ax, by - ay
        wx, wy = X - ax, Y - ay
        h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-9), 0, 1)
        d = np.minimum(d, (wx - ex * h) ** 2 + (wy - ey * h) ** 2)
        c1 = Y >= ay
        c2 = Y < by
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def draw_sdf(cv: Canvas, d: np.ndarray, fg, fill="#", edge="+", aa=0.7, bg=None, mask=None):
    """Fill cells inside an SDF (d<0) with ``fill``; soft edge with ``edge``."""
    inside = d < 0
    rim = (d >= 0) & (d < aa)
    if mask is not None:
        inside &= mask
        rim &= mask
    if edge:
        cv.fill(rim, edge, fg=fg)
    cv.fill(inside, fill, fg=fg, bg=bg)
    return inside


# --------------------------------------------------------------------- globe


@lru_cache(maxsize=1)
def earth_mask() -> np.ndarray:
    rows = [r for r in (ROOT / "assets" / "earth_mask.txt").read_text().splitlines()
            if r and not r.startswith("#")]
    return np.array([[c == "#" for c in r] for r in rows], dtype=bool)


def globe(cv: Canvas, cx: float, cy: float, R: float, lon0: float, tilt: float = 0.35,
          fg=None, dim=None, accent=None, light=(-0.5, -0.45, 0.75), grid=True,
          land_chars="%#@", sea_chars=" .:", rim_char="o", land_bright=1.0,
          mask_out: np.ndarray | None = None) -> np.ndarray:
    """Orthographic ASCII Earth. Returns boolean mask of the disc."""
    x0, x1 = int(max(0, cx - R - 2)), int(min(cv.W, cx + R + 2))
    y0 = int(max(0, (cy - R) / cv.aspect - 2))
    y1 = int(min(cv.H, (cy + R) / cv.aspect + 2))
    if x1 <= x0 or y1 <= y0:
        return np.zeros((cv.H, cv.W), bool)
    X = cv.X[y0:y1, x0:x1]
    Y = cv.Y[y0:y1, x0:x1]
    dx, dy = (X - cx) / R, (Y - cy) / R
    r2 = dx * dx + dy * dy
    disc = r2 < 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    # rotate (dx, -dy, z) around x axis by tilt
    py = -dy
    ct, st = math.cos(tilt), math.sin(tilt)
    yy = py * ct + z * st
    zz = -py * st + z * ct
    lat = np.degrees(np.arcsin(np.clip(yy, -1, 1)))
    lon = (np.degrees(np.arctan2(dx, zz)) + lon0 + 180) % 360 - 180
    em = earth_mask()
    li = np.clip(((90 - lat) / 180 * em.shape[0]).astype(int), 0, em.shape[0] - 1)
    lj = np.clip(((lon + 180) / 360 * em.shape[1]).astype(int), 0, em.shape[1] - 1)
    land = em[li, lj] & disc
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    shade = np.clip((dx * lx + -dy * -ly + z * lz) / ln, 0, 1)  # screen-space lambert
    shade = 0.25 + 0.75 * shade

    ch = cv.ch[y0:y1, x0:x1]
    fgc = cv.fg[y0:y1, x0:x1]
    land_ids = cv.ids(land_chars)
    sea_ids = cv.ids(sea_chars)
    k = np.clip((shade * land_bright * len(land_ids)).astype(int), 0, len(land_ids) - 1)
    ch[land] = land_ids[k[land]]
    sea = disc & ~land
    ks = np.clip((shade * len(sea_ids)).astype(int), 0, len(sea_ids) - 1)
    ch[sea] = sea_ids[ks[sea]]
    if fg is not None:
        fgc[land] = fg
    if dim is not None:
        fgc[sea] = dim
    if grid:
        latg = np.abs(((lat + 7.5) % 15) - 7.5) < 1.6
        long_ = np.abs(((lon + 7.5) % 15) - 7.5) < 1.6 / np.maximum(0.25, np.cos(np.radians(lat)))
        g = disc & ~land & (latg | long_) & (z > 0.12)
        ch[g & latg] = cv.ids("-")[0]
        ch[g & ~latg] = cv.ids(":")[0]
        if dim is not None:
            fgc[g] = dim
    rim = (r2 >= 0.86) & (r2 < 1.0)
    ch[rim & ~land] = cv.ids(rim_char)[0]
    if accent is not None:
        fgc[rim] = accent
    full = np.zeros((cv.H, cv.W), bool)
    full[y0:y1, x0:x1] = disc
    return full


# ------------------------------------------------------------- picture frame

FRAME_STYLES = {
    # ring chars from outside in: (corner, horizontal, vertical)
    "gilded": [("#", "=", "H"), ("@", "~", "{"), ("+", "-", "|"), (".", ".", ":")],
    "simple": [("+", "-", "|"), (".", ".", ":")],
    "heavy": [("#", "#", "#"), ("=", "=", "I"), ("+", "-", "|")],
}


def picture_frame(cv: Canvas, x0: float, y0: float, x1: float, y1: float, fg, dim=None,
                  style: str = "gilded", depth: int | None = None, bg=None, clear_inside=False,
                  hl=None) -> None:
    """An ornamental picture frame (額縁) drawn as concentric character rings.

    Coordinates are in cells. Top/left rings use ``hl`` (highlight), the
    bottom/right use ``dim``, so the moulding reads as a bevelled object.
    """
    rings = FRAME_STYLES[style][: depth or None]
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    if clear_inside and bg is not None:
        ys, xs = slice(max(0, y0), max(0, min(cv.H, y1 + 1))), slice(max(0, x0), max(0, min(cv.W, x1 + 1)))
        cv.ch[ys, xs] = 0
        cv.bg[ys, xs] = bg
    hl = fg if hl is None else hl
    dim = fg if dim is None else dim
    for i, (c, h, v) in enumerate(rings):
        # vertical sides step 1 cell, horizontal sides step 1 row
        ax0, ax1 = x0 + i * 2, x1 - i * 2
        ay0, ay1 = y0 + i, y1 - i
        if ax1 - ax0 < 2 or ay1 - ay0 < 1:
            break
        cv.line(ax0, ay0, ax1, ay0, hl, h)
        cv.line(ax0, ay1, ax1, ay1, dim, h)
        cv.line(ax0, ay0, ax0, ay1, hl, v)
        cv.line(ax1, ay0, ax1, ay1, dim, v)
        if i < len(rings) - 1:  # double-width verticals for outer rings
            cv.line(ax0 + 1, ay0, ax0 + 1, ay1, hl, v)
            cv.line(ax1 - 1, ay0, ax1 - 1, ay1, dim, v)
        for (px, py) in ((ax0, ay0), (ax1, ay0), (ax0, ay1), (ax1, ay1)):
            cv.scatter([px], [py], c, fg)
    # little ornaments in the middle of each side of the outer ring
    if style == "gilded" and x1 - x0 > 20 and y1 - y0 > 6:
        mx, my = (x0 + x1) // 2, (y0 + y1) // 2
        cv.put(mx - 2, y0, "<@@>", fg)
        cv.put(mx - 2, y1, "<@@>", dim)
        cv.scatter([x0, x0 + 1], [my, my], "@", fg)
        cv.scatter([x1, x1 - 1], [my, my], "@", dim)


def frame_inner(x0, y0, x1, y1, style="gilded", depth=None):
    n = len(FRAME_STYLES[style][: depth or None])
    return x0 + 2 * n, y0 + n, x1 - 2 * n, y1 - n


# -------------------------------------------------------------------- figure
# An original, generic silhouette of the song's narrator (a girl with a bob
# haircut and a skirt).  Poses are joint lists in units of body height.

def _figure_parts(pose: str, ph: float):
    """Return list of primitives in body-height units, origin at feet centre."""
    P = []
    s, c = math.sin, math.cos

    def hair(hx, hy, tilt=0.0):
        # bob haircut: round crown + straight sides ending at the chin
        P.append(("circle", hx, hy, 0.064))
        P.append(("circle", hx - 0.004, hy - 0.016, 0.074))
        P.append(("box", hx - 0.004 + tilt, hy + 0.012, 0.074, 0.058, 0.02))

    if pose in ("stand", "walk", "run"):
        amp = {"stand": 0.0, "walk": 0.38, "run": 0.75}[pose]
        sw = s(ph * 2 * math.pi) * amp
        bob = abs(s(ph * 2 * math.pi)) * 0.018 * (amp > 0)
        lean = 0.07 * (pose == "run")
        hip = (lean * 0.3, -0.45 - bob)
        sh = (lean, -0.76 - bob)
        head = (lean * 1.25, -0.885 - bob)
        hair(*head)
        P.append(("cap", head[0], head[1] + 0.06, sh[0], sh[1], 0.018))  # neck
        P.append(("poly", [(sh[0] - 0.062, sh[1]), (sh[0] + 0.062, sh[1]),
                           (hip[0] + 0.05, hip[1] - 0.05), (hip[0] - 0.05, hip[1] - 0.05)]))
        flare = 0.025 * abs(sw)
        P.append(("poly", [(hip[0] - 0.055, hip[1] - 0.07), (hip[0] + 0.055, hip[1] - 0.07),
                           (hip[0] + 0.12 + flare, hip[1] + 0.12),
                           (hip[0] - 0.12 - flare, hip[1] + 0.12)]))
        for side, k in ((-1, 1), (1, -1)):
            a = sw * k
            hx = hip[0] + side * 0.04
            knee = (hx + s(a) * 0.22, hip[1] + 0.02 + c(a) * 0.22)
            bend = max(0.0, -a) * 1.0 + 0.04
            foot = (knee[0] + s(a - bend) * 0.22, knee[1] + c(a - bend) * 0.22)
            P.append(("cap", hx, hip[1] + 0.04, knee[0], knee[1], 0.02))
            P.append(("cap", knee[0], knee[1], foot[0], foot[1], 0.017))
            P.append(("cap", foot[0], foot[1], foot[0] + 0.045, foot[1] + 0.005, 0.014))
            arm = -a * 0.85 + side * (0.14 if amp == 0 else 0.05)
            elbow = (sh[0] + side * 0.07 + s(arm) * 0.15, sh[1] + 0.02 + c(arm) * 0.15)
            fore = arm + (1.7 if pose == "run" else 0.25 * (amp > 0))
            hand = (elbow[0] + s(fore) * 0.14, elbow[1] + c(fore) * 0.14)
            P.append(("cap", sh[0] + side * 0.07, sh[1] + 0.02, elbow[0], elbow[1], 0.016))
            P.append(("cap", elbow[0], elbow[1], hand[0], hand[1], 0.014))
    elif pose == "sit":  # sitting on the floor hugging her knees, facing right
        br = s(ph * 2 * math.pi) * 0.006
        hip = (-0.07, -0.07)
        sh = (-0.05, -0.38 + br)
        head = (0.0, -0.50 + br)
        knee = (0.15, -0.27)
        ankle = (0.20, -0.03)
        P.append(("circle", hip[0], hip[1] + 0.01, 0.07))                 # seat
        P.append(("cap", hip[0], hip[1], sh[0], sh[1], 0.055))             # back
        hair(*head, tilt=-0.004)
        P.append(("cap", hip[0] + 0.03, hip[1], knee[0], knee[1], 0.045))  # thigh + skirt
        P.append(("cap", head[0] - 0.01, head[1] + 0.06, sh[0] + 0.01, sh[1], 0.018))  # neck
        P.append(("cap", knee[0], knee[1], ankle[0], ankle[1], 0.022))     # shin
        P.append(("cap", ankle[0], ankle[1], ankle[0] + 0.05, ankle[1] + 0.01, 0.016))
        P.append(("cap", sh[0] + 0.02, sh[1] + 0.03, knee[0] + 0.035, knee[1] + 0.06, 0.02))  # arm
    elif pose == "lie":  # lying on her side, head to the left, knees drawn up
        br = s(ph * 2 * math.pi) * 0.008
        hair(-0.44, -0.075)
        P.append(("cap", -0.36, -0.07 - br, -0.02, -0.075 - br, 0.058))  # torso
        P.append(("cap", -0.02, -0.075, 0.2, -0.13, 0.05))               # thighs
        P.append(("cap", 0.2, -0.13, 0.36, -0.035, 0.022))               # shins
        P.append(("cap", -0.30, -0.11, -0.14, -0.17, 0.016))             # arm
    return P


def figure_sdf(X, Y, x, y, h, pose="stand", ph=0.0, flip=False, min_r=0.42):
    """SDF of the figure, feet at (x, y), height h (square units)."""
    d = np.full(X.shape, np.inf, np.float32)
    sx = -1.0 if flip else 1.0
    for p in _figure_parts(pose, ph):
        kind = p[0]
        if kind == "circle":
            _, px, py, r = p
            dd = sd_circle(X, Y, x + sx * px * h, y + py * h, max(min_r, r * h))
        elif kind == "cap":
            _, ax, ay, bx, by, r = p
            dd = sd_capsule(X, Y, x + sx * ax * h, y + ay * h, x + sx * bx * h, y + by * h, max(min_r, r * h))
        elif kind == "box":
            _, px, py, hw, hh, r = p
            dd = sd_box(X, Y, x + sx * px * h, y + py * h, hw * h, hh * h, r * h)
        elif kind == "poly":
            pts = [(x + sx * a * h, y + b * h) for a, b in p[1]]
            dd = sd_poly(X, Y, pts)
        d = np.minimum(d, dd)
    return d


def figure(cv: Canvas, x, y, h, pose="stand", ph=0.0, fg=None, flip=False,
           fill="#", edge="+", bg=None, window: tuple | None = None):
    """Draw the figure; returns its inside mask (full canvas)."""
    if window is None:
        x0, x1 = int(max(0, x - h * 0.7)), int(min(cv.W, x + h * 0.7 + 1))
        y0 = int(max(0, (y - h * 1.05) / cv.aspect))
        y1 = int(min(cv.H, (y + h * 0.1) / cv.aspect + 1))
    else:
        x0, y0, x1, y1 = window
    full = np.zeros((cv.H, cv.W), bool)
    if x1 <= x0 or y1 <= y0:
        return full
    d = figure_sdf(cv.X[y0:y1, x0:x1], cv.Y[y0:y1, x0:x1], x, y, h, pose, ph, flip)
    D = np.full((cv.H, cv.W), np.inf, np.float32)
    D[y0:y1, x0:x1] = d
    return draw_sdf(cv, D, fg, fill, edge, bg=bg)


# --------------------------------------------------------------------- clock

def clock(cv: Canvas, cx: float, cy: float, R: float, hours: float, fg, dim, accent=None,
          numerals=True, rim="o", sweep: float | None = None):
    """Analog clock face (the 'face of everyday'). hours: 0..12 float."""
    n = int(2 * math.pi * R * 1.2)
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    cv.scatter(cx + R * np.cos(a), (cy + R * np.sin(a)) / cv.aspect - 0.5, rim, dim)
    cv.scatter(cx + (R + 1.3) * np.cos(a), (cy + (R + 1.3) * np.sin(a)) / cv.aspect - 0.5, ".", dim)
    for k in range(60):
        ang = k / 60 * 2 * math.pi - math.pi / 2
        rr = R - (2.2 if k % 5 == 0 else 1.2)
        cv.scatter([cx + rr * math.cos(ang)], [(cy + rr * math.sin(ang)) / cv.aspect - 0.5],
                   "|" if k % 15 == 0 and k % 30 != 0 else ("-" if k % 30 == 0 else ("+" if k % 5 == 0 else ".")), fg if k % 5 == 0 else dim)
    if numerals:
        for k in range(1, 13):
            ang = k / 12 * 2 * math.pi - math.pi / 2
            rr = R - 5.0
            s = str(k)
            cv.put(int(round(cx + rr * math.cos(ang) - len(s) / 2)),
                   int(round((cy + rr * math.sin(ang)) / cv.aspect - 0.5)), s, fg, bold=True)
    mins = (hours % 1.0) * 60
    for length, ang, col, ch in ((R * 0.5, hours / 12 * 2 * math.pi, fg, "#"),
                                 (R * 0.8, mins / 60 * 2 * math.pi, fg, None)):
        ang -= math.pi / 2
        ex, ey = cx + length * math.cos(ang), cy + length * math.sin(ang)
        cv.line(cx, cy / cv.aspect - 0.5, ex, ey / cv.aspect - 0.5, col, ch, bold=True)
    if sweep is not None and accent is not None:
        ang = sweep * 2 * math.pi - math.pi / 2
        ex, ey = cx + R * 0.88 * math.cos(ang), cy + R * 0.88 * math.sin(ang)
        cv.line(cx, cy / cv.aspect - 0.5, ex, ey / cv.aspect - 0.5, accent)
    cv.scatter([cx], [cy / cv.aspect - 0.5], "@", accent if accent is not None else fg)


# ------------------------------------------------------------- seven segment

_SEG = {  # a b c d e f g
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd",
    "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g", " ": "",
}


def seven_seg(cv: Canvas, x: int, y: int, s: str, fg, off=None, w: int = 6, h: int = 5,
              bold=True) -> int:
    """Draw digits as seven-segment glyphs; returns end x. '.' is a dot."""
    for c in s:
        if c in ".:":
            if c == ".":
                cv.put(x, y + 2 * h, "o", fg, bold=bold)
            else:
                cv.put(x, y + h // 2 + 1, "o", fg, bold=bold)
                cv.put(x, y + h + h // 2 + 1, "o", fg, bold=bold)
            x += 2
            continue
        segs = _SEG.get(c, "")
        for sname in "abcdefg":
            col = fg if sname in segs else off
            if col is None:
                continue
            if sname == "a":
                cv.line(x + 1, y, x + w - 2, y, col, "=", bold)
            elif sname == "g":
                cv.line(x + 1, y + h, x + w - 2, y + h, col, "=", bold)
            elif sname == "d":
                cv.line(x + 1, y + 2 * h, x + w - 2, y + 2 * h, col, "=", bold)
            elif sname == "f":
                cv.line(x, y + 1, x, y + h - 1, col, "#", bold)
            elif sname == "b":
                cv.line(x + w - 1, y + 1, x + w - 1, y + h - 1, col, "#", bold)
            elif sname == "e":
                cv.line(x, y + h + 1, x, y + 2 * h - 1, col, "#", bold)
            elif sname == "c":
                cv.line(x + w - 1, y + h + 1, x + w - 1, y + 2 * h - 1, col, "#", bold)
        x += w + 2
    return x


def seven_seg_width(s: str, w: int = 6) -> int:
    return sum(2 if c in ".:" else w + 2 for c in s)


# ------------------------------------------------------------------ starfield

def stars(cv: Canvas, t: float, seed: int, density: float, fg, dim, drift=(0.0, 0.0),
          twinkle=1.5, chars=".'+*"):
    rng = np.random.default_rng(seed)
    n = int(cv.W * cv.H * density)
    xs = rng.uniform(0, cv.W, n)
    ys = rng.uniform(0, cv.H, n)
    ph = rng.uniform(0, 2 * math.pi, n)
    sz = rng.uniform(0, 1, n) ** 3
    xs = (xs + drift[0] * t) % cv.W
    ys = (ys + drift[1] * t) % cv.H
    tw = 0.5 + 0.5 * np.sin(ph + t * twinkle * (0.6 + sz * 2))
    level = np.clip(sz * 0.7 + tw * 0.4, 0, 0.999)
    idx = (level * len(chars)).astype(int)
    ids = cv.ids(chars)
    cv.scatter(xs, ys, ids[idx], fg=None)
    bright = level > 0.55
    cv.scatter(xs[bright], ys[bright], ids[idx[bright]], fg=fg)
    cv.scatter(xs[~bright], ys[~bright], ids[idx[~bright]], fg=dim)


# --------------------------------------------------------------- stick people

WALKERS = [
    [" o ", "/|\\", "/ \\"],
    [" o ", "-|-", " | "],
    [" o ", "/|\\", " |\\"],
    [" o ", "\\|/", "/ |"],
]


def walker(cv: Canvas, x: float, y: int, phase: float, fg, bold=False):
    fr = WALKERS[int(phase * 4) % 4]
    for i, row in enumerate(fr):
        cv.put(int(round(x)) - 1, y - 2 + i, row, fg, bold=bold)


# ----------------------------------------------------------------- glitches

def glitch_rows(cv: Canvas, rng: np.random.Generator, amount: float, max_shift: int = 12) -> None:
    """Shift random horizontal bands sideways."""
    if amount <= 0:
        return
    n = int(1 + amount * 8)
    for _ in range(n):
        y0 = int(rng.integers(0, cv.H))
        h = int(rng.integers(1, max(2, int(3 + amount * 6))))
        k = int(rng.integers(-max_shift, max_shift + 1) * amount)
        sl = slice(y0, min(cv.H, y0 + h))
        cv.ch[sl] = np.roll(cv.ch[sl], k, axis=1)
        cv.fg[sl] = np.roll(cv.fg[sl], k, axis=1)
        cv.bg[sl] = np.roll(cv.bg[sl], k, axis=1)


def char_noise(cv: Canvas, rng: np.random.Generator, p: float, chars="!#$%&*+-/0123456789:;<=>?@ABCDEFXYZ\\^_|~",
               fg=None, only_ink=False) -> None:
    if p <= 0:
        return
    m = rng.random((cv.H, cv.W)) < p
    if only_ink:
        m &= cv.ch != 0
    ids = cv.ids(chars)
    cv.ch[m] = ids[rng.integers(0, len(ids), m.sum())]
    if fg is not None:
        cv.fg[m] = fg


def invert(cv: Canvas, mask: np.ndarray | None = None) -> None:
    if mask is None:
        cv.fg[:], cv.bg[:] = cv.bg.copy(), cv.fg.copy()
    else:
        f = cv.fg[mask].copy()
        cv.fg[mask] = cv.bg[mask]
        cv.bg[mask] = f


def ripple_rings(cv: Canvas, cx, cy, t, speed, spacing, fg, chars="-~=", width=0.6, maxr=200,
                 fade=0.0):
    r = np.hypot(cv.X - cx, cv.Y - cy)
    ph = (r - speed * t) / spacing
    m = (np.abs(ph - np.round(ph)) * spacing < width) & (r < maxr) & (r > 0.5)
    if chars == "arc":
        ids = cv.ids("()-")
        ca = (cv.X - cx) / np.maximum(r, 1e-3)
        k = np.where(ca > 0.6, 1, np.where(ca < -0.6, 0, 2))
    else:
        ids = cv.ids(chars)
        k = (np.round(ph).astype(int)) % len(ids)
    cv.ch[m] = ids[k[m]]
    cv.fg[m] = fg
    return m
