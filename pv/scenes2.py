"""Composed per-line scenes (v3): every lyric line is a small scene in one
world -- her room, the window and the city, the station, the night
streets, the stage, the Earth -- with a background, props and an action on
the beat.  Shot sizes vary (wide / medium / close-up) and the places recur,
so the PV tells a night's story: the message on the machine, the escape
into the city, sinking, and the way back to the framed Earth on her wall.

Rows 0-45 are picture, row 47 the Japanese line, rows 51-53 the Chinese
caption strip (render.py).
"""
from __future__ import annotations

import math

import numpy as np

from . import motifs as M
from . import shapes as S
from . import world as Wd
from .canvas import Canvas, hexc
from .palette import DAY, GREY, INK, NIGHT, PAPER, RED, Mode, mix
from .raster import Post
from .scenes import ease, ease_out, seg
from .shots import finish, beats_in, sym, solid, REDM, PIC_H
from .timeline import Ctx
from .world import (CONCRETE, NIGHT_SKY, NIGHT_SKY2, REDBG, REDDK, STEEL, TATAMI, WARM, WARM_DIM,
                    WOOD, fill_rect, paint, rect, sprite, vgrad)

WALL_N = hexc("#1c1e27")      # room wall at night
WALL_D = hexc("#d8d2c4")      # room wall by day
FLOOR_N = hexc("#2a2620")
DESK = hexc("#4a3a2c")


# ======================================================== the room (night)

def room_night(cv: Canvas, ctx: Ctx, pan: float = 0.0, lamp=False, machine_led=True,
               lcd="01", window_open=0.0, wall=WALL_N, sky_fn=None):
    """Wide shot of her room at night.  Returns key positions (cells)."""
    t = ctx.t
    p = -pan
    cv.clear(wall, PAPER)
    # floor
    fill_rect(cv, 0, 35, cv.W, PIC_H, FLOOR_N)
    Wd.tatami_floor(cv, 35, PIC_H, 80 + p, mix(FLOOR_N, PAPER, 0.18))
    cv.line(0, 35, cv.W, 35, mix(wall, PAPER, 0.3), "=")
    # window with the night city
    wx0, wy0, wx1, wy1 = 12 + p, 2, 76 + p, 20
    with Wd.clip(cv, wx0, wy0, wx1, wy1):
        if sky_fn:
            sky_fn(wx0, wy0, wx1, wy1)
        else:
            Wd.vgrad(cv, wy0, wy1, NIGHT_SKY, NIGHT_SKY2, wx0, wx1)
            S.stars(cv, t, 5, 0.02, PAPER, GREY)
            Wd.moon(cv, wx0 + 50, 7, 3.5, crescent=0.6)
            Wd.skyline(cv, wy1, 3, 4, 13, hexc("#101219"), lit=0.3, x0=wx0 - 5, x1=wx1 + 5, t=t,
                       scroll=p * 0.3)
            Wd.powerline(cv, wx0, wy0 + 8, wx1, wy0 + 6, 3, GREY, birds=2, t=t)
    Wd.window_frame(cv, wx0, wy0, wx1, wy1, mix(wall, PAPER, 0.55), mullions=(0.5,))
    if window_open > 0:
        # the right sash slides away
        cv.line(wx0 + (wx1 - wx0) * (0.5 + 0.45 * window_open), wy0, wx0 + (wx1 - wx0) * (0.5 + 0.45 * window_open),
                wy1, mix(wall, PAPER, 0.55), "|", bold=True)
    # moonlight on the floor
    ml = Wd.rect(cv, 0, 36, cv.W, PIC_H) & (np.abs((cv.xx - (30 + p)) - (cv.yy - 36) * 1.2) < 14)
    cv.bg[ml] = mix(FLOOR_N, PAPER, 0.12)
    # desk under the window
    dx0, dx1, dy = 16 + p, 72 + p, 30
    fill_rect(cv, dx0, dy, dx1, dy + 1, DESK, "=", mix(DESK, PAPER, 0.4))
    cv.line(dx0 + 2, dy + 2, dx0 + 2, 38, DESK, "|", bold=True)
    cv.line(dx1 - 2, dy + 2, dx1 - 2, 38, DESK, "|", bold=True)
    mx, my = dx0 + 4, dy - 5
    sprite(cv, "machine", mx, my, mix(wall, PAPER, 0.7),
           colors={"*": RED if machine_led and (ctx.beat_frac < 0.5) else REDDK})
    cv.put(int(mx) + 14, int(my) + 1, lcd, RED, bold=True)
    sprite(cv, "mug", dx1 - 12, dy - 6, mix(wall, PAPER, 0.6))
    sprite(cv, "lamp", dx0 + 28, dy - 6, WARM if lamp else mix(wall, PAPER, 0.5))
    # wall: clock, calendar, shelf
    hrs = 23 + 47 / 60 + (t - 38.0) / 3600 * 60
    Wd.wall_clock(cv, 99 + p, 8, 9, hrs, mix(wall, PAPER, 0.7), mix(wall, PAPER, 0.3), RED)
    Wd.calendar(cv, 88 + p, 18, 9, INK, REDBG)
    Wd.bookshelf(cv, 118 + p, 5, 32, 29, mix(wall, PAPER, 0.5), seed=2)
    Wd.sprite(cv, "plant", 126 + p, 1, mix(wall, hexc("#7fae6a"), 0.6))
    return {"machine": (mx, my), "desk": (dx0, dx1, dy), "window": (wx0, wy0, wx1, wy1)}


