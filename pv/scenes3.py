"""Composed per-line scenes, verse 2 and the pre-choruses.

Verse 2 stays in and around her flat (the cramped room, the cat, the
building at night, the phone, the electronics-store window, the desk);
pre-chorus 1 moves to the rooftop; pre-chorus 2 drives away, sinks into the
sea, sits an exam and ends in a too-clean show room.
"""
from __future__ import annotations

import math

import numpy as np

from . import motifs as M
from . import shapes as S
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, NIGHT, DAY, PAPER, RED, mix
from .raster import Post
from .scenes import ease, ease_out, seg
from .scenes2 import WALL_N, FLOOR_N, DESK, room_night
from .shots import finish, beats_in, poly
from .timeline import Ctx
from .world import (CONCRETE, NIGHT_SKY, NIGHT_SKY2, REDBG, REDDK, WARM, WARM_DIM, fill_rect, paint,
                    rect, sprite, vgrad)


def fin_n(cv, ctx, hit=0.6, **kw):
    kw.setdefault("glow", 0.18)
    return finish(cv, ctx, NIGHT, hit, **kw)


def fin_d(cv, ctx, hit=0.6, **kw):
    return finish(cv, ctx, DAY, hit, **kw)


def night_city(cv: Canvas, ctx: Ctx, horizon=30, scroll=0.0, moon=True, stars=0.02, layers=3,
               sky=(NIGHT_SKY, NIGHT_SKY2), lit=0.35):
    cv.clear(sky[1], PAPER)
    vgrad(cv, 0, horizon, sky[0], sky[1])
    if stars:
        S.stars(cv, ctx.t, 41, stars, PAPER, GREY)
        cv.ch[horizon:] = 0
    if moon:
        Wd.moon(cv, 128, 7, 4, crescent=0.55)
    shades = [hexc("#1c1f2c"), hexc("#14161f"), hexc("#0c0d13")]
    for i in range(layers):
        Wd.skyline(cv, horizon, 50 + i, 4 + i * 3, 10 + i * 5, shades[i], lit=lit * (0.6 + 0.3 * i),
                   win_on=mix(WARM, shades[i], 0.25 * (2 - i)), scroll=scroll * (0.3 + 0.35 * i), t=ctx.t,
                   wmin=6 + i * 2, wmax=12 + i * 3)


# ============================================================ VERSE 2

def v_sooty(cv: Canvas, ctx: Ctx) -> Post:
    """A sooty four-and-a-half-mat room.  Wide, cramped: laundry hanging from a
    line across the room, boxes stacked, the futon half folded, dust drifting
    in the moonlight beam; the camera creeps in."""
    pan = 6 * ctx.u
    room_night(cv, ctx, pan=pan, lamp=False)
    p = -pan
    # laundry line with shirts swaying
    Wd.powerline(cv, 0, 4, cv.W, 5, 3, mix(WALL_N, PAPER, 0.5))
    for i, x in enumerate((20, 46, 90, 112, 140)):
        sw = math.sin(ctx.t * 1.5 + i) * 0.8
        x = x + p * 1.4
        col = [hexc("#c9c4b6"), hexc("#7a8aa6"), hexc("#a65a5a"), hexc("#c9c4b6"), hexc("#5a7a5a")][i]
        fill_rect(cv, x - 4 + sw, 7, x + 4 + sw, 13, col, "|", mix(col, INK, 0.25))
        fill_rect(cv, x - 6 + sw, 7, x + 6 + sw, 8, col, "=", mix(col, INK, 0.25))
        cv.put(int(x), 6, "^", mix(WALL_N, PAPER, 0.6))
    # cardboard boxes
    for (x, y, w, h) in ((126, 30, 18, 8), (130, 23, 14, 7), (146, 33, 12, 6)):
        x += p * 1.2
        fill_rect(cv, x, y, x + w, y + h, hexc("#8a6a44"), "-", hexc("#a6865c"))
        cv.box(x, y, x + w, y + h, hexc("#5a4224"), "+-|")
        cv.line(x + w / 2, y, x + w / 2, y + 2, hexc("#c9b48a"), "|")
    # futon half folded on the floor
    sprite(cv, "futon", 70 + p * 1.5, 38, mix(hexc("#d8d2c4"), INK, 0.2))
    # dust in the moonbeam
    beam = (np.abs((cv.xx - (34 + p)) - (cv.yy - 2) * 0.9) < 9) & (cv.yy < 44) & (cv.yy > 20)
    cv.bg[beam] = mix(cv.bg[beam], PAPER, 0.06)
    rng = np.random.default_rng(6)
    n = 160
    xs = rng.uniform(0, cv.W, n)
    ys = (rng.uniform(0, 44, n) + ctx.lt * rng.uniform(0.5, 2, n)) % 44
    xs = xs + np.sin(ctx.t + np.arange(n)) * 1.5
    inb = beam[np.clip(ys.astype(int), 0, 45), np.clip(xs.astype(int), 0, 159)]
    cv.scatter(xs[inb], ys[inb], ".", fg=PAPER)
    cv.scatter(xs[~inb], ys[~inb], ",", fg=mix(WALL_N, PAPER, 0.25))
    return fin_n(cv, ctx, 0.4)


