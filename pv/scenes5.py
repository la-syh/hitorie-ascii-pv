"""Abstract scenes (v4): the opening verses and the sinking, rethought as
moving images made of characters rather than depictions of objects.

The ideas stay tied to each line -- a message unspooling, a low hum, a
front line, a flow that won't settle, stored-up laughter, interference,
a lattice one escapes from, truth made of lies, the descent -- but they are
drawn as fields, particles and typography.  Palette: ink, paper, one red,
with a deep blue only for the sea.
"""
from __future__ import annotations

import math

import numpy as np

from . import abstract as A
from . import shapes as S
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, NIGHT, DAY, PAPER, RED, mix
from .raster import Post
from .scenes import ease, ease_out, seg
from .shots import finish, beats_in, PIC_H
from .timeline import Ctx

DEEP = hexc("#07070b")
RED2 = hexc("#ff3b2e")
REDDK = hexc("#3a0806")
BLUE = hexc("#1d4f8a")
ABYSS = hexc("#02040a")
P = PIC_H


def fin(cv, ctx, hit=0.6, **kw):
    kw.setdefault("glow", 0.35)
    return finish(cv, ctx, NIGHT, hit, **kw)


def line_text(ctx) -> str:
    ln = ctx.line()
    return ln.text if ln else "日常と地球の額縁"


def btot(ctx):
    return max(1e-3, ctx.grid.beat_pos(ctx.t1) - ctx.grid.beat_pos(ctx.t0))


# =========================================================== VERSE 1

def a_message(cv: Canvas, ctx: Ctx) -> Post:
    """Answering-machine service.  Black; one red REC dot breathes in the
    centre.  On PLAY the message unspools out of it as a spiral of tape whose
    characters are the line itself, turning like a reel, widening each beat."""
    cv.clear(DEEP, PAPER)
    t, b = ctx.t, beats_in(ctx)
    cx, cy = 80, 23
    ids = A.text_glyphs(cv, line_text(ctx) + "  ", True)
    unspool = ease_out(min(1.0, max(0.0, b - 0.6) / 3.0))
    n = int(900 * unspool)
    k = np.arange(n)
    th = k * 0.055 - t * 1.6
    r = 2.5 + k * 0.045
    xs = cx + r * np.cos(th) * 1.0
    ys = cy + r * np.sin(th) / cv.aspect
    ok = (xs >= 0) & (xs < 160) & (ys >= 0) & (ys < P)
    xs, ys, k = xs[ok], ys[ok], k[ok]
    fade = np.clip(1 - k / 900, 0.15, 1)[:, None]
    col = PAPER * fade + DEEP * (1 - fade)
    head = k > n - 25
    col[head] = RED2
    cv.scatter(xs, ys, ids[k % len(ids)], fg=col)
    # the dot
    pulse = 1 + 0.4 * math.sin(t * 5)
    Wd.paint(cv, Wd.disc(cv, cx, cy, 2.2 * pulse), RED2, "@", PAPER)
    ring = Wd.disc(cv, cx, cy, 4 + 3 * ctx.pulse(5)) & ~Wd.disc(cv, cx, cy, 3 + 3 * ctx.pulse(5))
    cv.ch[ring] = cv.ids(".")[0]
    cv.fg[ring] = RED2
    cv.put(4, 2, "● REC  MESSAGE 01", RED2 if int(t * 2) % 2 else REDDK, bold=True)
    cv.put(140, 2, f"0:{int(ctx.lt * 10) % 60:02d}", GREY)
    return fin(cv, ctx, 0.4)


