"""Larger set pieces built from the primitives: room, answering machine,
spotlight, frame tunnel, shatter, speed lines..."""
from __future__ import annotations

import math

import numpy as np

from .canvas import Canvas
from . import shapes as S


# ---------------------------------------------------------------------- room

def room_frame_rect(vp, back=0.42, frame_w=0.32, frame_h=0.36):
    """Rectangle (cells) of the picture frame hanging on the back wall."""
    x0, y0, x1, y1 = vp
    W, H = x1 - x0, y1 - y0
    cx, cy = x0 + W * 0.5, y0 + H * 0.46
    bw, bh = W * back * 0.5, H * back * 0.5
    fw, fh = 2 * bw * frame_w, 2 * bh * frame_h
    fx0 = cx - fw / 2
    fy0 = cy - bh + 2 * bh * (0.5 - frame_h / 2) - 2 * bh * 0.06
    return fx0, fy0, fx0 + fw, fy0 + fh


def room(cv: Canvas, vp, fg, dim, faint, t: float = 0.0, back=0.42, tatami=True,
         window=True, wall_frame=True, frame_globe_lon: float | None = None, accent=None,
         night_window=True, frame_w=0.32, frame_h=0.36):
    """A small Japanese room (四畳半) in one-point perspective inside viewport
    ``vp`` = (x0, y0, x1, y1) in cells. Returns a dict of useful coordinates
    (in cells), e.g. the floor line and the wall-frame rectangle."""
    x0, y0, x1, y1 = vp
    W, H = x1 - x0, y1 - y0
    cx, cy = x0 + W * 0.5, y0 + H * 0.46
    bw, bh = W * back * 0.5, H * back * 0.5
    bx0, bx1 = cx - bw, cx + bw
    by0, by1 = cy - bh, cy + bh
    # back wall
    cv.box(bx0, by0, bx1, by1, dim, "+-|")
    # edges to the viewport corners
    cv.line(x0, y0, bx0, by0, dim)
    cv.line(x1, y0, bx1, by0, dim)
    cv.line(x0, y1, bx0, by1, fg)
    cv.line(x1, y1, bx1, by1, fg)
    # floor: tatami seams in perspective
    if tatami:
        for k in (0.25, 0.5, 0.75):
            fx = bx0 + (bx1 - bx0) * k
            ex = x0 + (x1 - x0) * k
            cv.line(fx, by1, ex, y1, faint, ":")
        for d in (0.18, 0.42, 0.72):
            yy = by1 + (y1 - by1) * d
            xl = bx0 + (x0 - bx0) * d
            xr = bx1 + (x1 - bx1) * d
            cv.line(xl, yy, xr, yy, faint, "-")
    # ceiling light cord
    cv.line(cx, y0, cx, by0 - 1, faint, "|")
    cv.put(int(cx) - 1, int(by0 - 1), "(_)", dim)
    info = {"floor_y": by1, "back": (bx0, by0, bx1, by1), "cx": cx}
    # window on the left wall (a skewed quad)
    if window:
        def lw(u, v):  # u along depth (0 front -> 1 back), v vertical (0 top -> 1 bottom)
            xf, xb = x0 + W * 0.04, bx0
            x = xf + (xb - xf) * u
            top = y0 + (by0 - y0) * u + H * 0.12 * (1 - u)
            bot = y1 + (by1 - y1) * u - H * 0.40 * (1 - u)
            return x, top + (bot - top) * v
        q = [lw(0.25, 0.15), lw(0.75, 0.25), lw(0.75, 0.75), lw(0.25, 0.85)]
        cv.polyline(q, dim, closed=True)
        a, b = lw(0.5, 0.2), lw(0.5, 0.8)
        cv.line(a[0], a[1], b[0], b[1], dim, "|")
        if night_window:
            for i, (u, v) in enumerate([(0.35, 0.35), (0.62, 0.5), (0.4, 0.62), (0.68, 0.33)]):
                px, py = lw(u, v)
                if (t * 1.3 + i * 0.37) % 1 < 0.7:
                    cv.put(int(px), int(py), "." if i % 2 else "*", faint)
        info["window"] = q
    # picture frame on the back wall
    if wall_frame:
        fx0, fy0, fx1, fy1 = room_frame_rect(vp, back, frame_w, frame_h)
        fw = fx1 - fx0
        S.picture_frame(cv, fx0, fy0, fx1, fy1, fg, dim, style="simple" if fw < 34 else "gilded",
                        depth=2 if fw < 34 else 3)
        info["frame"] = (fx0, fy0, fx1, fy1)
        if frame_globe_lon is not None:
            ix0, iy0, ix1, iy1 = S.frame_inner(fx0, fy0, fx1, fy1, "simple" if fw < 34 else "gilded",
                                               2 if fw < 34 else 3)
            R = min((ix1 - ix0) * 0.5, (iy1 - iy0) * cv.aspect * 0.5) * 0.9
            if R > 1.5:
                S.globe(cv, (ix0 + ix1) / 2 + 0.5, ((iy0 + iy1) / 2 + 0.5) * cv.aspect, R,
                        frame_globe_lon, fg=fg, dim=faint, grid=R > 6, accent=accent)
    from .illustration import furnishings
    furnishings(cv, vp, fg, dim, faint, t)
    return info