def v_ultrasound(cv: Canvas, ctx: Ctx) -> Post:
    """The ultrasound she brought in.  Low on the tatami: a small radio she
    carried home sweeps its dial; nobody hears a thing -- except the cat,
    whose ears snap up on every beat while the glasses on the shelf tremble."""
    t = ctx.t
    cv.clear(WALL_N, PAPER)
    fill_rect(cv, 0, 28, cv.W, 45, hexc("#3a3622"), "-", hexc("#4f4a30"))
    for y in (32, 37, 43):
        cv.line(0, y, cv.W, y, hexc("#3e3a24"), "=")
    for x in (40, 100, 150):
        cv.line(x, 28, x + 6, 45, hexc("#3e3a24"), "|")
    cv.line(0, 27, cv.W, 27, hexc("#2a2620"), "#", bold=True)
    # shelf with glasses
    fill_rect(cv, 92, 9, 156, 10, DESK, "=", mix(DESK, PAPER, 0.3))
    for i, x in enumerate(range(96, 152, 8)):
        jit = int(round(math.sin(t * 50 + i) * ctx.pulse(5)))
        cv.put(x + jit, 6, "|~|", mix(PAPER, NEON_C(), 0.4))
        cv.put(x + jit, 7, "| |", mix(PAPER, NEON_C(), 0.4))
        cv.put(x + jit, 8, "'-'", mix(PAPER, NEON_C(), 0.4))
    # the radio
    rx0, ry0 = 12, 14
    fill_rect(cv, rx0, ry0, rx0 + 46, ry0 + 15, hexc("#a8402a"), " ")
    cv.box(rx0, ry0, rx0 + 46, ry0 + 15, hexc("#5a1a10"), "+=|", bold=True)
    cv.line(rx0 + 8, ry0, rx0 + 30, ry0 - 9, GREY, "/")
    fill_rect(cv, rx0 + 3, ry0 + 3, rx0 + 20, ry0 + 12, hexc("#3a1a14"), ":", hexc("#7a3a2a"))
    fill_rect(cv, rx0 + 23, ry0 + 3, rx0 + 43, ry0 + 6, hexc("#f2e2b0"), " ")
    for k, fq in enumerate((20, 40, 60, 80, 100)):
        cv.put(rx0 + 24 + k * 4, ry0 + 4, str(fq)[0], INK)
    needle = rx0 + 24 + int(18 * (0.5 + 0.5 * math.sin(t * 1.7)))
    cv.line(needle, ry0 + 3, needle, ry0 + 6, RED, "|", bold=True)
    cv.put(rx0 + 25, ry0 + 9, "40 kHz", PAPER, bold=True)
    # inaudible waves (fine arcs) from the radio
    S.ripple_rings(cv, rx0 + 46, (ry0 + 7) * cv.aspect, ctx.lt, 50, 3.0,
                   mix(WALL_N, NEON_C(), 0.55), "arc", width=0.35, maxr=110)
    # the cat
    ears = ctx.pulse(6) > 0.4
    cx, cy = 118, 20
    fill_rect(cv, cx - 10, cy + 2, cx + 14, cy + 7, hexc("#222222"), " ")
    cat = [
        "  /\\_/\\  " if ears else "  __ __  ",
        " ( o.o ) " if ears else " ( -.- ) ",
        "  > ^ <  ",
        " /     \\~~",
        "(_______)",
    ]
    sprite(cv, cat, cx - 4, cy - 2, PAPER, bold=True, colors={"o": hexc("#ffd84a")})
    if ears:
        cv.put(cx - 7, cy - 4, "!", RED, bold=True)
    return fin_n(cv, ctx, 0.6)


def NEON_C():
    return Wd.NEON_C


def apartment(cv: Canvas, ctx: Ctx, x0, y0, floors, units, lit_mask, her=None, fg=None):
    """Front of a small walk-up apartment block: floors of doors and windows,
    open corridors, an outside staircase on the right."""
    fh, uw = 8, 16
    W = units * uw
    body = hexc("#2a2c36")
    fill_rect(cv, x0, y0, x0 + W, y0 + floors * fh, body)
    for f in range(floors):
        y = y0 + f * fh
        cv.line(x0, y + fh - 1, x0 + W + 18, y + fh - 1, hexc("#6b6e7a"), "=", bold=True)
        for c in range(0, int(W + 18), 3):
            cv.put(x0 + c, y + fh - 3, "|", hexc("#4a4d58"))
        for u in range(units):
            x = x0 + u * uw
            on = lit_mask(f, u)
            fill_rect(cv, x + 2, y + 1, x + 9, y + 4, WARM if on else hexc("#141620"),
                      "#" if on else " ", mix(WARM, PAPER, 0.4))
            cv.box(x + 11, y + 1, x + 14, y + 5, hexc("#6b6e7a"), "+-|")
            cv.put(x + 12, y + 3, ".", hexc("#c9c4b6"))
    # outside stairs
    sx = x0 + W + 2
    for f in range(floors):
        y = y0 + f * fh
        cv.line(sx, y + fh - 1, sx + 14, y + fh + 7, hexc("#8a8e9a"), "\\" if f % 2 == 0 else "\\")
    return sx