# ============================================================ VERSE 1

def v_machine(cv: Canvas, ctx: Ctx) -> Post:
    """Answering-machine service.  Wide: her dark room at night, the red light
    blinking on the desk; on beat 2 the PLAY key goes down, the lamp comes on
    and the machine's voice prints across the wall."""
    b = beats_in(ctx)
    played = b >= 1
    room_night(cv, ctx, pan=2 * ctx.u, lamp=played, lcd="01")
    if played:
        k = min(1.0, (b - 1) * 2)
        # cone of warm light from the desk lamp
        lx = 48 + 2 * ctx.u
        cone = (cv.yy >= 27) & (cv.yy <= 29) & (np.abs(cv.xx - lx) < 3 + (cv.yy - 26) * 5)
        cv.bg[cone] = mix(cv.bg[cone], WARM_DIM, 0.3 * k)
        wallglow = (np.hypot(cv.xx - lx, (cv.yy - 24) * 2.5) < 22) & (cv.yy < 27)
        cv.bg[wallglow] = mix(cv.bg[wallglow], WARM_DIM, 0.18 * k)
        msg = "> PLAYING MESSAGE 01 / 01  ..."
        n = int(len(msg) * min(1, (b - 1) / 1.5))
        cv.box(84, 34, 152, 38, RED, "+-|", fill=True, bg=REDDK)
        cv.put(86, 36, msg[:n], PAPER, bold=True)
    else:
        cv.box(84, 34, 152, 38, GREY, "+-|", fill=True, bg=INK)
        cv.put(86, 36, "( 1 )  NEW MESSAGE", RED, bold=True)
    return finish(cv, ctx, NIGHT, glow=0.18, hit=0.6)


