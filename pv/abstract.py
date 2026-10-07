"""Abstract toolkit: ASCII 'shaders'.

Fields f(x, y, t) evaluated on the character grid and drawn through glyph
ramps and colour gradients -- noise, flow, interference, caustics -- plus
helpers to use text itself as the texture of a field.  All pure functions of
their arguments.
"""
from __future__ import annotations

import math

import numpy as np

from .canvas import Canvas

_PERM = {}


def _grid(seed: int, n: int = 64) -> np.ndarray:
    g = _PERM.get((seed, n))
    if g is None:
        g = np.random.default_rng(seed).random((n, n)).astype(np.float32)
        _PERM[(seed, n)] = g
    return g


def vnoise(x: np.ndarray, y: np.ndarray, seed: int = 0) -> np.ndarray:
    """Smooth value noise in [0,1], periodic over 64 units."""
    g = _grid(seed)
    n = g.shape[0]
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    xf, yf = x - xi, y - yi
    xf = xf * xf * (3 - 2 * xf)
    yf = yf * yf * (3 - 2 * yf)
    x0, y0 = xi % n, yi % n
    x1, y1 = (x0 + 1) % n, (y0 + 1) % n
    a = g[y0, x0] * (1 - xf) + g[y0, x1] * xf
    b = g[y1, x0] * (1 - xf) + g[y1, x1] * xf
    return a * (1 - yf) + b * yf


def fbm(x, y, seed=0, octaves=4, lac=2.0, gain=0.5):
    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s = s + amp * vnoise(x, y, seed + o * 17)
        tot += amp
        x, y = x * lac + 5.2, y * lac + 1.3
        amp *= gain
    return s / tot


def warp(x, y, t, seed=0, k=2.0, scale=1.0):
    """Domain-warped fbm (the 'liquid' look)."""
    qx = fbm(x * scale + 0.0 + t * 0.1, y * scale + 0.0, seed)
    qy = fbm(x * scale + 5.2, y * scale + 1.3 - t * 0.1, seed + 3)
    return fbm(x * scale + k * qx, y * scale + k * qy + t * 0.05, seed + 7)


def coords(cv: Canvas, rows: int = 46):
    """Square-unit coordinates of the picture area (x in cells, y scaled)."""
    return cv.X[:rows], cv.Y[:rows]


def gradient(stops, v: np.ndarray) -> np.ndarray:
    """Map v in [0,1] through colour stops [(pos, rgb), ...] -> (..., 3)."""
    v = np.clip(v, 0, 1)[..., None]
    out = np.zeros(v.shape[:-1] + (3,), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (v >= p0) & (v <= p1)
        k = (v - p0) / max(1e-6, p1 - p0)
        col = np.asarray(c0, np.float32) * (1 - k) + np.asarray(c1, np.float32) * k
        out = np.where(m, col, out)
    return out


def shade(cv: Canvas, field: np.ndarray, ramp: str, stops, bg_stops=None, thresh=0.0, rows=46,
          bg_scale=0.35):
    """Draw a field: glyph from ramp, fg colour from stops, background a darker
    version (or bg_stops) so the image reads as continuous tone."""
    f = np.clip(field, 0, 1)
    col = gradient(stops, f)
    cv.density(f, ramp, color=col, thresh=thresh)
    cv.bg[:rows] = gradient(bg_stops, f) if bg_stops else col * bg_scale


def text_fill(cv: Canvas, mask: np.ndarray, text: str, fg, offset: int = 0, bold=False):
    """Fill the cells of ``mask`` with the characters of ``text`` (half-width
    cells; wide chars use both halves), in reading order."""
    ids = []
    for c in text:
        g = cv.atlas.get(c, bold)
        if isinstance(g, tuple):
            ids.extend(g)
        else:
            ids.append(g)
    if not ids:
        return
    ids = np.asarray(ids)
    ys, xs = np.nonzero(mask)
    n = len(ids)
    # even/odd x pairs map to (left, right) halves of wide characters
    k = (((xs // 2) * 2 + ys * 14 + offset * 2) % n + (xs % 2)) % n
    cv.ch[ys, xs] = ids[k]
    cv.fg[ys, xs] = fg if np.ndim(fg) == 1 else fg[ys, xs]


def text_glyphs(cv: Canvas, text: str, bold=False) -> np.ndarray:
    ids = []
    for c in text:
        g = cv.atlas.get(c, bold)
        ids.extend(g if isinstance(g, tuple) else (g,))
    return np.asarray(ids)