def v_escape(cv: Canvas, ctx: Ctx) -> Post:
    """She ran away from the everyday.  Wide, outside: her apartment block at
    night; her window goes dark on beat 1, then a small red light slips down
    the outside stairs and out past the street lamp."""
    t = ctx.t
    night_city(cv, ctx, horizon=40, moon=True, layers=2)
    b = beats_in(ctx)
    her_on = b < 1
    sx = apartment(cv, ctx, 20, 6, 4, 6,
                   lambda f, u: her_on if (f, u) == (1, 2) else Wd.h32(f, u, 7) % 3 == 0)
    fill_rect(cv, 0, 38, cv.W, 45, hexc("#24252c"), ".", hexc("#3a3b44"))
    cv.line(0, 38, cv.W, 38, hexc("#55565c"), "_")
    Wd.streetlamp(cv, 134, 38, 16, hexc("#8a8e9a"), on=True)
    # path of the red light: from her door down the stairs, along the street, off screen
    pts = [(20 + 2 * 16 + 12, 6 + 8 + 5), (sx, 6 + 8 + 7), (sx + 14, 6 + 16 + 7), (sx, 6 + 24 + 7),
           (sx + 14, 6 + 32 + 6), (170, 41)]
    k = max(0.0, b - 1) / max(1e-3, beats_in_total(ctx) - 1)
    k = min(1.0, k)
    seglen = [math.dist(a, c) for a, c in zip(pts, pts[1:])]
    d = k * sum(seglen)
    pos = pts[-1]
    for (a, c), L in zip(zip(pts, pts[1:]), seglen):
        if d <= L:
            pos = (a[0] + (c[0] - a[0]) * d / L, a[1] + (c[1] - a[1]) * d / L)
            break
        d -= L
    if b >= 1:
        cv.put(int(pos[0]), int(pos[1]), "@", RED, bold=True)
        cv.put(int(pos[0]) - 2, int(pos[1]), "..", REDDK)
    return fin_n(cv, ctx, 0.4)


def beats_in_total(ctx: Ctx) -> float:
    return ctx.grid.beat_pos(ctx.t1) - ctx.grid.beat_pos(ctx.t0)


def phone_chat(cv: Canvas, ctx: Ctx, msgs, x0=56, y0=1, w=48, h=44, typing=None, header="GROUP (5)",
               shake=0.0, bottom=None):
    """A phone held in the dark: a chat app whose bubbles scroll up."""
    jit = int(round(shake * math.sin(ctx.t * 50)))
    x0 += jit
    fill_rect(cv, x0 - 2, y0, x0 + w + 2, y0 + h, hexc("#111111"), " ")
    cv.box(x0 - 2, y0, x0 + w + 2, y0 + h, hexc("#5a5d68"), "+=|", bold=True)
    fill_rect(cv, x0, y0 + 2, x0 + w, y0 + h - 2, hexc("#e9edf2"), " ")
    fill_rect(cv, x0, y0 + 2, x0 + w, y0 + 4, hexc("#3a6ea6"), " ")
    cv.put(x0 + 2, y0 + 3, "<  " + header, PAPER, bold=True)
    y = y0 + h - 7 if bottom is None else bottom
    for (side, text, col) in reversed(msgs):
        bw = min(w - 8, len(text) + 4)
        bx = x0 + 2 if side == "L" else x0 + w - bw - 2
        if y < y0 + 5:
            break
        fill_rect(cv, bx, y - 1, bx + bw, y + 1, col, " ")
        cv.put(bx + 2, y, text, INK if col is not None else INK, bold=True)
        y -= 4
    iy = y0 + h - 4 if bottom is None else bottom + 3
    fill_rect(cv, x0, iy, x0 + w, iy + 2, hexc("#f7f7f7"), " ")
    cv.box(x0 + 1, iy, x0 + w - 1, iy + 2, GREY, "+-|")
    cv.put(x0 + 3, iy + 1, typing if typing is not None else "Aa", INK if typing else GREY, bold=True)
    return x0


def v_laugh(cv: Canvas, ctx: Ctx) -> Post:
    """You'll laugh at me.  Close-up: her phone in the dark street; the group
    chat floods with www, stickers and 'lol' faster than she can read."""
    night_city(cv, ctx, horizon=38, moon=False, layers=3)
    fill_rect(cv, 0, 38, cv.W, 45, hexc("#18191f"))
    n = 2 + int(beats_in(ctx) * 3)
    pool = ["www", "wwwwww", "lol", "LOL", "(^o^)", "草", "まじか www", "ww", "ちょw", "HAHAHA", "XD", "w"]
    cols = [hexc("#ffffff"), hexc("#bfe6a6"), hexc("#ffffff"), hexc("#f7d6e0")]
    msgs = [("L" if i % 3 else "R", pool[i % len(pool)], cols[i % len(cols)]) for i in range(n)]
    phone_chat(cv, ctx, msgs, typing="", shake=ctx.pulse(8))
    # glow of the screen on the wall around
    glow = (np.abs(cv.xx - 80) < 40) & (cv.yy > 0)
    cv.bg[glow & (cv.ch == 0)] = mix(cv.bg[glow & (cv.ch == 0)], hexc("#3a6ea6"), 0.12)
    cv.put(20, 42, f"{n:3d} new", RED, bold=True)
    return fin_n(cv, ctx, 0.8)


