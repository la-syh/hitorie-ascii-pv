"""World kit: the places and props the per-line scenes are built from.

The PV now happens in one consistent world -- her small room, the window
and the city outside, the station and trains, the night streets, the stage,
the Earth -- so each lyric line can be a composed scene (background,
mid-ground, props, an action) rather than one big symbol.

Everything here is a pure function of its arguments.  Sprites are small,
original ASCII drawings; transparent cells are spaces.
"""
from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np

from . import shapes as S
from .canvas import Canvas, hexc
from .palette import GREY, INK, PAPER, RED, mix

# ------------------------------------------------------------- palette bits
NIGHT_SKY = hexc("#0b0d16")
NIGHT_SKY2 = hexc("#1a1c2c")
DUSK = hexc("#6b2a2a")
WARM = hexc("#ffcf7a")        # lit window
WARM_DIM = hexc("#8a6a3a")
NEON_C = hexc("#4fd6e8")
NEON_M = hexc("#ff5fae")
NEON_G = hexc("#7cff8a")
STEEL = hexc("#3a3f4c")
CONCRETE = hexc("#55565c")
WOOD = hexc("#8a6a48")
TATAMI = hexc("#b9b07c")
SNOW = hexc("#e8eef5")
SEA = hexc("#0e2236")
SEA2 = hexc("#1d4566")
REDBG = hexc("#c4241c")
REDDK = hexc("#5a0f0c")


# ------------------------------------------------------------------ sprites
SPR = {
    "mug": [
        " ( (    ",
        "  ) )   ",
        ".______.",
        "|      |]",
        "\\      / ",
        " `----'  ",
    ],
    "lamp": [
        "   ____   ",
        "  /    \\  ",
        " /______\\ ",
        "    ||    ",
        "    ||    ",
        "  __||__  ",
    ],
    "plant": [
        " \\ | / ",
        "--\\|/--",
        "  /|\\  ",
        " [___] ",
    ],
    "machine": [
        ".--------------------.",
        "| (o)  (o)  | 01 | * |",
        "| :::::::   '----'   |",
        "| [<<] [>] [=] [DEL] |",
        "'--------------------'",
    ],
    "tv": [
        ".----------------.",
        "|                |",
        "|                |",
        "|                |",
        "|                |",
        "'----------------'",
        "    /        \\    ",
    ],
    "cat": [
        " /\\_/\\ ",
        "( o.o )",
        " > ^ < ",
    ],
    "cat_sleep": [
        "  /\\_/\\_ ",
        " ( -.- ) )",
        "  `~~~~~' ",
    ],
    "car": [
        "   _____      ",
        " _/__|__\\___  ",
        "|  _      _  |",
        "'-(_)----(_)-'",
    ],
    "traffic": [
        " ___ ",
        "|(o)|",
        "|(o)|",
        "|(o)|",
        " '-' ",
        "  |  ",
        "  |  ",
    ],
    "vending": [
        ".--------.",
        "|[][][][]|",
        "|[][][][]|",
        "|[][][][]|",
        "|  ____  |",
        "|_|____|_|",
    ],
    "washer": [
        ".---------.",
        "| [==]  o |",
        "|  _____  |",
        "| /     \\ |",
        "| \\_____/ |",
        "'---------'",
    ],
    "camera": [
        " ______    ",
        "[______]=(o",
        "    |      ",
    ],
    "phone_hand": [
        ".-------.",
        "|       |",
        "|       |",
        "|       |",
        "|       |",
        "|  ---  |",
        "'-------'",
    ],
    "futon": [
        ".--------------------------------.",
        "|(___)                           |",
        "|      ~~~~~~~~~~~~~~~~~~~~~~    |",
        "'--------------------------------'",
    ],
    "paperplane": [
        "__        ",
        "\\ `-._    ",
        " \\____`>  ",
        " /_.-'    ",
    ],
    "boat": [
        "    |\\    ",
        "    | \\   ",
        "____|__\\__",
        "\\________/",
    ],
    "trophy": [
        "  ___  ",
        " (   ) ",
        "  \\_/  ",
        "  _|_  ",
        " [___] ",
    ],
    "umbrella_top": [
        "   .-^-.   ",
        " .'=^=^='. ",
        "'---------'",
        "     |     ",
        "     J     ",
    ],
    "kite": [
        "  /\\  ",
        " /  \\ ",
        " \\  / ",
        "  \\/  ",
        "   \\  ",
        "   /  ",
    ],
}


