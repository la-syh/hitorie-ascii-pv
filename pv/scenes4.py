"""Composed per-line scenes: choruses and the second B section.

Chorus places recur so the three choruses rhyme: the shrine, the live hall,
the Ferris wheel, the Earth, the arcade, her phone, the snowy crossing, the
last train.  Chorus 2 adds the konbini, the laundromat, the loop line and
the wall of security monitors that has been watching every place so far.
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
from .scenes2 import WALL_N, FLOOR_N, DESK, room_night, _scenery
from .scenes3 import fin_n, fin_d, night_city, phone_chat, beats_in_total
from .shots import beats_in, poly, solid
from .timeline import Ctx
from .world import (CONCRETE, NIGHT_SKY, NIGHT_SKY2, REDBG, REDDK, WARM, WARM_DIM, fill_rect, paint,
                    rect, sprite, vgrad)

COLD_BG = hexc("#dfe8f0")
NEON = [Wd.NEON_M, Wd.NEON_C, Wd.NEON_G, hexc("#ffd84a")]


# ================================================================= shrine

def c_omikuji(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect.  A shrine at night: torii, paper lanterns swaying, a
    rack of tied fortunes.  The fortune slip unrolls toward us on the beat --
    大凶 -- and a red stamp lands: 期待しないこと."""
    red = ctx.params.get("red", False)
    t = ctx.t
    cv.clear(hexc("#0d0b10") if not red else hexc("#2a0806"), PAPER)
    S.stars(cv, t, 17, 0.015, PAPER, GREY)
    # torii
    tor = REDBG
    fill_rect(cv, 6, 3, 74, 5, tor, "=", mix(tor, PAPER, 0.3))
    fill_rect(cv, 10, 8, 70, 9, tor, "=", mix(tor, PAPER, 0.3))
    fill_rect(cv, 16, 5, 20, 40, tor, "|", mix(tor, INK, 0.3))
    fill_rect(cv, 60, 5, 64, 40, tor, "|", mix(tor, INK, 0.3))
    fill_rect(cv, 36, 5, 44, 8, INK, " ")
    cv.put(38, 6, "神社", PAPER, bold=True)
    # stone path and lanterns
    fill_rect(cv, 0, 40, cv.W, 45, hexc("#2a2a30"), ".", hexc("#3a3a42"))
    for i, x in enumerate((28, 52)):
        sw = math.sin(t * 2 + i) * 1.0
        cv.line(x, 10, x + sw, 13, GREY, "|")
        paint(cv, Wd.disc(cv, x + sw, 16, 3.2), hexc("#ff9a4a"), "=", hexc("#ffd0a0"))
        glow = Wd.disc(cv, x + sw, 16, 9) & (cv.ch == 0)
        cv.bg[glow] = mix(cv.bg[glow], hexc("#5a2a10"), 0.4)
    # rack of tied fortunes
    for r in range(3):
        y = 24 + r * 5
        cv.line(80, y, 156, y, hexc("#8a6a48"), "=", bold=True)
        for x in range(82, 156, 3):
            cv.put(x, y + 1, "&", PAPER if (x + r) % 4 else hexc("#c9c4b6"))
    cv.line(80, 22, 80, 40, hexc("#8a6a48"), "|", bold=True)
    cv.line(156, 22, 156, 40, hexc("#8a6a48"), "|", bold=True)
    # the slip unrolling
    b = beats_in(ctx)
    k = ease_out(min(1.0, b / 1.2))
    sx0, sy0 = 96, 2
    sh = 2 + 18 * k
    fill_rect(cv, sx0, sy0, sx0 + 44, sy0 + sh, hexc("#f4efe0"), " ")
    cv.box(sx0, sy0, sx0 + 44, sy0 + sh, REDBG, "+-|")
    if k > 0.5:
        cv.put(sx0 + 3, sy0 + 1, "第 十 番   おみくじ", REDBG, bold=True)
        bmp = cv.text_bitmap("大凶", 9, True)
        cv.shape_field(bmp, int(sx0 + 22 - bmp.shape[1] / 2), sy0 + 4, INK)
    if b >= 2:
        s = min(1.0, (b - 2) * 5)
        st = 1.6 - 0.6 * s
        fill_rect(cv, sx0 + 18 - 12 * st, 15, sx0 + 18 + 12 * st, 15 + 4 * st, REDBG, " ")
        cv.put(sx0 + 8, 17, "期待しないこと", PAPER, bold=True)
    return fin_n(cv, ctx, 1.2)


# ================================================================== hall