def v_lowfreq(cv: Canvas, ctx: Ctx) -> Post:
    """The low hum recorded on the tape.  Close-up on the desk: the speaker
    grille throbs, rings run across the tea in her mug, the papers shiver."""
    low = ctx.feat("low")
    t = ctx.t
    cv.clear(WALL_N, PAPER)
    # window light falling on the wall
    for k in range(3):
        m = (np.abs(cv.xx - 100 - k * 12 + cv.yy * 0.6) < 4) & (cv.yy < 30)
        cv.bg[m] = mix(WALL_N, PAPER, 0.06)
    fill_rect(cv, 0, 30, cv.W, PIC_H, DESK, "=", mix(DESK, PAPER, 0.25))
    # the machine, big
    fill_rect(cv, 6, 6, 92, 31, hexc("#2b2d36"))
    cv.box(6, 6, 92, 31, mix(WALL_N, PAPER, 0.6), "+=|", bold=True)
    gx, gy = 30, 18
    S.ripple_rings(cv, gx, gy * cv.aspect, ctx.lt, 18, 2.6, mix(WALL_N, PAPER, 0.25 + 0.5 * low), "arc",
                   width=0.6, maxr=17 + 2 * low)
    Wd.paint(cv, Wd.disc(cv, gx, gy, 3 + 2 * low), RED, "@", PAPER)
    # LCD with the waveform
    fill_rect(cv, 56, 10, 88, 18, hexc("#0c1a12"))
    xs = np.arange(57, 88)
    ys = 14 + (2 + 3 * low) * np.sin(xs * 0.5 - t * 12) * np.sin(xs * 0.11 + t)
    cv.scatter(xs, ys, "~", fg=hexc("#5dff8a"))
    cv.put(57, 20, "REC  0:0" + str(int(ctx.lt * 3) % 10) + "  LOW FREQ", mix(WALL_N, PAPER, 0.6))
    cv.put(57, 23, "[<<] [>] [=] [DEL]", mix(WALL_N, PAPER, 0.55))
    # mug of tea with rings
    cx, cy = 124, 22
    fill_rect(cv, 108, 22, 140, 33, hexc("#d9d2c2"), "|", hexc("#b8b0a0"))
    cv.line(108, 22, 140, 22, INK, "=")
    cv.put(141, 25, ")", hexc("#d9d2c2"), bold=True)
    tea = (np.hypot((cv.xx - cx) / 1.0, (cv.yy - 20.5) * 3.6) < 16) & (cv.yy < 22.5)
    paint(cv, tea, hexc("#5a3b1e"), " ")
    rings = tea & (np.abs(((np.hypot(cv.xx - cx, (cv.yy - 20.5) * 3.6) - t * 20) % 5) - 2.5) < 0.8)
    cv.ch[rings] = cv.ids("~")[0]
    cv.fg[rings] = mix(hexc("#5a3b1e"), PAPER, 0.5 + 0.4 * low)
    # papers shivering on the desk
    for i in range(4):
        x = 100 + i * 12 + int(round(low * 2 * math.sin(t * 40 + i)))
        cv.put(x - 40, 34 + i % 2 * 2, "[========]", mix(PAPER, DESK, 0.3))
    return finish(cv, ctx, NIGHT, glow=0.18, hit=1.2)


def _city_day(cv: Canvas, ctx: Ctx, y1=24):
    Wd.vgrad(cv, 0, y1, hexc("#cfe0ec"), hexc("#f2ece0"))
    Wd.skyline(cv, y1, 11, 6, 18, hexc("#b5bccb"), win_on=hexc("#e8eef5"), lit=0.4, t=ctx.t,
               scroll=ctx.lt * 2, outline=hexc("#8a93a6"))
    Wd.skyline(cv, y1, 12, 3, 9, hexc("#8b93a3"), win_on=hexc("#c9d2e0"), lit=0.3, t=ctx.t,
               scroll=ctx.lt * 5, wmin=10, wmax=20)