def a_lowfreq(cv: Canvas, ctx: Ctx) -> Post:
    """The low hum on the tape.  The whole screen is a sea of horizontal
    strokes heaving in long slow swells; every kick throws a pressure wave
    through it from the centre and the swell turns red at the crest."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    low = ctx.feat("low")
    d = np.hypot(X - 80, Y - 23 * cv.aspect)
    swell = 0.5 + 0.5 * np.sin(X * 0.06 - t * 1.4 + 0.6 * np.sin(Y * 0.05 + t * 0.7))
    since = ctx.since_beat
    front = np.exp(-((d - since * 140) / 6) ** 2) * ctx.pulse(2.5)
    f = 0.45 * swell + 0.85 * front + 0.2 * low
    lines = (np.floor(Y / cv.aspect) % 2 == 0)
    f = np.where(lines, f, f * 0.5)
    col = A.gradient([(0, DEEP), (0.3, mix(DEEP, PAPER, 0.35)), (0.7, PAPER), (1.0, RED2)], f)
    cv.density(f, " .-~=≈", color=col, thresh=0.04)
    cv.ch[P:] = 0
    return fin(cv, ctx, 1.4, glow=0.5)


def a_frontline(cv: Canvas, ctx: Ctx) -> Post:
    """The front line of everyday.  A red vertical line cuts the frame.  Left
    of it, a dense tide of 日常 glyphs presses forward like a crowd; right of
    it, nothing.  On each beat the tide surges against the line, which bends."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    surge = ctx.pulse(4)
    yy = np.arange(P)
    bend = 6 * surge * np.exp(-((yy - 23) / 10) ** 2) + 1.5 * np.sin(yy * 0.3 + t * 2)
    lx = 96 + bend
    nz = A.fbm(X * 0.08 + t * 0.6, Y * 0.08, 3)
    edge = lx[:, None] - 3 - 12 * nz
    m = X < edge
    dens = np.clip((edge - X) / 30, 0, 1)
    glyphs = A.text_glyphs(cv, "日常日常日常", True)
    ys, xs = np.nonzero(m)
    k = ((xs // 2) * 2 + (xs % 2) + ys * 6 + int(t * 8) * 2) % len(glyphs)
    cv.ch[ys, xs] = glyphs[k]
    cv.fg[ys, xs] = (PAPER * (0.25 + 0.75 * dens[ys, xs, None]))
    for y in range(P):
        x = int(round(lx[y]))
        cv.put(x, y, "|", RED2, bold=True)
        cv.put(x + 1, y, "|", RED2, bold=True)
    cv.put(104, 4, "最前線", RED2, bold=True)
    cv.put(104, 6, "FRONT LINE", GREY)
    return fin(cv, ctx, 1.0)


def a_flow(cv: Canvas, ctx: Ctx) -> Post:
    """Where am I supposed to go?  Thousands of arrows follow a flow field
    that keeps turning; every half-beat the field is re-drawn and the arrows
    swing together -- one red arrow never agrees with the rest."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    k = beats_in(ctx) * 2
    phase = math.floor(k) + ease(k % 1)
    ang = A.fbm(X * 0.03 + phase * 0.7, Y * 0.03, 11) * 6.283 * 2 + t * 0.2
    sub = ((cv.xx[:P].astype(int) % 2 == 0) | (cv.yy[:P].astype(int) % 2 == 0))
    arrows = np.array(cv.ids("-/|\\-/|\\"))
    idx = (np.round(((-ang) % 6.2832) / 6.2832 * 8).astype(int)) % 8
    ys, xs = np.nonzero(sub)
    cv.ch[ys, xs] = arrows[idx[ys, xs]]
    br = 0.45 + 0.55 * A.vnoise(X * 0.1 + t, Y * 0.1, 3)
    cv.fg[ys, xs] = PAPER * br[ys, xs, None]
    # the red one
    rx, ry = 81, 22
    a = -ang[ry, rx] + math.pi
    cv.put(rx, ry, "→↑←↓"[int(round((a % 6.2832) / 6.2832 * 4)) % 4], RED2, bold=True)
    Wd.paint(cv, Wd.disc(cv, rx, ry, 2.6) & ~Wd.disc(cv, rx, ry, 1.6), REDDK, " ")
    return fin(cv, ctx, 0.8)


def _pile(cv, ctx, n, t_local, x0=30, x1=130, floor=44):
    """Characters falling and piling into a mound (sand-like)."""
    rng = np.random.default_rng(7)
    words = A.text_glyphs(cv, "HAhaw草www", True)
    heights = np.zeros(160, np.int32)
    for i in range(n):
        x = int(rng.normal(80, 14))
        x = min(x1, max(x0, x))
        # settle: roll down while a neighbour is lower
        for _ in range(6):
            l, r = heights[x - 1], heights[x + 1]
            if l < heights[x] - 1:
                x -= 1
            elif r < heights[x] - 1:
                x += 1
            else:
                break
        y = floor - heights[x]
        heights[x] += 1
        cv.ch[y, x] = words[i % len(words)]
        cv.fg[y, x] = PAPER if i % 9 else RED2
    return heights


def a_stockpile(cv: Canvas, ctx: Ctx) -> Post:
    """The jokes she stored up.  Laughter falls as grains -- H, a, w, 草 --
    and piles into a dune that grows on every beat; the air above is thick
    with more still falling."""
    cv.clear(DEEP, PAPER)
    b = beats_in(ctx)
    n = int(120 + 260 * b)
    _pile(cv, ctx, n, ctx.lt)
    rng = np.random.default_rng(3)
    m = 120
    xs = rng.normal(80, 16, m)
    ys = (rng.uniform(0, 40, m) + ctx.lt * rng.uniform(12, 24, m)) % 40
    words = A.text_glyphs(cv, "HAhaw", True)
    cv.scatter(xs, ys, words[np.arange(m) % len(words)], fg=mix(PAPER, DEEP, 0.4))
    cv.put(4, 2, f"STOCK  {n:4d}", GREY)
    return fin(cv, ctx, 0.5)


def a_burst(cv: Canvas, ctx: Ctx) -> Post:
    """…spat out all at once.  The dune detonates: every grain flies out in a
    fan with a trail, the screen floods red and the sound becomes letters."""
    t = ctx.lt
    cv.clear(mix(DEEP, RED2, min(1.0, t * 3)), PAPER)
    rng = np.random.default_rng(5)
    n = 1400
    x0 = rng.normal(80, 12, n)
    y0 = 44 - np.abs(rng.normal(0, 5, n))
    ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05, n)
    sp = rng.uniform(30, 150, n)
    words = A.text_glyphs(cv, "HAhaw草!?", True)
    for trail in range(5, -1, -1):
        tt = max(0.0, t - trail * 0.025)
        xs = x0 + np.cos(ang) * sp * tt
        ys = y0 + (np.sin(ang) * sp * tt + 40 * tt * tt) / cv.aspect
        col = PAPER if trail == 0 else mix(RED2, PAPER, 0.5 - trail * 0.08)
        cv.scatter(xs, ys, words[np.arange(n) % len(words)] if trail == 0 else ".", fg=col)
    p = fin(cv, ctx, 1.8, glow=0.3)
    p.flash = 0.35 * max(0.0, 1 - t * 6)
    return p


def a_freeze(cv: Canvas, ctx: Ctx) -> Post:
    """'Well, yeah.'  The explosion freezes mid-air, the image inverts to
    paper, and the frozen letters drift down slowly like snow."""
    cv.clear(PAPER, INK)
    rng = np.random.default_rng(5)
    n = 700
    tt = 0.45
    x0 = rng.normal(80, 12, n)
    y0 = 44 - np.abs(rng.normal(0, 5, n))
    ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05, n)
    sp = rng.uniform(30, 150, n)
    xs = x0 + np.cos(ang) * sp * tt
    ys = y0 + (np.sin(ang) * sp * tt + 40 * tt * tt) / cv.aspect + ctx.lt * rng.uniform(1, 4, n)
    words = A.text_glyphs(cv, "HAhaw草!?", True)
    cv.scatter(xs, ys, words[np.arange(n) % len(words)], fg=mix(INK, PAPER, 0.35))
    cv.put(76, 22, "そりゃ", INK, bold=True)
    return finish(cv, ctx, DAY, 0.2)


def a_timeriver(cv: Canvas, ctx: Ctx) -> Post:
    """Not stopping, even now.  A river of timestamps streams right-to-left
    in parallax bands, faster in the middle; the red current is now."""
    cv.clear(DEEP, PAPER)
    t = ctx.t
    for y in range(P):
        d = abs(y - 23) / 23
        sp = 160 * (1 - d) ** 2 + 12
        off = t * sp + y * 37
        s = "".join(f"{int((off / 9 + i) % 24):02d}:{int((off + i * 7) % 60):02d}  " for i in range(24))
        start = int(off) % 9
        col = RED2 if abs(y - 23) < 1 else PAPER * (0.2 + 0.8 * (1 - d))
        cv.put(-start, y, s[: 170], col, bold=abs(y - 23) < 1)
    return fin(cv, ctx, 0.8)


def a_kaleido(cv: Canvas, ctx: Ctx) -> Post:
    """Everything keeps changing.  A kaleidoscope of warped noise, six-fold
    mirrored, re-seeded and re-coloured on every half-beat."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    k = int(beats_in(ctx) * 2)
    dx, dy = X - 80, Y - 23 * cv.aspect
    r = np.hypot(dx, dy)
    a = np.arctan2(dy, dx)
    seg_ = math.pi / 3
    a = np.abs(((a + t * 0.3) % seg_) - seg_ / 2)
    u, v = r * np.cos(a) * 0.06, r * np.sin(a) * 0.06
    f = A.warp(u, v, t, seed=k * 5, k=2.5)
    f = (f - 0.3) * 2.2
    pal = [
        [(0, DEEP), (0.5, mix(DEEP, PAPER, 0.5)), (1, PAPER)],
        [(0, DEEP), (0.5, RED2), (1, PAPER)],
        [(0, PAPER), (0.5, GREY), (1, DEEP)],
        [(0, REDDK), (0.6, RED2), (1, hexc("#ffd0c0"))],
    ][k % 4]
    A.shade(cv, f, " .:-=+*#%@", pal)
    return fin(cv, ctx, 1.2, glow=0.2)


# =========================================================== VERSE 2

def a_soot(cv: Canvas, ctx: Ctx) -> Post:
    """A sooty four-and-a-half-mat room.  Soot as smoke: dark warped noise
    drifts across; out of it the faint outline of a tiny room condenses --
    the mats' pinwheel, a window -- then is smudged away again."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    f = A.warp(X * 0.025, Y * 0.025, t * 0.8, seed=21, k=3)
    reveal = math.sin(min(1.0, ctx.u * 1.15) * math.pi)
    A.shade(cv, (f - 0.35) * 1.6, " .,:;~", [(0, DEEP), (1, hexc("#6a6258"))], bg_scale=0.5)
    # the room drawn in soot: square of mats, seen from above
    snap = cv.snapshot()
    S_ = 18
    x0, y0 = 80 - S_ * 1.7, 23 - S_ / 2 * 1.0
    for (a, b, c, d) in ((0, 0, 2, 1), (2, 0, 3, 2), (1, 2, 3, 3), (0, 1, 1, 3), (1, 1, 2, 2)):
        cv.box(x0 + a * S_ * 1.13, y0 + b * S_ / 3 * 1.0, x0 + c * S_ * 1.13 - 1, y0 + d * S_ / 3 - 1,
               mix(DEEP, PAPER, 0.8), "+=|")
    keep = A.vnoise(X * 0.15 + t, Y * 0.15, 9) < reveal
    ch, fg, bg = snap
    cv.ch[:P][~keep] = ch[:P][~keep]
    cv.fg[:P][~keep] = fg[:P][~keep]
    cv.put(122, 41, "四畳半  4.5", GREY)
    return fin(cv, ctx, 0.3, glow=0.2)


def a_interference(cv: Canvas, ctx: Ctx) -> Post:
    """The ultrasound she carried in.  Two emitters; their rings cross into a
    moiré interference pattern that shimmers far too fast to hear; a third
    source appears on each beat and the pattern reorganises."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    nb = min(4, int(beats_in(ctx)) + 2)
    srcs = [(50, 23), (110, 23), (80, 6), (80, 40)][:nb]
    f = np.zeros_like(X)
    for i, (sx, sy) in enumerate(srcs):
        sx += 8 * math.sin(t * 0.7 + i)
        d = np.hypot(X - sx, Y - sy * cv.aspect)
        f += np.cos(d * 1.1 - t * 18)
    f = 0.5 + 0.5 * f / nb
    f = f ** 1.3
    col = A.gradient([(0, DEEP), (0.6, mix(DEEP, PAPER, 0.6)), (0.9, PAPER), (1, RED2)], f)
    cv.density(f, " .:+*#", color=col, thresh=0.05)
    for (sx, sy) in srcs:
        cv.put(int(sx), int(sy), "◎", RED2, bold=True)
    cv.put(4, 42, "40 kHz  ·  inaudible", GREY)
    return fin(cv, ctx, 0.8, glow=0.4)


def a_lattice(cv: Canvas, ctx: Ctx) -> Post:
    """She ran from the everyday.  A rigid lattice of '+' fills the frame; a
    red line threads through it, then bends free and tears out of the grid --
    the lattice ripples and buckles in its wake."""
    cv.clear(DEEP, PAPER)
    t = ctx.t
    u = ctx.u
    pts = []
    for i in range(200):
        s = i / 199
        x = 10 + 150 * s
        y = 23 + 8 * math.sin(s * 9)
        if s > 0.5:
            y += (s - 0.5) ** 2 * -90
        pts.append((x, y))
    nshow = int(200 * min(1.0, u * 1.2))
    head = pts[max(0, nshow - 1)]
    for gy in range(2, P, 3):
        for gx in range(2, 160, 5):
            d = math.hypot(gx - head[0], (gy - head[1]) * 1.6)
            push = 4 * math.exp(-d / 10) if nshow > 0 else 0
            wob = math.sin(d * 0.5 - t * 8) * math.exp(-d / 30) * 1.2 * (u > 0.5)
            dx = (gx - head[0]) / (d + 1e-3) * push
            cv.put(int(gx + dx + wob), int(gy + (gy - head[1]) / (d + 1e-3) * push * 0.5), "+",
                   mix(DEEP, PAPER, 0.7 if d > 12 else 1.0), bold=d < 12)
    for (x, y) in pts[:nshow]:
        cv.put(int(x), int(y), "#", RED2, bold=True)
    return fin(cv, ctx, 0.6)


def a_mouth(cv: Canvas, ctx: Ctx) -> Post:
    """You'll laugh at me.  The frame fills with w's in rows; their density
    draws a vast grinning crescent that widens on each beat around one small
    red dot."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    b = beats_in(ctx)
    open_ = 0.4 + 0.6 * ease(min(1.0, b / btot(ctx)))
    dx, dy = (X - 80) / 70, (Y - 23 * cv.aspect + 6) / 40
    outer = dx ** 2 + (dy - 0.15) ** 2 < 1
    inner = dx ** 2 + ((dy + 0.25 - 0.45 * open_) / 0.8) ** 2 < 1
    mouth = outer & ~inner & (dy > -0.1)
    rows = (cv.yy[:P].astype(int) % 2 == 0)
    ys, xs = np.nonzero(rows)
    cv.ch[ys, xs] = cv.ids("w")[0]
    cv.fg[ys, xs] = mix(DEEP, PAPER, 0.3)
    ys, xs = np.nonzero(mouth & rows)
    cv.ch[ys, xs] = cv.ids("W")[0]
    cv.fg[ys, xs] = PAPER
    Wd.paint(cv, Wd.disc(cv, 80, 16, 1.6 + 0.5 * ctx.pulse(5)), RED2, "@", PAPER)
    return fin(cv, ctx, 0.9)


def _word_of(cv, ctx, big: str, small: str, rows: int, fg, mark=None):
    bmp = cv.text_bitmap(big, rows, True)
    h, w = bmp.shape
    ox, oy = int(80 - w / 2), int(23 - h / 2)
    m = np.zeros((cv.H, cv.W), bool)
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(160, ox + w), min(P, oy + h)
    m[y0:y1, x0:x1] = bmp[y0 - oy:y1 - oy, x0 - ox:x1 - ox] > 0.45
    A.text_fill(cv, m, small, fg, offset=int(ctx.t * 6))
    return m


def a_truth_of_lies(cv: Canvas, ctx: Ctx) -> Post:
    """Even a mistaken truth.  A huge 本当 (truth) -- but look closely and it
    is written entirely in tiny 嘘 (lie); on the beat a red crack splits it."""
    cv.clear(DEEP, PAPER)
    A.text_fill(cv, cv.yy < P, "嘘", mix(DEEP, PAPER, 0.08))
    _word_of(cv, ctx, "本当", "嘘嘘嘘", 34, PAPER)
    b = beats_in(ctx)
    if b >= 1.5:
        k = min(1.0, (b - 1.5) * 3)
        rng = np.random.default_rng(2)
        x, y = 80.0, 0.0
        while y < P * k:
            nx, ny = x + rng.uniform(-5, 5), y + rng.uniform(2, 5)
            cv.line(x, y, nx, ny, RED2, None, bold=True)
            x, y = nx, ny
    return fin(cv, ctx, 1.0)


def a_lie_of_truths(cv: Canvas, ctx: Ctx) -> Post:
    """Even a correct lie.  The reverse: a huge 嘘 built of tiny 正 (correct),
    paper-white, stamped with a red circle of approval."""
    cv.clear(PAPER, INK)
    A.text_fill(cv, cv.yy < P, "正", mix(PAPER, INK, 0.07))
    _word_of(cv, ctx, "嘘", "正正正", 40, INK)
    b = beats_in(ctx)
    if b >= 1:
        k = min(1.0, (b - 1) * 4)
        r = 16 * (1.5 - 0.5 * k)
        ring = Wd.disc(cv, 112, 30, r) & ~Wd.disc(cv, 112, 30, r - 2.2)
        Wd.paint(cv, ring, RED2, "#", mix(RED2, PAPER, 0.3))
        cv.put(108, 30, "正解", RED2, bold=True)
    return finish(cv, ctx, DAY, 0.8)


def a_cutouts(cv: Canvas, ctx: Ctx) -> Post:
    """The correct answers she cut out.  The frame is a sheet of paper printed
    with an endless field of text; rectangles are cut out of it one per
    half-beat -- revealing the dark beneath -- and the cut pieces float away,
    turning."""
    cv.clear(PAPER, INK)
    A.text_fill(cv, cv.yy < P, "正解正しい答え", mix(PAPER, INK, 0.25))
    rng = np.random.default_rng(8)
    k = int(beats_in(ctx) * 2) + 1
    for i in range(min(k, 12)):
        w, h = rng.integers(12, 26), rng.integers(4, 9)
        x, y = rng.integers(4, 150 - w), rng.integers(2, P - h - 2)
        hole = Wd.rect(cv, x, y, x + w, y + h)
        Wd.paint(cv, hole, DEEP, " ")
        cv.box(x, y, x + w, y + h, mix(PAPER, INK, 0.5), "+-|")
        age = beats_in(ctx) * 2 - i
        if age > 0:
            fx = x + age * 7
            fy = y - age * 3
            snap_mask = Wd.rect(cv, fx, fy, fx + w * (0.8 + 0.2 * math.cos(age)), fy + h)
            Wd.paint(cv, snap_mask, mix(PAPER, hexc("#e8dcc0"), 0.5), " ")
            cv.put(int(fx) + 2, int(fy) + 1, "正解", RED2 if i == k - 1 else INK, bold=True)
    return finish(cv, ctx, DAY, 0.5)


def a_ticks(cv: Canvas, ctx: Ctx) -> Post:
    """Checking, every single day.  A wall of days -- 365 small cells -- ticked
    by a diagonal wave sweeping through on every beat; each pass leaves the
    same pattern as the last."""
    cv.clear(DEEP, PAPER)
    t = ctx.t
    ph = ctx.beat % 1.0
    for i in range(365):
        c, r = i % 26, i // 26
        x, y = 4 + c * 6, 2 + r * 3
        wave = abs(((c + r) / 40) - ph) < 0.06
        done = (c + r) / 40 < ph
        s = "[✓]" if done else "[ ]"
        col = RED2 if wave else (PAPER if done else mix(DEEP, PAPER, 0.3))
        cv.put(x, y, s, col, bold=wave)
    cv.put(4, 44, f"DAY {int(ctx.beat) % 365 + 1:03d} / 365   again", GREY)
    return fin(cv, ctx, 0.6)


# ============================================================ sinking

def a_descent(cv: Canvas, ctx: Ctx) -> Post:
    """Just want to sink, innocently.  We fall through water: caustic light
    nets ripple across the frame, darkening with depth; the sung characters
    themselves sink past us and come apart into bubbles; at the end only one
    red point keeps going down into the black."""
    X, Y = A.coords(cv)
    t = ctx.t
    u = ctx.u
    depth = ease(u)
    cv.clear(ABYSS, PAPER)
    # caustics: thin bright nets where two drifting noise fields cross
    n1 = A.fbm(X * 0.035 + t * 0.25, Y * 0.045 + t * 0.12, 31)
    n2 = A.fbm(X * 0.035 - t * 0.2, Y * 0.045 + 3 + t * 0.1, 37)
    c = 1 - np.abs(np.sin((n1 - n2) * 14))
    c = c ** 4
    light = (1 - depth ** 1.4) * (1 - Y / (P * cv.aspect) * 0.5)
    f = np.clip(c * light * 1.6, 0, 1)
    cv.bg[:P] = A.gradient([(0, ABYSS), (0.5, hexc("#0b2a4e")), (1, BLUE)], light * 0.9 + 0.05)
    col = A.gradient([(0, BLUE), (0.5, hexc("#7fb6e8")), (1, PAPER)], f)
    cv.density(f, " .-~=*", color=col, thresh=0.3)
    for k in range(4):
        rx = 30 + k * 34 + 6 * math.sin(t * 0.4 + k)
        ray = (np.abs(cv.xx[:P] - rx - cv.yy[:P] * 0.5) < 2.5 + k % 2)
        cv.bg[:P][ray] = mix(cv.bg[:P][ray], hexc("#5a8ab0"), 0.22 * (1 - depth))
    # the sung characters, big, sinking past us and eroding into bubbles
    ln = ctx.line()
    if ln is not None:
        for i, ch_ in enumerate(ln.text):
            tc = ln.t + i * 0.13
            if t < tc:
                continue
            age = t - tc
            x = 6 + (i * 17) % 150 + 3 * math.sin(age * 1.5 + i)
            y = -10 + age * 13 + (i % 3) * 3 - ((i * 17) // 150) * 12
            if y > P:
                continue
            bmp = cv.text_bitmap(ch_, 9, True)
            h, w = bmp.shape
            ox, oy = int(x), int(y)
            yy, xx = np.mgrid[0:h, 0:w]
            erode = A.vnoise((xx + ox) * 0.6, (yy + oy) * 0.6 + i * 5, 5 + i) < max(0.0, age - 0.6) * 0.3
            b2 = np.where(erode, 0, bmp)
            y0c, x0c = max(0, oy), max(0, ox)
            y1c, x1c = min(P, oy + h), min(160, ox + w)
            if y1c > y0c and x1c > x0c:
                cv.ch[y0c:y1c, x0c:x1c] = 0
            cv.shape_field(b2, ox, oy, mix(PAPER, BLUE, min(0.7, depth)), fill="#")
            ey, ex = np.nonzero(erode & (bmp > 0.4))
            if len(ex):
                rise = (age * 10 + ex * 0.7) % 9
                cv.scatter(ox + ex, oy + ey - rise, "o", fg=mix(PAPER, BLUE, 0.35))
    # depth gauge and the red point
    dm = int(depth * 1200)
    cv.put(146, 3, f"-{dm:4d} m", hexc("#7fb6e8"))
    for k in range(0, P, 3):
        cv.put(156, k, "-" if (k + int(dm / 10)) % 9 else "=", mix(BLUE, PAPER, 0.4))
    ry = 10 + 30 * depth
    Wd.paint(cv, Wd.disc(cv, 80, ry, 1.4), RED2, "@", PAPER)
    for j in range(1, 7):
        cv.put(80 + (j % 2) * 2 - 1, int(ry - j * 2), "o", mix(PAPER, BLUE, 0.5))
    p = fin(cv, ctx, 0.2, glow=0.45)
    p.fade = 1 - 0.2 * depth
    return p
