"""Variety pass on the abstract verses + question/answer/verdict lines.

Each verse line now has its own palette, scale and grammar (dark / red /
paper / blue / full colour; huge type vs. particles; split frames), and
lines about answers, truth and expectation play as rapid quiz sequences.
"""
from __future__ import annotations

import math

import numpy as np

from . import abstract as A
from . import quiz as Q
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, NIGHT, DAY, PAPER, mix
from .raster import Post
from .scenes import ease, ease_out
from .scenes5 import (DEEP, RED2, REDDK, P, fin, line_text, _word_of, btot)
from .shots import finish, beats_in
from .timeline import Ctx

REDBG = hexc("#d9261c")
CYAN = hexc("#4fd6e8")
YEL = hexc("#ffd84a")


def fin_paper(cv, ctx, hit=0.6, **kw):
    kw.setdefault("glow", 0.05)
    return finish(cv, ctx, DAY, hit, **kw)


def fin_red(cv, ctx, hit=0.8, **kw):
    kw.setdefault("glow", 0.2)
    return finish(cv, ctx, NIGHT, hit, **kw)


def quiz_post(p, hit):
    if hit > 0.3:
        p.chroma = max(p.chroma, int(4 * hit))
        p.shake = (int(4 * hit), int(2 * hit))
    return p


# ------------------------------------------------------------------ verse 1

def b_oscillo(cv: Canvas, ctx: Ctx) -> Post:
    """The low hum on the tape.  Full red frame; a giant black oscillograph
    trace fills it -- the slow wave of the bass drawn as a thick band of
    strokes -- and each kick throws a spike that rings out across."""
    cv.clear(REDBG, INK)
    t = ctx.t
    low = ctx.feat("low")
    xs = np.arange(160)
    since = ctx.since_beat
    spike = ctx.pulse(3) * np.exp(-((xs - (20 + since * 260)) / 12) ** 2) * 14
    y = 23 + (6 + 9 * low) * np.sin(xs * 0.045 - t * 2.2) + spike * np.sin(xs * 0.9)
    for x in range(160):
        th = 2 + int(4 * low)
        for k in range(-th, th + 1):
            yy = int(round(y[x] + k))
            if 0 <= yy < P:
                cv.put(x, yy, "#" if abs(k) < th else "=", INK, bold=True)
    for gx in range(0, 160, 20):
        cv.line(gx, 0, gx, P - 1, mix(REDBG, INK, 0.25), ":")
    for gy in range(3, P, 8):
        cv.line(0, gy, 159, gy, mix(REDBG, INK, 0.25), "-")
    cv.put(3, 1, f"CH1  {20 + int(40 * low):2d} Hz   5 V/div", INK, bold=True)
    return fin_red(cv, ctx, 1.3)


def b_tide_paper(cv: Canvas, ctx: Ctx) -> Post:
    """The front line of everyday, on paper: an ink tide of 日常 glyphs
    against a red line -- and on each beat the line is pushed one step back."""
    cv.clear(PAPER, INK)
    X, Y = A.coords(cv)
    t = ctx.t
    retreat = int(beats_in(ctx)) * 6
    yy = np.arange(P)
    lx = 70 + retreat + 4 * ctx.pulse(5) * np.exp(-((yy - 23) / 9) ** 2) + 1.2 * np.sin(yy * 0.4 + t * 3)
    nz = A.fbm(X * 0.09 + t * 0.8, Y * 0.09, 3)
    edge = lx[:, None] - 2 - 14 * nz
    m = X < edge
    A.text_fill(cv, m, "日常日常日常", INK, offset=int(t * 10))
    dens = np.clip((edge - X) / 25, 0.15, 1)
    cv.fg[:P][m] = mix(PAPER, INK, 1.0) * dens[m][:, None] + PAPER * (1 - dens[m][:, None])
    for y in range(P):
        x = int(round(lx[y]))
        for d in range(3):
            cv.put(x + d, y, "|", RED2, bold=True)
    cv.put(int(lx[3]) + 6, 3, "← 最前線", RED2, bold=True)
    return fin_paper(cv, ctx, 1.0)


def b_where_quiz(cv: Canvas, ctx: Ctx) -> Post:
    """Where am I supposed to go?  A terminal asks; destinations are tried and
    pass or fail in turn, faster and faster; the last returns null."""
    cards = [("where_to_go", "home", "✗"), ("where_to_go", "the sea", "✓"),
             ("where_to_go", "anywhere", "✗"), ("where_to_go", "null", "?")]
    hit, _ = Q.run(cv, ctx, cards, skin="term", beats_per_card=max(0.8, btot(ctx) / 4))
    return quiz_post(fin(cv, ctx, 0.4, glow=0.3), hit)