def tv_wall(cv: Canvas, ctx: Ctx, draw_screen, cols=4, rows=3):
    """An electronics-store window at night: a wall of TVs all showing the same
    broadcast, the street reflected faintly in the glass."""
    cv.clear(hexc("#0d0e13"), PAPER)
    fill_rect(cv, 0, 40, cv.W, 45, hexc("#202128"), ".", hexc("#33343c"))
    sw, sh = 34, 11
    gx, gy = 8, 2
    for r in range(rows):
        for c in range(cols):
            x0, y0 = gx + c * (sw + 3), gy + r * (sh + 2)
            fill_rect(cv, x0, y0, x0 + sw, y0 + sh, hexc("#2a2b30"))
            with Wd.clip(cv, x0 + 1, y0 + 1, x0 + sw - 1, y0 + sh - 1):
                draw_screen(x0 + 1, y0 + 1, x0 + sw - 1, y0 + sh - 1, r * cols + c)
            cv.box(x0, y0, x0 + sw, y0 + sh, hexc("#55565e"), "+-|")
    # window frame and reflection
    cv.box(2, 0, 157, 40, hexc("#777a86"), "+=|", bold=True)
    refl = (cv.xx + cv.yy * 2) % 37 < 2
    cv.fg[refl & (cv.ch != 0)] = mix(cv.fg[refl & (cv.ch != 0)], PAPER, 0.3)
    cv.put(6, 42, "SALE  4K / 8K   本日限り", REDBG, bold=True)


def v_wrong_truth(cv: Canvas, ctx: Ctx) -> Post:
    """Even mistaken truths.  The store window's wall of TVs runs the late news;
    the headline reads TRUE -- then a red CORRECTION banner wipes across every
    screen at once."""
    b = beats_in(ctx)
    wipe = min(1.0, max(0.0, (b - 1.2) * 1.5))

    def scr(x0, y0, x1, y1, i):
        fill_rect(cv, x0, y0, x1, y1, hexc("#1a3a6a"))
        fill_rect(cv, x0, y1 - 3, x1, y1, hexc("#e9edf2"))
        cv.put(x0 + 2, y1 - 2, "NEWS  ★ TRUE STORY", INK, bold=True)
        cv.put(x0 + 3, y0 + 1, "( o_o )", PAPER)
        cv.put(x0 + 2, y0 + 3, "[desk====]", hexc("#8aa6c8"))
        if wipe > 0:
            wx = x0 + (x1 - x0) * wipe
            fill_rect(cv, x0, y1 - 3, wx, y1, REDBG)
            if wipe > 0.6:
                cv.put(x0 + 2, y1 - 2, "訂正 CORRECTION", PAPER, bold=True)

    tv_wall(cv, ctx, scr)
    return fin_n(cv, ctx, 1.0)


def v_right_lie(cv: Canvas, ctx: Ctx) -> Post:
    """Even correct lies.  Same window, next segment: a commercial -- a family
    smiling too widely, '100% HAPPY ✓' -- the checkmarks ticking on every
    screen in turn."""
    b = beats_in(ctx)

    def scr(x0, y0, x1, y1, i):
        fill_rect(cv, x0, y0, x1, y1, hexc("#ffe08a"))
        cv.put(x0 + 2, y0 + 1, "(^_^) (^_^) (^o^)", INK, bold=True)
        cv.put(x0 + 2, y0 + 3, "100% HAPPY", REDBG, bold=True)
        on = i <= int(b * 3)
        cv.put(x0 + 2, y0 + 6, "[✓] TRUE" if on else "[ ] TRUE", hexc("#1f8a3a") if on else GREY, bold=True)
        cv.put(x0 + 14, y0 + 6, "*個人の感想です", hexc("#7a6a3a"))

    tv_wall(cv, ctx, scr)
    return fin_n(cv, ctx, 0.8)


def desk_top(cv: Canvas, ctx: Ctx, lamp=True):
    """Her desk, seen from above under the lamp."""
    cv.clear(DESK, mix(DESK, PAPER, 0.3))
    for y in range(0, 46, 3):
        cv.line(0, y, cv.W, y, mix(DESK, INK, 0.25), "-")
    if lamp:
        pool = np.hypot(cv.xx - 80, (cv.yy - 22) * 2.4) < 70
        cv.bg[pool] = mix(DESK, WARM_DIM, 0.45)