def v_frontline(cv: Canvas, ctx: Ctx) -> Post:
    """The front line of everyday.  Wide, morning: an elevated platform at
    rush hour; ranks of commuters wait behind the red safety line; a train
    brakes into the station on the beat and the ranks surge."""
    u = ctx.u
    cv.clear(PAPER, INK)
    _city_day(cv, ctx, 22)
    for x in (10, 60, 110, 158):
        Wd.pole(cv, x, 22, 12, hexc("#6b7080"))
    Wd.powerline(cv, 10, 11, 60, 11, 2, hexc("#6b7080"))
    Wd.powerline(cv, 60, 11, 110, 11, 2, hexc("#6b7080"), birds=3, t=ctx.t)
    Wd.powerline(cv, 110, 11, 158, 11, 2, hexc("#6b7080"))
    # canopy
    fill_rect(cv, 0, 0, cv.W, 2, hexc("#3a3f4c"), "=", hexc("#6b7080"))
    for x in range(8, cv.W, 30):
        cv.line(x, 2, x, 30, hexc("#3a3f4c"), "|", bold=True)
    Wd.flapboard(cv, 52, 4, ["07:42  RAPID  for CITY", "07:44  LOCAL  for CITY"], hexc("#ffcf7a"), width=26)
    # train braking in
    arrive = ease_out(min(1.0, u * 1.6))
    Wd.train(cv, cv.W - 10 - 150 * arrive, 21, 4, INK, hexc("#c9ced6"), win=hexc("#6b7080"),
             lit=True)
    Wd.platform(cv, 32, INK, edge=REDBG)
    surge = 1.5 * ctx.pulse(5)
    for r, y in enumerate((35, 38, 41, 44)):
        Wd.walkers(cv, 0, 30 + r, 16, y - surge * (1 if r == 0 else 0.5), mix(INK, PAPER, 0.15 + 0.12 * r),
                   speed=0)
    cv.put(4, 33, "- - - - KEEP BEHIND THE LINE - - - -", PAPER, bold=True)
    return finish(cv, ctx, DAY, hit=0.8)


def v_where(cv: Canvas, ctx: Ctx) -> Post:
    """Where am I supposed to go?  Medium: the concourse departure board
    cannot settle -- every destination keeps flipping -- while arrows on the
    floor point every way and a small red marker (her) turns on the spot."""
    t = ctx.t
    cv.clear(hexc("#22252e"), PAPER)
    fill_rect(cv, 0, 30, cv.W, PIC_H, CONCRETE, ".", mix(CONCRETE, PAPER, 0.2))
    for x in range(0, cv.W, 20):
        cv.line(x, 30, x + (x - 80) * 0.6, PIC_H, mix(CONCRETE, PAPER, 0.25), None)
    rng = np.random.default_rng(int(beats_in(ctx) * 4))
    dests = ["CITY", "SEA", "HOME", "????", "NOWHERE", "NORTH", "AIRPORT", "THE MOON", "BACK"]
    rows = []
    for i in range(5):
        d = dests[int(rng.integers(0, len(dests)))]
        tm = f"{23 if i else 23}:{(47 + i * 3) % 60:02d}"
        rows.append(f"{tm}  {d:<9} {'--' if rng.random() < 0.5 else str(int(rng.integers(1, 9)))}")
    Wd.flapboard(cv, 36, 2, rows, WARM, width=40)
    cv.put(36, 14, "DEPARTURES   出発", mix(PAPER, INK, 0.3), bold=True)
    for i, (x, y, a) in enumerate(((20, 36, 0), (60, 40, 2), (110, 37, 1), (140, 42, 3), (34, 43, 2))):
        ar = "<<--" if (a + int(beats_in(ctx) * 2)) % 2 else "-->>"
        cv.put(x, y, ar, hexc("#ffcf3a"), bold=True)
    cv.box(2, 4, 28, 8, PAPER, "+-|", fill=True, bg=hexc("#2f5fa3"))
    cv.put(5, 6, "<- EXIT A  1 2", PAPER, bold=True)
    cv.box(130, 4, 157, 8, PAPER, "+-|", fill=True, bg=hexc("#2f5fa3"))
    cv.put(133, 6, "3 4  EXIT B ->", PAPER, bold=True)
    a = beats_in(ctx) * math.pi
    tri = [(80 + 3 * math.cos(a), 36 + 1.5 * math.sin(a)), (80 + 3 * math.cos(a + 2.4), 36 + 1.5 * math.sin(a + 2.4)),
           (80 + 3 * math.cos(a - 2.4), 36 + 1.5 * math.sin(a - 2.4))]
    from .shots import poly
    paint(cv, poly(cv, tri), RED, "#", PAPER)
    Wd.crowd_top(cv, ctx.lt, 9, 40, 0, 31, cv.W, 45, mix(CONCRETE, INK, 0.6), speed=14)
    return finish(cv, ctx, NIGHT, glow=0.18, hit=0.6)


