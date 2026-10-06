"""Lyric typography on the character grid.

Lines are revealed character by character over the time they are sung (an
approximation: the LRC file only gives line start times).  Characters that are
about to appear first flicker through random ASCII -- a "decoding" effect that
keeps the lyric layer made of the same stuff as the pictures.
"""
from __future__ import annotations

import math

import numpy as np

from .canvas import Canvas
from .lrc import Line, char_width, text_width
from .timeline import Ctx

SCRAMBLE = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`{|}~"


def sing_time(line: Line) -> float:
    n = max(1, len(line.text))
    return min(line.dur * 0.85, 0.15 * n + 0.15)


def char_times(line: Line) -> np.ndarray:
    n = len(line.text)
    st = sing_time(line)
    return line.t + st * np.arange(n) / max(1, n)


def revealed(line: Line, t: float) -> int:
    return int((char_times(line) <= t).sum())


def _scramble_char(rng: np.random.Generator) -> str:
    return SCRAMBLE[int(rng.integers(0, len(SCRAMBLE)))]


def decode_text(ctx: Ctx, line: Line, t: float | None = None, lead: float = 0.22) -> list[tuple[str, int]]:
    """Return [(char, state)] where state: 0 hidden, 1 scrambling, 2 fresh, 3 settled."""
    t = ctx.t if t is None else t
    ts = char_times(line)
    rng = ctx.rng(ctx.frame, line.index, 77)
    out = []
    for c, tc in zip(line.text, ts):
        if t < tc - lead:
            out.append((c, 0))
        elif t < tc:
            s = _scramble_char(rng)
            if char_width(c) == 2:
                s += _scramble_char(rng)
            out.append((s, 1))
        elif t < tc + 0.14:
            out.append((c, 2))
        else:
            out.append((c, 3))
    return out


def subtitle(cv: Canvas, ctx: Ctx, line: Line | None, y: int, fg, accent, dim=None,
             band=None, cx: float | None = None, align: str = "center", x: int = 0,
             bold=True, pad: int = 2) -> None:
    """Single-row lyric with decode effect."""
    if line is None:
        return
    parts = decode_text(ctx, line)
    w = text_width(line.text)
    if align == "center":
        x0 = int(round((cv.W if cx is None else 2 * cx) / 2 - w / 2))
    elif align == "right":
        x0 = x - w
    else:
        x0 = x
    if band is not None:
        cv.ch[y, max(0, x0 - pad):min(cv.W, x0 + w + pad)] = 0
        cv.bg[y, max(0, x0 - pad):min(cv.W, x0 + w + pad)] = band
    xx = x0
    for (s, st), c in zip(parts, line.text):
        cw = char_width(c)
        if st == 1:
            cv.put(xx, y, s, dim if dim is not None else fg, bold=False)
        elif st == 2:
            cv.put(xx, y, c, accent, bold=bold)
        elif st == 3:
            cv.put(xx, y, c, fg, bold=bold)
        xx += cw


def vertical(cv: Canvas, ctx: Ctx, line: Line | None, x: int, y0: int, fg, accent, dim=None,
             bold=True) -> None:
    """Tategaki (top-to-bottom) lyric column. Each char takes 2 cells x 1 row."""
    if line is None:
        return
    rot = {"ー": "|", "、": "`", "。": "o", "？": "?", "！": "!", "～": "S"}
    for i, ((s, st), c) in enumerate(zip(decode_text(ctx, line), line.text)):
        y = y0 + i
        if y >= cv.H:
            break
        c2 = rot.get(c, c)
        xo = x if char_width(c2) == 2 else x + 0  # half-width glyphs sit in the left cell
        if st == 1:
            cv.put(x, y, s[:2].ljust(2), dim if dim is not None else fg, bold=False)
        elif st == 2:
            cv.put(xo, y, c2, accent, bold=bold)
        elif st == 3:
            cv.put(xo, y, c2, fg, bold=bold)