def v_cutout(cv: Canvas, ctx: Ctx) -> Post:
    """The correct answers she cut out.  Overhead on her desk: a newspaper
    quiz page; the scissors snip around one answer box per beat and the
    pieces slide into a scrapbook."""
    desk_top(cv, ctx)
    # newspaper
    fill_rect(cv, 8, 3, 96, 43, hexc("#e8e2d0"), " ")
    for y in range(5, 42, 2):
        cv.put(10, y, ("=" * 20 + "  " + "-" * 20 + " ") * 2, hexc("#b8b2a0"))
    cv.put(12, 4, "DAILY QUIZ   今日の正解", INK, bold=True)
    boxes = [(14, 9), (52, 9), (14, 21), (52, 21), (14, 33), (52, 33)]
    b = beats_in(ctx)
    ncut = int(b * 2)
    for i, (x, y) in enumerate(boxes):
        if i < ncut:
            fill_rect(cv, x, y, x + 30, y + 8, hexc("#3a2c20"), " ")
            continue
        fill_rect(cv, x, y, x + 30, y + 8, PAPER, " ")
        for d in range(0, 30, 2):
            cv.put(x + d, y, "-", GREY)
            cv.put(x + d, y + 8, "-", GREY)
        cv.put(x + 3, y + 3, f"Q{i + 1}. ANSWER", INK, bold=True)
        cv.put(x + 3, y + 5, "  = CORRECT", REDBG)
    # scissors on the current box
    if ncut < len(boxes):
        x, y = boxes[ncut]
        fr = (b * 2) % 1
        sx = x + 30 * fr
        sprite(cv, ["\\  /", " ><", "(_)(_)"], sx - 2, y - 1, GREY, bold=True)
    # scrapbook
    fill_rect(cv, 104, 6, 156, 42, hexc("#2f4a6a"), " ")
    cv.box(104, 6, 156, 42, hexc("#1a2a3a"), "+=|", bold=True)
    cv.put(110, 8, "SCRAPBOOK", PAPER, bold=True)
    for i in range(min(ncut, 6)):
        x, y = 108 + (i % 2) * 24, 12 + (i // 2) * 10
        fill_rect(cv, x, y, x + 20, y + 7, PAPER, " ")
        cv.put(x + 2, y + 3, f"Q{i + 1} ✓", REDBG, bold=True)
    return fin_n(cv, ctx, 0.5)


def v_everyday(cv: Canvas, ctx: Ctx) -> Post:
    """Checking them, every single day.  The same desk, the same pose -- but
    day and night flip on every beat, the calendar tears a page each time and
    the coffee rings pile up."""
    b = beats_in(ctx)
    k = int(b * 2)
    day = k % 2 == 0
    desk_top(cv, ctx, lamp=not day)
    if day:
        cv.bg[:46] = mix(cv.bg[:46], hexc("#f2e8d0"), 0.35)
    # coffee rings
    rng = np.random.default_rng(1)
    for i in range(min(k + 1, 30)):
        x, y = rng.uniform(10, 150), rng.uniform(4, 42)
        rr = Wd.disc(cv, x, y, 4) & ~Wd.disc(cv, x, y, 3.2)
        cv.ch[rr] = cv.ids("o")[0]
        cv.fg[rr] = hexc("#5a3a1a")
    # tear-off calendar
    fill_rect(cv, 60, 6, 100, 36, PAPER, " ")
    cv.box(60, 6, 100, 36, INK, "+=|", bold=True)
    fill_rect(cv, 60, 6, 100, 10, REDBG, " ")
    cv.put(70, 8, "OCTOBER", PAPER, bold=True)
    day_n = 7 + k
    bmp = cv.text_bitmap(f"{day_n % 31 + 1}", 18, True)
    cv.shape_field(bmp, int(80 - bmp.shape[1] / 2), 13, INK)
    fr = (b * 2) % 1
    if fr < 0.35:
        # the torn page flying off
        fill_rect(cv, 100 + fr * 120, 6 + fr * 30, 130 + fr * 120, 26 + fr * 30, PAPER, " ")
    sprite(cv, "mug", 118, 30, PAPER)
    cv.put(16, 40, "CHECK  ✓ ✓ ✓ ✓ ✓ ✓ ✓"[: 8 + min(k, 14)], REDBG, bold=True)
    sun = "☀" if day else "☾"
    cv.put(146, 3, sun, hexc("#ffcf3a") if day else PAPER, bold=True)
    return fin_d(cv, ctx, 0.5) if day else fin_n(cv, ctx, 0.5)


# ======================================================== PRE-CHORUS 1

def rooftop(cv: Canvas, ctx: Ctx, horizon=30, sky=None, lit=0.35, stars=0.02, moon=True):
    night_city(cv, ctx, horizon=horizon, moon=moon, stars=stars, sky=sky or (NIGHT_SKY, NIGHT_SKY2), lit=lit)
    fill_rect(cv, 0, 36, cv.W, 45, hexc("#3a3b42"), ".", hexc("#4a4b52"))
    # fence
    for x in range(0, cv.W, 4):
        cv.line(x, 28, x, 36, hexc("#6b6e7a"), "|")
    for y in (28, 32):
        cv.line(0, y, cv.W, y, hexc("#8a8e9a"), "=")
    # water tank and AC units
    fill_rect(cv, 6, 18, 26, 35, hexc("#5a5d68"), "|", hexc("#6b6e7a"))
    cv.box(6, 18, 26, 35, hexc("#8a8e9a"), "+-|")
    cv.put(9, 16, "/~~~~~~~~~~~~~\\", hexc("#8a8e9a"))
    for x in (120, 140):
        fill_rect(cv, x, 37, x + 14, 42, hexc("#8a8e9a"), " ")
        cv.put(x + 2, 39, "(@)  ::", INK)


def v_distant(cv: Canvas, ctx: Ctx) -> Post:
    """It has gone far away.  On the rooftop at night: along the elevated line
    the last train's lights shrink toward the vanishing point and are gone."""
    rooftop(cv, ctx)
    # elevated track running into the distance
    vx, vy = 92, 24
    for side in (-1, 1):
        cv.line(vx, vy, vx + side * 70 - 10, 36, hexc("#8a8e9a"), None)
    k = ease_out(ctx.u)
    tx = vx + (-80) * (1 - k)
    ty = vy + 12 * (1 - k)
    w = 30 * (1 - k) + 1
    if w > 1.5:
        fill_rect(cv, tx - w, ty - w * 0.25, tx + w * 0.2, ty + 0.5, hexc("#c9ced6"))
        for i in range(int(w / 3)):
            cv.put(int(tx - w + 2 + i * 3), int(ty - w * 0.12), "#", WARM)
    cv.put(int(tx + w * 0.2), int(ty), "*", RED, bold=True)
    return fin_n(cv, ctx, 0.3)


def v_dusk(cv: Canvas, ctx: Ctx) -> Post:
    """Waited for the dark, dark night.  The same rooftop, time-lapsed: the
    sun drops behind the towers, the sky darkens band by band and the windows
    switch on block by block."""
    u = ease(ctx.u)
    top = mix(hexc("#e0784a"), NIGHT_SKY, u)
    bot = mix(hexc("#f7c27a"), NIGHT_SKY2, u)
    sun_y = 14 + 22 * u
    cv.clear(bot, PAPER)
    vgrad(cv, 0, 30, top, bot)
    if u < 0.95:
        Wd.paint(cv, Wd.disc(cv, 60, sun_y, 9) & (cv.yy < 30), hexc("#ff6a3a"), "#", hexc("#ffb07a"))
    S.stars(cv, ctx.t, 8, 0.03 * u, PAPER, GREY)
    cv.ch[30:] = 0
    shades = [mix(hexc("#5a4a5a"), hexc("#1c1f2c"), u), mix(hexc("#3a2a3a"), hexc("#0c0d13"), u)]
    for i, sh in enumerate(shades):
        Wd.skyline(cv, 30, 60 + i, 5 + i * 4, 12 + i * 6, sh, lit=0.45 * u, t=ctx.t, wmin=7, wmax=14)
    fill_rect(cv, 0, 30, cv.W, 45, mix(hexc("#5a5d68"), hexc("#25262c"), u), ".", hexc("#4a4b52"))
    for x in range(0, cv.W, 4):
        cv.line(x, 28, x, 36, hexc("#6b6e7a"), "|")
    for y in (28, 32):
        cv.line(0, y, cv.W, y, hexc("#8a8e9a"), "=")
    hh = 17 + int(u * 6)
    cv.put(136, 40, f"{hh:02d}:{int(u * 59) % 60:02d}", PAPER, bold=True)
    return fin_n(cv, ctx, 0.3)


def v_nocolor(cv: Canvas, ctx: Ctx) -> Post:
    """Suddenly the colours were gone.  The neon shopping street below the
    roof: signs, billboards, a vending machine -- all draining to grey from
    left to right."""
    t = ctx.t
    cv.clear(hexc("#0b0b12"), PAPER)
    fill_rect(cv, 0, 38, cv.W, 45, hexc("#1a1a22"), ".", hexc("#2a2a33"))
    signs = [(4, 3, "カラオケ", Wd.NEON_M), (34, 8, "居酒屋", hexc("#ff8a3a")), (58, 2, "24H", Wd.NEON_G),
             (80, 6, "BAR", Wd.NEON_C), (100, 3, "パチンコ", hexc("#ffd84a")), (132, 9, "薬", Wd.NEON_M)]
    drain = ease(seg(ctx.u, 0.2, 0.9))
    for i, (x, y, s, col) in enumerate(signs):
        local = max(0.0, min(1.0, drain * 1.6 - (x / cv.W) * 0.6))
        g = float(np.mean(col))
        c = mix(col, np.array([g, g, g], np.float32) * 0.6, local)
        flick = (math.sin(t * 13 + i * 3) > -0.9)
        w = len(s) * 4 + 6
        fill_rect(cv, x, y, x + w, y + 7, mix(hexc("#111111"), c, 0.15))
        cv.box(x, y, x + w, y + 7, c if flick else mix(c, INK, 0.5), "+=|", bold=True)
        bmp = cv.text_bitmap(s, 4, True)
        cv.shape_field(bmp, int(x + w / 2 - bmp.shape[1] / 2), y + 2, c)
        # glow on the street
        gl = (np.abs(cv.xx - (x + w / 2)) < w * 0.7) & (cv.yy > 38)
        cv.bg[gl] = mix(cv.bg[gl], c, 0.25 * (1 - local))
    # buildings behind
    for x in range(0, cv.W, 26):
        cv.line(x, 18, x, 38, hexc("#2a2a33"), "|")
    sprite(cv, "vending", 140, 31, PAPER)
    Wd.walkers(cv, ctx.lt, 70, 8, 40, mix(PAPER, INK, 0.3), speed=6)
    p = fin_n(cv, ctx, 0.3, glow=0.35 * (1 - drain) + 0.1)
    return p


def v_stagger(cv: Canvas, ctx: Ctx) -> Post:
    """Staggering, on purpose.  Point of view walking along the rooftop's
    edge: the yellow line on the parapet, the drop to the street below, and
    the whole view swaying with each step."""
    t = ctx.t
    cv.clear(NIGHT_SKY, PAPER)
    # the street far below
    fill_rect(cv, 0, 0, cv.W, 45, hexc("#0e0f15"))
    for k in range(6):
        y = 6 + k * 6
        cv.line(0, y, cv.W, y + 2, hexc("#22242e"), "-")
    rng = np.random.default_rng(4)
    for i in range(30):
        x = (rng.uniform(0, 160) + t * rng.uniform(4, 9)) % 160
        y = rng.uniform(3, 30)
        cv.put(int(x), int(y), "=", WARM if i % 3 else RED)
    # the parapet in perspective (we look down along it)
    pts = [(60, 45), (100, 45), (84, 4), (78, 4)]
    paint(cv, poly(cv, pts), hexc("#6b6e7a"), ".", hexc("#8a8e9a"))
    for k in range(14):
        z = ((k / 14) + t * 0.5) % 1
        y = 4 + 41 * z ** 1.6
        hw = 2 + 18 * z ** 1.6
        cv.line(81 - hw * 0.25, y, 81 + hw * 0.25, y, hexc("#ffd84a"), "=", bold=True)
    # sway: roll the rows
    sway = math.sin(t * 3.3) * 4 + math.sin(t * 7.1) * 1.5
    for y in range(46):
        k = int(round(sway * (y - 23) / 23))
        if k:
            for a in (cv.ch, cv.fg, cv.bg):
                a[y] = np.roll(a[y], k, axis=0)
    return fin_n(cv, ctx, 0.5)


# ======================================================== PRE-CHORUS 2

def v_faraway(cv: Canvas, ctx: Ctx) -> Post:
    """Somewhere far away.  Night highway from the passenger seat: green
    direction signs sweep overhead (TOKYO / SEA / FAR AWAY →), the dashboard
    clock, the road lights streaming."""
    t = ctx.t
    cv.clear(NIGHT_SKY, PAPER)
    vgrad(cv, 0, 20, NIGHT_SKY, hexc("#24203a"))
    vx, vy = 80, 18
    paint(cv, poly(cv, [(79, vy), (81, vy), (190, 46), (-30, 46)]), hexc("#1c1c22"), ".", hexc("#2a2a33"))
    for k in range(12):
        z = ((k / 12) + t * 0.9) % 1
        zz = z ** 2.3
        y = vy + (46 - vy) * zz
        cv.line(80, y, 80, y + 0.4 + 3 * zz, PAPER, "|", bold=True)
        for side in (-1, 1):
            x = 80 + side * (6 + 110 * zz)
            cv.line(x, y - 2 - 10 * zz, x, y, hexc("#555555"), "|")
            cv.put(int(x), int(y - 2 - 10 * zz), "*", WARM)
    # overhead sign rushing toward us
    z = (ctx.u * 1.2) % 1
    zz = z ** 2.2
    w = 6 + 120 * zz
    h = 2 + 12 * zz
    y = vy - 2 - 16 * zz
    fill_rect(cv, 80 - w / 2, y - h, 80 + w / 2, y, hexc("#1f7a4a"), " ")
    cv.box(80 - w / 2, y - h, 80 + w / 2, y, PAPER, "+-|")
    if w > 40:
        bmp = cv.text_bitmap("遠いとこ  FAR AWAY →", max(3, int(h * 0.5)), True)
        cv.shape_field(bmp, int(80 - bmp.shape[1] / 2), int(y - h * 0.75), PAPER)
    # dashboard
    fill_rect(cv, 0, 38, cv.W, 45, hexc("#141418"), " ")
    cv.put(70, 41, f"02:{14 + int(ctx.lt):02d}  ♪ RADIO  ---", Wd.NEON_C, bold=True)
    return fin_n(cv, ctx, 0.4)


def v_sink(cv: Canvas, ctx: Ctx) -> Post:
    """Just want to sink, innocently.  Under the night sea off the sea wall:
    moonlight shafts, a jellyfish, bubbles rising -- and her phone sinking,
    still glowing, past a drowned bicycle."""
    t = ctx.t
    u = ctx.u
    cv.clear(hexc("#02070d"), PAPER)
    vgrad(cv, 0, 46, hexc("#0e2a44"), hexc("#02070d"))
    # surface at the top
    M.wave_line(cv, 1.5, 0.7, 14, t, 0.3, mix(PAPER, hexc("#0e2a44"), 0.3), 0, cv.W)
    for k in range(5):
        x = 20 + k * 32 + 4 * math.sin(t * 0.5 + k)
        shaft = (np.abs(cv.xx - x - cv.yy * 0.4) < 3 - cv.yy * 0.05) & (cv.yy < 40)
        cv.bg[shaft] = mix(cv.bg[shaft], hexc("#5a8ab0"), 0.18)
    M.bubbles(cv, t, 9, 60, mix(PAPER, hexc("#0e2a44"), 0.4))
    # jellyfish
    jx, jy = 124 + 4 * math.sin(t * 0.7), 14 - 2 * math.sin(t * 1.4)
    sprite(cv, ["  .-~~-.  ", " (  ..  ) ", "  )|||( ", "  ( | ) ", "   )|(  "], jx - 5, jy, hexc("#d6a6ff"))
    # seabed with the bicycle
    fill_rect(cv, 0, 41, cv.W, 45, hexc("#141008"), ".", hexc("#2a2010"))
    sprite(cv, ["  __o  ", " _`\\<,_", "(*)/ (*)"], 24, 37, hexc("#4a4a4a"))
    for x in range(4, 160, 11):
        h = 3 + (x * 7) % 5
        for k in range(h):
            cv.put(x + int(math.sin(t * 2 + x + k) * 0.8), 40 - k, ")" if k % 2 else "(", hexc("#2a5a3a"))
    # the phone sinking, glowing
    py = 4 + 32 * ease(u)
    px = 80 + 6 * math.sin(u * 6)
    glow = Wd.disc(cv, px + 3, py + 3, 9)
    cv.bg[glow] = mix(cv.bg[glow], hexc("#3a6ea6"), 0.35)
    fill_rect(cv, px, py, px + 6, py + 7, hexc("#cfe2f7"), " ")
    cv.box(px, py, px + 6, py + 7, INK, "+-|")
    cv.put(int(px) + 2, int(py) + 3, "w", INK)
    return fin_n(cv, ctx, 0.2, glow=0.3)


def v_noanswer(cv: Canvas, ctx: Ctx) -> Post:
    """But I don't know the answer.  An exam room after hours: rows of empty
    desks, the clock over the blackboard racing; on her sheet the pencil
    writes an answer, erases it, writes another -- every box ends up '?'."""
    t = ctx.t
    cv.clear(hexc("#3a4a3e"), PAPER)
    # blackboard
    fill_rect(cv, 10, 2, 110, 14, hexc("#1f3a2a"), " ")
    cv.box(10, 2, 110, 14, hexc("#7a6a4a"), "+=|", bold=True)
    cv.put(16, 5, "期末テスト  FINAL EXAM", PAPER, bold=True)
    cv.put(16, 8, "Q. 私は何処に行けば ?   (50点)", mix(PAPER, hexc("#1f3a2a"), 0.3))
    cv.put(16, 11, "残り時間  " + f"{max(0, 9 - int(ctx.lt * 3)):02d}:00", hexc("#ffd84a"))
    Wd.wall_clock(cv, 132, 7, 7, 10 + ctx.lt * 4, PAPER, GREY, RED)
    # desks in rows (perspective)
    fill_rect(cv, 0, 16, cv.W, 45, hexc("#8a7a5a"), "-", hexc("#9a8a6a"))
    for r, (y, w) in enumerate(((18, 14), (23, 18), (30, 24))):
        for c in range(6 if r < 2 else 5):
            x = 8 + c * (w + 8) + r * 3
            fill_rect(cv, x, y, x + w, y + 2, hexc("#c9a46a"), "=", hexc("#a6844a"))
            cv.line(x + 1, y + 3, x + 1, y + 5, hexc("#555555"), "|")
    # her answer sheet in front
    fill_rect(cv, 40, 33, 120, 45, PAPER, " ")
    cv.box(40, 33, 120, 45, GREY, "+-|")
    k = int(beats_in(ctx) * 2)
    attempts = ["A", "B", "C", "D", "?"]
    for i in range(4):
        y = 35 + i * 2 + (i // 2)
        cv.put(43, y, f"({i + 1})", INK)
        if i < k // 2:
            cv.put(50, y, "?", REDBG, bold=True)
        elif i == k // 2:
            a = attempts[k % len(attempts)]
            cv.put(50, y, a, INK, bold=True)
            if k % 2:
                cv.put(49, y, "---", REDBG)
    cv.put(96, 36, "____ 点", INK)
    sprite(cv, ["  /", " / ", "/  "], 54 + (k % 4) * 3, 33, hexc("#ffcf3a"))
    return fin_d(cv, ctx, 0.4)


def v_showroom(cv: Canvas, ctx: Ctx) -> Post:
    """Inside a pointlessly beautiful room.  A furniture-store model room:
    perfect sofa, a plant, a framed print, price tags on everything, a glint
    sweeping across; when the band stops, the lights cut out."""
    P = ctx.params
    cv.clear(hexc("#f4f1ea"), INK)
    fill_rect(cv, 0, 32, cv.W, 45, hexc("#e2dccf"), "-", hexc("#d2ccbf"))
    cv.line(0, 32, cv.W, 32, hexc("#b8b2a4"), "_")
    # framed print + shelves
    S.picture_frame(cv, 62, 4, 98, 18, INK, GREY, style="simple", depth=2)
    paint(cv, rect(cv, 67, 6, 93, 16), hexc("#e9dccb"), " ")
    paint(cv, Wd.disc(cv, 80, 11, 4), hexc("#e36a4a"), " ")
    for x in (20, 128):
        cv.line(x, 10, x + 22, 10, GREY, "=")
        cv.put(x + 3, 9, "[] () []", GREY)
    # sofa
    fill_rect(cv, 46, 24, 114, 31, hexc("#c9c4b6"), " ")
    fill_rect(cv, 44, 22, 50, 31, hexc("#b8b2a4"), " ")
    fill_rect(cv, 110, 22, 116, 31, hexc("#b8b2a4"), " ")
    cv.line(46, 27, 114, 27, hexc("#a6a094"), "-")
    for x in (56, 70, 90, 104):
        cv.put(x, 25, "(  )", hexc("#a6a094"))
    sprite(cv, "plant", 20, 25, hexc("#5a8a5a"))
    sprite(cv, "lamp", 128, 22, GREY)
    # price tags
    for (x, y, s) in ((50, 20, "¥198,000"), (24, 22, "¥4,980"), (130, 19, "¥12,900"), (84, 19, "¥29,800")):
        cv.put(x, y, "[" + s + "]", REDBG, bold=True)
    cv.put(4, 1, "MODEL ROOM  - please do not sit -", GREY)
    gx = (ctx.lt * 80) % 240 - 40
    for k in range(-3, 4):
        m = (np.abs(cv.xx - (gx + k) + cv.yy * 0.6) < 0.5) & (cv.yy < 32)
        cv.fg[m & (cv.ch != 0)] = PAPER
        cv.bg[m] = mix(cv.bg[m], PAPER, 0.6)
    p = fin_d(cv, ctx, 0.2, vignette=0.12)
    stop = P.get("stop", 1e9)
    if ctx.t >= stop:
        if ctx.feat("onset") > 0.8:
            from .shots import jp
            cv.bg[:] = INK
            cv.ch[:] = 0
            jp(cv, ctx, NIGHT)
        p.fade = 1 - 0.35 * seg(ctx.t, stop, ctx.t1)
    return p