def _corkboard(cv, ctx, x0, y0, x1, y1, n_notes, blow=0.0, window=None):
    fill_rect(cv, x0, y0, x1, y1, hexc("#7a5a3a"), ".", hexc("#9a7a52"))
    cv.box(x0, y0, x1, y1, hexc("#4a3424"), "+=|", bold=True)
    rng = np.random.default_rng(2)
    words = ["HA", "lol", "www", "HAHA", ":D", "w", "ha!", "(^o^)", "XD", "hehe"]
    cols = [hexc("#f2e27a"), hexc("#f7a6b8"), hexc("#9fdcf0"), hexc("#bff0a6")]
    for i in range(n_notes):
        w, h = 9, 4
        x = rng.uniform(x0 + 1, x1 - w - 1)
        y = rng.uniform(y0 + 1, y1 - h - 1)
        if blow > 0 and window is not None:
            delay = rng.uniform(0, 0.4)
            k = max(0.0, blow - delay) / (1 - 0.4)
            wx, wy = window
            e = ease(min(1.0, k * 1.4))
            x = x + (wx - x) * e - max(0.0, k - 0.6) * 160
            y = y + (wy - y) * e - max(0.0, k - 0.6) * 25 + 4 * math.sin(k * 9 + i) * (1 - e)
        col = cols[i % len(cols)]
        fill_rect(cv, x, y, x + w, y + h, col, " ")
        cv.put(int(x) + 1, int(y) + 1, words[i % len(words)], INK, bold=True)
        cv.put(int(x) + 4, int(y), "o", RED)


def v_jokes(cv: Canvas, ctx: Ctx) -> Post:
    """All the jokes she kept to herself.  Medium: the corkboard over her desk
    fills with sticky notes -- HA, lol, www -- a new one pinned on every
    half-beat until the board is buried."""
    room_night(cv, ctx, lamp=True, lcd="01")
    n = 2 + int(beats_in(ctx) * 4)
    _corkboard(cv, ctx, 84, 2, 152, 30, min(n, 40))
    cv.put(84, 33, f"NOTES  {min(n, 40):02d}", WARM, bold=True)
    return finish(cv, ctx, NIGHT, glow=0.18, hit=0.7)


def v_spit(cv: Canvas, ctx: Ctx) -> Post:
    """…and spat them all out at once.  The window flies open and every note
    tears off the board and streams out over the night city."""
    u = ctx.u
    room_night(cv, ctx, lamp=True, window_open=min(1, u * 4))
    _corkboard(cv, ctx, 84, 2, 152, 30, 40, blow=min(1.0, u * 1.2), window=(50, 8))
    p = finish(cv, ctx, NIGHT, 1.4)
    p.flash = 0.25 * max(0.0, 1 - ctx.lt * 5)
    return p