def b_bigclock(cv: Canvas, ctx: Ctx) -> Post:
    """Not stopping, even now.  Paper; one giant stopwatch reading that fills
    the frame, hundredths a red blur, a sweep bar racing underneath."""
    cv.clear(PAPER, INK)
    t = ctx.t * 3.7
    s = f"{int(t // 60) % 60:02d}:{int(t) % 60:02d}"
    bmp = cv.text_bitmap(s, 24, True)
    cv.shape_field(bmp, int(70 - bmp.shape[1] / 2), 6, INK)
    hs = f".{int(t * 100) % 100:02d}"
    bmp = cv.text_bitmap(hs, 12, True)
    cv.shape_field(bmp, 122, 17, RED2)
    k = (ctx.t * 1.3) % 1
    Wd.fill_rect(cv, 6, 38, 6 + 148 * k, 40, RED2, "=", PAPER)
    cv.box(6, 37, 154, 41, INK, "+-|")
    return fin_paper(cv, ctx, 0.8)


def b_kaleido_color(cv: Canvas, ctx: Ctx) -> Post:
    """Everything keeps changing -- in colour this time: a kaleidoscope whose
    palette jumps on every half-beat."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    k = int(beats_in(ctx) * 2)
    dx, dy = X - 80, Y - 23 * cv.aspect
    r = np.hypot(dx, dy)
    a = np.arctan2(dy, dx)
    seg_ = math.pi / 4
    a = np.abs(((a + t * 0.4) % seg_) - seg_ / 2)
    u, v = r * np.cos(a) * 0.07, r * np.sin(a) * 0.07
    f = (A.warp(u, v, t, seed=k * 5, k=2.5) - 0.3) * 2.2
    pals = [
        [(0, hexc("#12002a")), (0.4, hexc("#ff3b8a")), (0.8, YEL), (1, PAPER)],
        [(0, hexc("#001a2a")), (0.4, CYAN), (0.8, hexc("#7cff8a")), (1, PAPER)],
        [(0, hexc("#2a0a00")), (0.4, RED2), (0.8, hexc("#ff9a3a")), (1, PAPER)],
        [(0, PAPER), (0.4, hexc("#8a7cff")), (0.8, hexc("#2a1a6a")), (1, INK)],
    ]
    A.shade(cv, f, " .:-=+*#%@", pals[k % 4], bg_scale=0.45)
    return fin(cv, ctx, 1.2, glow=0.2)


# ------------------------------------------------------------------ verse 2

def b_moire_color(cv: Canvas, ctx: Ctx) -> Post:
    """The ultrasound she carried in.  Interference of two to four sources,
    in spectral colour on black -- each band a different hue, shimmering."""
    cv.clear(hexc("#020308"), PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    nb = min(4, int(beats_in(ctx)) + 2)
    srcs = [(50, 23), (110, 23), (80, 6), (80, 40)][:nb]
    f = np.zeros_like(X)
    for i, (sx, sy) in enumerate(srcs):
        sx += 8 * math.sin(t * 0.7 + i)
        f += np.cos(np.hypot(X - sx, Y - sy * cv.aspect) * 1.1 - t * 18)
    f = 0.5 + 0.5 * f / nb
    hue = (np.hypot(X - 80, Y - 23 * cv.aspect) * 0.02 + t * 0.2) % 1
    col = A.gradient([(0, hexc("#ff3b8a")), (0.33, CYAN), (0.66, YEL), (1, hexc("#ff3b8a"))], hue)
    col = col * (0.25 + 0.75 * f[..., None])
    cv.density(f ** 1.2, " .:+*#", color=col, thresh=0.12)
    cv.bg[:P] = col * 0.12
    for (sx, sy) in srcs:
        cv.put(int(sx), int(sy), "◎", PAPER, bold=True)
    return fin(cv, ctx, 0.8, glow=0.45)


def b_lattice_paper(cv: Canvas, ctx: Ctx) -> Post:
    """She ran from the everyday -- on paper: a printed grid, a red line
    tearing out of it, the paper behind it ripping open to black."""
    cv.clear(PAPER, INK)
    u, t = ctx.u, ctx.t
    pts = []
    for i in range(200):
        s = i / 199
        y = 23 + 8 * math.sin(s * 9) + (min(0.0, 0.5 - s) * 90 if s > 0.5 else 0)
        pts.append((10 + 150 * s, y))
    nshow = int(200 * min(1.0, u * 1.2))
    for gy in range(1, P, 3):
        for gx in range(1, 160, 4):
            cv.put(gx, gy, "+", mix(PAPER, INK, 0.45))
    for (x, y) in pts[:nshow]:
        tear = Wd.disc(cv, x, y, 1.6 + (1.2 if x > 85 else 0))
        Wd.paint(cv, tear & (cv.yy < P), INK, " ")
    for (x, y) in pts[:nshow]:
        cv.put(int(x), int(y), "#", RED2, bold=True)
    return fin_paper(cv, ctx, 0.6)


def b_grin_red(cv: Canvas, ctx: Ctx) -> Post:
    """You'll laugh at me.  A red frame packed with w's; the grin opens wider
    on every beat and the w's inside it turn white."""
    cv.clear(REDBG, INK)
    X, Y = A.coords(cv)
    b = beats_in(ctx)
    open_ = 0.3 + 0.7 * ease(min(1.0, b / btot(ctx)))
    dx, dy = (X - 80) / 72, (Y - 23 * cv.aspect + 4) / 38
    mouth = (dx ** 2 + (dy - 0.1) ** 2 < 1) & ~(dx ** 2 + ((dy + 0.3 - 0.5 * open_) / 0.8) ** 2 < 1) & (dy > -0.15)
    rows = cv.yy[:P].astype(int) % 2 == 0
    ys, xs = np.nonzero(rows)
    cv.ch[ys, xs] = cv.ids("w")[0]
    cv.fg[ys, xs] = mix(REDBG, INK, 0.45)
    ys, xs = np.nonzero(mouth)
    cv.ch[ys, xs] = cv.ids("W")[0]
    cv.fg[ys, xs] = PAPER
    cv.bg[ys, xs] = INK
    for ex in (52, 108):
        Wd.paint(cv, Wd.disc(cv, ex, 11, 4 + ctx.pulse(5)) & ~Wd.disc(cv, ex, 13, 4), INK, "^", PAPER)
    return fin_red(cv, ctx, 1.0)