def sprite(cv: Canvas, name_or_rows, x: float, y: float, fg, bold=False, colors: dict | None = None):
    """Draw an ASCII sprite with its top-left at cell (x, y). Spaces are transparent.
    ``colors`` maps a character to a colour (e.g. {'*': RED})."""
    rows = SPR[name_or_rows] if isinstance(name_or_rows, str) else name_or_rows
    x, y = int(round(x)), int(round(y))
    for j, row in enumerate(rows):
        yy = y + j
        if yy < 0 or yy >= cv.H:
            continue
        for i, c in enumerate(row):
            if c == " ":
                continue
            xx = x + i
            if 0 <= xx < cv.W:
                col = colors.get(c, fg) if colors else fg
                cv.put(xx, yy, c, col, bold=bold)


def sprite_size(name):
    rows = SPR[name]
    return max(len(r) for r in rows), len(rows)


# ------------------------------------------------------------------ masks

def rect(cv, x0, y0, x1, y1):
    return (cv.xx >= x0) & (cv.xx <= x1) & (cv.yy >= y0) & (cv.yy <= y1)


def disc(cv, cx, cy, r):
    return np.hypot(cv.X - cx, cv.Y - cy * cv.aspect) < r


def paint(cv, mask, bg, ch=" ", fg=None):
    cv.bg[mask] = bg
    cv.ch[mask] = cv.ids(ch)[0] if ch != " " else 0
    cv.fg[mask] = bg * 0.6 if fg is None else fg


def fill_rect(cv, x0, y0, x1, y1, bg, ch=" ", fg=None):
    paint(cv, rect(cv, x0, y0, x1, y1), bg, ch, fg)


def vgrad(cv, y0, y1, top, bottom, x0=0, x1=None):
    """Vertical background gradient between rows y0..y1."""
    x1 = cv.W - 1 if x1 is None else x1
    n = max(1, int(y1 - y0))
    for k in range(n + 1):
        y = int(y0 + k)
        if 0 <= y < cv.H:
            cv.bg[y, max(0, int(x0)):int(x1) + 1] = mix(top, bottom, k / n)


@contextmanager
def clip(cv: Canvas, x0, y0, x1, y1):
    """Everything drawn inside the block is kept only within the rectangle."""
    snap = cv.snapshot()
    yield
    out = ~rect(cv, x0, y0, x1, y1)
    ch, fg, bg = snap
    cv.ch[out] = ch[out]
    cv.fg[out] = fg[out]
    cv.bg[out] = bg[out]


def h32(*k):
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


# ------------------------------------------------------------------ the city