def v_shrug(cv: Canvas, ctx: Ctx) -> Post:
    """'Well, yeah.'  Medium: the TV in the dark room is showing a sitcom --
    a shrug on screen, the laugh track printed as captions -- the cat asleep
    on top of the set."""
    cv.clear(WALL_N, PAPER)
    fill_rect(cv, 0, 34, cv.W, PIC_H, FLOOR_N)
    tx, ty = 46, 6
    fill_rect(cv, tx - 4, ty - 2, tx + 72, ty + 28, hexc("#2b2d36"))
    cv.box(tx - 4, ty - 2, tx + 72, ty + 28, mix(WALL_N, PAPER, 0.6), "+=|", bold=True)
    fill_rect(cv, tx, ty, tx + 68, ty + 24, hexc("#bcd3e6"), " ")
    # the sitcom picture: a living-room set and a shrug
    fill_rect(cv, tx, ty + 17, tx + 68, ty + 24, hexc("#9a8a72"))
    cv.put(tx + 6, ty + 13, "[sofa=========]", hexc("#6a5a4a"))
    bmp = cv.text_bitmap("\\_(ツ)_/", 9, True)
    cv.shape_field(bmp, int(tx + 34 - bmp.shape[1] / 2), ty + 4 - int(ctx.pulse(6) * 1.5), INK)
    cv.put(tx + 20, ty + 22, "( LAUGHTER )" if int(ctx.lt * 4) % 2 else "( LAUGHTER ) ", INK, bold=True)
    sprite(cv, "cat_sleep", tx + 54, ty - 5, mix(WALL_N, PAPER, 0.75))
    # TV glow on the floor
    glow = (cv.yy > 34) & (np.abs(cv.xx - (tx + 34)) < (cv.yy - 30) * 4)
    cv.bg[glow] = mix(FLOOR_N, hexc("#bcd3e6"), 0.18)
    sprite(cv, "mug", 20, 36, mix(WALL_N, PAPER, 0.5))
    cv.put(118, 40, "remote [:::]", mix(WALL_N, PAPER, 0.45))
    return finish(cv, ctx, NIGHT, glow=0.18, hit=0.8)


def _train_interior(cv, ctx, window_fn):
    """Inside a night train: three windows (window_fn draws into each), seats,
    hanging straps, the door display."""
    t = ctx.t
    cv.clear(hexc("#c9c4b6"), INK)
    fill_rect(cv, 0, 0, cv.W, 3, hexc("#e8e4d8"), "-", hexc("#b8b2a4"))
    for i in range(6):
        cv.put(6 + i * 26, 4, "[ AD ]  " if i % 2 else "[ 広告 ]", hexc("#7a7468"))
    wins = [(6, 8, 50, 26), (58, 8, 102, 26), (110, 8, 154, 26)]
    for i, (x0, y0, x1, y1) in enumerate(wins):
        with Wd.clip(cv, x0, y0, x1, y1):
            window_fn(i, x0, y0, x1, y1)
        cv.box(x0, y0, x1, y1, hexc("#6b665a"), "+=|", bold=True)
    # straps swaying
    sway = math.sin(t * 3.3) * 2 + 1.5 * ctx.pulse(5)
    for x in range(12, cv.W, 14):
        cv.line(x, 3, x + sway * 0.3, 6, hexc("#6b665a"), "|")
        cv.put(int(x + sway * 0.4) - 1, 7, "( )", hexc("#3a3a3a"))
    # seats
    fill_rect(cv, 0, 30, cv.W, 35, hexc("#3a5a8a"), "=", hexc("#5a7aaa"))
    fill_rect(cv, 0, 36, cv.W, PIC_H, hexc("#8a8478"), ".", hexc("#a49e92"))
    cv.line(0, 29, cv.W, 29, hexc("#6b665a"), "-")


