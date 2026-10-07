"""No-repeat pass (v7): fresh shots for lyric lines that come back.

The song repeats its chorus three times and 高い高い / さ、おいでよ five and
three times.  Earlier passes reused the same shot for the same words; here
every recurrence gets its own image, still tied to what the line says:

- 期待しちゃいけないよ   a balloon of 期待 inflates and pops / lines written out 'as punishment'
- 痛いくらいの才能       a level meter driven into the red, clipping
- スポットライトぶっ壊して  a lighting rig whose lamps blow out one by one, then all at once
- 高い高い…             lanterns of text released upward / an endless staircase / a chart
                         that keeps leaving the top of its own axis / a city falling away below
- 逃げ道も無いよ         every EXIT sign turns to point back inside
- ここはただの球面上     a flat world map that wraps: walk off the right edge, come back on the left
- 痛いくらいの感情       a thermal camera: 感情 heating to white
- 日常の顔は冷たいなあ   a wall of identical blank faces that all turn to look at us
- さ、おいでよ           a path of lights switching on toward the horizon at dawn
"""
from __future__ import annotations

import math

import numpy as np

from . import abstract as A
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, NIGHT, DAY, PAPER, mix
from .raster import Post
from .scenes import ease, ease_out, seg
from .scenes5 import DEEP, RED2, REDDK, BLUE, P, fin, btot
from .scenes6 import fin_paper, fin_red, YEL, CYAN
from .scenes7 import (glyph_field, polar, big_mask, full, fin_blue, GOLD, ICE, NAVY, LILAC,
                      ORANGE, PINK, GREEN, TEAL)
from .shots import finish, beats_in
from .timeline import Ctx

EXITG = hexc("#13a85a")
AMBER = hexc("#ffb040")


def _pad3(a):
    return np.pad(a, ((0, 8), (0, 0), (0, 0)))


def _pad2(a):
    return np.pad(a, ((0, 8), (0, 0)))


# ------------------------------------------------------------ 期待しちゃいけないよ