def hall(cv: Canvas, ctx: Ctx, beam=True, mic_light=True, crowd_lights=True, rig_y=3):
    """A live house seen from the back of the crowd."""
    t = ctx.t
    cv.clear(hexc("#08080c"), PAPER)
    # stage
    fill_rect(cv, 10, 26, 150, 31, hexc("#1a1a20"), "=", hexc("#2a2a33"))
    cv.line(10, 26, 150, 26, hexc("#5a5d68"), "_")
    # back wall LED screen with the band name
    fill_rect(cv, 30, 7, 130, 21, hexc("#101018"))
    for x in range(30, 130, 2):
        for y in range(7, 21, 2):
            v = 0.5 + 0.5 * math.sin(x * 0.2 + y * 0.3 + t * 3)
            cv.put(x, y, ".", mix(hexc("#101018"), RED, 0.3 * v))
    bmp = cv.text_bitmap("LIVE", 7, True)
    cv.shape_field(bmp, int(80 - bmp.shape[1] / 2), 10, mix(RED, PAPER, 0.3))
    # amps, drum kit, mic stand
    for x in (14, 132):
        fill_rect(cv, x, 15, x + 14, 25, hexc("#202024"), ":", hexc("#3a3a40"))
        cv.box(x, 15, x + 14, 25, GREY, "+-|")
        cv.put(x + 2, 16, "Marsh" if x < 50 else "ORNG", hexc("#c9a040"))
    sprite(cv, ["   ___   ", " _(___)_ ", "(_)   (_)", " /|   |\\ "], 70, 20, GREY)
    cv.line(80, 18, 80, 25, PAPER, "|", bold=True)
    cv.put(79, 17, "(o)", PAPER, bold=True)
    cv.put(77, 25, "/_|_\\", PAPER)
    # lighting rig
    cv.line(10, rig_y, 150, rig_y, GREY, "=", bold=True)
    cols = [hexc("#ff4a4a"), hexc("#4a8aff"), hexc("#ffd84a"), hexc("#ff4aff")]
    if beam:
        for i, x in enumerate(range(18, 150, 22)):
            ang = math.sin(t * 1.3 + i) * 0.6
            col = cols[(i + ctx.beat_i) % len(cols)]
            ex = x + math.sin(ang) * 30
            for k in range(1, 20):
                yy = rig_y + 1 + k
                xx = x + (ex - x) * k / 20
                cv.put(int(xx), yy, ":", mix(INK, col, 0.6 - k * 0.02))
            cv.put(x - 1, rig_y + 1, "[o]", col, bold=True)
    # crowd from behind: heads, raised hands, penlights
    for row in range(4):
        y = 33 + row * 3
        for x in range(-2 + (row % 2) * 3, 162, 6):
            bob = int(round(ctx.pulse(6) * (1 if (x // 6 + row) % 2 else 0)))
            col = mix(hexc("#22222c"), hexc("#0c0c10"), 0.3 * row)
            paint(cv, Wd.disc(cv, x + 1, y - bob, 1.6), col, "@", mix(col, PAPER, 0.15))
            fill_rect(cv, x - 2, y + 1 - bob, x + 4, y + 3 - bob, col, " ")
            if crowd_lights and (x + row * 7) % 18 == 0:
                col = cols[(x // 6 + ctx.beat_i) % len(cols)]
                wave = int(round(math.sin(t * 6 + x) * 1.5))
                cv.line(x + 1, y - 3 - bob, x + 1 + wave, y - 6 - bob, col, "|", bold=True)


def c_stage(cv: Canvas, ctx: Ctx) -> Post:
    """A talent so sharp it hurts.  The live house from the back: penlights
    waving, moving heads sweeping, and the amp's red glow stabbing out across
    the crowd on every hit."""
    hall(cv, ctx)
    hit = ctx.pulse(5)
    if hit > 0.3:
        for i in range(6):
            a = -0.6 + i * 0.25
            cv.line(28, 20, 28 + 130 * math.cos(a), 20 + 30 * math.sin(a), mix(INK, RED, hit), "-")
    return fin_n(cv, ctx, 1.3, glow=0.35)


def c_spotlight(cv: Canvas, ctx: Ctx) -> Post:
    """Smash the spotlight.  The follow-spot finds the empty mic on stage --
    then the whole rig shatters and rains down over the crowd."""
    tb = ctx.params["break"]
    if ctx.t < tb:
        hall(cv, ctx, beam=False, crowd_lights=False)
        M.spotlight(cv, 80, 4, 25, 12, PAPER, intensity=0.9, flicker=0.25, rng=ctx.rng(ctx.frame))
        cv.put(79, 17, "(o)", PAPER, bold=True)
        return fin_n(cv, ctx, 0.5, glow=0.6)
    hall(cv, ctx, beam=False, crowd_lights=True, rig_y=-5)
    tmp = cv.snapshot()
    cv.ch[:] = 0
    cv.line(10, 3, 150, 3, GREY, "=", bold=True)
    M.spotlight(cv, 80, 4, 25, 12, PAPER, intensity=1.0)
    for x in range(18, 150, 22):
        cv.put(x - 1, 4, "[o]", RED, bold=True)
    snap = cv.snapshot()
    cv.restore(tmp)
    M.shatter(cv, snap, ctx.t - tb, (80, 6), seed=3, speed=50, gravity=90)
    p = fin_n(cv, ctx, 1.2)
    k = max(0.0, 1 - (ctx.t - tb) * 5)
    p.flash, p.chroma = 0.5 * k, int(6 * k)
    return p


# ============================================================ ferris wheel

def c_ferris(cv: Canvas, ctx: Ctx) -> Post:
    """Up, up high!  A Ferris wheel by the bay at night, lights chasing round
    the rim; the red gondola climbs to the very top as the line ends.
    ``inside=True``: from inside the gondola, the city dropping away below."""
    t = ctx.t
    if ctx.params.get("inside"):
        e = ease(ctx.u)
        cv.clear(NIGHT_SKY, PAPER)
        vgrad(cv, 0, 46, NIGHT_SKY, hexc("#2a2440"))
        S.stars(cv, t, 41, 0.02, PAPER, GREY)
        Wd.moon(cv, 120, 8, 4, crescent=0.55)
        base = 30 + 22 * e
        shades = [hexc("#1c1f2c"), hexc("#14161f"), hexc("#0c0d13")]
        for i in range(3):
            Wd.skyline(cv, base + i * 5, 80 + i, 8 + i * 4, 18 + i * 6, shades[i], lit=0.4 + 0.1 * i,
                       t=t, wmin=6 + i * 2, wmax=12 + i * 3)
        fill_rect(cv, 0, base + 14, 160, 46, hexc("#0a0b10"), ".", WARM_DIM)
        # gondola window frame
        fill_rect(cv, 0, 0, 12, 45, hexc("#7a1a14"))
        fill_rect(cv, 148, 0, 159, 45, hexc("#7a1a14"))
        fill_rect(cv, 0, 0, 159, 3, hexc("#7a1a14"))
        fill_rect(cv, 0, 38, 159, 45, hexc("#5a120e"))
        cv.box(12, 3, 148, 38, hexc("#c9c4b6"), "+=|", bold=True)
        cv.line(80, 3, 80, 38, hexc("#c9c4b6"), "|", bold=True)
        cv.put(60, 41, f"ALT {int(40 + 60 * ctx.u):3d} m   ▲", PAPER, bold=True)
        return fin_n(cv, ctx, 0.6)
    night_city(cv, ctx, horizon=34, moon=True, layers=2, lit=0.4)
    fill_rect(cv, 0, 34, cv.W, 45, Wd.SEA, "~", Wd.SEA2)
    cx, cy, R = 64, 18, 15
    rot = t * 0.35
    n = 16
    for i in range(n):
        a = rot + i / n * 2 * math.pi
        x, y = cx + R * 1.7 * math.cos(a), cy + R * math.sin(a)
        cv.line(cx, cy, x, y, mix(GREY, INK, 0.3), None)
    for k in range(120):
        a = k / 120 * 2 * math.pi
        on = (k + int(t * 30)) % 6 < 3
        col = NEON[(k // 6) % 4] if on else mix(GREY, INK, 0.4)
        cv.put(int(cx + R * 1.7 * math.cos(a)), int(cy + R * math.sin(a)), "o", col)
    for i in range(n):
        a = rot + i / n * 2 * math.pi
        x, y = cx + R * 1.7 * math.cos(a), cy + R * math.sin(a)
        cv.put(int(x) - 1, int(y) + 1, "[_]", PAPER)
    # the red gondola: starts at the bottom and climbs to the top
    a = math.pi / 2 - math.pi * ease(ctx.u)
    x, y = cx + R * 1.7 * math.cos(a), cy + R * math.sin(a)
    cv.put(int(x) - 1, int(y) + 1, "[#]", RED, bold=True)
    cv.line(cx - 8, cy, cx - 14, 34, GREY, "/")
    cv.line(cx + 8, cy, cx + 14, 34, GREY, "\\")
    # reflections in the bay
    for k in range(0, 160, 3):
        if (k + int(t * 8)) % 5 == 0:
            cv.put(k, 36 + (k // 3) % 6, "~", NEON[(k // 3) % 4])
    cv.put(112, 30, "BAYSIDE  ★  OPEN 24:00", hexc("#ffd84a"), bold=True)
    return fin_n(cv, ctx, 0.8, glow=0.3)


# ================================================================== Earth

def c_sphere(cv: Canvas, ctx: Ctx) -> Post:
    """No way out -- just the surface of a sphere.  From orbit: the night side
    of the Earth scattered with city lights, a satellite drifting past; a red
    route sets off from her city, runs once round the globe and arrives back
    where it began.  ``pull``: the camera pulls back into a frame."""
    t = ctx.t
    cv.clear(INK, PAPER)
    S.stars(cv, t, 23, 0.03, PAPER, GREY)
    pull = ctx.params.get("pull", False)
    R = 34 if not pull else 34 - 14 * ease(ctx.u)
    cx, cy = 80, 23 * cv.aspect
    S.globe(cv, cx, cy, R, 140 - 90 * ctx.u, tilt=0.4, fg=mix(PAPER, INK, 0.15), dim=hexc("#1a2a44"),
            accent=hexc("#4a8ad0"))
    # city lights on the night (right) half
    rng = np.random.default_rng(5)
    for i in range(140):
        a = rng.uniform(-math.pi / 2, math.pi / 2)
        r = R * math.sqrt(rng.uniform(0, 1))
        x = cx + abs(r * math.cos(a)) * 1.0
        y = cy + r * math.sin(a)
        if (x - cx) > R * 0.2 and (i + int(t * 3)) % 7:
            cv.put(int(x), int(y / cv.aspect), ".", WARM)
    # route around the globe
    u = ctx.u
    for i in range(240):
        a = i / 240 * 2 * math.pi
        if a > u * 2.1 * math.pi:
            break
        x = cx + R * 1.06 * math.cos(a + math.pi)
        y = cy + R * 0.3 * math.sin(a + math.pi) + R * 0.1
        front = math.sin(a + math.pi) > 0
        cv.put(int(x), int(y / cv.aspect), "=" if front else "-", RED if front else REDDK, bold=front)
    cv.put(int(cx - R * 1.06) - 6, int((cy + R * 0.1) / cv.aspect), "HOME●", RED, bold=True)
    if u > 0.85:
        cv.put(int(cx - R * 1.06) - 14, int((cy + R * 0.1) / cv.aspect) + 2, "= HOME again", PAPER, bold=True)
    # satellite
    sx = (t * 10) % 200 - 20
    sprite(cv, ["[]-o-[]"], sx, 6, GREY)
    Wd.moon(cv, 146, 8, 4, PAPER, crescent=0.5)
    if pull:
        for i in range(3):
            k = 1 + i * 0.3
            S.picture_frame(cv, 80 - R * k - 6, 23 - R * k / cv.aspect - 2, 80 + R * k + 6,
                            23 + R * k / cv.aspect + 2, hexc("#c8a040"), hexc("#7a6020"), style="simple", depth=2)
    return fin_n(cv, ctx, 0.8)


# ================================================================= arcade

def arcade_bg(cv: Canvas, ctx: Ctx):
    cv.clear(hexc("#120a1e"), PAPER)
    for x in range(0, 160, 2):
        cv.put(x, 0, "=", NEON[(x // 8 + int(ctx.t * 4)) % 4])
    fill_rect(cv, 0, 40, cv.W, 45, hexc("#24123a"), "*", hexc("#3a2058"))


def c_crane(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect.  An arcade crane game: the claw slides over, drops on
    the beat, grabs the plush cat, lifts it… and lets go right over the chute.
    ``drop_early``: it slips straight out of the claw."""
    t = ctx.t
    arcade_bg(cv, ctx)
    early = ctx.params.get("drop_early", False)
    # cabinet
    x0, x1, y0, y1 = 34, 126, 2, 40
    fill_rect(cv, x0, y0, x1, y1, hexc("#1a1030"))
    cv.box(x0, y0, x1, y1, Wd.NEON_M, "+=|", bold=True)
    fill_rect(cv, x0 + 2, y0 + 4, x1 - 2, y1 - 8, hexc("#0e0a18"))
    cv.put(x0 + 30, y0 + 1, "★ UFO CATCHER ★", hexc("#ffd84a"), bold=True)
    # pile of prizes
    rng = np.random.default_rng(2)
    for i in range(14):
        px, py = rng.uniform(x0 + 6, x1 - 16), rng.uniform(y1 - 15, y1 - 11)
        sprite(cv, ["(o.o)", "(___)"], px, py, NEON[i % 4])
    # chute
    fill_rect(cv, x0 + 3, y1 - 16, x0 + 14, y1 - 9, hexc("#2a1a40"), "|", hexc("#3a2a58"))
    cv.put(x0 + 4, y1 - 17, "PRIZE", PAPER)
    # claw motion phases
    u = ctx.u
    tx = 90.0
    if early:
        phases = [(0.0, 0.25), (0.25, 0.45), (0.45, 0.6), (0.6, 1.0)]
    else:
        phases = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.75), (0.75, 1.0)]
    (a0, a1), (b0, b1), (c0, c1), (d0, d1) = phases
    cx = x1 - 10 + (tx - (x1 - 10)) * ease(seg(u, a0, a1))
    depth = ease(seg(u, b0, b1)) - ease(seg(u, c0, c1))
    cx = cx + (x0 + 9 - tx) * ease(seg(u, c0, d0 + 0.1)) if u > c0 else cx
    cy = y0 + 5 + depth * 22
    cv.line(cx, y0 + 4, cx, cy, GREY, "|", bold=True)
    grab = u > b1
    sprite(cv, [" |", "/ \\" if not grab else "|_|"], cx - 1, cy, PAPER, bold=True)
    # the prize: in the claw between grab and release
    release = d0 + (0.05 if not early else -0.05)
    if grab and u < release:
        sprite(cv, ["(o.o)", "(___)"], cx - 2, cy + 2, RED, bold=True)
    elif u >= release:
        fall = (u - release) * 60
        fx = cx + (5 if not early else 0)
        sprite(cv, ["(x.x)", "(___)"], fx - 2, min(y1 - 12, cy + 2 + fall), RED, bold=True)
        if fall > 4:
            cv.put(int(fx) + 6, int(cy), "!?" if not early else "...", PAPER, bold=True)
    cv.put(x1 + 4, 10, "1 PLAY", hexc("#ffd84a"), bold=True)
    cv.put(x1 + 4, 12, "¥100", PAPER)
    cv.put(x1 + 4, 16, f"CREDIT {max(0, 3 - int(u * 3))}", Wd.NEON_C)
    for x in (4, 140):
        fill_rect(cv, x, 6, x + 16, 39, hexc("#1a1030"))
        cv.box(x, 6, x + 16, 39, NEON[x % 4], "+-|")
    return fin_n(cv, ctx, 0.8, glow=0.3)


def c_gameover(cv: Canvas, ctx: Ctx) -> Post:
    """Second / third failure.  An arcade cabinet's screen: GAME OVER, the
    lives counter emptied, CONTINUE? counting down -- the third time it says
    NO."""
    n = ctx.params["n"]
    arcade_bg(cv, ctx)
    x0, x1, y0, y1 = 40, 120, 3, 36
    fill_rect(cv, x0 - 6, y0 - 3, x1 + 6, 40, hexc("#2a1a40"))
    cv.box(x0 - 6, y0 - 3, x1 + 6, 40, Wd.NEON_C, "+=|", bold=True)
    fill_rect(cv, x0, y0, x1, y1, hexc("#04020a"))
    b = beats_in(ctx)
    bmp = cv.text_bitmap("GAME OVER", 6, True)
    cv.shape_field(bmp, int(80 - bmp.shape[1] / 2), y0 + 3, RED if int(b * 2) % 2 == 0 else PAPER)
    lives = "♥" * max(0, 3 - n) + "×" * n
    cv.put(x0 + 4, y0 + 12, "LIFE " + " ".join(lives), PAPER, bold=True)
    cnt = max(0, 9 - int(b * 2))
    if n < 3:
        cv.put(x0 + 18, y0 + 18, f"CONTINUE ?   {cnt}", hexc("#ffd84a"), bold=True)
        cv.put(x0 + 18, y0 + 21, "INSERT COIN", PAPER if int(b * 4) % 2 else GREY)
    else:
        cv.put(x0 + 18, y0 + 18, "CONTINUE ?", hexc("#ffd84a"), bold=True)
        cv.put(x0 + 18, y0 + 21, "> YES     NO <" if b < 1.5 else "  YES   > NO <", PAPER, bold=True)
    cv.put(x0 + 4, y1 - 2, f"SCORE 000{n}00   HI 999999", GREY)
    # joystick & buttons
    cv.put(60, 38, "(O)  (o)(o)(o)", PAPER, bold=True)
    for x in (4, 132):
        fill_rect(cv, x, 6, x + 22, 39, hexc("#1a1030"))
        cv.box(x, 6, x + 22, 39, NEON[(x // 4) % 4], "+-|")
        fill_rect(cv, x + 3, 9, x + 19, 20, hexc("#05030a"))
        cv.put(x + 5, 14, "DEMO" if x < 50 else "1UP", NEON[(x // 4 + 1) % 4])
    return fin_n(cv, ctx, 1.3, glow=0.3)


# ================================================================== phone

def c_typing(cv: Canvas, ctx: Ctx) -> Post:
    """An emotion that hurts.  Lying awake in the dark, phone over her face:
    she types 'I'm fine', deletes it, types it again; 'read' appears under the
    other person's last message and nothing more comes."""
    t = ctx.t
    cv.clear(hexc("#08080c"), PAPER)
    # ceiling with the phone's glow
    glow = np.hypot(cv.xx - 80, (cv.yy - 22) * 2) < 60
    cv.bg[glow] = mix(hexc("#08080c"), hexc("#1a2a44"), 0.5)
    cv.line(0, 2, 160, 2, hexc("#1a1a22"), "-")
    s_full = "大丈夫だよ"
    b = beats_in(ctx)
    cyc = (b * 1.2) % 2
    n = int(len(s_full) * min(1, cyc)) if cyc < 1 else int(len(s_full) * (2 - cyc))
    typing = s_full[:n] + ("|" if int(t * 3) % 2 else " ")
    msgs = [("L", "最近どう？", PAPER), ("L", "無理してない？", PAPER), ("L", "既読 23:58", None)]
    msgs = [(a, b_, c if c is not None else hexc("#e9edf2")) for a, b_, c in msgs]
    x0 = phone_chat(cv, ctx, msgs, x0=54, y0=1, w=52, h=44, typing=typing, header="◯◯ (1)", bottom=24)
    # keyboard
    fill_rect(cv, x0, 30, x0 + 52, 41, hexc("#d2d6dc"), " ")
    rows = ["q w e r t y u i o p", " a s d f g h j k l", "  z x c v b n m  ⌫"]
    for i, r in enumerate(rows):
        cv.put(x0 + 4, 32 + i * 3, r, INK)
    hit = int(b * 8) % 19
    cv.put(x0 + 4 + hit * 2, 32 + (hit % 3) * 3, "▮", RED)
    cv.put(118, 40, "03:12   battery 4%", RED)
    return fin_n(cv, ctx, 0.5, glow=0.25)


# ================================================================ crossing

def c_crossing(cv: Canvas, ctx: Ctx) -> Post:
    """The everyday's face is cold.  A scramble crossing from above in the
    morning snow: umbrellas pour across the stripes, a giant street screen
    shows the time and the temperature, nobody looks up.
    ``peek``: seen through the slats of her blinds."""
    t = ctx.t
    cv.clear(hexc("#9aa4ae"), INK)
    # zebra stripes in an X
    for k in range(-12, 13):
        for (x, y) in ((80 + k * 5, 23), (80, 23 + k * 2)):
            pass
    for k in range(10):
        fill_rect(cv, 20 + k * 12, 18, 25 + k * 12, 28, PAPER, " ")
        fill_rect(cv, 70, 2 + k * 4, 90, 3 + k * 4, PAPER, " ")
    # snow lying at the kerbs
    fill_rect(cv, 0, 0, 12, 45, Wd.SNOW, ".", GREY)
    fill_rect(cv, 148, 0, 160, 45, Wd.SNOW, ".", GREY)
    # umbrellas crossing (two flows)
    rng = np.random.default_rng(8)
    n = 70
    for i in range(n):
        horiz = i % 2 == 0
        sp = rng.uniform(5, 9) * (1 if i % 4 < 2 else -1)
        if horiz:
            x = (rng.uniform(0, 180) + sp * t) % 180 - 10
            y = rng.uniform(16, 30)
        else:
            x = rng.uniform(66, 94)
            y = (rng.uniform(0, 60) + sp * t * 0.5) % 60 - 8
        col = hexc("#2a2a33") if i % 5 else hexc("#3a4a6a")
        paint(cv, Wd.disc(cv, x, y, 1.8), col, "@", mix(col, PAPER, 0.25))
    # her: the one red umbrella, standing still
    paint(cv, Wd.disc(cv, 104, 31, 1.8), RED, "@", PAPER)
    # snow falling
    rng = np.random.default_rng(3)
    xs = (rng.uniform(0, 160, 200) + np.sin(t + np.arange(200)) * 2) % 160
    ys = (rng.uniform(0, 46, 200) + t * rng.uniform(3, 6, 200)) % 46
    cv.scatter(xs, ys, "*", fg=PAPER)
    # big screen on a building corner
    fill_rect(cv, 116, 2, 156, 13, hexc("#0c0c12"))
    cv.box(116, 2, 156, 13, GREY, "+=|", bold=True)
    tc = -2.0 - 3 * ctx.u
    cv.put(119, 4, f"07:5{int(ctx.lt) % 10}", hexc("#9fd0ff"), bold=True)
    cv.put(119, 7, f"{tc:+.1f}°C   ❄ 雪", hexc("#9fd0ff"), bold=True)
    cv.put(119, 10, "今日も一日がんばろう", PAPER)
    p = fin_d(cv, ctx, 0.4, vignette=0.4)
    if ctx.params.get("peek"):
        # blinds: dark slats with a finger-made gap
        gap = (cv.yy >= 10) & (cv.yy <= 34) & (np.abs(cv.xx - 80) < 70 * ease_out(min(1, ctx.u * 3)))
        slat = (cv.yy % 4 == 0) & ~gap & (cv.yy < 46)
        cv.ch[slat] = cv.ids("=")[0]
        cv.bg[slat] = hexc("#2a2a30")
        cv.fg[slat] = hexc("#3a3a42")
        cv.put(6, 9, "( |||| )", hexc("#c9a080"), bold=True)
    return p


# ================================================================== train

def c_traindoor(cv: Canvas, ctx: Ctx) -> Post:
    """Come on, over here.  The last train waits at the empty platform; the
    doors slide open, warm light spills out over the yellow line, the chime
    plays -- and we step in."""
    t = ctx.t
    morning = ctx.params.get("morning", False)
    cv.clear(hexc("#0c0d14") if not morning else hexc("#c9d6e2"), PAPER)
    fill_rect(cv, 0, 0, cv.W, 3, hexc("#2a2b33"), "=", hexc("#4a4b55"))
    for x in range(10, 160, 30):
        fill_rect(cv, x, 3, x + 14, 4, hexc("#e9f2ff"), "=", PAPER)
    zoom = ease(seg(ctx.t, ctx.t1 - 0.9, ctx.t1))
    s = 1 + 3 * zoom ** 2
    # train side
    ty0, ty1 = 23 - 15 * s, 23 + 15 * s
    fill_rect(cv, 0, ty0, cv.W, ty1, hexc("#c9ced6"))
    cv.line(0, 23 + 8 * s, cv.W, 23 + 8 * s, hexc("#2a8a4a"), "=", bold=True)
    for x in (10, 128):
        fill_rect(cv, 80 + (x - 80) * s, 23 - 9 * s, 80 + (x + 20 - 80) * s, 23 - 1 * s, hexc("#2a2a33"), "#",
                  hexc("#3a3a44"))
    op = ease_out(seg(ctx.u, 0.15, 0.45))
    dw = 18 * s
    gap = dw * op
    fill_rect(cv, 80 - gap, 23 - 12 * s, 80 + gap, 23 + 13 * s, hexc("#ffe7b8"), " ")
    for side in (-1, 1):
        x0 = 80 + side * gap
        x1 = x0 + side * dw
        fill_rect(cv, min(x0, x1), 23 - 12 * s, max(x0, x1), 23 + 13 * s, hexc("#b8bec8"), " ")
        cv.box(min(x0, x1), 23 - 12 * s, max(x0, x1), 23 + 13 * s, GREY, "+-|")
        fill_rect(cv, min(x0, x1) + 3 * s, 23 - 9 * s, max(x0, x1) - 3 * s, 23 - 1 * s, hexc("#ffe7b8"), " ")
    # inside: seats and straps visible through the gap
    if gap > 3:
        for x in range(int(80 - gap) + 1, int(80 + gap), 6):
            cv.put(x, int(23 - 10 * s) + 1, "o", GREY)
    # platform
    fill_rect(cv, 0, 37, cv.W, 45, CONCRETE, ".", mix(CONCRETE, PAPER, 0.2))
    cv.line(0, 37, cv.W, 37, hexc("#ffd84a"), "=", bold=True)
    spill = (cv.yy > 37) & (np.abs(cv.xx - 80) < gap + (cv.yy - 37) * 3)
    cv.bg[spill] = mix(cv.bg[spill], hexc("#ffe7b8"), 0.4)
    if op > 0.2:
        cv.put(56, 41, "♪ ドアが開きます  DOORS OPEN", WARM, bold=True)
    cv.put(4, 1, "終電  LAST TRAIN  23:59", RED if not morning else INK, bold=True)
    p = fin_n(cv, ctx, 0.4, glow=0.08) if not morning else fin_d(cv, ctx, 0.4)
    p.flash = 0.7 * zoom ** 3
    return p


# ====================================================== B section 2 scenes

def b_rearview(cv: Canvas, ctx: Ctx) -> Post:
    """It has gone far away.  From the last car's rear window: the rails
    unspool behind us and the lit station shrinks to a point."""
    t = ctx.t
    night_city(cv, ctx, horizon=22, moon=True, layers=2)
    fill_rect(cv, 0, 22, cv.W, 45, hexc("#14141a"), ".", hexc("#22222a"))
    vx, vy = 80, 22
    for side in (-1, 1):
        cv.line(vx + side, vy, vx + side * 46, 45, GREY, None, bold=True)
        cv.line(vx + side * 3, vy, vx + side * 120, 45, mix(GREY, INK, 0.4), None)
    for k in range(14):
        z = ((k / 14) - t * 0.9) % 1
        zz = z ** 2.2
        y = vy + (45 - vy) * zz
        w = 1 + 46 * zz
        cv.line(vx - w, y, vx + w, y, hexc("#5a4a3a"), "=")
    k = ease_out(ctx.u)
    w = 26 * (1 - k) + 1
    fill_rect(cv, vx - w, vy - w * 0.4, vx + w, vy, hexc("#e9e0c0"), "#", WARM)
    cv.put(int(vx - 2), int(vy - w * 0.4) - 1, "駅", PAPER if w > 6 else GREY)
    # window frame
    fill_rect(cv, 0, 0, 8, 45, hexc("#9aa0aa"))
    fill_rect(cv, 152, 0, 159, 45, hexc("#9aa0aa"))
    cv.box(8, 0, 152, 45, hexc("#5a5d68"), "+=|", bold=True)
    return fin_n(cv, ctx, 0.3)


def b_bench(cv: Canvas, ctx: Ctx) -> Post:
    """Waited for the dark, dark night.  An empty platform after the last
    train: a bench, a vending machine humming, moths circling the lamp, the
    timetable stamped 'service ended'."""
    t = ctx.t
    night_city(cv, ctx, horizon=24, moon=True, layers=2, lit=0.15)
    fill_rect(cv, 0, 30, cv.W, 45, CONCRETE, ".", mix(CONCRETE, PAPER, 0.15))
    cv.line(0, 30, cv.W, 30, hexc("#ffd84a"), "=", bold=True)
    fill_rect(cv, 0, 0, cv.W, 2, hexc("#2a2b33"), "=", hexc("#4a4b55"))
    for x in (30, 120):
        cv.line(x, 2, x, 30, hexc("#3a3b44"), "|", bold=True)
    # lamp with moths
    cv.put(66, 3, "[==]", PAPER, bold=True)
    pool = Wd.disc(cv, 68, 24, 22) & (cv.yy > 4)
    cv.bg[pool] = mix(cv.bg[pool], hexc("#3a3a2a"), 0.5)
    for i in range(5):
        a = t * (2 + i * 0.4) + i
        cv.put(int(68 + 6 * math.cos(a)), int(6 + 2 * math.sin(a * 1.3)), "~", PAPER)
    # bench
    fill_rect(cv, 52, 25, 86, 26, WOOD := hexc("#8a6a48"), "=", mix(WOOD, PAPER, 0.3))
    cv.line(54, 27, 54, 30, GREY, "|")
    cv.line(84, 27, 84, 30, GREY, "|")
    cv.put(70, 24, "o", RED, bold=True)
    # vending machine glow
    fill_rect(cv, 96, 13, 112, 30, hexc("#e9f2ff"), " ")
    sprite(cv, "vending", 97, 15, hexc("#3a6ea6"))
    vg = (np.abs(cv.xx - 104) < 16) & (cv.yy > 30)
    cv.bg[vg] = mix(cv.bg[vg], hexc("#5a7aa6"), 0.3)
    # timetable
    fill_rect(cv, 6, 8, 26, 26, PAPER, " ")
    for i in range(7):
        cv.put(8, 10 + i * 2, f"{17 + i * 1}  12 34 56", INK)
    cv.put(8, 23, "本日の運転", REDBG, bold=True)
    cv.put(8, 24, "  終了しました", REDBG, bold=True)
    hh = int(ctx.lt * 4)
    cv.put(130, 26, f"00:{12 + hh:02d}", PAPER)
    return fin_n(cv, ctx, 0.3)


def b_express(cv: Canvas, ctx: Ctx) -> Post:
    """Suddenly someone brushed past.  An express blasts through without
    stopping: a wall of lit windows smears past, one face in one window looks
    back for a single frame, and the papers on the platform whirl up."""
    t = ctx.t
    cv.clear(hexc("#101118"), PAPER)
    fill_rect(cv, 0, 34, cv.W, 45, CONCRETE, ".", mix(CONCRETE, PAPER, 0.2))
    cv.line(0, 34, cv.W, 34, hexc("#ffd84a"), "=", bold=True)
    u = ctx.u
    pass_ = 0.2 < u < 0.8
    if pass_:
        k = (u - 0.2) / 0.6
        fill_rect(cv, 0, 6, cv.W, 32, hexc("#c9ced6"), "-", hexc("#a8aeb8"))
        off = int(k * 900)
        for x in range(-40, 200, 12):
            xx = (x - off) % 192 - 16
            fill_rect(cv, xx, 10, xx + 8, 18, WARM, "=", mix(WARM, PAPER, 0.4))
        cv.line(0, 24, cv.W, 24, RED, "=", bold=True)
        if abs(k - 0.5) < 0.04:
            cv.put(76, 13, "(o_o)", INK, bold=True)
    else:
        night_city(cv, ctx, horizon=32, moon=False, layers=2)
        fill_rect(cv, 0, 34, cv.W, 45, CONCRETE, ".", mix(CONCRETE, PAPER, 0.2))
        cv.line(0, 34, cv.W, 34, hexc("#ffd84a"), "=", bold=True)
    # papers whirling after it passes
    if u > 0.6:
        w = (u - 0.6) * 4
        rng = np.random.default_rng(4)
        for i in range(10):
            a = rng.uniform(0, 6.28) + w * 6
            cv.put(int(40 + i * 9 + 10 * math.cos(a) * w), int(38 - 12 * w * rng.uniform(0.3, 1) + 3 * math.sin(a)),
                   "[=]", PAPER)
    cv.put(70, 37, "o", RED, bold=True)
    cv.put(4, 40, "通過列車にご注意ください", hexc("#ffd84a"))
    p = fin_n(cv, ctx, 0.5)
    if pass_:
        p.chroma = 3
    return p


def b_dodge(cv: Canvas, ctx: Ctx) -> Post:
    """Dodging them on purpose.  From above, a night crossing: a river of
    heads; the red dot cuts across against the flow, slipping through gaps
    on every half-beat."""
    t = ctx.t
    cv.clear(hexc("#1a1b22"), PAPER)
    for k in range(10):
        fill_rect(cv, 4 + k * 16, 10, 12 + k * 16, 36, hexc("#3a3b44"), " ")
    rng = np.random.default_rng(12)
    n = 90
    hx = (rng.uniform(0, 180, n) + rng.uniform(4, 8, n) * t * np.where(np.arange(n) % 2, 1, -1)) % 180 - 10
    hy = rng.uniform(4, 42, n)
    for x, y in zip(hx, hy):
        paint(cv, Wd.disc(cv, x, y, 1.4), hexc("#0a0a0e"), "@", hexc("#2a2a33"))
    b = beats_in(ctx)
    k = b / max(1.0, beats_in_total(ctx))
    y = 44 - 40 * k
    x = 80 + 14 * math.sin(b * math.pi)
    for j in range(1, 10):
        yy = 44 - 40 * max(0, k - j * 0.012)
        xx = 80 + 14 * math.sin((b - j * 0.08) * math.pi)
        cv.put(int(xx), int(yy), ".", REDDK)
    paint(cv, Wd.disc(cv, x, y, 1.6), RED, "@", PAPER)
    for x0 in (0, 150):
        fill_rect(cv, x0, 0, x0 + 9, 45, hexc("#2a2b33"), ":", hexc("#3a3b44"))
    return fin_n(cv, ctx, 0.5)


def b_seaside(cv: Canvas, ctx: Ctx) -> Post:
    """Go somewhere far away.  A two-car local train runs along a seaside line
    at night; a lighthouse sweeps its beam, the moon lays a path on the water."""
    t = ctx.t
    night_city(cv, ctx, horizon=26, moon=False, layers=0, stars=0.04)
    Wd.moon(cv, 120, 7, 5, PAPER)
    fill_rect(cv, 0, 26, cv.W, 45, Wd.SEA, "~", Wd.SEA2)
    for y in range(27, 45, 2):
        w = 2 + (y - 26) * 0.8
        cv.line(120 - w + math.sin(t + y) * 2, y, 120 + w + math.sin(t + y) * 2, y, PAPER, "~")
    # lighthouse
    fill_rect(cv, 20, 12, 24, 26, PAPER, "|", GREY)
    cv.put(19, 11, "[##]", WARM, bold=True)
    a = t * 1.6
    for k in range(1, 50):
        cv.put(int(22 + k * 1.8 * math.cos(a)), int(11 + k * 0.35 * math.sin(a) * 0.4), ".",
               mix(WARM, INK, k / 50))
    # embankment and the train
    fill_rect(cv, 0, 30, cv.W, 32, hexc("#2a2a30"), "=", hexc("#4a4a52"))
    x = -60 + 220 * ctx.u
    Wd.train(cv, x, 21, 2, PAPER, hexc("#c9a46a"), win=WARM, length=30)
    for side in (0, 1):
        pass
    return fin_n(cv, ctx, 0.4, glow=0.3)


def b_futon(cv: Canvas, ctx: Ctx) -> Post:
    """Want to sleep, all by myself.  Her room from the ceiling: futon on the
    tatami, the phone face-down, the cat curled at her feet, the clock at
    3 a.m.; the last light goes out."""
    t = ctx.t
    cv.clear(hexc("#2a2a20"), PAPER)
    for y in range(0, 46, 11):
        cv.line(0, y, 160, y, hexc("#1a1a12"), "=")
    for x in (0, 54, 108):
        cv.line(x, 0, x, 46, hexc("#1a1a12"), "|")
    # futon
    fill_rect(cv, 40, 6, 120, 40, hexc("#d8d2c4"), " ")
    cv.box(40, 6, 120, 40, hexc("#8a8478"), "+-|")
    fill_rect(cv, 52, 8, 108, 12, PAPER, " ")
    # blanket with a curled shape
    fill_rect(cv, 42, 16, 118, 38, hexc("#6a7a9a"), "~", hexc("#7a8aaa"))
    br = 1 + 0.5 * math.sin(t * 1.4)
    paint(cv, Wd.disc(cv, 78, 24, 9 + br) & (cv.yy < 34), hexc("#5a6a8a"), "~", hexc("#6a7a9a"))
    paint(cv, Wd.disc(cv, 72, 10, 3.5), hexc("#1a1a1a"), "#", hexc("#2a2a2a"))
    sprite(cv, "cat_sleep", 104, 34, PAPER)
    fill_rect(cv, 124, 16, 130, 26, hexc("#111111"), " ")
    cv.box(124, 16, 130, 26, GREY, "+-|")
    sprite(cv, "mug", 136, 8, GREY)
    cv.put(8, 4, "03:00", RED, bold=True)
    for i in range(3):
        z = (t * 0.4 + i / 3) % 1
        cv.put(int(84 + 8 * z), int(8 - 6 * z), "zZ"[i % 2], mix(PAPER, INK, z))
    p = fin_n(cv, ctx, 0.2)
    p.fade = 1 - 0.45 * ease(ctx.u)
    return p


def b_rainwindow(cv: Canvas, ctx: Ctx) -> Post:
    """That seems sad.  Inside the dark room looking out: rain streams down
    the glass, drops sliding and joining, the city's lights blurred into
    soft dots behind."""
    t = ctx.t
    cv.clear(hexc("#0a0b10"), PAPER)
    rng = np.random.default_rng(9)
    for i in range(60):
        x, y = rng.uniform(10, 150), rng.uniform(4, 40)
        col = [WARM, RED, Wd.NEON_C, PAPER][i % 4]
        paint(cv, Wd.disc(cv, x, y, rng.uniform(1.0, 2.6)), mix(hexc("#0a0b10"), col, 0.35), " ")
    # drops sliding
    for i in range(40):
        x = rng.uniform(10, 150)
        sp = rng.uniform(1, 6)
        y = (rng.uniform(0, 46) + t * sp) % 46
        cv.line(x, y - sp * 0.8, x, y, mix(PAPER, INK, 0.4), "|")
        cv.put(int(x), int(y), "o", PAPER)
    Wd.rain(cv, t, 4, 120, mix(PAPER, INK, 0.6), speed=30, slant=0.1)
    Wd.window_frame(cv, 6, 1, 154, 42, hexc("#3a3a42"), mullions=(0.5,), sill=True)
    cv.put(10, 44, "( 雨 )", GREY)
    return fin_n(cv, ctx, 0.2, glow=0.35)


def b_underpass(cv: Canvas, ctx: Ctx) -> Post:
    """The bottom of a worn-out road.  Down the steps into a long underpass:
    flickering tubes, puddles, posters peeling, a vending machine at the far
    end; when the band breaks, the lights die."""
    P = ctx.params
    t = ctx.t
    cv.clear(hexc("#15161a"), PAPER)
    vx, vy = 80, 18
    paint(cv, poly(cv, [(70, vy - 5), (90, vy - 5), (160, 0), (0, 0)]), hexc("#22232a"), " ")
    paint(cv, poly(cv, [(70, vy + 5), (90, vy + 5), (160, 46), (0, 46)]), hexc("#2a2b30"), ".",
          hexc("#3a3b42"))
    for k in range(10):
        z = ((k / 10) + t * 0.3) % 1
        zz = z ** 2
        x0, x1 = 70 - 70 * zz, 90 + 70 * zz
        y = vy - 5 - 13 * zz
        flick = (math.sin(t * 23 + k * 7) > -0.6)
        cv.line(x0 + (x1 - x0) * 0.35, y, x0 + (x1 - x0) * 0.65, y, PAPER if flick else GREY, "=", bold=flick)
        yb = vy + 5 + 23 * zz
        if k % 3 == 0:
            cv.line(x0 + (x1 - x0) * 0.3, yb, x0 + (x1 - x0) * 0.5, yb, hexc("#3a4a5a"), "~")
    for side in (-1, 1):
        cv.line(vx + side * 10, vy - 5, vx + side * 80, 0, GREY, None)
        cv.line(vx + side * 10, vy + 5, vx + side * 80, 46, GREY, None)
        cv.line(vx + side * 10, vy - 5, vx + side * 10, vy + 5, GREY, "|")
    sprite(cv, "vending", 76, vy - 3, hexc("#3a6ea6"))
    for (x, y) in ((14, 12), (130, 14), (30, 26)):
        fill_rect(cv, x, y, x + 12, y + 8, hexc("#8a6a48"), "/", hexc("#a6865c"))
    p = fin_n(cv, ctx, 0.3)
    brk = seg(t, P.get("brk", 1e9), P.get("brk", 1e9) + 0.4)
    if brk > 0:
        S.char_noise(cv, ctx.rng(ctx.frame), 0.03 * brk)
        cv.fg[:46] = mix(cv.fg[:46], INK, 0.65 * brk)
        cv.bg[:46] = mix(cv.bg[:46], INK, 0.65 * brk)
    return p


# ============================================================ chorus 2 work

def c_register(cv: Canvas, ctx: Ctx) -> Post:
    """Nothing but monotonous work.  Behind a konbini register at night: the
    scanner beeps on every beat, items slide past, the receipt grows and the
    queue never shortens."""
    t = ctx.t
    cv.clear(hexc("#e9edf0"), INK)
    for y in range(2, 22, 5):
        cv.line(0, y, 160, y, hexc("#c9ced6"), "=")
        for x in range(2, 160, 7):
            col = [hexc("#e36a4a"), hexc("#4a8ad0"), hexc("#f2c24a"), hexc("#5aaa6a")][(x + y) % 4]
            cv.put(x, y - 1, "[]", col)
    fill_rect(cv, 0, 0, 160, 1, hexc("#2a8a4a"), "=", hexc("#5aaa6a"))
    cv.put(60, 0, " 24H  ★ MART ", PAPER, bold=True)
    # counter
    fill_rect(cv, 0, 26, 160, 45, hexc("#c9b48a"), "-", hexc("#b8a37a"))
    cv.line(0, 26, 160, 26, hexc("#8a7a5a"), "=", bold=True)
    # belt with items
    b = ctx.beat
    items = ["(milk)", "[onigiri]", "<bento>", "(coffee)", "[gum]", "{bread}"]
    for i in range(-2, 8):
        x = 140 - ((i + b) % 9) * 16
        cv.put(int(x), 28, items[(i + int(b)) % len(items)], INK, bold=True)
    # scanner flash
    beep = ctx.pulse(10)
    cv.box(68, 30, 92, 36, INK, "+=|", fill=True, bg=hexc("#2a2a30"))
    cv.put(72, 33, "PI!" if beep > 0.5 else "---", RED if beep > 0.5 else GREY, bold=True)
    if beep > 0.5:
        cv.line(70, 29, 90, 29, RED, "=", bold=True)
    # register display & receipt
    fill_rect(cv, 110, 30, 156, 38, hexc("#0c1a12"))
    total = 108 * int(b)
    cv.put(112, 33, f"TOTAL ¥{total % 100000:6d}", hexc("#5dff8a"), bold=True)
    rlen = min(14, int(beats_in(ctx) * 3))
    fill_rect(cv, 30, 30, 44, 30 + rlen, PAPER, " ")
    for k in range(rlen):
        cv.put(31, 30 + k, "¥108 ...." if k % 2 else "--------", GREY)
    # queue
    for i in range(6):
        cv.put(4 + i * 4, 23, "o", mix(INK, PAPER, 0.3 + 0.08 * i))
        cv.put(3 + i * 4, 24, "/|\\", mix(INK, PAPER, 0.3 + 0.08 * i))
    cv.put(4, 40, f"本日 {int(b) % 1000:03d} 件目", INK)
    return fin_d(cv, ctx, 0.6)


def c_laundromat(cv: Canvas, ctx: Ctx) -> Post:
    """How about doing it again and again?  A coin laundromat at 2 a.m.: a
    row of washers all spinning, clothes tumbling round, every timer
    resetting the moment it hits zero."""
    t = ctx.t
    cv.clear(hexc("#dfe6ea"), INK)
    fill_rect(cv, 0, 38, 160, 45, hexc("#b8c4ca"), "+", hexc("#a8b4ba"))
    for y in (0, 1):
        cv.line(0, y, 160, y, hexc("#9fd0f0"), "=")
    for i in range(5):
        x0 = 4 + i * 31
        fill_rect(cv, x0, 8, x0 + 28, 37, PAPER, " ")
        cv.box(x0, 8, x0 + 28, 37, GREY, "+=|", bold=True)
        cx, cy = x0 + 14, 24
        paint(cv, Wd.disc(cv, cx, cy, 11), hexc("#3a4a5a"), " ")
        paint(cv, Wd.disc(cv, cx, cy, 9.5), hexc("#5a7a9a"), " ")
        rot = t * (5 + i * 0.3)
        for k in range(5):
            a = rot + k * 1.25
            col = [RED, hexc("#f2c24a"), PAPER, hexc("#5aaa6a"), hexc("#4a8ad0")][(k + i) % 5]
            cv.put(int(cx + 5 * math.cos(a) * 1.7), int(cy + 5 * math.sin(a) * 0.6), "@@", col, bold=True)
        rem = (12 - int((ctx.beat + i * 3) % 12))
        cv.put(x0 + 3, 10, f"{rem:02d}:00", RED if rem < 3 else INK, bold=True)
        cv.put(x0 + 18, 10, "¥200", GREY)
    cv.put(4, 4, "COIN LAUNDRY  24H   ↻ ↻ ↻", INK, bold=True)
    cv.put(120, 40, "02:14", GREY)
    return fin_d(cv, ctx, 0.6)


def c_loopline(cv: Canvas, ctx: Ctx) -> Post:
    """There's no way out.  The loop-line map above the train door: the
    'you are here' light runs round and round the ring of stations, and the
    next stop is always the same one."""
    t = ctx.t
    cv.clear(hexc("#f4f4ee"), INK)
    fill_rect(cv, 0, 0, 160, 2, hexc("#5aaa3a"), "=", hexc("#7acc5a"))
    cx, cy, rx, ry = 80, 23, 58, 16
    for k in range(240):
        a = k / 240 * 2 * math.pi
        cv.put(int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)), "#", hexc("#5aaa3a"), bold=True)
    names = ["日常", "最前線", "四畳間", "球面上", "額縁", "日常", "遠いとこ", "部屋の中", "道の底", "日常", "球面上", "日常"]
    for i, nm in enumerate(names):
        a = i / len(names) * 2 * math.pi
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        cv.put(int(x) - 1, int(y), "(o)", INK, bold=True)
        lx = int(x + (6 if math.cos(a) >= 0 else -6 - 2 * len(nm)))
        cv.put(lx, int(y + (1 if math.sin(a) > 0.3 else -1 if math.sin(a) < -0.3 else 0)), nm, INK)
    pos = (ctx.beat * 0.5) % len(names)
    a = pos / len(names) * 2 * math.pi
    paint(cv, Wd.disc(cv, cx + rx * math.cos(a), cy + ry * math.sin(a), 1.8), RED, "@", PAPER)
    fill_rect(cv, 54, 18, 106, 28, hexc("#1a1a20"))
    cv.put(58, 20, "NEXT  つぎは", hexc("#ffb03a"), bold=True)
    bmp = cv.text_bitmap("日常", 4, True)
    cv.shape_field(bmp, 66, 23, hexc("#ffb03a"))
    cv.put(86, 24, f"LAP {int(ctx.beat / 24) + 1}", PAPER)
    return fin_d(cv, ctx, 0.6)


def _mini(kind, cv, ctx, x0, y0, x1, y1):
    if kind == "room":
        fill_rect(cv, x0, y0, x1, y1, hexc("#1c1e27"))
        Wd.window_frame(cv, x0 + 3, y0 + 1, x0 + 16, y0 + 6, GREY, sill=False)
        cv.line(x0, y1 - 3, x1, y1 - 3, GREY, "=")
        cv.put(x0 + 18, y1 - 4, "[≡]", RED)
    elif kind == "station":
        fill_rect(cv, x0, y0, x1, y1, hexc("#22252e"))
        cv.line(x0, y1 - 3, x1, y1 - 3, hexc("#ffd84a"), "=")
        cv.put(x0 + 2, y0 + 1, "[==========]", WARM)
        cv.put(x0 + 6, y1 - 2, "o o  o", GREY)
    elif kind == "crossing":
        fill_rect(cv, x0, y0, x1, y1, hexc("#9aa4ae"))
        for k in range(5):
            fill_rect(cv, x0 + 2 + k * 6, y0 + 3, x0 + 4 + k * 6, y1 - 2, PAPER, " ")
        cv.put(x0 + 14, y0 + 5, "@", RED)
    elif kind == "arcade":
        fill_rect(cv, x0, y0, x1, y1, hexc("#120a1e"))
        cv.put(x0 + 3, y0 + 2, "GAME OVER", RED)
        cv.put(x0 + 3, y0 + 5, "(o.o)", Wd.NEON_M)
    elif kind == "hall":
        fill_rect(cv, x0, y0, x1, y1, hexc("#08080c"))
        cv.put(x0 + 3, y0 + 2, "[o] [o] [o]", hexc("#ffd84a"))
        cv.put(x0 + 3, y1 - 2, "(_)(_)(_)(_)", GREY)
    elif kind == "shrine":
        fill_rect(cv, x0, y0, x1, y1, hexc("#0d0b10"))
        cv.line(x0 + 3, y0 + 2, x1 - 3, y0 + 2, REDBG, "=", bold=True)
        cv.line(x0 + 6, y0 + 2, x0 + 6, y1, REDBG, "|")
        cv.line(x1 - 6, y0 + 2, x1 - 6, y1, REDBG, "|")
    elif kind == "laundry":
        fill_rect(cv, x0, y0, x1, y1, hexc("#dfe6ea"))
        for k in range(3):
            cv.put(x0 + 2 + k * 9, y0 + 3, "(@)", hexc("#5a7a9a"))
    elif kind == "us":
        fill_rect(cv, x0, y0, x1, y1, hexc("#2a0806"))
        bmp = cv.text_bitmap("YOU", 4, True)
        cv.shape_field(bmp, int((x0 + x1) / 2 - bmp.shape[1] / 2), int((y0 + y1) / 2 - 2), RED)
    if int(ctx.t * 2) % 2:
        cv.put(x1 - 6, y0 + 1, "●REC", RED)


def c_cctv(cv: Canvas, ctx: Ctx) -> Post:
    """You've noticed, haven't you?  A guard's room: a wall of security
    monitors showing every place she has been tonight -- her room, the
    platform, the crossing, the arcade, the hall -- and a camera in the
    corner slowly turns to look at us; the last monitor shows YOU."""
    t = ctx.t
    cv.clear(hexc("#0a0c10"), PAPER)
    kinds = ["room", "station", "crossing", "arcade", "hall", "shrine", "laundry", "station", "us"]
    u = ctx.u
    for i in range(9):
        r, c = i // 3, i % 3
        x0, y0 = 6 + c * 40, 2 + r * 12
        x1, y1 = x0 + 36, y0 + 10
        k = kinds[i] if not (i == 8 and u < 0.6) else "room"
        with Wd.clip(cv, x0 + 1, y0 + 1, x1 - 1, y1 - 1):
            _mini(k, cv, ctx, x0 + 1, y0 + 1, x1 - 1, y1 - 1)
        cv.box(x0, y0, x1, y1, GREY, "+=|", bold=True)
        cv.put(x0 + 1, y1, f"CAM-{i + 1:02d}", GREY)
    # scanlines over monitors
    sl = (cv.yy % 2 == 0) & (cv.xx < 126)
    cv.bg[sl] = cv.bg[sl] * 0.85
    # the camera turning
    a = -0.6 + 1.4 * ease(seg(u, 0.2, 0.7))
    fill_rect(cv, 130, 0, 159, 45, hexc("#14161c"))
    cv.line(150, 0, 150, 6, GREY, "|", bold=True)
    bx, by = 148, 9
    ex, ey = bx - 14 * math.cos(a), by + 6 * math.sin(a) + 3
    cv.line(bx, by, ex, ey, PAPER, "=", bold=True)
    cv.line(bx, by + 1, ex, ey + 1, PAPER, "=", bold=True)
    lens_col = RED if u > 0.6 else GREY
    paint(cv, Wd.disc(cv, ex, ey + 0.5, 2.2), lens_col, "@", PAPER)
    cv.put(132, 40, "SECURITY", GREY)
    p = fin_n(cv, ctx, 0.5)
    if u > 0.6:
        p.chroma = 2
    return p


def c_lightswitch(cv: Canvas, ctx: Ctx) -> Post:
    """Want to stop expecting.  Back in her room: the light switch by the door
    is pressed OFF on the beat and the room drops into darkness, leaving only
    the moonlit window."""
    b = beats_in(ctx)
    off = b >= 1.5
    room_night(cv, ctx, lamp=not off, lcd="03")
    if off:
        k = min(1.0, (b - 1.5) * 3)
        dark = ~Wd.rect(cv, 12, 2, 76, 20)
        cv.bg[dark] = mix(cv.bg[dark], INK, 0.75 * k)
        cv.fg[dark] = mix(cv.fg[dark], INK, 0.7 * k)
    # the switch plate (close, on the right)
    fill_rect(cv, 128, 12, 148, 32, hexc("#e8e4d8"), " ")
    cv.box(128, 12, 148, 32, GREY, "+-|", bold=True)
    fill_rect(cv, 134, 15 if not off else 22, 142, 21 if not off else 28, PAPER, "=", GREY)
    cv.put(131, 13, "ON", RED if not off else GREY, bold=True)
    cv.put(131, 30, "OFF", PAPER if off else GREY, bold=True)
    cv.put(116, 34, "期待  EXPECT", GREY if off else WARM)
    return fin_n(cv, ctx, 0.6)


def c_balloon(cv: Canvas, ctx: Ctx) -> Post:
    """How about up high?  At dawn a red balloon slips past the apartment
    windows -- curtains, a cat, a hanging shirt -- and keeps rising into the
    pale sky."""
    t = ctx.t
    u = ctx.u
    cv.clear(hexc("#e9d8c8"), INK)
    vgrad(cv, 0, 46, hexc("#b8cce0"), hexc("#f2d0b0"))
    scroll = 40 * ease(u)
    for f in range(-2, 6):
        y0 = f * 12 + scroll % 12 + (scroll // 12) * 0 - 6
        y0 = int(f * 12 + (scroll % 12)) - 6
        fill_rect(cv, 0, y0, 54, y0 + 11, hexc("#c9b8a6"), " ")
        fill_rect(cv, 106, y0, 160, y0 + 11, hexc("#b8a896"), " ")
        for x in (6, 116, 136):
            fill_rect(cv, x, y0 + 2, x + 14, y0 + 8, hexc("#3a3a44"), " ")
            cv.box(x, y0 + 2, x + 14, y0 + 8, PAPER, "+-|")
        idx = f - int(scroll // 12)
        if idx % 3 == 0:
            sprite(cv, "cat", 9, y0 + 3, PAPER)
        elif idx % 3 == 1:
            cv.put(119, y0 + 4, "(  ~~  )", hexc("#e36a4a"))
        cv.line(0, y0 + 10, 54, y0 + 10, GREY, "=")
        cv.line(106, y0 + 10, 160, y0 + 10, GREY, "=")
    x = 80 + 4 * math.sin(t * 1.3)
    y = 30 - 14 * u
    cv.line(x, y + 6, x + 2 * math.sin(t * 3), y + 16, INK, "|")
    paint(cv, Wd.disc(cv, x, y, 5), REDBG, "@", mix(REDBG, PAPER, 0.35))
    paint(cv, Wd.disc(cv, x - 1.5, y - 1.5, 1.2), mix(REDBG, PAPER, 0.6), " ")
    return fin_d(cv, ctx, 0.5)
