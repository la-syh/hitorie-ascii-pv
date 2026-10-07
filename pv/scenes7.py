"""Whole-video pass (v6): the abstract / typographic grammar of the verses,
carried through the pre-choruses, choruses, solo, B2 and the finale.

Every shot is still tied to the literal meaning of its line -- receding,
night falling, colour draining, staggering, escaping, being lifted up,
walking around a sphere that has no exit, failing again, a face that is
cold -- but drawn as fields, particles, typography and quiz cards rather
than as depicted objects.  Neighbouring lines alternate palettes (ink,
paper, red, blue, full colour, pastel) so no two consecutive shots look
alike.  No flag-like motifs: no lone red disc on a white ground.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from . import abstract as A
from . import quiz as Q
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, NIGHT, DAY, PAPER, mix
from .raster import Post
from .scenes import ease, ease_out, seg
from .scenes5 import DEEP, RED2, REDDK, BLUE, ABYSS, P, fin, line_text, _word_of, btot
from .scenes6 import fin_paper, fin_red, quiz_post, CYAN, YEL, REDBG
from .shots import finish, beats_in, jp
from .timeline import Ctx

GOLD = hexc("#d8b04a")
GOLDDK = hexc("#5a4214")
ICE = hexc("#bfe6ff")
NAVY = hexc("#0a1030")
LILAC = hexc("#cdbfe8")
MINT = hexc("#cfeee0")
PEACH = hexc("#f6d6c4")
TEAL = hexc("#1f8a8a")
ORANGE = hexc("#ff8a3a")
PINK = hexc("#ff3b8a")
GREEN = hexc("#2fbf5a")
PHOS = hexc("#7dff9a")


# ------------------------------------------------------------------ helpers

def glyph_field(cv: Canvas, mask: np.ndarray, text: str, j: np.ndarray, fg, bold=False):
    """Put text characters on ``mask`` cells; the character index per cell
    comes from the integer field ``j`` (sampled on even columns so wide
    characters keep both halves together)."""
    pairs = []
    for c in text:
        g = cv.atlas.get(c, bold)
        pairs.append(g if isinstance(g, tuple) else (g, g))
    pairs = np.asarray(pairs)
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return
    xe = xs - (xs % 2)
    k = j[ys, xe].astype(np.int64) % len(pairs)
    cv.ch[ys, xs] = pairs[k, xs % 2]
    fgv = np.asarray(fg, np.float32)
    cv.fg[ys, xs] = fgv if fgv.ndim == 1 else fgv[ys, xs]


def polar(cv, cx=80.0, cy=23.0):
    X, Y = A.coords(cv)
    dx, dy = X - cx, Y - cy * cv.aspect
    return dx, dy, np.hypot(dx, dy), np.arctan2(dy, dx)


def big_mask(cv, s, rows, cx=80, cy=23, thr=0.45):
    bmp = cv.text_bitmap(s, max(3, int(rows)), True)
    h, w = bmp.shape
    ox, oy = int(round(cx - w / 2)), int(round(cy - h / 2))
    m = np.zeros((P, cv.W), bool)
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(cv.W, ox + w), min(P, oy + h)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = bmp[y0 - oy:y1 - oy, x0 - ox:x1 - ox] > thr
    return m


def full(m):
    """Pad a picture-area mask to the full canvas height."""
    out = np.zeros((m.shape[0] + 8, m.shape[1]), bool)
    out[:m.shape[0]] = m
    return out


def fin_blue(cv, ctx, hit=0.6, **kw):
    kw.setdefault("glow", 0.4)
    return finish(cv, ctx, NIGHT, hit, **kw)


# =========================================================== PRE-CHORUS 1

def z_recede(cv: Canvas, ctx: Ctx) -> Post:
    """Ah, that has gone far away.  Two planes of text -- floor and ceiling --
    stream away from us toward a vanishing point, fogging out; the line
    itself shrinks into the horizon and is gone."""
    cv.clear(DEEP, PAPER)
    t, u = ctx.t, ctx.u
    yy, xx = cv.yy[:P], cv.xx[:P]
    d = np.abs(yy - 22.5) + 0.6
    z = 40.0 / d
    speed = 6 + 18 * ease(u)
    tv = z - ctx.lt * speed
    tu = (xx - 80) / d * 1.2
    j = (np.floor(tu / 2) * 7 + np.floor(tv) * 3).astype(int)
    fog = np.clip(1 - z / 55, 0, 1) ** 1.6 * (np.floor(tv) % 2 == 0)
    stripe = (np.floor(tv) % 9 == 0)
    col = np.where(stripe[..., None], mix(DEEP, RED2, 1.0) * fog[..., None],
                   PAPER * fog[..., None] + DEEP * (1 - fog[..., None]))
    glyph_field(cv, full(fog > 0.06), "それは遠くなった", np.pad(j, ((0, 8), (0, 0))),
                np.pad(col, ((0, 8), (0, 0), (0, 0))))
    rows = 16 * (1 - ease(u)) ** 1.6
    if rows >= 3:
        m = big_mask(cv, "遠", rows, 80, 22.5)
        Wd.paint(cv, full(m), DEEP, " ")
        cv.ch[:P][m] = cv.ids("#", True)[0]
        cv.fg[:P][m] = PAPER
    else:
        cv.put(79, 22, "・", PAPER)
    return fin(cv, ctx, 0.4, glow=0.45)


def z_dark(cv: Canvas, ctx: Ctx) -> Post:
    """Waited for a dark, dark night.  A dusk-coloured field of 夜 is closed in
    by a wall of 暗 glyphs, one step on every beat, until only a sliver of
    evening is left in the middle."""
    cv.clear(NAVY, PAPER)
    dx, dy, r, a = polar(cv)
    b = beats_in(ctx)
    n = btot(ctx)
    k = (math.floor(b) + ease(min(1.0, (b % 1) * 3))) / n
    R = 95 * (1 - k) + 4
    wob = R + 2.5 * np.sin(a * 7 + ctx.t * 2)
    inside = r < wob
    jj = (cv.xx[:P] // 2 + cv.yy[:P] * 3).astype(int)
    jfull = np.pad(jj, ((0, 8), (0, 0)))
    out_col = mix(NAVY, hexc("#2a3a7a"), 0.7)
    glyph_field(cv, full(~inside), "暗", jfull, out_col, True)
    dusk = A.gradient([(0, hexc("#ff9a5a")), (0.5, hexc("#c4508a")), (1, hexc("#3a2a7a"))],
                      cv.yy[:P] / P)
    glyph_field(cv, full(inside), "夜を待った", jfull, np.pad(dusk, ((0, 8), (0, 0), (0, 0))))
    cv.bg[:P][inside] = dusk[inside] * 0.25
    edge = np.abs(r - wob) < 1.2
    cv.ch[:P][edge] = cv.ids("・")[0]
    cv.fg[:P][edge] = hexc("#ffd0a0")
    return fin_blue(cv, ctx, 0.9)


def z_drain(cv: Canvas, ctx: Ctx) -> Post:
    """Suddenly, the colour was gone.  A full-colour liquid field -- then, on
    'ふと', a grey disc opens in the middle and eats every hue outward; the
    glyphs turn from 色 to 無."""
    cv.clear(DEEP, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    f = A.warp(X * 0.03, Y * 0.03, t * 1.2, seed=41, k=3.0)
    hue = (f * 2.2 + t * 0.15) % 1
    col = A.gradient([(0, PINK), (0.25, YEL), (0.5, CYAN), (0.75, hexc("#8a5aff")), (1, PINK)], hue)
    lum = np.clip((f - 0.25) * 1.8, 0.15, 1)
    col = col * lum[..., None]
    _, _, r, a = polar(cv)
    R = 180 * ease(seg(ctx.u, 0.22, 1.0)) ** 1.3
    edge = R + 6 * np.sin(a * 5 + t * 3)
    grey = r < edge
    g = (col.mean(-1, keepdims=True) * 0.9 + 0.05) * np.ones(3)
    col = np.where(grey[..., None], g, col)
    j = np.pad((cv.xx[:P] // 2 + cv.yy[:P] * 5).astype(int), ((0, 8), (0, 0)))
    glyph_field(cv, full(~grey & (lum > 0.2)), "色色彩", j, np.pad(col, ((0, 8), (0, 0), (0, 0))))
    glyph_field(cv, full(grey & (lum > 0.2)), "無", j, np.pad(col, ((0, 8), (0, 0), (0, 0))))
    cv.bg[:P] = col * 0.22
    rim = np.abs(r - edge) < 1.0
    cv.ch[:P][rim] = cv.ids("*")[0]
    cv.fg[:P][rim] = PAPER
    return fin(cv, ctx, 0.5, glow=0.3)


def z_stagger(cv: Canvas, ctx: Ctx) -> Post:
    """Staggering, on purpose.  Paper; the word フラつく printed huge, every
    row of it sliding out of true; the ruled lines tilt like a deck; a red
    track of footsteps wavers across the bottom."""
    cv.clear(PAPER, INK)
    t, b = ctx.t, beats_in(ctx)
    tilt = 0.09 * math.sin(t * 2.4) + 0.04 * math.sin(t * 5.1)
    for y0 in range(3, P, 4):
        xs = np.arange(160)
        cv.scatter(xs, y0 + (xs - 80) * tilt, "-", fg=mix(PAPER, hexc("#7fa0c0"), 0.5))
    amp = 2 + 5 * ease(min(1.0, b / btot(ctx)))
    m = big_mask(cv, "フラつく", 24, 80, 20)
    out = np.zeros_like(m)
    for y in range(P):
        sh = int(round(amp * math.sin(y * 0.45 + t * 5) + (y - 20) * tilt * 3))
        out[y] = np.roll(m[y], sh)
    cv.bg[:P][out] = INK
    A.text_fill(cv, full(out), "わざわざ", PAPER, offset=int(t * 4))
    n = int(40 * min(1.0, ctx.u * 1.3))
    for i in range(n):
        x = 6 + i * 3.8
        y = 41 + 2.2 * math.sin(i * 0.9) + 1.2 * math.sin(i * 2.3 + 1)
        cv.put(x, y, "・" if i % 2 else "'", RED2, bold=True)
    return fin_paper(cv, ctx, 0.9)


def z_far(cv: Canvas, ctx: Ctx) -> Post:
    """Now -- go somewhere far.  A perspective floor of light rushes toward
    us under a drifting sky of 遠; the horizon glows and pulls."""
    pal = ctx.params.get("pal", "violet")
    c_mid, c_hi, c_line = ((hexc("#3a1a6a"), PINK, hexc("#8a3ad0")) if pal == "violet"
                           else (hexc("#123a6a"), CYAN, BLUE))
    cv.clear(ABYSS, PAPER)
    X, Y = A.coords(cv)
    t = ctx.t
    yy, xx = cv.yy[:P], cv.xx[:P]
    hz = 17
    sky = yy < hz
    f = A.warp(X * 0.03 + t * 0.2, Y * 0.05, t, seed=13, k=2)
    scol = A.gradient([(0, ABYSS), (0.5, c_mid), (1, c_hi)], f * (yy / hz))
    j = np.pad((xx // 2 + yy * 3 + int(t * 3)).astype(int), ((0, 8), (0, 0)))
    glyph_field(cv, full(sky & (f > 0.42)), "遠い", j, np.pad(scol, ((0, 8), (0, 0), (0, 0))))
    d = np.maximum(yy - hz + 0.5, 0.3)
    z = 14 / d
    sp = 5 + 10 * ctx.u
    hor = np.abs(((z + ctx.lt * sp) % 3) - 1.5) > 1.32
    rad = np.abs(((xx - 80) / d * 0.45) % 2 - 1) > 0.88
    floor = ~sky
    lum = np.clip(1.2 - z / 30, 0, 1)
    cv.bg[:P][floor] = (mix(ABYSS, c_mid, 0.5) * (0.4 + lum[..., None]))[floor]
    m1 = floor & hor
    m2 = floor & rad & ~hor
    cv.ch[:P][m1] = cv.ids("=")[0]
    cv.fg[:P][m1] = (mix(c_line, c_hi, 0.6) * (0.3 + 0.7 * lum[..., None]))[m1]
    cv.ch[:P][m2] = cv.ids("|")[0]
    cv.fg[:P][m2] = (c_line * (0.4 + 0.6 * lum[..., None]))[m2]
    glow = ctx.pulse(4)
    cv.line(0, hz, 159, hz, mix(c_hi, PAPER, 0.5 + 0.5 * glow), "-", bold=True)
    cv.put_center(hz - 1, "遠いとこ", PAPER, bold=True)
    return fin_blue(cv, ctx, 0.7)


def z_room(cv: Canvas, ctx: Ctx) -> Post:
    """Inside a pointlessly beautiful room.  A perfectly symmetric pastel room
    in one-point perspective -- empty -- with a slowly turning geometric
    ornament hanging in the centre and a glint sweeping across; beautiful,
    sterile, for no one.  When the band stops the lights cut out."""
    Pm = ctx.params
    t = ctx.t
    cv.clear(PEACH, INK)
    yy, xx = cv.yy[:P], cv.xx[:P]
    bx0, by0, bx1, by1 = 50, 11, 110, 31
    # perspective parameter: 0 at the back wall rectangle, 1 at the screen edge
    sx = np.where(xx < bx0, (bx0 - xx) / bx0, np.where(xx > bx1, (xx - bx1) / (159 - bx1), 0))
    sy = np.where(yy < by0, (by0 - yy) / by0, np.where(yy > by1, (yy - by1) / (P - 1 - by1), 0))
    back = (sx == 0) & (sy == 0)
    side = (sx > sy) & ~back
    ceil = (sy >= sx) & (yy < by0)
    floor = (sy >= sx) & (yy > by1)
    cv.bg[:P][back] = mix(MINT, PAPER, 0.4)
    cv.bg[:P][side] = (mix(MINT, LILAC, 0.5) * (0.8 + 0.2 * sx[..., None]))[side]
    cv.bg[:P][ceil] = mix(LILAC, PAPER, 0.5)
    cv.bg[:P][floor] = PEACH
    # floor tiles in perspective
    d = np.maximum(sy, 1e-3)
    zt = 1 / d
    chk = ((np.floor(zt * 1.5) + np.floor((xx - 80) * d * 0.25)) % 2 == 0) & floor
    cv.bg[:P][chk] = mix(PEACH, hexc("#e9b8a8"), 0.6)
    cv.ch[:P][floor & ~chk] = cv.ids(".")[0]
    cv.fg[:P][floor] = mix(PEACH, INK, 0.25)
    # wall panelling stripes on the sides
    st = side & (np.floor(1 / np.maximum(sx, 1e-3) * 2) % 2 == 0)
    cv.ch[:P][st] = cv.ids(":")[0]
    cv.fg[:P][side] = mix(MINT, INK, 0.25)
    # edges of the room
    edge_c = mix(LILAC, INK, 0.45)
    for (ax, ay, ex, ey) in ((bx0, by0, 0, 0), (bx1, by0, 159, 0), (bx0, by1, 0, P - 1), (bx1, by1, 159, P - 1)):
        cv.line(ax, ay, ex, ey, edge_c)
    cv.box(bx0, by0, bx1, by1, edge_c, "+-|")
    # the ornament: nested polygons turning in opposite directions
    cx, cy = 80, 21
    for k in range(6):
        nside = (4, 6, 3, 8, 4, 6)[k]
        R = 3 + k * 2.4
        ang = t * (0.35 + 0.1 * k) * (-1) ** k
        pts = [(cx + R * 1.7 * math.cos(ang + 2 * math.pi * i / nside),
                cy + R * math.sin(ang + 2 * math.pi * i / nside)) for i in range(nside)]
        cv.polyline(pts, GOLD if k % 2 == 0 else hexc("#9a7ad0"), closed=True, char="*" if k % 2 == 0 else ".")
    cv.line(cx, by0, cx, cy - 15, mix(LILAC, INK, 0.3), ":")
    # symmetric reflection on the floor, faint
    for k in range(3):
        R = 3 + k * 3
        pts = [(cx + R * 1.7 * math.cos(-t * 0.4 + 2 * math.pi * i / 6), 38 + R * 0.25 * math.sin(-t * 0.4 + 2 * math.pi * i / 6))
               for i in range(6)]
        cv.polyline(pts, mix(PEACH, GOLD, 0.5), closed=True, char=".")
    cv.put(bx0 + 2, by1 - 1, "無駄に綺麗", mix(MINT, INK, 0.35))
    # glint
    gx = (ctx.lt * 70) % 260 - 50
    g = np.abs(xx - gx + yy * 0.7) < 2.0
    cv.bg[:P][g] = mix(cv.bg[:P][g], PAPER, 0.7)
    p = finish(cv, ctx, DAY, 0.2, vignette=0.1, glow=0.05)
    stop = Pm.get("stop", 1e9)
    if ctx.t >= stop:
        if ctx.feat("onset") > 0.8:
            cv.bg[:] = INK
            cv.ch[:] = 0
            jp(cv, ctx, NIGHT)
        p.fade = 1 - 0.35 * seg(ctx.t, stop, ctx.t1)
    return p


# ================================================================ CHORUS

def z_quiz(cv: Canvas, ctx: Ctx) -> Post:
    """Quiz cards in full-frame type (the 'mustn't expect' lines): question,
    answer slammed in, verdict stamped -- the verdicts don't agree."""
    cards = ctx.params["cards"]
    skin = ctx.params.get("skin", "big")
    hit, _ = Q.run(cv, ctx, cards, skin=skin, beats_per_card=btot(ctx) / len(cards),
                   title=ctx.params.get("title", ""))
    if skin == "big_paper":
        p = fin_paper(cv, ctx, 0.4)
    elif skin == "big_red":
        p = fin_red(cv, ctx, 0.4)
    elif skin == "term":
        p = fin(cv, ctx, 0.4, glow=0.3)
    else:
        p = fin(cv, ctx, 0.4, glow=0.25)
    return quiz_post(p, hit)


def z_shards(cv: Canvas, ctx: Ctx) -> Post:
    """A talent that hurts.  Needles burst out of the word 才能 on every beat
    -- sharp, uneven, too many -- tips glowing red."""
    pal = ctx.params.get("pal", "dark")
    bg, fg = (DEEP, PAPER) if pal == "dark" else (PAPER, INK)
    cv.clear(bg, fg)
    dx, dy, r, a = polar(cv)
    bi = int(math.floor(beats_in(ctx) + 1e-6))
    for back in range(2):
        k = bi - back
        if k < 0:
            continue
        ph = beats_in(ctx) - k
        grow = ease_out(min(1.0, ph * 3)) * (0.55 if back else 1.0)
        rng = np.random.default_rng(100 + k)
        n = 22
        ang = rng.uniform(-math.pi, math.pi, n)
        L = rng.uniform(25, 95, n) * grow
        w = rng.uniform(0.05, 0.12, n)
        for i in range(n):
            da = np.abs((a - ang[i] + math.pi) % (2 * math.pi) - math.pi)
            m = (r < L[i]) & (r > 6) & (da < w[i] * (1 - r / max(L[i], 1e-3)))
            if not m.any():
                continue
            tip = np.clip((r / max(L[i], 1e-3)) ** 2, 0, 1)
            tipc = RED2 if pal == "dark" else mix(INK, BLUE, 0.6)
            col = (fg * (1 - tip[..., None]) + tipc * tip[..., None])
            if back:
                col = mix(bg, fg, 0.3) * np.ones_like(col)
            cv.ch[:P][m] = cv.ids("\\" if (ang[i] % math.pi) < math.pi / 2 else "/")[0]
            cv.fg[:P][m] = col[m]
    m = _word_of(cv, ctx, "才能", "痛痛痛", 18, fg)
    p = (fin if pal == "dark" else fin_paper)(cv, ctx, 1.2)
    if ctx.pulse(8) > 0.5:
        p.chroma = max(p.chroma, 3)
    return p


def z_spot(cv: Canvas, ctx: Ctx) -> Post:
    """Smash the spotlight.  A cone of light made of 光 pours from the top;
    on the hit it shatters into shards that tumble out of frame and the
    stage behind goes red."""
    t = ctx.t
    brk = ctx.params.get("break", ctx.t0 + 1.0)
    after = max(0.0, t - brk)
    broke = t >= brk
    cv.clear(mix(REDDK, RED2, 0.25 * math.exp(-after * 2)) if broke else DEEP, PAPER)
    yy, xx = cv.yy[:P], cv.xx[:P]
    cone = np.abs(xx - 80) < (yy + 3) * 1.15
    lum = np.clip(1 - np.abs(xx - 80) / ((yy + 3) * 1.15 + 1e-3), 0, 1) ** 0.6 * (0.55 + 0.45 * yy / P)
    col = mix(PAPER, YEL, 0.25) * lum[..., None] + DEEP * (1 - lum[..., None])
    j = (xx // 2 + yy * 7 + int(t * 10)).astype(int)
    if not broke:
        glyph_field(cv, full(cone), "光", np.pad(j, ((0, 8), (0, 0))), np.pad(col, ((0, 8), (0, 0), (0, 0))))
        floor = ((xx - 80) / 55) ** 2 + ((yy - 41) / 4) ** 2 < 1
        cv.bg[:P][floor] = mix(DEEP, PAPER, 0.25)
        dust = A.vnoise(xx * 0.7, yy * 0.7 - t * 3, 4) > 0.82
        cv.ch[:P][cone & dust] = cv.ids(".")[0]
    else:
        # shards: blocks of the cone fly apart with gravity
        sid = (np.floor((xx + 3 * np.sin(yy * 0.7)) / 9) * 13 + np.floor((yy + 2 * np.sin(xx * 0.3)) / 5)).astype(int)
        ys, xs = np.nonzero(cone)
        s = sid[ys, xs]
        rng = np.random.default_rng(9)
        vx = rng.uniform(-60, 60, 4096)[s % 4096] + (xs - 80) * 0.8
        vy = rng.uniform(-30, 5, 4096)[s % 4096]
        spin = rng.uniform(-1, 1, 4096)[s % 4096]
        nx = xs + vx * after + spin * (ys - 23) * after
        ny = ys + (vy * after + 60 * after * after) / cv.aspect
        cc = mix(PAPER, YEL, 0.3) * (0.4 + 0.6 * lum[ys, xs, None]) * max(0.15, 1 - after * 0.8)
        ids = np.where((s % 3) == 0, cv.ids("/")[0], np.where((s % 3) == 1, cv.ids("\\")[0], cv.ids("#")[0]))
        ok = (nx >= 0) & (nx < 160) & (ny >= 0) & (ny < P)
        cv.ch[ny[ok].astype(int), nx[ok].astype(int)] = ids[ok]
        cv.fg[ny[ok].astype(int), nx[ok].astype(int)] = cc[ok]
    p = fin(cv, ctx, 1.0, glow=0.5)
    if broke:
        k = max(0.0, 1 - after * 4)
        p.flash, p.chroma = 0.45 * k, int(6 * k)
        p.shake = (int(6 * k), int(3 * k))
    return p


RISE_PALS = {
    "dusk": [(0, hexc("#2a1240")), (0.6, hexc("#c4508a")), (1, hexc("#ffb070"))],
    "sky": [(0, hexc("#0a2a5a")), (0.6, hexc("#3a8ad0")), (1, hexc("#cfeaff"))],
    "night": [(0, hexc("#02030a")), (0.6, hexc("#141a40")), (1, hexc("#4a3a8a"))],
    "dawn": [(0, hexc("#1a1030")), (0.5, hexc("#8a6ab0")), (1, hexc("#ffd8b0"))],
    "red": [(0, hexc("#1a0302")), (0.6, hexc("#8a1410")), (1, hexc("#ff5a3a"))],
}


def z_rise(cv: Canvas, ctx: Ctx) -> Post:
    """'Up, up high -- how's that?'  (たかいたかい, lifting a child.)  The
    world streams downward past us in parallax as we rise; a bright point is
    tossed up on every beat, each time higher, the altitude counting up."""
    pal = ctx.params.get("pal", "sky")
    stops = RISE_PALS[pal]
    t, lt, b = ctx.t, ctx.lt, beats_in(ctx)
    cv.clear(stops[0][1], PAPER)
    yy = cv.yy[:P]
    alt = lt * 0.6 + 0.2 * ease(ctx.u)
    sky = A.gradient(stops, np.clip(1 - yy / P * 0.8 + alt * 0.2, 0, 1))
    cv.bg[:P] = sky * 0.85
    # cloud layers rushing down past us
    X, Y = A.coords(cv)
    for li, (sc_, sp_, amt) in enumerate(((0.04, 22, 0.55), (0.025, 45, 0.9))):
        cl = A.fbm(X * sc_ + li * 7, (Y - lt * sp_ * cv.aspect) * sc_ * 1.6, 50 + li)
        cl = np.clip((cl - 0.52) * 3.2, 0, 1) * amt
        ccol = mix(PAPER, stops[-1][1], 0.35) * np.ones((P, 160, 3))
        cv.density(cl, " .:-=+*", color=ccol * (0.5 + 0.5 * cl[..., None]), thresh=0.08)
        cv.bg[:P] = cv.bg[:P] * (1 - cl[..., None] * 0.35) + ccol * cl[..., None] * 0.35
    rng = np.random.default_rng(31)
    for layer, (n, sp, ch, k) in enumerate(((140, 40, "|", 0.35), (90, 75, "高", 0.6), (40, 140, "|", 0.95))):
        x = rng.uniform(0, 160, n)
        y0 = rng.uniform(0, 60, n)
        y = (y0 + lt * sp) % 60 - 6
        col = mix(stops[-1][1], PAPER, 0.3) * k
        if ch == "高":
            for xi, yi in zip(x, y):
                cv.put(xi, yi, "高", col)
        else:
            for tail in range(3):
                cv.scatter(x, y - tail, ":" if tail else "|", fg=col * (1 - tail * 0.3))
    # altitude ticks rushing down
    for k in range(6):
        ty = (k * 9 + lt * 30) % 54 - 4
        cv.put(150, ty, f"-{int((alt * 100 + (5 - k)) % 1000):03d}", mix(PAPER, stops[1][1], 0.4))
    # the toss
    bi = math.floor(b + 1e-6)
    ph = b - bi
    hmax = 10 + 7 * min(bi, 3)
    y = 40 - hmax * 4 * ph * (1 - ph)
    acc = YEL if pal in ("night", "red") else PAPER
    Wd.paint(cv, Wd.disc(cv, 80, y, 1.8), acc, "@", INK)
    for j in range(1, 6):
        yj = 40 - hmax * 4 * max(0, ph - j * 0.03) * (1 - max(0, ph - j * 0.03))
        cv.put(80, yj, "・", mix(acc, stops[0][1], j * 0.15))
    cv.line(66, 42, 94, 42, mix(PAPER, stops[0][1], 0.4), "=")
    cv.put(4, 2, f"ALT {int(alt * 1000):05d} m", PAPER, bold=True)
    return fin(cv, ctx, 0.6, glow=0.4)


def _sphere(cv, cx, cy, R, rot, tilt, text, fg, dim, bg):
    """A sphere of text: returns (mask, z) and draws it."""
    X, Y = A.coords(cv)
    dx, dy = (X - cx) / R, (Y - cy * cv.aspect) / R
    rr = dx * dx + dy * dy
    m = rr < 1
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    # undo tilt (about x axis), then longitude rotation
    y2 = dy * math.cos(tilt) - z * math.sin(tilt)
    z2 = dy * math.sin(tilt) + z * math.cos(tilt)
    lon = np.arctan2(dx, z2) + rot
    lat = np.arcsin(np.clip(y2, -1, 1))
    j = (np.floor(lon / (math.pi / 12)) + np.floor(lat / (math.pi / 10)) * 5).astype(int)
    grid = (np.abs(((lon / (math.pi / 6)) % 1) - 0.5) > 0.44) | (np.abs(((lat / (math.pi / 6)) % 1) - 0.5) > 0.42)
    shade = (0.25 + 0.75 * z)[..., None]
    col = np.where(grid[..., None], fg * shade, dim * shade)
    glyph_field(cv, full(m), text, np.pad(j, ((0, 8), (0, 0))), np.pad(col, ((0, 8), (0, 0), (0, 0))))
    cv.bg[:P][m] = (bg * (0.5 + 0.5 * z[..., None]))[m]
    return m


def _project(cx, cy, R, rot, tilt, lon, lat, aspect):
    x = np.cos(lat) * np.sin(lon - rot)
    y = np.sin(lat)
    z = np.cos(lat) * np.cos(lon - rot)
    y2 = y * math.cos(tilt) + z * math.sin(tilt)
    z2 = -y * math.sin(tilt) + z * math.cos(tilt)
    return cx + x * R, cy + y2 * R / aspect, z2


def z_sphere(cv: Canvas, ctx: Ctx) -> Post:
    """No way out -- this is just the surface of a sphere.  A globe made of
    the words 逃げ道も無いよ turns; a red path sets out from START, walks
    all the way round, and arrives back at START.  ('pull': the globe
    shrinks back into a picture frame.)"""
    pull = ctx.params.get("pull", False)
    cv.clear(DEEP, PAPER)
    u, t = ctx.u, ctx.t
    R = 30.0 if not pull else 30.0 * (1 - 0.45 * ease(u))
    rot = t * 0.5
    tilt = 0.35
    _sphere(cv, 80, 22, R, rot, tilt, "逃げ道も無いよ", mix(PAPER, CYAN, 0.2), mix(DEEP, PAPER, 0.35),
            hexc("#0a1428"))
    # great-circle path, inclined
    s = np.linspace(0, 2 * math.pi * min(1.0, u * 1.15), 240)
    inc = 0.5
    lon = s + 0.3
    lat = np.arcsin(np.sin(inc) * np.sin(s))
    px, py, pz = _project(80, 22, R, rot, tilt, lon, lat, cv.aspect)
    front = pz > 0
    cv.scatter(px[front], py[front], "#", fg=RED2, bold=True)
    cv.scatter(px[~front], py[~front], ".", fg=REDDK)
    sx, sy, sz = _project(80, 22, R, rot, tilt, np.array([0.3]), np.array([0.0]), cv.aspect)
    if sz[0] > 0:
        cv.put(sx[0] + 2, sy[0] - 1, "START", PAPER if u < 0.85 else RED2, bold=True)
    if u > 0.85:
        cv.put_center(42, "START = GOAL", RED2, bold=True)
    if pull:
        k = ease(seg(u, 0.3, 1.0))
        w, h = 60 * k + 2, 20 * k + 1
        cv.box(80 - w, 22 - h, 80 + w, 22 + h, GOLD, "#=|", bold=True)
        cv.box(80 - w + 2, 22 - h + 1, 80 + w - 2, 22 + h - 1, GOLDDK, "+-|")
    return fin(cv, ctx, 0.6, glow=0.4)


def z_ecg(cv: Canvas, ctx: Ctx) -> Post:
    """An emotion that hurts -- does it?  A heart monitor: the trace spikes on
    every beat, taller each time, too tall for the screen; a big '？'."""
    pal = ctx.params.get("pal", "green")
    if pal == "green":
        bg, tr, gridc = hexc("#020a05"), PHOS, hexc("#0c2a14")
    else:
        bg, tr, gridc = REDBG, INK, mix(REDBG, INK, 0.25)
    cv.clear(bg, tr)
    for gx in range(0, 160, 8):
        cv.line(gx, 0, gx, P - 1, gridc, ":")
    for gy in range(2, P, 5):
        cv.line(0, gy, 159, gy, gridc, "-")
    t = ctx.t
    span = 2.6  # seconds across the screen
    xs = np.arange(160)
    head = (t / span % 1) * 160
    age = (head - xs) % 160 / 160 * span
    tx = t - age
    bp = np.array([ctx.grid.beat_pos(v) for v in tx])
    since = (bp - np.floor(bp)) * ctx.grid.ibi
    nb = np.clip(bp - ctx.grid.beat_pos(ctx.t0), 0, None)
    gain = 0.6 + 0.35 * np.floor(nb)
    y = 26 - gain * (18 * np.exp(-((since - 0.04) / 0.012) ** 2) - 6 * np.exp(-((since - 0.075) / 0.015) ** 2)
                     + 3 * np.exp(-((since - 0.22) / 0.05) ** 2))
    fade = np.clip(1 - age / span, 0, 1)
    for x in range(160):
        if fade[x] <= 0.02:
            continue
        y0 = y[x]
        y1 = y[x - 1] if x > 0 else y0
        lo, hi = int(round(min(y0, y1))), int(round(max(y0, y1)))
        for yy_ in range(max(0, lo), min(P, hi + 1)):
            cv.put(x, yy_, "#" if hi - lo < 2 else "|", mix(bg, tr, fade[x]), bold=True)
    hx = int(head)
    cv.put(hx, int(round(y[hx % 160])), "@", PAPER if pal == "green" else PAPER, bold=True)
    for k in range(1, 4):
        cv.line(hx + k, 0, hx + k, P - 1, bg, " ")
    bmp = cv.text_bitmap("？", 22, True)
    cv.shape_field(bmp, 122, 6, mix(bg, tr, 0.5 + 0.5 * ctx.pulse(5)))
    cv.put(4, 1, f"HR 152  ♥", tr, bold=True)
    return fin(cv, ctx, 0.9, glow=0.5) if pal == "green" else fin_red(cv, ctx, 0.9)


@lru_cache(maxsize=4)
def _dendrites(seed: int):
    rng = np.random.default_rng(seed)
    segs = []

    def grow(x, y, a, L, depth, t0):
        if depth == 0 or L < 1.5:
            return
        x1, y1 = x + math.cos(a) * L, y + math.sin(a) * L / 1.67
        segs.append((x, y, x1, y1, t0, t0 + L * 0.012))
        t1 = t0 + L * 0.012
        for s in (-1, 1):
            if rng.random() < 0.85:
                grow(x1, y1, a + s * rng.uniform(0.5, 1.0), L * rng.uniform(0.5, 0.7), depth - 1, t1)
        grow(x1, y1, a + rng.uniform(-0.2, 0.2), L * 0.8, depth - 1, t1)

    for i in range(10):
        side = i % 4
        if side == 0:
            x, y, a = rng.uniform(0, 160), 0, math.pi / 2
        elif side == 1:
            x, y, a = rng.uniform(0, 160), P - 1, -math.pi / 2
        elif side == 2:
            x, y, a = 0, rng.uniform(0, P), 0
        else:
            x, y, a = 159, rng.uniform(0, P), math.pi
        grow(x, y, a + rng.uniform(-0.4, 0.4), rng.uniform(14, 22), 5, rng.uniform(0, 0.3))
    return segs


def z_frost(cv: Canvas, ctx: Ctx) -> Post:
    """The everyday's face is cold, isn't it?  A face -- two eyes and a flat
    mouth -- made of 日常, in ice blue; frost ferns creep in from every
    edge and snow drifts across."""
    pal = ctx.params.get("pal", "ice")
    t, u = ctx.t, ctx.u
    if pal == "ice":
        bg, fg, frost = hexc("#06101e"), ICE, mix(ICE, PAPER, 0.5)
    else:
        bg, fg, frost = hexc("#e8f2f8"), hexc("#14304a"), hexc("#5a8ab0")
    cv.clear(bg, fg)
    X, Y = A.coords(cv)
    cv.bg[:P] = A.gradient([(0, bg), (1, mix(bg, BLUE, 0.4))], cv.yy[:P] / P)
    A.text_fill(cv, full(np.ones((P, 160), bool)), "冷たい", mix(bg, fg, 0.1))
    # the face
    face = np.zeros((P, 160), bool)
    for ex in (52, 108):
        e = ((cv.xx[:P] - ex) / 16) ** 2 + ((cv.yy[:P] - 16) / 3.2) ** 2 < 1
        face |= e
    mouth = (np.abs(cv.yy[:P] - 32) < 1) & (np.abs(cv.xx[:P] - 80) < 26)
    face |= mouth
    A.text_fill(cv, full(face), "日常", fg, offset=int(t * 2), bold=True)
    for ex in (52, 108):
        look = 3 * math.sin(t * 0.7)
        Wd.paint(cv, full(Wd.disc(cv, ex + look, 16, 2.4)[:P]), fg, "@", bg)
    # frost
    k = ease(min(1.0, u * 1.2)) * 1.6
    for (x0, y0, x1, y1, a, b) in _dendrites(3 if pal == "ice" else 5):
        if k <= a:
            continue
        f = min(1.0, (k - a) / max(1e-3, b - a))
        cv.line(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, frost)
    # snow
    rng = np.random.default_rng(11)
    n = 160
    sx = (rng.uniform(0, 160, n) + t * rng.uniform(-6, 2, n)) % 160
    sy = (rng.uniform(0, P, n) + t * rng.uniform(3, 8, n)) % P
    cv.scatter(sx, sy, "*", fg=mix(fg, bg, 0.3))
    return (fin_blue if pal == "ice" else fin_paper)(cv, ctx, 0.5)


def z_door(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on.'  The frame is a curtain of the line's own text in columns;
    it parts from the middle and light pours through -- an invitation.
    ('morning': the light is dawn-coloured.)"""
    morning = ctx.params.get("morning", False)
    t, u = ctx.t, ctx.u
    open_ = ease(seg(u, 0.1, 0.9))
    cv.clear(DEEP, PAPER)
    xx, yy = cv.xx[:P], cv.yy[:P]
    shift = open_ * 82
    left = xx < 80 - shift
    right = xx >= 80 + shift
    src = np.where(left, xx + shift, np.where(right, xx - shift, -1))
    light = ~(left | right)
    _, _, r, a = polar(cv)
    if morning:
        stops = [(0, hexc("#fff0e0")), (0.35, hexc("#ffb0a0")), (1, hexc("#4a3a8a"))]
    else:
        stops = [(0, mix(PAPER, YEL, 0.3)), (0.35, mix(YEL, ORANGE, 0.4)), (1, hexc("#5a1a08"))]
    lc = A.gradient(stops, np.clip(r / 90, 0, 1))
    # soft ripples of light and floating dust (no radiating rays)
    rip = 0.5 + 0.5 * np.sin(r * 0.35 - t * 3)
    lc = lc * (0.85 + 0.15 * rip)[..., None]
    cv.bg[:P][light] = lc[light]
    dust = light & (A.vnoise(xx * 0.6 + t, yy * 0.9 - t * 2, 12) > 0.8)
    cv.ch[:P][dust] = cv.ids(".")[0]
    cv.fg[:P][light] = (lc * 0.85)[light]
    j = (np.floor(src / 2) * 0 + yy + np.floor(src / 4) * 3).astype(int)
    cur = left | right
    shade = np.clip(np.abs(src - 80) / 80, 0, 1)
    col = mix(DEEP, PAPER, 1.0) * (0.25 + 0.6 * shade[..., None])
    col = np.where(((np.floor(src / 4)) % 2 == 0)[..., None], col, col * 0.6)
    ids_ok = cur
    glyph_field(cv, full(ids_ok), "さおいでよ", np.pad(j, ((0, 8), (0, 0))),
                np.pad(col, ((0, 8), (0, 0), (0, 0))))
    cv.bg[:P][cur] = DEEP
    if open_ > 0.3:
        w = ease(seg(u, 0.4, 1.0))
        bm = big_mask(cv, "おいで", 12, 80, 22)
        cv.ch[:P][bm & light] = cv.ids("#", True)[0]
        cv.fg[:P][bm & light] = mix(lc[22, 80], INK, w)
    return fin(cv, ctx, 0.4, glow=0.25)


# ================================================================== SOLO

def _tunnel(cv, ctx, phase, pal, twist=0.0, text="額縁"):
    """Nested picture frames zooming: phase in [0,1) per frame step."""
    xx, yy = cv.xx[:P], cv.yy[:P]
    dx, dy = (xx - 79.5) / 80, (yy - 22.5) / 23
    if twist:
        r = np.hypot(dx, dy) + 1e-3
        ang = twist * np.log(r)
        c, s = np.cos(ang), np.sin(ang)
        dx, dy = dx * c - dy * s, dx * s + dy * c
    d = np.maximum(np.abs(dx), np.abs(dy)) + 1e-3
    lvl = np.log(d) / math.log(0.72) + phase
    fr = lvl % 1
    k = np.floor(lvl).astype(int)
    border = fr < 0.16
    vert = np.abs(dx) > np.abs(dy)
    c0, c1, cin = pal
    col = np.where((k % 2 == 0)[..., None], c0, c1)
    fade = np.clip(1.1 - lvl / 9, 0.1, 1)[..., None]
    cv.ch[:P][border & vert] = cv.ids("|", True)[0]
    cv.ch[:P][border & ~vert] = cv.ids("=", True)[0]
    cv.fg[:P][border] = (col * fade)[border]
    inner = (fr > 0.16) & (fr < 0.3)
    jj = np.pad((xx // 2 + yy * 3 + k * 5).astype(int), ((0, 8), (0, 0)))
    glyph_field(cv, full(inner), text, jj, np.pad(cin * fade * np.ones((P, 160, 3)), ((0, 8), (0, 0), (0, 0))))
    cv.bg[:P] = (col * 0.12 * fade)


def z_solo(cv: Canvas, ctx: Ctx) -> Post:
    """Guitar solo.  Every two bars the frame changes: a tunnel of picture
    frames (額縁), a colour kaleidoscope, spectral interference, a turning
    globe of text -- then in the last bars they accelerate together and
    burn out to white."""
    Pm = ctx.params
    t = ctx.t
    cv.clear(DEEP, PAPER)
    bar = ctx.bar
    count = t >= Pm["count0"]
    step = 1 if count and t < Pm["count1"] else 2
    pat = int(math.floor(bar / step)) % 4
    warp = seg(t, Pm["warp"], ctx.t1)
    X, Y = A.coords(cv)
    spec = ctx.spectrum
    if t >= Pm["count1"]:
        pat = 0
    if pat == 0:
        sp = 0.5 + 6 * warp
        _tunnel(cv, ctx, (ctx.beat * sp / 2) % 1,
                (GOLD, mix(GOLD, RED2, 0.6), mix(PAPER, GOLD, 0.3)))
    elif pat == 1:
        dx, dy, r, a = polar(cv)
        segA = math.pi / 3
        a2 = np.abs(((a + t * 0.5) % segA) - segA / 2)
        f = (A.warp(r * np.cos(a2) * 0.06, r * np.sin(a2) * 0.06, t, seed=int(bar) * 3, k=2.5) - 0.3) * 2.2
        pals = [[(0, hexc("#12002a")), (0.4, PINK), (0.8, YEL), (1, PAPER)],
                [(0, hexc("#001a2a")), (0.4, CYAN), (0.8, hexc("#7cff8a")), (1, PAPER)]]
        A.shade(cv, f, " .:-=+*#%@", pals[int(bar) % 2], bg_scale=0.4)
    elif pat == 2:
        f = np.zeros_like(X)
        srcs = [(40, 23), (120, 23), (80, 5), (80, 41)]
        for i, (sx, sy) in enumerate(srcs):
            f += np.cos(np.hypot(X - sx - 10 * math.sin(t + i), Y - sy * cv.aspect) * (0.8 + 0.3 * spec[i * 3 % len(spec)]) - t * 14)
        f = 0.5 + 0.5 * f / 4
        hue = (np.hypot(X - 80, Y - 23 * cv.aspect) * 0.02 + t * 0.3) % 1
        col = A.gradient([(0, PINK), (0.33, CYAN), (0.66, YEL), (1, PINK)], hue) * (0.2 + 0.8 * f[..., None])
        cv.density(f ** 1.2, " .:+*#", color=col, thresh=0.1)
        cv.bg[:P] = col * 0.1
    else:
        _sphere(cv, 80, 22, 26, t * 1.2, 0.3, "日常と地球の額縁", mix(PAPER, CYAN, 0.3),
                mix(DEEP, PAPER, 0.3), hexc("#0a1428"))
        n = len(spec)
        for i in range(n * 2):
            v = float(spec[i % n])
            ang = i / (n * 2) * 2 * math.pi + t * 0.3
            r0, r1 = 28, 29 + v * 14
            cv.line(80 + r0 * math.cos(ang), 22 + r0 * math.sin(ang) / cv.aspect,
                    80 + r1 * math.cos(ang), 22 + r1 * math.sin(ang) / cv.aspect,
                    RED2 if v > 0.85 else PAPER)
    # spectrum strip along the bottom of the picture
    n = len(spec)
    for i in range(160):
        v = float(spec[int(i / 160 * n)])
        h = int(v * 5)
        for k in range(h):
            cv.put(i, P - 1 - k, "|", mix(GOLD, RED2, k / 5))
    p = fin(cv, ctx, 0.9, glow=0.45)
    if warp > 0:
        p.flash = 0.6 * warp ** 2
    return p


# ============================================================ B SECTION 2

def z_frames(cv: Canvas, ctx: Ctx) -> Post:
    """Ah, that has gone far away (again).  We are pulled back through a
    corridor of picture frames; each frame we pass is one more removed; the
    words at the centre get smaller and smaller."""
    cv.clear(DEEP, PAPER)
    phase = (-ctx.lt * 0.9) % 1
    _tunnel(cv, ctx, phase, (GOLD, mix(GOLD, PAPER, 0.4), mix(GOLD, DEEP, 0.3)), text="遠く")
    rows = max(3, 9 * (1 - ease(ctx.u)) + 3)
    m = big_mask(cv, "遠くなった", rows, 80, 22.5)
    Wd.paint(cv, full(m), DEEP, " ")
    cv.ch[:P][m] = cv.ids("#", True)[0]
    cv.fg[:P][m] = PAPER
    return fin(cv, ctx, 0.5, glow=0.5)


def z_stars(cv: Canvas, ctx: Ctx) -> Post:
    """Waited for a dark, dark night (again).  A long exposure: stars made
    of 夜 wheel around the pole and draw arcs that lengthen as we wait."""
    cv.clear(hexc("#03040e"), PAPER)
    cv.bg[:P] = A.gradient([(0, hexc("#03040e")), (1, hexc("#141a40"))], cv.yy[:P] / P)
    rng = np.random.default_rng(17)
    n = 260
    R = rng.uniform(3, 110, n)
    a0 = rng.uniform(0, 2 * math.pi, n)
    br = rng.uniform(0.25, 1, n)
    exp = 0.15 + 1.4 * ease(ctx.u)
    px, py = 80, 6
    k = np.linspace(0, 1, 30)
    for i in range(n):
        aa = a0[i] + ctx.t * 0.05 - k * exp
        xs = px + R[i] * np.cos(aa)
        ys = py + R[i] * np.sin(aa) / cv.aspect
        cv.scatter(xs, ys, "-", fg=mix(hexc("#03040e"), mix(PAPER, CYAN, 0.3), br[i] * 0.9))
        hx, hy = xs[0], ys[0]
        if 0 <= hx < 160 and 0 <= hy < P:
            cv.put(hx, hy, "夜" if br[i] > 0.8 else "*", mix(PAPER, YEL, 0.2) * br[i], bold=br[i] > 0.8)
    cv.put(px, py, "*", YEL, bold=True)
    m = big_mask(cv, "暗", 12, 80, 34)
    cv.ch[:P][m] = cv.ids("#")[0]
    cv.fg[:P][m] = mix(hexc("#03040e"), PAPER, 0.25)
    return fin_blue(cv, ctx, 0.4)


def z_graze(cv: Canvas, ctx: Ctx) -> Post:
    """Suddenly, someone brushed past.  Paper.  A stream of 私 runs left to
    right, a stream of 誰か right to left, on the same line -- at the
    crossing they bend around each other and a shiver runs through both."""
    cv.clear(PAPER, INK)
    t, lt = ctx.t, ctx.lt
    for y in range(2, P, 4):
        cv.line(0, y, 159, y, mix(PAPER, INK, 0.07), "-")
    cross = 0.45 * (ctx.t1 - ctx.t0)
    xx, yy = cv.xx[:P], cv.yy[:P]
    vel = 75.0
    for who, sgn, col, txt in ((0, 1, INK, "私私私"), (1, -1, RED2, "誰か誰か")):
        head = 80 + sgn * (lt - cross) * vel
        behind = (head - xx) * sgn          # distance behind the head
        on = (behind > 0) & (behind < 150)
        # the two ribbons share a lane; near each other they bow apart
        other = 80 - sgn * (lt - cross) * vel
        near = np.exp(-((xx - 80) / 26) ** 2) * math.exp(-((lt - cross) * 1.4) ** 2)
        cy = 23 + (-1 if who == 0 else 1) * (1.5 + 7 * near) + 1.2 * np.sin(xx * 0.12 + t * 4 + who * 2)
        thick = 2.6 * np.clip(behind / 12, 0, 1) * np.clip((150 - behind) / 40, 0, 1)
        rib = on & (np.abs(yy - cy) < thick)
        fade = np.clip(1 - behind / 150, 0.15, 1)[..., None]
        c = PAPER * (1 - fade) + col * fade
        j = np.pad(((xx - sgn * lt * vel) // 2).astype(int), ((0, 8), (0, 0)))
        glyph_field(cv, full(rib), txt, j, np.pad(c, ((0, 8), (0, 0), (0, 0))), True)
        hd = int(round(head))
        if 0 <= hd < 160:
            cv.put(hd, int(round(cy[23, hd])), "@", col, bold=True)
    # shimmer where they passed
    k = math.exp(-abs(lt - cross) * 4)
    for y in range(4, 42):
        if (y + int(t * 20)) % 3 == 0:
            cv.put(80 + int(3 * math.sin(y + t * 30) * k), y, "|", mix(PAPER, INK, 0.5 * k))
    return fin_paper(cv, ctx, 0.8)


def z_dodge(cv: Canvas, ctx: Ctx) -> Post:
    """Dodging on purpose.  Rain of 人 falling; one red point side-steps on
    every beat, and the rain parts around it -- nothing touches it."""
    cv.clear(DEEP, PAPER)
    t, b = ctx.t, beats_in(ctx)
    bi = math.floor(b + 1e-6)
    tgt = [80, 50, 104, 64, 96, 72, 88][bi % 7]
    prev = [80, 50, 104, 64, 96, 72, 88][(bi - 1) % 7] if bi > 0 else 80
    dx_ = prev + (tgt - prev) * ease_out(min(1.0, (b - bi) * 4))
    dy_ = 30.0
    rng = np.random.default_rng(23)
    n = 900
    x = rng.uniform(0, 160, n)
    sp = rng.uniform(14, 30, n)
    y = (rng.uniform(0, 60, n) + t * sp) % 56 - 6
    ddx, ddy = x - dx_, (y - dy_) * cv.aspect
    d = np.hypot(ddx, ddy) + 1e-3
    push = np.clip(9 - d, 0, None)
    x2 = x + ddx / d * push * 1.6
    col = mix(DEEP, PAPER, 0.85)
    for tail in range(3, -1, -1):
        cv.scatter(x2, y - tail, "|" if tail else "人", fg=col * (1 - tail * 0.25), bold=tail == 0)
    Wd.paint(cv, full(Wd.disc(cv, dx_, dy_, 1.6)[:P]), RED2, "@", PAPER)
    ring = Wd.disc(cv, dx_, dy_, 9) & ~Wd.disc(cv, dx_, dy_, 8)
    cv.ch[ring] = cv.ids(".")[0]
    cv.fg[ring] = REDDK
    return fin(cv, ctx, 0.9)


def z_sea(cv: Canvas, ctx: Ctx) -> Post:
    """Now -- go somewhere far (again).  Not the city this time: bands of
    evening over a wide sea; the lines of the swell converge on a horizon
    where the words 遠いとこ drift, very small."""
    t = ctx.t
    cv.clear(hexc("#0a1830"), PAPER)
    yy, xx = cv.yy[:P], cv.xx[:P]
    hz = 18
    sky = yy < hz
    band = A.gradient([(0, hexc("#2a2050")), (0.5, hexc("#c4608a")), (0.85, ORANGE), (1, hexc("#ffd0a0"))],
                      yy / hz)
    cv.bg[:P][sky] = band[sky]
    bands = sky & (np.floor(yy) % 3 == 0)
    cv.ch[:P][bands] = cv.ids("-")[0]
    cv.fg[:P][bands] = (band * 1.15)[bands].clip(0, 1)
    d = np.maximum(yy - hz + 0.4, 0.3)
    z = 10 / d
    wave = np.sin(z * 3 + t * 2 + (xx - 80) / d * 0.08 + np.sin(xx * 0.1 + t))
    sea = ~sky
    cv.bg[:P][sea] = (mix(TEAL, hexc("#06141e"), 0.6) * (0.5 + 0.5 / (1 + z[..., None] * 0.1)))[sea]
    crest = sea & (wave > 0.6)
    cv.ch[:P][crest] = cv.ids("~")[0]
    cv.fg[:P][crest] = mix(TEAL, PAPER, 0.4)
    glit = sea & (np.abs(xx - 80) < 3 + (yy - hz) * 0.9) & (A.vnoise(xx * 0.5, yy * 0.8 - t * 4, 6) > 0.6)
    cv.ch[:P][glit] = cv.ids("=")[0]
    cv.fg[:P][glit] = hexc("#ffd0a0")
    cv.line(0, hz, 159, hz, mix(ORANGE, PAPER, 0.5), "_")
    cv.put(80 + 30 * math.sin(t * 0.15) - 4, hz - 1, "遠いとこ", PAPER)
    return fin(cv, ctx, 0.5, glow=0.4)


def z_breath(cv: Canvas, ctx: Ctx) -> Post:
    """I want to sleep all by myself.  Near-black violet; one small glow in
    the middle breathes slowly, sending out rings of z's that fade before
    they reach anyone."""
    cv.clear(hexc("#08040e"), PAPER)
    t, lt = ctx.t, ctx.lt
    dx, dy, r, a = polar(cv)
    br = 0.5 + 0.5 * math.sin(lt * 1.6 - 1.5)
    glow = np.exp(-(r / (8 + 6 * br)) ** 2)
    col = A.gradient([(0, hexc("#08040e")), (0.5, hexc("#4a2a6a")), (1, hexc("#e8d0ff"))], glow)
    cv.bg[:P] = col * 0.5
    cv.density(glow, " .:-=+", color=col, thresh=0.05)
    for k in range(4):
        R = ((lt * 7 + k * 14) % 56) + 4
        ring = np.abs(r - R) < 0.7
        f = max(0.0, 1 - R / 60)
        sel = ring & (np.floor(a * 12) % 2 == 0)
        cv.ch[:P][sel] = cv.ids("z")[0]
        cv.fg[:P][sel] = mix(hexc("#08040e"), LILAC, f)
    cv.put_center(22, "一人", mix(hexc("#e8d0ff"), INK, 0.5), bold=True)
    return fin(cv, ctx, 0.15, glow=0.6)


def z_rain(cv: Canvas, ctx: Ctx) -> Post:
    """But that looks sad.  Behind wet glass a huge 悲 is only visible where
    the rain runs down over it; streaks slide, pause, slide again."""
    cv.clear(hexc("#1a2028"), PAPER)
    t = ctx.t
    cv.bg[:P] = A.gradient([(0, hexc("#2a3442")), (1, hexc("#141a22"))], cv.yy[:P] / P)
    m = big_mask(cv, "悲", 40, 80, 23)
    A.text_fill(cv, full(m), "悲しそう", mix(hexc("#1a2028"), PAPER, 0.22))
    cv.bg[:P][m] = mix(hexc("#2a3442"), ICE, 0.12)
    rng = np.random.default_rng(29)
    n = 160
    x = rng.uniform(0, 160, n)
    sp = rng.uniform(4, 14, n)
    ph = rng.uniform(0, 10, n)
    y = (ph * 6 + t * sp + 3 * np.sin(t * 2 + ph)) % 54 - 4
    for tail in range(8):
        yy_ = y - tail
        xi = x.astype(int)
        inside = np.array([0 <= int(yv) < P and 0 <= xv < 160 and m[int(yv), xv] for xv, yv in zip(xi, yy_)])
        col = np.where(inside[:, None], mix(PAPER, ICE, 0.4), mix(hexc("#2a3442"), PAPER, 0.35))
        col = col * (1 - tail / 9)
        cv.scatter(x, yy_, "|" if tail else "o", fg=col)
    rng2 = np.random.default_rng(31)
    dx = rng2.uniform(0, 160, 200)
    dyy = rng2.uniform(0, P, 200)
    cv.scatter(dx, dyy, ".", fg=mix(hexc("#2a3442"), PAPER, 0.3))
    return fin_blue(cv, ctx, 0.3)


def z_vortex(cv: Canvas, ctx: Ctx) -> Post:
    """The bottom of a worn-out road.  A road of text spirals down into a
    vortex at the centre, everything sliding inward; at the break it all
    stops and only the bottom remains."""
    brk = ctx.params.get("brk", 1e9)
    t = min(ctx.t, brk)
    cv.clear(hexc("#0c0804"), PAPER)
    dx, dy, r, a = polar(cv)
    s = np.log(r + 1) * 3.2 - a - t * 2.2
    road = (np.abs((s / (2 * math.pi)) % 1 - 0.5) < 0.16)
    edge = (np.abs((s / (2 * math.pi)) % 1 - 0.5) - 0.16) < 0.03
    depth = np.clip(r / 70, 0, 1)
    col = A.gradient([(0, hexc("#0c0804")), (0.4, hexc("#5a3a14")), (1, hexc("#e8c890"))], depth)
    j = np.pad(np.floor(s * 2 + r * 0.3).astype(int), ((0, 8), (0, 0)))
    glyph_field(cv, full(road), "疲れ果てた道の底", j, np.pad(col, ((0, 8), (0, 0), (0, 0))))
    e = edge & ~road
    cv.ch[:P][e] = cv.ids(".")[0]
    cv.fg[:P][e] = (col * 0.6)[e]
    cv.bg[:P] = col * 0.15
    k = seg(ctx.t, brk, brk + 0.4)
    if k > 0:
        cv.fg[:P] = mix(cv.fg[:P], INK, 0.85 * k)
        cv.bg[:P] = mix(cv.bg[:P], INK, 0.85 * k)
        cv.put_center(22, "底", mix(INK, PAPER, k), bold=True)
    return fin(cv, ctx, 0.6 if k == 0 else 0.0)


# ================================================================ CHORUS 2

def z_retry(cv: Canvas, ctx: Ctx) -> Post:
    """The second (third) failure.  Attempt bars: the earlier ones already
    failed at 99 %; the current one fills -- and fails too.  A huge 2 (3)
    stands behind."""
    n = ctx.params.get("n", 2)
    paper = ctx.params.get("paper", False)
    bg, fg = (PAPER, INK) if paper else (hexc("#0b0806"), hexc("#ffb040"))
    cv.clear(bg, fg)
    bmp = cv.text_bitmap(str(n), 44, True)
    cv.shape_field(bmp, int(118 - bmp.shape[1] / 2), 1, mix(bg, fg, 0.15))
    u = ctx.u
    for i in range(n):
        y = 6 + i * 11
        cur = i == n - 1
        prog = 0.99 if not cur else min(0.99, ease(min(1.0, u / 0.7)) * 0.99)
        failed = (not cur) or u >= 0.72
        cv.put(6, y, f"ATTEMPT {i + 1}", fg, bold=True)
        cv.box(6, y + 2, 106, y + 6, fg, "+-|")
        w = int(98 * prog)
        Wd.fill_rect(cv, 7, y + 3, 7 + w, y + 5, RED2 if failed else fg, "#", mix(RED2 if failed else fg, PAPER, 0.3))
        cv.put(110, y + 4, f"{int(prog * 100):3d}%", fg, bold=True)
        if failed:
            cv.put(118, y + 4, "FAILED", RED2, bold=True)
    if u >= 0.72:
        Q.stamp(cv, "×", 56, 6 + (n - 1) * 11 + 4, 14, RED2, (u - 0.72) / 0.06)
    p = (fin_paper if paper else fin)(cv, ctx, 1.0)
    if 0.72 <= u < 0.8:
        p.shake = (4, 2)
    return p


def z_stamp(cv: Canvas, ctx: Ctx) -> Post:
    """Nothing but monotonous work.  A sheet of identical boxes; one stamp
    (blue ink, square) lands per half-beat, always the same 済, filling the
    page in rows."""
    cv.clear(PAPER, INK)
    b = beats_in(ctx)
    nst = int(b * 2) + 1
    ink = hexc("#2a4aa0")
    cols, rows = 10, 4
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        x, y = 4 + c * 15.5, 3 + r * 10.5
        cv.box(x, y, x + 13, y + 8, mix(PAPER, INK, 0.3), "+-|")
        cv.put(x + 2, y + 1, f"No.{i + 1:02d}", mix(PAPER, INK, 0.45))
        if i < nst:
            k = 1.0 if i < nst - 1 else min(1.0, (b * 2 % 1) / 0.25)
            off = int(round((1 - k) * 2))
            Wd.fill_rect(cv, x + 2 - off, y + 2 - off, x + 11 + off, y + 7 + off, ink, " ")
            cv.box(x + 2 - off, y + 2 - off, x + 11 + off, y + 7 + off, mix(ink, PAPER, 0.4), "+=|", bold=True)
            cv.put(x + 5, y + 4, "済", PAPER, bold=True)
    cv.put(120, 44, f"×{nst:03d}", ink, bold=True)
    return fin_paper(cv, ctx, 1.0)


def z_droste(cv: Canvas, ctx: Ctx) -> Post:
    """How about repeating it, over and over?  A Droste spiral: the frame
    inside the frame inside the frame, twisted, in teal and orange, winding
    in for ever."""
    cv.clear(DEEP, PAPER)
    _tunnel(cv, ctx, (ctx.lt * 0.8) % 1, (ORANGE, TEAL, mix(PAPER, ORANGE, 0.3)),
            twist=0.55 + 0.1 * math.sin(ctx.t), text="繰り返し")
    return fin(cv, ctx, 0.9, glow=0.4)


@lru_cache(maxsize=4)
def _maze(seed: int, cw: int = 26, chh: int = 11):
    rng = np.random.default_rng(seed)
    walls_h = np.ones((chh + 1, cw), bool)   # wall above cell (r, c)
    walls_v = np.ones((chh, cw + 1), bool)   # wall left of cell (r, c)
    seen = np.zeros((chh, cw), bool)
    start = (chh // 2, cw // 2)
    stack = [start]
    seen[start] = True
    order = [start]
    while stack:
        r, c = stack[-1]
        nb = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= r + dr < chh and 0 <= c + dc < cw and not seen[r + dr, c + dc]]
        if not nb:
            stack.pop()
            if stack:
                order.append(stack[-1])
            continue
        nr, nc = nb[rng.integers(len(nb))]
        if nr != r:
            walls_h[max(r, nr), c] = False
        else:
            walls_v[r, max(c, nc)] = False
        seen[nr, nc] = True
        stack.append((nr, nc))
        order.append((nr, nc))
    return walls_h, walls_v, order


def z_maze(cv: Canvas, ctx: Ctx) -> Post:
    """There's no way out.  A maze with no exit; a red head searches it,
    running into dead end after dead end, back-tracking, never reaching an
    edge that opens."""
    paper = ctx.params.get("paper", False)
    bg, wall = (PAPER, INK) if paper else (hexc("#04100a"), hexc("#3aa86a"))
    cv.clear(bg, wall)
    wh, wv, order = _maze(5 if not paper else 8)
    cw, chh = 6, 4
    ox, oy = 2, 1
    flash = ctx.pulse(6)
    wc = mix(wall, PAPER if not paper else RED2, 0.4 * flash)
    for r in range(wh.shape[0]):
        for c in range(wh.shape[1]):
            if wh[r, c]:
                cv.line(ox + c * cw, oy + r * chh, ox + (c + 1) * cw, oy + r * chh, wc, "#")
    for r in range(wv.shape[0]):
        for c in range(wv.shape[1]):
            if wv[r, c]:
                cv.line(ox + c * cw, oy + r * chh, ox + c * cw, oy + (r + 1) * chh, wc, "#")
    k = int(len(order) * 0.22 * ease(ctx.u)) + 1
    trail = order[max(0, k - 60):k]
    for i, (r, c) in enumerate(trail):
        f = (i + 1) / len(trail)
        cv.put(ox + c * cw + 3, oy + r * chh + 2, "・", mix(bg, RED2, f))
    r, c = order[k - 1]
    cv.put(ox + c * cw + 3, oy + r * chh + 2, "@", RED2, bold=True)
    return (fin_paper if paper else fin)(cv, ctx, 0.8)


def _eye(cv, cx, cy, w, h, open_, look, iris_c, sclera_text, bg, t):
    xx, yy = cv.xx[:P], cv.yy[:P]
    nx = (xx - cx) / w
    lid = h * open_ * (1 - nx ** 2)
    eye = (np.abs(nx) < 1) & (np.abs(yy - cy) < lid)
    A.text_fill(cv, full(eye), sclera_text, mix(bg, PAPER, 0.55))
    cv.bg[:P][eye] = mix(bg, PAPER, 0.08)
    ix = cx + look * w * 0.4
    ir = h * 0.85
    d = np.hypot((xx - ix) / 1.7, yy - cy)
    iris = eye & (d < ir)
    ang = np.arctan2(yy - cy, (xx - ix) / 1.7)
    spoke = (np.floor(ang * 8 / math.pi + t) % 2 == 0)
    cv.ch[:P][iris] = np.where(spoke[iris], cv.ids("/")[0], cv.ids("*")[0])
    cv.fg[:P][iris] = iris_c * (0.5 + 0.5 * (d[iris] / ir))[:, None]
    pupil = eye & (d < ir * 0.42)
    cv.ch[:P][pupil] = cv.ids("@")[0]
    cv.fg[:P][pupil] = INK
    cv.bg[:P][pupil] = INK
    hl = eye & (np.hypot((xx - ix - 2) / 1.7, yy - cy + 1.2) < 0.9)
    cv.ch[:P][hl] = cv.ids("o")[0]
    cv.fg[:P][hl] = PAPER
    top = (np.abs(nx) < 1) & (np.abs(yy - (cy - lid)) < 0.6)
    bot = (np.abs(nx) < 1) & (np.abs(yy - (cy + lid)) < 0.6)
    cv.ch[:P][top | bot] = cv.ids("=")[0]
    cv.fg[:P][top | bot] = PAPER


def z_eye(cv: Canvas, ctx: Ctx) -> Post:
    """You've noticed, haven't you?  A huge eye made of text glances around
    -- then snaps straight at us; it blinks once, and keeps looking."""
    cv.clear(DEEP, PAPER)
    b = beats_in(ctx)
    t = ctx.t
    if b < 2:
        look = 0.8 * math.sin(t * 3)
    else:
        look = 0.8 * math.sin(t * 3) * math.exp(-(b - 2) * 6)
    blink = 1.0
    bb = b - 4.0
    if 0 <= bb < 0.5:
        blink = abs(1 - bb * 4) if bb < 0.5 else 1
    A.text_fill(cv, full(np.ones((P, 160), bool)), "気づいているのでしょう", mix(DEEP, PAPER, 0.07))
    _eye(cv, 80, 22, 66, 15, blink, look, mix(GOLD, RED2, 0.4), "気づいて", DEEP, t)
    return fin(cv, ctx, 0.9)


def z_slats(cv: Canvas, ctx: Ctx) -> Post:
    """Peek at the everyday's face.  Behind blind slats, a face made of 日常
    -- it is only visible through the gaps, which open a little on each
    beat; the eyes are already looking back."""
    cv.clear(hexc("#dfe8ee"), INK)
    t, b = ctx.t, beats_in(ctx)
    A.text_fill(cv, full(np.ones((P, 160), bool)), "日常", mix(hexc("#dfe8ee"), BLUE, 0.25))
    for ex in (48, 112):
        _eye(cv, ex, 18, 20, 4.5, 1.0, 0.0, BLUE, "日常", hexc("#dfe8ee"), t)
    mouth = (np.abs(cv.yy[:P] - 33) < 0.8) & (np.abs(cv.xx[:P] - 80) < 24)
    cv.ch[:P][mouth] = cv.ids("=")[0]
    cv.fg[:P][mouth] = BLUE
    gap = 0.15 + 0.55 * ease(min(1.0, (math.floor(b) + ease(min(1, (b % 1) * 4))) / btot(ctx)))
    period = 4
    yy = cv.yy[:P]
    slat = ((yy % period) / period) >= gap
    sh = A.gradient([(0, hexc("#5a646e")), (1, hexc("#aab4be"))], ((yy % period) / period))
    cv.bg[:P][slat] = sh[slat]
    cv.ch[:P][slat] = cv.ids("-")[0]
    cv.fg[:P][slat] = (sh * 0.75)[slat]
    return fin_paper(cv, ctx, 0.7)


# ================================================================ FINALE

def z_finale(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on' one last time.  White void.  The globe of text we have been
    walking on turns, shrinks, and a gilded frame of characters assembles
    around it: the Earth, framed -- 日常と地球の額縁."""
    Pm = ctx.params
    hold = Pm["hold"]
    cv.clear(PAPER, INK)
    u = ease(seg(ctx.t, ctx.t0, hold))
    R = 40 * (1 - u) + 14 * u
    cy = 22
    _sphere(cv, 80, cy, R, ctx.t * 0.6, 0.35, "日常と地球の額縁", hexc("#1f3a6a"),
            mix(PAPER, hexc("#1f3a6a"), 0.45), mix(PAPER, ICE, 0.6))
    k = ease(seg(ctx.t, ctx.t0 + 0.3, hold))
    if k > 0:
        w, h = 46, 17
        x0, x1, y0, y1 = 80 - w, 80 + w, cy - h, cy + h
        # (start, end, outward normal) per side, drawn clockwise
        sides = (((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)),
                 ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0)))
        for i, ((ax, ay), (bx, by), (nx, ny)) in enumerate(sides):
            f = min(1.0, max(0.0, k * 4 - i))
            if f <= 0:
                continue
            for th in range(3):
                ch_ = "#" if th == 1 else ("=" if ny else "|")
                cv.line(ax + nx * th, ay + ny * th, ax + nx * th + (bx - ax) * f, ay + ny * th + (by - ay) * f,
                        mix(GOLD, GOLDDK, th / 3), ch_, bold=True)
        if k >= 1:
            for (x, y) in ((x0 - 3, y0 - 3), (x1 + 1, y0 - 3), (x0 - 3, y1 + 2), (x1 + 1, y1 + 2)):
                cv.put(x, y, "@@", GOLD, bold=True)
                cv.put(x, y + 1, "@@", GOLDDK, bold=True)
    p = finish(cv, ctx, DAY, 0.2, vignette=0.35, glow=0.08)
    if ctx.t >= hold:
        cv.ch[P:] = 0
        cv.put_center(43, "日常と地球の額縁", INK, bold=True)
    hit = Pm["hit"]
    if ctx.t >= hit:
        p.flash = 0.6 * max(0.0, 1 - (ctx.t - hit) * 4)
    if ctx.t >= Pm["out"]:
        p.fade = max(0.0, 1 - (ctx.t - Pm["out"]) * 6)
    return p