def y_pop(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect.  The word 期待 swells like a balloon, wobbling, bigger
    on every beat -- then pops, and its pieces fly off and fall."""
    cv.clear(NAVY, PAPER)
    b, n = beats_in(ctx), btot(ctx)
    pop = max(2.0, round(n * 0.62))
    if b < pop:
        k = ease(b / pop)
        rows = 8 + 26 * k + 1.2 * math.sin(ctx.t * 9) * k
        m = big_mask(cv, "期待", rows, 80 + 1.5 * math.sin(ctx.t * 3), 23)
        cv.bg[:P][m] = mix(NAVY, PINK, 0.25 + 0.3 * k)
        A.text_fill(cv, full(m), "期待期待", mix(PAPER, PINK, 0.3 * k), offset=int(ctx.t * 5))
        # outline
        mm = m.copy()
        edge = mm & ~(np.roll(mm, 1, 0) & np.roll(mm, -1, 0) & np.roll(mm, 1, 1) & np.roll(mm, -1, 1))
        cv.ch[:P][edge] = cv.ids("o")[0]
        cv.fg[:P][edge] = PAPER
        p = fin_blue(cv, ctx, 0.3)
        p.shake = (int(2 * k * ctx.pulse(6)), 0)
        return p
    after = (b - pop) * ctx.grid.ibi
    m = big_mask(cv, "期待", 34, 80, 23)
    ys, xs = np.nonzero(m)
    rng = np.random.default_rng(4)
    vx = (xs - 80) * rng.uniform(1.5, 3.5, len(xs))
    vy = (ys - 23) * rng.uniform(1.5, 3.5, len(xs)) * 1.6 - 10
    nx = xs + vx * after
    ny = ys + (vy * after + 70 * after * after) / cv.aspect
    ids = A.text_glyphs(cv, "期待パン", True)
    col = mix(PAPER, PINK, 0.4) * max(0.2, 1 - after * 0.9)
    cv.scatter(nx, ny, ids[np.arange(len(xs)) % len(ids)], fg=col)
    if after < 0.25:
        cv.put_center(22, "パン", PAPER, bold=True)
    p = fin_blue(cv, ctx, 1.4)
    p.flash = 0.3 * max(0.0, 1 - after * 6)
    return p


def y_lines(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect (last time).  A ruled notebook page filled with the
    same sentence written out as if for punishment -- 期待しない。 -- line
    after line, faster and faster; the last line slips into 期待したい and is
    struck through in red."""
    cv.clear(PAPER, INK)
    for y in range(2, P, 2):
        cv.line(0, y, 159, y, mix(PAPER, hexc("#9fb8d0"), 0.4), "_")
    cv.line(10, 0, 10, P - 1, mix(PAPER, RED2, 0.45), "|")
    b, n = beats_in(ctx), btot(ctx)
    total = 80
    written = total * min(1.0, (b / n) ** 1.6 * 1.05)
    nfull = int(written)
    for i in range(min(total, nfull + 1)):
        col_i, row = i // 20, i % 20
        x, y = 13 + col_i * 37 + (i * 7) % 3, 1 + row * 2
        last = i == total - 1
        s = "期待したい。" if last else "期待しない。"
        if i == nfull:
            s = s[: int(len(s) * (written - nfull))]
        ink = mix(INK, hexc("#1f3a8a"), 0.5 + 0.3 * math.sin(i))
        cv.put(x, y, s, RED2 if last else ink, bold=last)
        if last and written >= total - 0.05:
            cv.line(x - 1, y, x + 12, y, RED2, "-", bold=True)
    cv.put(2, 44, f"×{min(total, nfull):02d}", RED2, bold=True)
    return fin_paper(cv, ctx, 0.5)


# ------------------------------------------------------------ 痛いくらいの才能

def y_meter(cv: Canvas, ctx: Ctx) -> Post:
    """A talent that hurts (again).  Five level meters; the signal climbs on
    every beat past 0 dB into the red until it clips -- CLIP lights blaze and
    the bars spill out of the frame."""
    cv.clear(hexc("#060504"), AMBER)
    b, t = beats_in(ctx), ctx.t
    cv.put(4, 1, "才能  INPUT LEVEL", AMBER, bold=True)
    x0, x1 = 14, 150
    zero = x0 + int((x1 - x0) * 0.72)
    for k in range(5):
        y = 6 + k * 8
        lvl = 0.45 + 0.17 * b + 0.12 * ctx.pulse(5) + 0.05 * math.sin(t * 11 + k * 1.7)
        w = int((x1 - x0) * lvl)
        for x in range(x0, x0 + w, 2):
            if x >= 160:
                break
            c = GREEN if x < zero - 20 else (YEL if x < zero else RED2)
            for dy in range(4):
                cv.put(x, y + dy, "#", c, bold=x >= zero)
        cv.put(2, y + 1, f"CH{k + 1}", mix(AMBER, INK, 0.3))
        clip = x0 + w > zero
        cv.put(152, y + 1, "CLIP" if clip else "    ", PAPER if clip and int(t * 8) % 2 else RED2, bold=True)
    cv.line(zero, 4, zero, 44, PAPER, ":", bold=True)
    cv.put(zero - 1, 45 - 1, "0dB", PAPER)
    for x, lab in ((x0, "-60"), (x0 + 40, "-30"), (x0 + 70, "-12")):
        cv.put(x, 44, lab, mix(AMBER, INK, 0.5))
    p = fin(cv, ctx, 1.2, glow=0.5)
    over = max(0.0, 0.45 + 0.17 * b - 0.72)
    if over > 0:
        p.chroma = max(p.chroma, int(2 + 6 * over))
    return p


# ------------------------------------------------------- スポットライトぶっ壊して

def y_rig(cv: Canvas, ctx: Ctx) -> Post:
    """Smash the spotlight (last time).  A lighting rig of eight lamps over
    an empty stage; one blows out on every beat with a spray of sparks, and
    on the hit the rest burst together and glass rains down in the dark."""
    t, brk = ctx.t, ctx.params.get("break", ctx.t1 - 0.5)
    b = beats_in(ctx)
    cv.clear(hexc("#0c0614"), PAPER)
    xx, yy = cv.xx[:P], cv.yy[:P]
    cv.line(0, 3, 159, 3, mix(GREY, INK, 0.3), "=", bold=True)
    lamps = [12 + i * 19.5 for i in range(8)]
    order = [3, 6, 1, 4, 7, 0, 5, 2]
    broke = t >= brk
    dead_n = len(lamps) if broke else min(len(lamps), int(b))
    dead = set(order[:dead_n])
    for i, lx in enumerate(lamps):
        alive = i not in dead
        if alive:
            cone = (yy > 4) & (np.abs(xx - lx) < (yy - 4) * 0.42 + 1)
            lum = np.clip(1 - np.abs(xx - lx) / ((yy - 4) * 0.42 + 1.5), 0, 1) * (0.5 + 0.5 * (1 - yy / P))
            c = mix(LILAC, YEL, 0.5 if i % 2 else 0.2)
            cv.bg[:P][cone] = np.maximum(cv.bg[:P][cone], (c * lum[..., None] * 0.55)[cone])
            dust = cone & (A.vnoise(xx * 0.8 + i, yy * 0.8 - t * 3, 8) > 0.84)
            cv.ch[:P][dust] = cv.ids(".")[0]
            cv.fg[:P][dust] = c
            cv.put(lx - 1, 4, "[@]", PAPER, bold=True)
        else:
            cv.put(lx - 1, 4, "[ ]", GREY)
            when = order.index(i)
            tb = brk if broke and when >= int(min(len(lamps), b if not broke else 99)) else None
            # sparks for the most recent death
            age = (b - when) * ctx.grid.ibi if not broke else (t - brk)
            if 0 <= age < 0.6:
                rng = np.random.default_rng(i * 7)
                n = 40
                ang = rng.uniform(0.2, math.pi - 0.2, n)
                sp = rng.uniform(20, 60, n)
                cv.scatter(lx + np.cos(ang) * sp * age, 5 + (np.sin(ang) * sp * age + 40 * age * age) / cv.aspect,
                           "*", fg=mix(YEL, ORANGE, age))
    floor = (yy > 40)
    cv.bg[:P][floor] = np.maximum(cv.bg[:P][floor], mix(hexc("#0c0614"), LILAC, 0.08))
    if broke:
        after = t - brk
        rng = np.random.default_rng(3)
        n = 260
        gx = rng.uniform(0, 160, n)
        gy = 5 + (rng.uniform(0, 30, n) * after + 50 * after * after) / cv.aspect + rng.uniform(-2, 0, n)
        ch = np.where(rng.random(n) < 0.5, cv.ids("/")[0], cv.ids("\\")[0])
        cv.scatter(gx, gy, ch, fg=mix(PAPER, CYAN, 0.3) * max(0.2, 1 - after * 0.5))
    p = fin(cv, ctx, 0.9, glow=0.5)
    if broke:
        k = max(0.0, 1 - (t - brk) * 4)
        p.flash, p.chroma = 0.45 * k, int(6 * k)
        p.shake = (int(6 * k), int(3 * k))
    return p


# ------------------------------------------------------------ 高い高い (×4)

def y_lanterns(cv: Canvas, ctx: Ctx) -> Post:
    """'Up high -- how's that?'  The line's own characters are released from
    below like sky lanterns, a batch on every beat, swaying, shrinking and
    dimming as they climb into the violet night."""
    cv.clear(hexc("#0e0820"), PAPER)
    cv.bg[:P] = A.gradient([(0, hexc("#05030e")), (0.7, hexc("#2a1440")), (1, hexc("#6a2a50"))], cv.yy[:P] / P)
    t, b = ctx.t, beats_in(ctx)
    txt = "高い高いはどうだい"
    for batch in range(int(b) + 1):
        age = (b - batch) * ctx.grid.ibi
        rng = np.random.default_rng(60 + batch)
        for i in range(9):
            x = rng.uniform(8, 150) + 3 * math.sin(age * 2 + i)
            y = 48 - age * rng.uniform(22, 34)
            if y < -2:
                continue
            h = y / P
            ch = txt[(batch * 3 + i) % len(txt)]
            warm = mix(ORANGE, YEL, 0.3) * (0.35 + 0.65 * h)
            if h > 0.5:
                bm = cv.text_bitmap(ch, 5, True)
                halo = Wd.disc(cv, x + 4, y + 2, 6)[:P]
                cv.bg[:P][halo] = np.maximum(cv.bg[:P][halo], warm * 0.25)
                cv.shape_field(bm, int(x), int(y), warm)
            else:
                cv.put(x, y, ch, warm, bold=h > 0.3)
    rng = np.random.default_rng(2)
    cv.scatter(rng.uniform(0, 160, 80), rng.uniform(0, 20, 80), ".", fg=mix(PAPER, LILAC, 0.5) * 0.6)
    return fin(cv, ctx, 0.3, glow=0.6)


def y_stairs(cv: Canvas, ctx: Ctx) -> Post:
    """'How about up high?'  An endless staircase on paper, its risers
    printed with 高; it keeps sliding down-left under one small dot that
    climbs and climbs without ever arriving."""
    cv.clear(PAPER, INK)
    t, lt = ctx.t, ctx.lt
    sw, sh = 10, 2.3
    off = lt * 14
    xx, yy = cv.xx[:P], cv.yy[:P]
    step = np.floor((xx + off) / sw)
    prof = 44 - (step - off / sw) * sh       # the stair stays put; its steps slide down-left
    below = yy > prof
    j = _pad2((step * 3 + np.floor(yy / 2)).astype(int))
    glyph_field(cv, full(below), "高", j, mix(PAPER, INK, 0.75))
    cv.bg[:P][below] = mix(PAPER, INK, 0.12)
    edge = below & ~np.roll(below, 1, 0)
    cv.ch[:P][edge] = cv.ids("_")[0]
    cv.fg[:P][edge] = INK
    riser = below & (step != np.roll(step, 1, 1))
    cv.ch[:P][riser] = cv.ids("|")[0]
    cv.fg[:P][riser] = INK
    x = 80
    py = float(prof[0, x]) if 0 <= prof[0, x] < P else 23
    hop = abs(math.sin(ctx.beat * math.pi)) * 2.5
    Wd.paint(cv, full(Wd.disc(cv, x, py - 1.5 - hop, 1.4)[:P]), hexc("#2a4aa0"), "@", PAPER)
    cv.put(4, 2, f"STEP {int(off / sw) + 1:04d}", hexc("#2a4aa0"), bold=True)
    return fin_paper(cv, ctx, 0.6)


def y_chart(cv: Canvas, ctx: Ctx) -> Post:
    """'Up high -- how's that?'  A chart line labelled 高い keeps shooting out
    of the top of its own axis; on every beat the axis rescales ×10 to catch
    it, and it shoots out again."""
    cv.clear(hexc("#04081a"), CYAN)
    b = beats_in(ctx)
    bi = int(math.floor(b + 1e-6))
    for gy in range(4, 42, 6):
        cv.line(12, gy, 156, gy, hexc("#12204a"), "-")
    for gx in range(12, 157, 12):
        cv.line(gx, 3, gx, 41, hexc("#12204a"), ":")
    cv.line(12, 41, 156, 41, mix(CYAN, INK, 0.4), "=")
    cv.line(12, 3, 12, 41, mix(CYAN, INK, 0.4), "|")
    scale = 10.0 ** bi
    ph = b - bi
    zoom = ease_out(min(1.0, ph * 3))
    top = scale * (1 + 9 * (1 - zoom))  # just rescaled: line looks small, then grows out again
    xs = np.linspace(0, 1, 140)
    head = min(1.0, 0.25 + 0.75 * ctx.u)
    vals = np.exp(xs * head * 9.5 * (1 + 0.25 * bi)) - 1
    vals = vals / (np.exp(head * 9.5 * (1 + 0.25 * bi)) - 1) * scale * (1 + 9 * ease(ph)) * 0.95
    vis = xs <= head
    px = 12 + xs * 144
    py = 41 - 38 * vals / top
    for i in range(1, len(xs)):
        if not vis[i]:
            break
        y0, y1 = py[i - 1], py[i]
        if y1 < 0 and y0 < 0:
            continue
        cv.line(px[i - 1], max(-1, y0), px[i], max(-1, y1), CYAN, "#" if i % 2 else "*", bold=True)
    hi = int(np.argmax(np.where(vis, px, 0)))
    hy = py[hi]
    if hy < 2:
        cv.put(px[hi] - 4, 1, "↑ 高い", YEL, bold=True)
    else:
        cv.put(px[hi] + 1, hy - 1, "高い", YEL, bold=True)
    for k in range(7):
        v = top * (6 - k) / 6
        cv.put(1, 4 + k * 6 - 0, f"{v:8.0f}"[-9:] if v < 1e8 else f"{v:.0e}", mix(CYAN, INK, 0.45))
    cv.put(120, 44, f"SCALE ×10^{bi}", YEL, bold=True)
    return fin(cv, ctx, 0.7, glow=0.4)


def y_citydrop(cv: Canvas, ctx: Ctx) -> Post:
    """'Up high -- how's that?' (last time).  Looking straight down as we
    rise: a night city of text blocks and lit windows shrinks away beneath
    us, streets to threads, the altitude counting up."""
    cv.clear(hexc("#05060c"), PAPER)
    lt = ctx.lt
    scale = math.exp(lt * 0.9)          # world units per cell grows = we rise
    xx, yy = cv.xx[:P], cv.yy[:P]
    wx = (xx - 80) * scale * 0.5
    wy = (yy - 23) * scale * 0.5 * cv.aspect
    street = (np.abs(((wx + 6) % 12) - 6) < 0.9) | (np.abs(((wy + 5) % 10) - 5) < 0.9)
    big = (np.abs(((wx + 30) % 60) - 30) < 2.2) | (np.abs(((wy + 25) % 50) - 25) < 2.2)
    win = A.vnoise(wx * 0.9, wy * 0.9, 3) > 0.64
    blk = ~street
    roof = A.vnoise(np.floor(wx / 12) * 3.1, np.floor(wy / 10) * 2.7, 9)
    cv.bg[:P][blk] = (hexc("#0e1220") + hexc("#20283a") * roof[..., None])[blk]
    tex = blk & (A.vnoise(wx * 0.4, wy * 0.4, 5) > 0.45)
    cv.ch[:P][tex] = cv.ids("#")[0]
    cv.fg[:P][tex] = (hexc("#2a3450") * (0.6 + roof[..., None]))[tex]
    cv.ch[:P][blk & win] = cv.ids(".")[0]
    cv.fg[:P][blk & win] = mix(YEL, ORANGE, 0.4) * 0.9
    cv.ch[:P][street] = cv.ids(":")[0]
    cv.fg[:P][street] = mix(hexc("#3a4a6a"), PAPER, 0.2)
    cv.ch[:P][big] = cv.ids("=")[0]
    cv.fg[:P][big] = mix(ORANGE, PAPER, 0.4)
    haze = np.clip(scale / 25, 0, 0.8)
    cv.fg[:P] = mix(cv.fg[:P], hexc("#2a3a6a"), haze * 0.6)
    cv.put(4, 2, f"ALT {int(scale * 40):6d} m", PAPER, bold=True)
    cv.put(76, 22, "[+]", RED2, bold=True)
    return fin(cv, ctx, 0.5, glow=0.45)


# ------------------------------------------------------------ 逃げ道も無いよ

def y_exits(cv: Canvas, ctx: Ctx) -> Post:
    """No way out (last time).  A wall of green EXIT signs; their arrows
    point every which way -- then on the beat they all swing round to point
    back at the middle, and the middle says 無い."""
    cv.clear(hexc("#020604"), PAPER)
    b = beats_in(ctx)
    turn = ease(min(1.0, max(0.0, b - 1.0) * 2))
    rng = np.random.default_rng(12)
    arrows = "→↓←↑"
    for r in range(3):
        for c in range(6):
            x0, y0 = 3 + c * 26, 2 + r * 14
            cx, cy = x0 + 11, y0 + 5
            if r == 1 and c in (2, 3):
                continue
            Wd.fill_rect(cv, x0, y0, x0 + 22, y0 + 10, EXITG, " ")
            cv.box(x0, y0, x0 + 22, y0 + 10, mix(EXITG, PAPER, 0.5), "+-|")
            a_rand = rng.uniform(0, 2 * math.pi)
            a_in = math.atan2(-(23 - cy) * cv.aspect, 80 - cx)
            a_in = math.atan2((23 - cy), (80 - cx) / cv.aspect)
            da = ((a_in - a_rand + math.pi) % (2 * math.pi)) - math.pi
            a = a_rand + da * turn
            ax_, ay_ = x0 + 6.5, y0 + 5
            ux, uy = math.cos(a) * 4.5, math.sin(a) * 4.5 / cv.aspect * 1.4
            cv.line(ax_ - ux, ay_ - uy, ax_ + ux, ay_ + uy, PAPER, "#", bold=True)
            for s_ in (-1, 1):
                ha = a + math.pi + s_ * 0.6
                cv.line(ax_ + ux, ay_ + uy, ax_ + ux + math.cos(ha) * 3, ay_ + uy + math.sin(ha) * 3 / cv.aspect * 1.4,
                        PAPER, "#", bold=True)
            cv.put(x0 + 13, y0 + 4, "非常口", PAPER, bold=True)
            cv.put(x0 + 14, y0 + 6, "EXIT", PAPER)
    # the middle
    cv.box(55, 16, 105, 29, mix(RED2, INK, 0.2), "#=|", bold=True)
    if b >= 1.5:
        bm = cv.text_bitmap("無い", 9, True)
        cv.shape_field(bm, int(80 - bm.shape[1] / 2), 18, RED2)
    else:
        cv.put_center(22, "出口", mix(PAPER, INK, 0.4), bold=True)
    return fin(cv, ctx, 0.8, glow=0.45)


# ------------------------------------------------------------ ここはただの球面上

def y_wrap(cv: Canvas, ctx: Ctx) -> Post:
    """It's only the surface of a sphere (last time).  A flat world map of
    text; a red walker heads east, walks off the right edge -- and comes
    straight back in on the left.  The edges are the same place."""
    cv.clear(hexc("#e9e0c8"), INK)
    xx, yy = cv.xx[:P], cv.yy[:P]
    th = xx / 160 * 2 * math.pi
    w = xx / 160                         # blend two noise copies so x=0 and x=160 match
    land = A.fbm(xx * 0.05, yy * 0.11, 7) * (1 - w) + A.fbm((xx - 160) * 0.05, yy * 0.11, 7) * w
    land = (land > 0.53) & (yy > 2) & (yy < 43)
    ocean = ~land
    j = _pad2((xx // 2 + yy * 3).astype(int))
    glyph_field(cv, full(land), "日常", j, mix(hexc("#e9e0c8"), hexc("#5a4a2a"), 0.8))
    cv.bg[:P][land] = hexc("#d8c8a0")
    cv.ch[:P][ocean & ((xx.astype(int) + yy.astype(int)) % 4 == 0)] = cv.ids("~")[0]
    cv.fg[:P][ocean] = mix(hexc("#e9e0c8"), hexc("#3a6a8a"), 0.6)
    for gx in range(0, 160, 20):
        cv.line(gx, 0, gx, P - 1, mix(hexc("#e9e0c8"), INK, 0.3), ":")
    for gy in (6, 15, 23, 31, 40):
        cv.line(0, gy, 159, gy, mix(hexc("#e9e0c8"), INK, 0.3), "-" if gy != 23 else "=")
    cv.put(1, 1, "180°W", INK, bold=True)
    cv.put(153, 1, "180°E", INK, bold=True)
    sp = 160 / max(0.8, (ctx.t1 - ctx.t0) * 0.55)
    head = 100 + ctx.lt * sp
    for k in range(120):
        x = (head - k * 0.9) % 160
        y = 26 + 3 * math.sin((head - k * 0.9) * 0.05)
        cv.put(x, y, "#" if k == 0 else ".", RED2 if k < 60 else mix(RED2, hexc("#e9e0c8"), 0.6), bold=k == 0)
    hx = head % 160
    hy = 26 + 3 * math.sin(head * 0.05) - 2
    Wd.fill_rect(cv, hx - 3, hy - 1, hx + 2, hy + 1, RED2, " ")
    cv.put(hx - 2, hy, "私", PAPER, bold=True)
    for e in (0, 159):
        cv.line(e, 0, e, P - 1, RED2, "|", bold=True)
    cv.put_center(43, "← ここ = ここ →", RED2, bold=True)
    return fin_paper(cv, ctx, 0.5)


# ------------------------------------------------------------ 痛いくらいの感情

def y_thermal(cv: Canvas, ctx: Ctx) -> Post:
    """An emotion that hurts (last time).  A thermal camera: heat blooms in
    blobs and the word 感情 at the centre goes from red to white-hot on each
    beat; the temperature readout climbs."""
    cv.clear(INK, PAPER)
    X, Y = A.coords(cv)
    t, b = ctx.t, beats_in(ctx)
    dx, dy, r, a = polar(cv)
    heat = 0.35 * A.warp(X * 0.03, Y * 0.04, t * 1.5, seed=77, k=2.5)
    heat += 0.55 * np.exp(-(r / (30 + 6 * b)) ** 2) * (0.5 + 0.15 * b + 0.25 * ctx.pulse(4))
    m = big_mask(cv, "感情", 22, 80, 22)
    heat = np.where(m, heat + 0.35 + 0.12 * b, heat)
    stops = [(0, hexc("#05010a")), (0.25, hexc("#3a0a6a")), (0.45, hexc("#c4105a")),
             (0.65, hexc("#ff6a1a")), (0.85, hexc("#ffd84a")), (1, hexc("#ffffff"))]
    A.shade(cv, np.clip(heat, 0, 1), " .:-=+*#%@", stops, bg_scale=0.55)
    cv.line(70, 22, 90, 22, PAPER, "-")
    cv.line(80, 17, 80, 27, PAPER, "|")
    temp = 36.5 + 2.2 * b + 0.4 * ctx.pulse(5)
    cv.put(4, 2, f"{temp:4.1f}℃", PAPER, bold=True)
    cv.put(4, 4, "MAX", GREY)
    for i in range(30):
        cv.put(154, 4 + i, "#", A.gradient(stops, np.array(1 - i / 29)))
    return fin(cv, ctx, 0.8, glow=0.5)


# ------------------------------------------------------------ 日常の顔は冷たいなあ

def y_faces(cv: Canvas, ctx: Ctx) -> Post:
    """The everyday's face is cold (last time).  A wall of hundreds of the
    same blank face, (・_・), in cold grey, each glancing its own way --
    then on the beat every one of them turns to look at us at once."""
    bg = hexc("#1a2028")
    cv.clear(bg, ICE)
    b = beats_in(ctx)
    snap = b >= 1.0
    rng = np.random.default_rng(21)
    looks = rng.integers(0, 3, 400)
    variants = ["(・_・ )", "( ・_・)", "(・_・)"]
    i = 0
    for r in range(15):
        for c in range(17):
            x = 2 + c * 9 + (4 if r % 2 else 0)
            y = 1 + r * 3
            v = 2 if snap else int(looks[i])
            if not snap and int(ctx.t * 3 + i) % 7 == 0:
                v = (v + 1) % 2
            d = math.hypot(x - 80, (y - 22) * 1.6)
            col = mix(bg, ICE, 0.7 + 0.3 * (1 - min(1.0, d / 90)))
            cv.put(x, y, variants[v], col, bold=True)
            i += 1
    p = fin_blue(cv, ctx, 0.9 if snap else 0.2)
    if snap and b < 1.15:
        p.shake = (2, 1)
    return p


# ------------------------------------------------------------ さ、おいでよ

def y_path(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on' (morning).  A dark field at dawn; a path of small lights
    switches on from our feet toward the horizon, one after another, and at
    the far end the word おいで glows."""
    cv.clear(hexc("#0a0a18"), PAPER)
    xx, yy = cv.xx[:P], cv.yy[:P]
    hz = 15
    sky = yy < hz
    sk = A.gradient([(0, hexc("#1a1440")), (0.6, hexc("#a05a8a")), (1, hexc("#ffc8a0"))], yy / hz)
    cv.bg[:P][sky] = sk[sky]
    bands = sky & (yy.astype(int) % 3 == 1)
    cv.ch[:P][bands] = cv.ids("-")[0]
    cv.fg[:P][bands] = (sk * 1.1).clip(0, 1)[bands]
    ground = ~sky
    d = np.maximum(yy - hz + 0.5, 0.3)
    cv.bg[:P][ground] = (hexc("#0a0a18") + hexc("#2a1a30") * (1 / (1 + (14 / d)[..., None] * 0.1)))[ground]
    grass = ground & (A.vnoise(xx * 0.5, yy * 1.3, 4) > 0.62)
    cv.ch[:P][grass] = cv.ids("'")[0]
    cv.fg[:P][grass] = hexc("#3a3050")
    on = ease(seg(ctx.u, 0.05, 0.85))
    n = 22
    for k in range(n):
        z = 1 + k * 1.2
        y = hz + 30 / z
        x = 80 + 9 * math.sin(k * 0.5) / z * 4
        lit = k / n < on
        c = mix(YEL, PAPER, 0.4) if lit else hexc("#4a4060")
        spread = 26 / z
        for sx in (-spread, spread):
            if lit:
                halo = Wd.disc(cv, x + sx, y, max(1.0, 5 / z))[:P]
                cv.bg[:P][halo] = np.maximum(cv.bg[:P][halo], mix(hexc("#0a0a18"), YEL, 0.35))
            cv.put(x + sx, y, "@" if z < 4 else "o", c, bold=lit)
    if on > 0.9:
        cv.put_center(hz - 2, "おいで", mix(hexc("#ffc8a0"), PAPER, 0.5), bold=True)
    cv.line(0, hz, 159, hz, mix(hexc("#ffc8a0"), PAPER, 0.3), "_")
    return fin(cv, ctx, 0.3, glow=0.5)