def big_layout(cv: Canvas, text: str, rows: int, max_w: int, bold=True, gap: int = 1):
    """Per-character big bitmaps, shrunk until they fit ``max_w`` cells."""
    while rows > 3:
        bmps = [cv.text_bitmap(c, rows, bold) if c.strip() else np.zeros((rows, max(2, rows // 2)))
                for c in text]
        total = sum(b.shape[1] for b in bmps) + gap * (len(bmps) - 1)
        if total <= max_w:
            return rows, bmps, total
        rows -= 1
    bmps = [cv.text_bitmap(c, rows, bold) for c in text]
    return rows, bmps, sum(b.shape[1] for b in bmps) + gap * (len(bmps) - 1)


def _script(c: str) -> str:
    o = ord(c)
    if 0x30A0 <= o <= 0x30FF:
        return "kata"
    if 0x3040 <= o <= 0x309F:
        return "hira"
    if 0x4E00 <= o <= 0x9FFF:
        return "kanji"
    return "other"


def _split_point(text: str) -> int:
    """Where to wrap a long line (a heuristic, no tokenizer): after punctuation,
    else after a particle, else where hiragana meets kanji/katakana; never
    inside a katakana word or between a kanji and its okurigana."""
    n = len(text)
    best, score = n // 2, -1e9
    for i in range(max(1, int(n * 0.3)), min(n - 1, int(n * 0.7)) + 1):
        a, b = text[i - 1], text[i]
        sa, sb = _script(a), _script(b)
        if a in "、。 　？！":
            pri = 3
        elif a in "よねはのでをもにがと":
            pri = 2
        elif sa == "hira" and sb in ("kanji", "kata"):
            pri = 1
        elif sa == "kata" and sb == "kata":
            pri = -3
        elif sa == "kanji" and sb == "hira":
            pri = -1
        else:
            pri = 0
        sc = pri * 10 - abs(i - n / 2)
        if sc > score:
            best, score = i, sc
    return best


def big(cv: Canvas, ctx: Ctx, line: Line | None, cy: float, rows: int, fg, accent,
        ramp: str = "shape", max_w: int | None = None, cx: float | None = None,
        gap: int = 1, pop: float = 0.0, t: float | None = None, color_fresh=True,
        fill: str = "#", wrap: bool = True, thresh=0.12) -> tuple[int, int, int, int]:
    """Big ASCII-art lyric line, characters popping in as they're sung.

    Long lines that would have to shrink a lot are wrapped onto two rows.
    Freshly sung characters flash in the accent colour and hop up (``pop``).
    Returns the bounding box (x0, y0, x1, y1).
    """
    if line is None:
        return (0, 0, 0, 0)
    t = ctx.t if t is None else t
    text = line.text
    max_w = max_w or cv.W - 6
    rows_, bmps, total = big_layout(cv, text, rows, max_w, gap=gap)
    chunks = [(0, text)]
    if wrap and rows_ < rows * 0.8 and len(text) > 6:
        k = _split_point(text)
        chunks = [(0, text[:k]), (k, text[k:])]
        rows_ = min(big_layout(cv, c, rows, max_w, gap=gap)[0] for _, c in chunks)
    ts = char_times(line)
    nlines = len(chunks)
    total_h = nlines * rows_ + (nlines - 1)
    y_top = cy - total_h / 2
    y_top = min(max(0.0, y_top), cv.H - total_h)   # keep wrapped lines on screen
    bbox = [cv.W, cv.H, 0, 0]
    for li, (off, chunk) in enumerate(chunks):
        _, bm, tot = big_layout(cv, chunk, rows_, 10 ** 6, gap=gap)
        x = int(round((cv.W if cx is None else 2 * cx) / 2 - tot / 2))
        y = int(round(y_top + li * (rows_ + 1)))
        bbox = [min(bbox[0], x), min(bbox[1], y), max(bbox[2], x + tot), max(bbox[3], y + rows_)]
        for i, (c, b) in enumerate(zip(chunk, bm)):
            tc = ts[min(off + i, len(ts) - 1)]
            if t >= tc - 0.02:
                fresh = t < tc + 0.16
                col = accent if (fresh and color_fresh) else fg
                yo = y - (int(round(pop * rows_ * 0.2)) if (pop > 0 and fresh) else 0)
                if ramp == "shape" or ramp is None:
                    cv.shape_field(b, x, yo, col, fill=fill)
                else:
                    cv.density(b ** 0.7, ramp, fg=col, thresh=thresh, offset=(x, yo))
            x += b.shape[1] + gap
    return tuple(bbox)


def log_box(cv: Canvas, ctx: Ctx, lines: list[Line], x0: int, y0: int, x1: int, y1: int,
            fg, dim, accent, stamp=True) -> None:
    """Terminal-like transcript: past lines dim, current line decoding."""
    rows = y1 - y0 + 1
    shown = [ln for ln in lines if ln.t <= ctx.t + 0.25][-rows:]
    for i, ln in enumerate(shown):
        y = y0 + i
        ts = f"[{int(ln.t // 60):02d}:{ln.t % 60:05.2f}] " if stamp else "> "
        cur = ln.t <= ctx.t < ln.end
        cv.put(x0, y, ts, accent if cur else dim)
        if cur or ln.t > ctx.t:
            subtitle(cv, ctx, ln, y, fg, accent, dim, align="left", x=x0 + len(ts))
        else:
            cv.put(x0 + len(ts), y, ln.text, dim)
    # blinking cursor
    if (ctx.t * 2.5) % 1 < 0.6 and shown:
        last = shown[-1]
        y = y0 + len(shown) - 1
        n = revealed(last, ctx.t)
        xe = x0 + 11 + text_width(last.text[:n])
        if xe < x1:
            cv.put(xe, y, "_", accent)


def scatter_line(cv: Canvas, ctx: Ctx, line: Line | None, fg, accent, seed: int = 0,
                 box=(4, 3, 156, 50), dim=None) -> None:
    """Characters of the line placed at random spots, each appearing when sung."""
    if line is None:
        return
    rng = np.random.default_rng(line.index * 31 + seed)
    x0, y0, x1, y1 = box
    for (s, st), c in zip(decode_text(ctx, line), line.text):
        x = int(rng.integers(x0, x1 - 2))
        y = int(rng.integers(y0, y1))
        if st == 1:
            cv.put(x, y, s, dim if dim is not None else fg)
        elif st >= 2:
            cv.put(x, y, c, accent if st == 2 else fg, bold=True)