def b_truth_verdicts(cv: Canvas, ctx: Ctx) -> Post:
    """Even a mistaken truth.  本当 written in tiny 嘘 -- and a judge stamps it
    each beat: ○, ×, ○, × … it cannot decide, and the stamps crack it in two."""
    cv.clear(DEEP, PAPER)
    A.text_fill(cv, cv.yy < P, "嘘", mix(DEEP, PAPER, 0.08))
    _word_of(cv, ctx, "本当", "嘘嘘嘘", 34, PAPER)
    b = beats_in(ctx)
    marks = ["○", "×", "○", "×"]
    i = min(len(marks) - 1, int(b))
    k = (b % 1) / 0.2
    col = hexc("#2fbf5a") if marks[i] == "○" else RED2
    Q.stamp(cv, marks[i], 130 if i % 2 else 30, 12, 12, col, k)
    for j in range(i):
        cv.put(4 + j * 4, 42, marks[j], hexc("#2fbf5a") if marks[j] == "○" else RED2, bold=True)
    if b >= 2.2:
        rng = np.random.default_rng(2)
        x, y = 80.0, 0.0
        while y < P * min(1.0, (b - 2.2) * 2):
            nx, ny = x + rng.uniform(-5, 5), y + rng.uniform(2, 5)
            cv.line(x, y, nx, ny, RED2, None, bold=True)
            x, y = nx, ny
    return quiz_post(fin(cv, ctx, 1.0), (1 - min(1, k)) if b % 1 < 0.2 else 0)


def b_check_show(cv: Canvas, ctx: Ctx) -> Post:
    """Checking, every single day.  A quiz show that asks the same question
    again and again -- 'same as yesterday?' -- 'yes' ✓ -- with the odd slip ✗ --
    faster each time."""
    cards = [("今日も昨日と同じ？", "はい", "✓"), ("明日も今日と同じ？", "いいえ", "✗"),
             ("今日も昨日と同じ？", "はい", "✓"), ("本当に同じ？", "はい", "✓"),
             ("昨日は何曜日？", "……", "✗"), ("今日も昨日と同じ？", "はい", "✓")]
    hit, _ = Q.run(cv, ctx, cards, skin="show", beats_per_card=max(0.6, btot(ctx) / 6))
    return quiz_post(fin(cv, ctx, 0.4, glow=0.25), hit)


# ------------------------------------------------------- pre-chorus 2 / chorus 2

def b_exam(cv: Canvas, ctx: Ctx) -> Post:
    """But I don't know the answer.  An exam sheet: question, answer, verdict
    -- ✓, ✗, ✓, ✗ -- quicker each time, until the last answer is only '?'."""
    cards = [("私は何処に行けば", "A. 遠いとこ", "✓"), ("正しい嘘とは", "B. 本当", "✗"),
             ("日常の顔は", "C. 冷たい", "✓"), ("期待しても", "D. いい", "✗"),
             ("答えは", "?", "?")]
    hit, _ = Q.run(cv, ctx, cards, skin="exam", beats_per_card=btot(ctx) / 5)
    return quiz_post(fin_paper(cv, ctx, 0.3), hit)


def b_loss_show(cv: Canvas, ctx: Ctx) -> Post:
    """Expecting it was a loss.  Quiz show: 'Did you expect it?' -- 'YES' --
    ✗, buzzer, the score drains; 'Will you again?' -- 'NO' -- ✓."""
    cards = [("期待した？", "YES", "✗"), ("また期待する？", "NO", "✓")]
    hit, _ = Q.run(cv, ctx, cards, skin="show", beats_per_card=btot(ctx) / 2)
    cv.put(120, 44, f"SCORE {max(0, 3000 - int(beats_in(ctx) * 900)):5d}", YEL, bold=True)
    return quiz_post(fin(cv, ctx, 0.6, glow=0.25), hit)