def skyline(cv: Canvas, base: float, seed: int, hmin: int, hmax: int, body, win_on=WARM,
            win_off=None, lit: float = 0.35, x0: float = -10, x1: float | None = None,
            scroll: float = 0.0, t: float = 0.0, roofs=True, outline=None, wmin=7, wmax=16):
    """A row of buildings standing on row ``base``; windows lit at random."""
    x1 = cv.W + 10 if x1 is None else x1
    rng = np.random.default_rng(seed)
    blds = []
    x = x0 - (scroll % 400)
    while x < x1 + 400:
        w = int(rng.integers(wmin, wmax))
        h = int(rng.integers(hmin, hmax))
        blds.append((x, w, h, int(rng.integers(0, 4))))
        x += w + int(rng.integers(0, 3))
    for (bx, w, h, kind) in blds:
        if bx > x1 or bx + w < x0:
            continue
        top = base - h
        fill_rect(cv, bx, top, bx + w, base, body)
        if outline is not None:
            cv.line(bx, top, bx + w, top, outline, "_")
        if roofs:
            if kind == 0:
                cv.line(bx + w // 2, top - 3, bx + w // 2, top - 1, outline if outline is not None else body * 1.6, "|")
                cv.put(int(bx + w // 2), int(top - 4), "*", RED if (t * 1.3 + bx) % 2 < 1 else REDDK)
            elif kind == 1:
                fill_rect(cv, bx + 2, top - 2, bx + 6, top - 1, body * 1.3, "=", body * 2)
        for wy in range(int(top) + 2, int(base) - 1, 2):
            for wx in range(int(bx) + 2, int(bx + w) - 1, 3):
                hv = h32(seed, int(wx + scroll), wy) % 1000 / 1000
                on = hv < lit
                if on:
                    cv.put(wx, wy, "#", win_on)
                elif win_off is not None:
                    cv.put(wx, wy, ".", win_off)
    return blds


def powerline(cv: Canvas, x0, y0, x1, y1, sag, fg, birds: int = 0, t: float = 0.0):
    n = int(abs(x1 - x0)) + 1
    xs = np.linspace(x0, x1, n)
    u = np.linspace(0, 1, n)
    ys = y0 + (y1 - y0) * u + sag * 4 * u * (1 - u)
    cv.scatter(xs, ys, "-", fg=fg)
    for b in range(birds):
        k = int(n * (0.2 + 0.6 * ((b * 0.37) % 1)))
        cv.put(int(xs[k]), int(ys[k]) - 1, "v" if (t * 2 + b) % 3 < 2.5 else "^", fg)


def pole(cv: Canvas, x, base, h, fg):
    cv.line(x, base - h, x, base, fg, "|", bold=True)
    cv.line(x - 3, base - h + 1, x + 3, base - h + 1, fg, "=")
    cv.line(x - 2, base - h + 3, x + 2, base - h + 3, fg, "-")


def streetlamp(cv: Canvas, x, base, h, fg, light=WARM, on=True):
    cv.line(x, base - h, x, base, fg, "|", bold=True)
    cv.put(int(x) - 1, int(base - h), "(=)", light if on else fg, bold=True)
    if on:
        for k in range(1, 4):
            cv.line(x - k * 2, base - h + 1 + k, x + k * 2, base - h + 1 + k, mix(light, INK, 0.5 + k * 0.12), ".")


def stars(cv, t, seed, density, y1=None, fg=PAPER, dim=GREY):
    S.stars(cv, t, seed, density, fg, dim)
    if y1 is not None:
        pass


def moon(cv, x, y, r, fg=PAPER, crescent=0.0):
    m = disc(cv, x, y, r)
    if crescent:
        m &= ~disc(cv, x + r * crescent, y - r * 0.2, r * 0.95)
    paint(cv, m, fg, "@", mix(fg, INK, 0.3))
    return m


def rain(cv, t, seed, n, fg, speed=38, slant=0.3, y1=None, mask=None):
    y1 = cv.H if y1 is None else y1
    rng = np.random.default_rng(seed)
    xs = rng.uniform(0, cv.W, n)
    ys = (rng.uniform(0, y1, n) + t * rng.uniform(0.8, 1.2, n) * speed) % y1
    xs = (xs + ys * slant) % cv.W
    if mask is not None:
        ok = ~mask[np.clip(ys.astype(int), 0, cv.H - 1), np.clip(xs.astype(int), 0, cv.W - 1)]
        xs, ys = xs[ok], ys[ok]
    cv.scatter(xs, ys, "/" if slant > 0 else "|", fg=fg)


# --------------------------------------------------------------- the room

def window_frame(cv: Canvas, x0, y0, x1, y1, fg, mullions=(0.5,), transom=None, sill=True):
    cv.box(x0, y0, x1, y1, fg, "+=|", bold=True)
    for k in mullions:
        x = x0 + (x1 - x0) * k
        cv.line(x, y0, x, y1, fg, "|", bold=True)
    if transom is not None:
        y = y0 + (y1 - y0) * transom
        cv.line(x0, y, x1, y, fg, "-")
    if sill:
        cv.line(x0 - 2, y1 + 1, x1 + 2, y1 + 1, fg, "=", bold=True)


def wall_clock(cv: Canvas, cx, cy, r, hours, fg, dim, accent):
    S.clock(cv, cx, cy * cv.aspect, r, hours, fg, dim, accent, numerals=r > 12)


def calendar(cv: Canvas, x, y, ticks: int, fg, accent, title="10"):
    cv.box(x, y, x + 22, y + 13, fg, "+-|", fill=True, bg=PAPER)
    cv.put(x + 2, y + 1, f"OCT  {title}", accent, bold=True)
    for k in range(28):
        cx, cy = x + 2 + (k % 7) * 3, y + 3 + (k // 7) * 2 + 1
        cv.put(cx, cy, "x" if k < ticks else ".", accent if k == ticks - 1 else fg)


def bookshelf(cv: Canvas, x, y, w, h, fg, seed=1):
    cv.box(x, y, x + w, y + h, fg, "+-|")
    rng = np.random.default_rng(seed)
    for sy in range(y + 1, y + h, 4):
        cv.line(x, sy + 3, x + w, sy + 3, fg, "-")
        bx = x + 1
        while bx < x + w - 1:
            bh = int(rng.integers(2, 4))
            col = mix(fg, REDBG, 0.6) if rng.random() < 0.15 else fg
            for yy in range(sy + 3 - bh, sy + 3):
                cv.put(bx, yy, "|", col)
            bx += 1 + int(rng.random() < 0.3)


def tatami_floor(cv: Canvas, y0, y1, vx, fg, base=None):
    """Floor in one-point perspective from row y0 (horizon side) to y1."""
    if base is not None:
        fill_rect(cv, 0, y0, cv.W, y1, base)
    for k in range(-6, 7):
        cv.line(vx + k * 10, y0, vx + k * 36, y1, fg, None)
    for d in (0.15, 0.35, 0.6, 0.95):
        y = y0 + (y1 - y0) * d
        cv.line(0, y, cv.W, y, fg, "-")


# ------------------------------------------------------------- the station

def train(cv: Canvas, x, y, cars, fg, body, win=WARM, door_open=False, length=44, lit=True):
    """Side view of a commuter train; (x, y) top-left of the first car."""
    for c in range(cars):
        cx = x + c * (length + 2)
        fill_rect(cv, cx, y, cx + length, y + 9, body, " ")
        cv.box(cx, y, cx + length, y + 9, fg, "+-|", bold=True)
        cv.line(cx, y + 6, cx + length, y + 6, REDBG, "=")
        for wx in range(int(cx) + 3, int(cx + length) - 5, 8):
            fill_rect(cv, wx, y + 2, wx + 5, y + 4, win if lit else body * 0.7, "#" if lit else " ",
                      mix(win, PAPER, 0.4))
        cv.put(int(cx) + 4, int(y) + 10, "(O)", fg)
        cv.put(int(cx + length) - 7, int(y) + 10, "(O)", fg)


def platform(cv: Canvas, y, fg, edge=REDBG):
    fill_rect(cv, 0, y, cv.W, y + 2, CONCRETE, "_", mix(CONCRETE, PAPER, 0.3))
    cv.line(0, y, cv.W, y, edge, "=", bold=True)


def flapboard(cv: Canvas, x, y, rows: list[str], fg, bg=INK, width=None, flicker=None):
    """Split-flap departure board."""
    width = width or max(len(r) for r in rows) + 2
    cv.box(x, y, x + width + 1, y + len(rows) * 2 + 1, fg, "+=|", fill=True, bg=bg, bold=True)
    for i, r in enumerate(rows):
        s = r if (flicker is None or flicker[i] is None) else flicker[i]
        cv.put(x + 2, y + 1 + i * 2, s, fg, bold=True)


# --------------------------------------------------------------- screens

def monitor(cv: Canvas, x0, y0, x1, y1, fg, bg=INK, stand=True):
    cv.box(x0, y0, x1, y1, fg, "+=|", fill=True, bg=bg, bold=True)
    if stand:
        cv.put(int((x0 + x1) / 2) - 2, int(y1) + 1, "/__\\", fg)


def crowd_top(cv: Canvas, t, seed, n, x0, y0, x1, y1, fg, speed=8.0, chars="o0O"):
    """People from above (heads/umbrellas), drifting horizontally both ways."""
    rng = np.random.default_rng(seed)
    xs = rng.uniform(x0, x1, n)
    ys = rng.uniform(y0, y1, n)
    d = np.where(rng.random(n) < 0.5, -1, 1)
    sp = rng.uniform(0.5, 1.2, n) * speed
    xs = x0 + (xs - x0 + d * sp * t) % (x1 - x0)
    ids = cv.ids(chars)
    cv.scatter(xs, ys, ids[np.arange(n) % len(ids)], fg=fg)
    return xs, ys


def walkers(cv: Canvas, t, seed, n, y, fg, speed=10, x0=-10, x1=None, dir_=1):
    x1 = cv.W + 10 if x1 is None else x1
    rng = np.random.default_rng(seed)
    for i in range(n):
        off = rng.uniform(0, x1 - x0)
        sp = speed * rng.uniform(0.7, 1.3)
        x = x0 + (off + dir_ * sp * t) % (x1 - x0)
        S.walker(cv, x, int(y + rng.integers(-1, 2)), t * sp * 0.25 + i * 0.3, fg)