def _scenery(kind, cv, ctx, x0, y0, x1, y1, speed=60):
    t = ctx.t
    if kind == "city":
        Wd.vgrad(cv, y0, y1, NIGHT_SKY, NIGHT_SKY2, x0, x1)
        Wd.skyline(cv, y1, 21, 3, 14, hexc("#101219"), lit=0.4, scroll=t * speed, t=t)
        for k in range(4):
            xx = x1 - ((t * speed * 2 + k * 23) % (x1 - x0 + 10))
            cv.line(xx, y1 - 2, xx + 8, y1 - 2, WARM, "-")
    elif kind == "sea":
        Wd.vgrad(cv, y0, y1, hexc("#f2b48a"), hexc("#f7e2c2"), x0, x1)
        fill_rect(cv, x0, (y0 + y1) / 2 + 2, x1, y1, hexc("#3b6e9a"), "~", hexc("#7aa6c8"))
        Wd.paint(cv, Wd.disc(cv, (x0 + x1) / 2, (y0 + y1) / 2 + 1, 5) & (cv.yy < (y0 + y1) / 2 + 2), hexc("#ff7a3a"), "@", PAPER)
    elif kind == "tunnel":
        fill_rect(cv, x0, y0, x1, y1, INK)
        for k in range(5):
            xx = x1 - ((t * speed * 3 + k * 14) % (x1 - x0 + 4))
            cv.line(xx, y0 + 3, xx, y1 - 3, WARM, "|", bold=True)
    elif kind == "snow":
        fill_rect(cv, x0, y0, x1, y1, hexc("#c8d2dc"))
        fill_rect(cv, x0, y1 - 5, x1, y1, Wd.SNOW, "_", hexc("#aab4c0"))
        rng = np.random.default_rng(3)
        xs = rng.uniform(x0, x1, 40)
        ys = rng.uniform(y0, y1, 40)
        cv.scatter((xs - t * speed) % (x1 - x0) + x0, (ys + t * 6) % (y1 - y0) + y0, "*", fg=PAPER)
    elif kind == "field":
        Wd.vgrad(cv, y0, y1, hexc("#9fd0f0"), hexc("#e8f4fa"), x0, x1)
        fill_rect(cv, x0, (y0 + y1) / 2 + 3, x1, y1, hexc("#7fae4a"), "\"", hexc("#a6d070"))
        for k in range(3):
            xx = x1 - ((t * speed + k * 19) % (x1 - x0 + 6))
            Wd.pole(cv, xx, (y0 + y1) / 2 + 4, 7, hexc("#4a4a4a"))
    elif kind == "earth":
        fill_rect(cv, x0, y0, x1, y1, INK)
        S.stars(cv, t, 7, 0.05, PAPER, GREY)
        S.globe(cv, (x0 + x1) / 2, (y0 + y1) / 2 * cv.aspect, 13, t * 60, fg=PAPER, dim=GREY, accent=RED)


def v_nonstop(cv: Canvas, ctx: Ctx) -> Post:
    """Not stopping, even now.  Inside the last train: the city streaks past
    the windows, the straps swing, the door display scrolls."""
    _train_interior(cv, ctx, lambda i, *r: _scenery("city", cv, ctx, *r, speed=90))
    msg = "  NEXT >>>  NEXT >>>  NEXT >>>  DOES NOT STOP  "
    off = int(ctx.t * 14) % len(msg)
    fill_rect(cv, 60, 38, 100, 42, INK)
    cv.put(62, 40, (msg * 2)[off:off + 36], hexc("#ffb03a"), bold=True)
    return finish(cv, ctx, DAY, hit=0.8)


def v_changing(cv: Canvas, ctx: Ctx) -> Post:
    """Everything keeps changing.  The same three train windows -- now each one
    a picture frame -- flick to a different landscape twice a beat."""
    kinds = ["city", "sea", "tunnel", "snow", "field", "earth"]
    k = int(beats_in(ctx) * 2)

    def fn(i, *r):
        _scenery(kinds[(k + i * 2) % len(kinds)], cv, ctx, *r, speed=30)
    _train_interior(cv, ctx, fn)
    for i, (x0, y0, x1, y1) in enumerate([(6, 8, 50, 26), (58, 8, 102, 26), (110, 8, 154, 26)]):
        S.picture_frame(cv, x0 - 2, y0 - 1, x1 + 2, y1 + 1, hexc("#c8a040"), hexc("#7a6020"), style="simple",
                        depth=2)
    return finish(cv, ctx, DAY, hit=1.0)