def soot(cv: Canvas, t: float, seed: int, n: int, fg, chars=".,'`"):
    """Slowly falling soot/dust specks."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, cv.W, n)
    y = rng.uniform(0, cv.H, n)
    sp = rng.uniform(0.6, 2.2, n)
    ph = rng.uniform(0, 6.28, n)
    xs = (x + 1.5 * np.sin(ph + t * 0.7 * sp)) % cv.W
    ys = (y + sp * t * 1.2) % cv.H
    ids = cv.ids(chars)
    cv.scatter(xs, ys, ids[(np.arange(n) % len(ids))], fg=fg)


# ---------------------------------------------------------- answering machine

def answering_machine(cv: Canvas, x0: int, y0: int, w: int, h: int, fg, dim, accent, t: float,
                      led_on: bool, count: str = "01", spin: float = 0.0, label="MESSAGE"):
    """A desk answering machine drawn from boxes and characters."""
    x1, y1 = x0 + w, y0 + h
    cv.box(x0, y0, x1, y1, fg, "+-|", bold=True)
    cv.box(x0 + 1, y0 + 1, x1 - 1, y1 - 1, dim, ".-|")
    # handset on top
    hx0, hx1 = x0 + 3, x0 + int(w * 0.62)
    cv.box(hx0, y0 - 3, hx1, y0 - 1, fg, "+=|", bold=True)
    cv.put(hx0 + 1, y0 - 2, "(" + "_" * max(1, (hx1 - hx0 - 3)) + ")", dim)
    # cassette window with two reels
    cx0, cy0 = x0 + 3, y0 + 3
    cw_, ch_ = int(w * 0.5), max(5, int(h * 0.38))
    cv.box(cx0, cy0, cx0 + cw_, cy0 + ch_, fg, "+-|")
    spokes = "|/-\\"
    for k, rx in enumerate((cx0 + cw_ * 0.28, cx0 + cw_ * 0.72)):
        ry = cy0 + ch_ / 2
        cv.put(int(rx) - 2, int(ry) - 1, " ___ ", dim)
        cv.put(int(rx) - 2, int(ry), "(   )", fg)
        cv.put(int(rx), int(ry), spokes[int(spin * 4 + k) % 4], accent if led_on else fg, bold=True)
        cv.put(int(rx) - 2, int(ry) + 1, " ~~~ ", dim)
    cv.line(cx0 + cw_ * 0.28 + 3, cy0 + ch_ / 2 + 1, cx0 + cw_ * 0.72 - 3, cy0 + ch_ / 2 + 1, dim, "_")
    # LCD counter
    lx = cx0 + cw_ + 4
    cv.box(lx, cy0, x1 - 3, cy0 + 12, dim, "+-|")
    S.seven_seg(cv, lx + 2, cy0 + 1, count, accent, off=None, w=6, h=5)
    cv.put(lx + 2, cy0 + 13, label, dim)
    # LED
    cv.put(x1 - 6, y0 + 2, "(*)" if led_on else "( )", accent if led_on else dim, bold=True)
    # speaker grille
    gy0 = cy0 + ch_ + 2
    for yy in range(gy0, min(y1 - 3, gy0 + 6)):
        cv.put(x0 + 3, yy, ": " * max(1, int(cw_ / 2)), dim)
    # buttons
    by = y1 - 2
    bx = x0 + 3
    for lab in ("[<<]", "[ >]", "[[]]", "[>>]", "[DEL]"):
        cv.put(bx, by, lab, fg)
        bx += len(lab) + 2
    return {"speaker": (x0 + 3 + cw_ / 2, gy0 + 3)}


# ---------------------------------------------------------------- spotlight

def spotlight(cv: Canvas, cx: float, top: float, bottom: float, half_w: float, fg,
              intensity=1.0, ramp=" .:;!|", flicker=0.0, rng=None):
    """Cone of light from (cx, top) widening to half_w at bottom (cells)."""
    y = cv.yy
    h = max(1e-3, bottom - top)
    v = (y - top) / h
    w = 1.5 + v * half_w
    d = np.abs(cv.xx - cx) / np.maximum(w, 1e-3)
    inside = (v >= 0) & (v <= 1) & (d < 1)
    val = (1 - d ** 2) * (0.35 + 0.65 * v) * intensity
    if flicker and rng is not None:
        val *= 1 - flicker * rng.random(val.shape) * 0.5
    field = np.where(inside, np.clip(val, 0, 1), 0)
    cv.density(field, ramp, fg=fg, thresh=0.05)
    # pool of light on the floor
    pool = ((cv.xx - cx) / (half_w + 2)) ** 2 + ((cv.yy - bottom) / 2.2) ** 2 < 1
    cv.fill(pool & (cv.ch == 0), "_", fg=fg)
    return inside


def lamp(cv: Canvas, cx: float, top: int, fg, dim):
    cv.put(int(cx) - 3, top, "__|__", dim)
    cv.put(int(cx) - 4, top + 1, "/_____\\", fg, bold=True)


# ------------------------------------------------------------- frame tunnel

def frame_tunnel(cv: Canvas, t: float, phase: float, fg, dim, faint, n=7, ratio=0.62,
                 center=None, style="gilded", accent=None, accent_k: int | None = None,
                 aspect_hw=None):
    """Nested picture frames receding to the centre. ``phase`` (0..1) zooms
    one step; drive it with beat/bar position for a continuous dolly."""
    cx, cy = center or (cv.W / 2, cv.H / 2)
    hw0, hh0 = aspect_hw or (cv.W * 0.62, cv.H * 0.62)
    for k in range(n, -1, -1):
        s = ratio ** (k - phase)
        hw, hh = hw0 * s, hh0 * s
        if hw < 3 or hh < 1.5:
            continue
        depth_k = k - phase
        col = fg if depth_k < 1.0 else (dim if depth_k < 3 else faint)
        if accent is not None and accent_k is not None and k == accent_k:
            col = accent
        st = style if hw > 18 else "simple"
        S.picture_frame(cv, cx - hw, cy - hh, cx + hw, cy + hh, col, dim if col is fg else faint,
                        style=st, depth=None if hw > 30 else 2, hl=col)


# ---------------------------------------------------------------- shatter

def shatter(cv: Canvas, snap, dt: float, origin, seed: int, n_shards: int = 48,
            speed: float = 34.0, gravity: float = 60.0, spin: float = 1.5):
    """Explode a snapshot (ch, fg, bg) outward from origin; dt = time since break."""
    ch, fg, bg = snap
    ys, xs = np.nonzero(ch)
    if len(xs) == 0:
        return
    rng = np.random.default_rng(seed)
    sx = rng.uniform(0, cv.W, n_shards)
    sy = rng.uniform(0, cv.H, n_shards)
    # assign cells to nearest seed (in square units)
    d = (xs[:, None] - sx[None, :]) ** 2 + ((ys[:, None] - sy[None, :]) * cv.aspect) ** 2
    shard = np.argmin(d, axis=1)
    ox, oy = origin
    dirx = sx - ox
    diry = (sy - oy) * cv.aspect
    norm = np.hypot(dirx, diry) + 1e-3
    v = speed * rng.uniform(0.5, 1.4, n_shards)
    vx = dirx / norm * v + rng.normal(0, 6, n_shards)
    vy = diry / norm * v - rng.uniform(5, 25, n_shards)
    rot = rng.normal(0, spin, n_shards) * dt
    # per-cell displacement: shard translation + small rotation about shard centre
    px = xs + vx[shard] * dt
    py = ys * cv.aspect + vy[shard] * dt + 0.5 * gravity * dt * dt
    cxs, cys = sx[shard], sy[shard] * cv.aspect
    rx, ry = px - cxs - vx[shard] * dt, py - cys - vy[shard] * dt - 0.5 * gravity * dt * dt
    c, s_ = np.cos(rot[shard]), np.sin(rot[shard])
    px = cxs + vx[shard] * dt + rx * c - ry * s_
    py = cys + vy[shard] * dt + 0.5 * gravity * dt * dt + rx * s_ + ry * c
    cv.scatter(px, py / cv.aspect, ch[ys, xs], fg=fg[ys, xs])


# -------------------------------------------------------------- speed lines

def speed_lines(cv: Canvas, t: float, seed: int, n: int, speed: float, fg, chars="|:'",
                direction=1, length=6):
    """Vertical streaks; direction=+1 falls (we rise), -1 rises (we fall)."""
    rng = np.random.default_rng(seed)
    x = rng.integers(0, cv.W, n)
    y0 = rng.uniform(0, cv.H + length, n)
    sp = rng.uniform(0.6, 1.4, n) * speed
    ln = rng.integers(2, length + 1, n)
    ids = cv.ids(chars)
    for i in range(n):
        yh = (y0[i] + direction * sp[i] * t) % (cv.H + length) - length / 2
        ys = np.arange(ln[i]) * (-direction) + yh
        cv.scatter(np.full(ln[i], x[i]), ys, ids[np.minimum(np.arange(ln[i]), len(ids) - 1)], fg=fg)


def bubbles(cv: Canvas, t: float, seed: int, n: int, fg, chars="oO0.", speed=6.0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, cv.W, n)
    y = rng.uniform(0, cv.H, n)
    sp = rng.uniform(0.5, 1.5, n) * speed
    ph = rng.uniform(0, 6.28, n)
    xs = x + 1.2 * np.sin(ph + t * 2.0)
    ys = (y - sp * t) % cv.H
    ids = cv.ids(chars)
    cv.scatter(xs, ys, ids[np.arange(n) % len(ids)], fg=fg)


def wave_line(cv: Canvas, y: float, amp: float, wavelen: float, t: float, speed: float, fg,
              x0: int = 0, x1: int | None = None, chars=None, jitter=None, bold=False):
    """A continuous travelling wave: slope-aware characters, vertical runs
    filled with '|' so steep parts stay connected."""
    x1 = cv.W if x1 is None else x1
    xs = np.arange(int(x0), int(x1))
    if len(xs) == 0:
        return np.zeros(0)
    ph = (xs / wavelen - t * speed) * 2 * math.pi
    ys = y + amp * np.sin(ph)
    if jitter is not None:
        ys = ys + jitter[: len(xs)]
    yi = np.round(ys).astype(int)
    ids = cv.ids("-/\\|_")
    prev = np.concatenate([[yi[0]], yi[:-1]])
    nxt = np.concatenate([yi[1:], [yi[-1]]])
    d = nxt - prev
    k = np.where(d < 0, 1, np.where(d > 0, 2, 0))
    k = np.where((yi > prev) & (yi > nxt), 4, k)   # valley bottom
    gid = ids[k]
    px, py, pg = [xs], [yi], [gid]
    # connect vertical gaps
    for j in range(1, len(xs)):
        a, b = yi[j - 1], yi[j]
        if abs(b - a) > 1:
            lo, hi = (a + 1, b) if b > a else (b + 1, a)
            rr = np.arange(lo, hi)
            px.append(np.full(len(rr), xs[j] if b > a else xs[j - 1]))
            py.append(rr)
            pg.append(np.full(len(rr), ids[3]))
    cv.scatter(np.concatenate(px), np.concatenate(py), np.concatenate(pg), fg=fg)
    return ys
