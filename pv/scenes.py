"""Scene functions. Each draws one frame: ``scene(cv, ctx) -> Post``.

Scenes are pure functions of ``ctx.t`` (plus the audio features), so frames
can be rendered in any order and in parallel.  Song-specific timings live in
``storyboard.py`` and reach the scenes through ``ctx.params``.
"""
from __future__ import annotations

import datetime as _dt
import math

import numpy as np

from . import lyricfx as L
from . import motifs as M
from . import shapes as S
from .canvas import Canvas
from .lrc import text_width
from .palette import DAY, DIM, FAINT, GREY, INK, NIGHT, PAPER, PAPER_DIM, RED, RED_DIM, Mode, mix
from .raster import Post
from .timeline import Ctx


# ------------------------------------------------------------------ helpers

def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def seg(t: float, a: float, b: float) -> float:
    return min(1.0, max(0.0, (t - a) / max(1e-6, b - a)))


def base(cv: Canvas, m: Mode) -> None:
    cv.clear(m.bg, m.fg)


def post_for(m: Mode, ctx: Ctx, **kw) -> Post:
    # (film grain is off by default: per-pixel noise triples the video bitrate)
    if m.paper:
        p = Post(glow=0.12, glow_radius=4, scan=0.05, vignette=0.32, grain=0.0)
    else:
        p = Post(glow=0.6, glow_radius=5, scan=0.10, vignette=0.38, grain=0.0)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def beat_hit(p: Post, ctx: Ctx, amount: float = 1.0) -> Post:
    """Camera shake + chroma split on beats, scaled by kick energy."""
    pl = ctx.pulse(9.0) * amount * (0.4 + ctx.feat("low"))
    if pl > 0.15:
        rng = ctx.rng(ctx.beat_i, 5)
        p.shake = (int(rng.integers(-4, 5) * pl), int(rng.integers(-3, 4) * pl))
        p.chroma = int(round(3 * pl))
    return p


def flip_mode(ctx: Ctx, every: str = "beat", start_paper=False) -> Mode:
    k = ctx.beat_i if every == "beat" else int(math.floor(ctx.bar + 1e-6))
    return DAY if ((k % 2 == 0) ^ (not start_paper)) else NIGHT


def bottom_lyric(cv: Canvas, ctx: Ctx, m: Mode, y: int | None = None, band=True):
    y = cv.H - 4 if y is None else y
    L.subtitle(cv, ctx, ctx.line(), y, m.fg, m.accent, m.mid, band=m.bg if band else None)


def reveal_by_angle(cv: Canvas, before, frac: float, cx=None, cy=None):
    """Keep only the part of what was drawn since ``before`` (a snapshot)
    whose angle around the centre is < frac * 360deg (clockwise from top-left)."""
    cx = cv.W / 2 if cx is None else cx
    cy = cv.H / 2 if cy is None else cy
    a_tl = math.atan2((0 - cy) * cv.aspect, 0 - cx)
    ang = ((np.arctan2((cv.yy - cy) * cv.aspect, cv.xx - cx) - a_tl) % (2 * math.pi)) / (2 * math.pi)
    hide = ang > frac
    ch, fg, bg = before
    cv.ch[hide] = ch[hide]
    cv.fg[hide] = fg[hide]
    cv.bg[hide] = bg[hide]


# ===================================================================== INTRO

def intro_signal(cv: Canvas, ctx: Ctx) -> Post:
    """Guitar riff alone: a lone signal line, an answering-machine HUD, and the
    picture frame (額縁) drawing itself around the screen."""
    m = NIGHT
    base(cv, m)
    t = ctx.t
    P = ctx.params
    t_line, t_frame0, t_frame1, t_build, t_end = P["line"], P["frame0"], P["frame1"], P["build"], ctx.t1
    mid, onset, high = ctx.feat("mid"), ctx.feat("onset"), ctx.feat("high")
    build = seg(t, t_build, t_end)

    # HUD
    on = ctx.beat_frac < 0.5
    cv.put(4, 2, "(*) REC" if on else "( ) REC", m.accent if on else m.low, bold=True)
    ff = int((t % 1) * 30)
    cv.put(cv.W - 15, 2, f"{int(t // 60):02d}:{int(t % 60):02d}:{ff:02d}", m.mid)
    cv.put(4, cv.H - 3, "CH-1   LOW FREQ", m.low)
    cv.put(cv.W - 17, cv.H - 3, "MESSAGE  01/01", m.low)

    cy = cv.H / 2
    if t < t_line:
        if (t * 2) % 1 < 0.55:
            cv.put(cv.W // 2, int(cy), "_", m.fg, bold=True)
    else:
        rev = int(cv.W * ease_out(seg(t, t_line, t_line + 1.6)))
        amp = 1.6 + 4.0 * mid + 4.0 * onset * (0.3 + build) + 14 * build ** 2
        wl = 46 - 30 * seg(t, t_line, t_end)
        jit = None
        if build > 0:
            rng = ctx.rng(ctx.frame, 1)
            jit = rng.normal(0, build * 2.5, cv.W)
        M.wave_line(cv, cy, amp * 0.45, wl * 1.9, t, -0.15, m.low, 0, rev)
        M.wave_line(cv, cy, amp, wl, t, 0.35, m.fg, 0, rev, jitter=jit)
        # little tick marks like an oscilloscope graticule
        for x in range(0, cv.W, 10):
            cv.put(x, int(cy) + 9, "+", m.faint)
            cv.put(x, int(cy) - 9, "+", m.faint)

    # the frame draws itself clockwise
    if t >= t_frame0:
        snap = cv.snapshot()
        S.picture_frame(cv, 1, 4, cv.W - 2, cv.H - 5, m.fg, m.mid, style="gilded", depth=3, hl=m.fg)
        reveal_by_angle(cv, snap, ease(seg(t, t_frame0, t_frame1)))

    p = post_for(m, ctx)
    if build > 0:
        rng = ctx.rng(ctx.frame, 2)
        S.char_noise(cv, rng, 0.25 * build ** 2, fg=m.mid)
        S.glitch_rows(cv, rng, build, 10)
        p.chroma = int(4 * build * (0.5 + high))
        p.flash = 0.25 * max(0.0, 1 - abs(t - P.get("kick", -9)) * 8)
    return p


def title(cv: Canvas, ctx: Ctx) -> Post:
    """Band comes in: the title inside a gilded frame, the Earth turning behind."""
    m = NIGHT
    base(cv, m)
    t, P = ctx.t, ctx.params
    u = ctx.u
    # Earth behind, very dim
    S.globe(cv, cv.WU / 2, cv.HU / 2 + 4, 52 + 6 * u, lon0=100 - 18 * ctx.lt, tilt=0.4,
            fg=FAINT * 1.6, dim=FAINT, land_chars=".:+", sea_chars="  ", rim_char=".", grid=False)
    grow = ease(seg(t, P["grow"], ctx.t1)) * 0.25
    fx0, fy0 = 12 - 12 * grow, 3 - 3 * grow
    fx1, fy1 = cv.W - 13 + 12 * grow, cv.H - 4 + 3 * grow
    S.picture_frame(cv, fx0, fy0, fx1, fy1, m.fg, m.mid, style="gilded", hl=m.fg,
                    bg=m.bg, clear_inside=True)
    # title assembles on the beats of the first bar (two lines of big glyphs)
    ttl = P["title"]
    n = len(ttl)
    shown = int(min(n, max(0, (ctx.beat - ctx.grid.beat_pos(ctx.t0)) * 2 + 1)))
    rng = ctx.rng(ctx.frame)
    txt = "".join(c if i < shown else ttl[int(rng.integers(0, n))] for i, c in enumerate(ttl))
    sp = P.get("split", n)
    for li, (part, cy) in enumerate(((txt[:sp], 13), (txt[sp:], 28))):
        if not part:
            continue
        col = m.fg
        x = cv.W / 2
        bb = L.big_layout(cv, part, 13, cv.W - 40)
        rows, bmps, total = bb
        xx = int(x - total / 2)
        for j, bm in enumerate(bmps):
            gi = j + (0 if li == 0 else sp)
            c_col = m.accent if gi == shown - 1 and shown < n else (m.mid if gi >= shown else col)
            cv.shape_field(bm, xx, int(cy - rows / 2), c_col, bold=True)
            xx += bm.shape[1] + 1
    # subtitle romanisation
    rom = P.get("romaji", "")
    k = int(len(rom) * ease(seg(t, ctx.t0 + 0.6, ctx.t0 + 2.6)))
    cv.put_center(37, " ".join(rom[:k]), m.mid)
    if t > P["credit"]:
        cv.put_center(41, P["artist"], m.fg, bold=True)
    if t > P["credit"] + 1.6:
        cv.put_center(43, P["credit_text"], m.mid)
    # downbeat inversion pulse of the frame ornaments
    bp = ctx.bar_pulse(6)
    if bp > 0.5:
        cv.put(int((fx0 + fx1) / 2) - 2, int(fy0), "<@@>", m.accent, bold=True)
        cv.put(int((fx0 + fx1) / 2) - 2, int(fy1), "<@@>", m.accent, bold=True)
    p = beat_hit(post_for(m, ctx), ctx, 0.6)
    p.flash = 0.35 * max(0.0, 1 - (t - ctx.t0) * 4)
    if t > ctx.t1 - 0.8:
        S.char_noise(cv, ctx.rng(ctx.frame), seg(t, ctx.t1 - 0.8, ctx.t1) * 0.4)
    return p


def globe_intro(cv: Canvas, ctx: Ctx) -> Post:
    """The Earth, frames emanating from it, the title orbiting as a ring."""
    m = NIGHT
    base(cv, m)
    t = ctx.t
    S.stars(cv, t, 11, 0.012, m.mid, m.low)
    zoom = seg(t, ctx.params["zoom"], ctx.t1)
    R = 30 + 6 * ctx.u + 160 * zoom ** 3 + 2.0 * ctx.pulse(8)
    cx, cy = cv.WU / 2, cv.HU / 2
    M.frame_tunnel(cv, t, (ctx.bar % 1.0) * 1.0, m.fg, m.mid, m.low, n=5, ratio=0.7,
                   aspect_hw=(cv.W * 0.95, cv.H * 0.95), style="gilded")
    # clear a disc behind the globe so frames don't overlap it
    disc = np.hypot(cv.X - cx, cv.Y - cy) < R + 3
    cv.ch[disc] = 0
    lon = 140 - 26 * ctx.lt - 8 * ctx.beat_i % 3
    S.globe(cv, cx, cy, R, lon, tilt=0.38, fg=m.fg, dim=m.low, accent=m.accent)
    # orbiting ring of text
    ring = ctx.params["ring"]
    n = len(ring)
    a = np.arange(n) / n * 2 * math.pi + t * 0.55
    rx, ry = R + 12, (R + 12) * 0.32
    xs = cx + rx * np.cos(a)
    ys = cy + ry * np.sin(a) - 4
    front = np.sin(a) > 0
    ids = cv.ids(ring)
    behind = ~front & (np.hypot(xs - cx, ys - cy) < R)
    vis = ~behind
    cv.scatter(xs[vis & ~front], ys[vis & ~front] / cv.aspect, ids[vis & ~front], fg=m.low)
    cv.scatter(xs[front], ys[front] / cv.aspect, ids[front], fg=m.fg)
    p = beat_hit(post_for(m, ctx), ctx, 0.8)
    p.flash = 0.9 * seg(t, ctx.t1 - 0.35, ctx.t1) ** 2
    return p


# ===================================================================== VERSE

def phone(cv: Canvas, ctx: Ctx) -> Post:
    """Verse 1: an answering machine replays the message; the low-frequency
    wave carries the lyric transcript."""
    m = DAY
    base(cv, m)
    t, P = ctx.t, ctx.params
    low = ctx.feat("low")
    led = ctx.beat_frac < 0.5
    chaos = seg(t, P["chaos"], P["chaos"] + 0.2) if t < ctx.t1 else 0
    count = "01" if t < P["chaos"] else f"{(ctx.frame * 7) % 100:02d}"
    info = M.answering_machine(cv, 6, 15, 62, 28, m.fg, m.mid, m.accent, t, led, count,
                               spin=t * 3.0)
    # wave out of the speaker
    M.wave_line(cv, 46.5, 0.6 + 2.2 * low, 26, t, 0.6, m.mid, 8, cv.W - 2)
    M.wave_line(cv, 48.5, 0.4 + 1.0 * low, 52, t, 0.25, m.low, 8, cv.W - 2)
    # transcript
    lx0, ly0, lx1, ly1 = 76, 3, cv.W - 5, 22
    cv.box(lx0, ly0, lx1, ly1, m.fg, "+-|")
    cv.put(lx0 + 2, ly0, " MESSAGE 01 / TRANSCRIPT ", m.fg, bold=True)
    lines = ctx.lines_between(ctx.t0, ctx.t1)
    L.log_box(cv, ctx, lines, lx0 + 3, ly0 + 2, lx1 - 2, ly1 - 2, m.fg, m.mid, m.accent)
    cur = ctx.line()
    if cur is not None:
        L.big(cv, ctx, cur, 32, 10, m.fg, m.accent, cx=(lx0 + lx1) / 2, max_w=lx1 - lx0)
    # the burst of stored-up jokes
    b0, b1 = P["burst"]
    if b0 <= t < b1 + 1.6:
        rng = np.random.default_rng(42)
        n = 140
        tb = rng.uniform(b0, b1, n)
        vx = rng.uniform(18, 70, n)
        vy = rng.normal(-6, 9, n)
        age = t - tb
        live = (age > 0) & (age < 1.6)
        sx, sy = info["speaker"]
        xs = sx + vx * age
        ys = sy + (vy * age + 14 * age * age) / cv.aspect
        words = "HAHAhaha!!??wwwW"
        ids = cv.ids(words)
        cv.scatter(xs[live], ys[live], ids[np.arange(n)[live] % len(ids)], fg=m.fg)
        cv.scatter(xs[live & (np.arange(n) % 5 == 0)], ys[live & (np.arange(n) % 5 == 0)], "!", fg=m.accent)
    p = post_for(m, ctx)
    if t >= P["chaos"]:
        rng = ctx.rng(ctx.beat_i, 9)
        if ctx.beat_i % 2 == 1:
            S.invert(cv)
        S.glitch_rows(cv, ctx.rng(ctx.frame, 3), 0.25 + 0.6 * ctx.pulse(6), 14)
        S.char_noise(cv, rng, 0.02 * ctx.pulse(5))
        p = beat_hit(p, ctx, 1.0)
    return p


def room_scene(cv: Canvas, ctx: Ctx) -> Post:
    """Verse 2: a sooty four-and-a-half-mat room; the narrator hugs her knees."""
    m = DAY
    sootbg = mix(PAPER, GREY, 0.18)
    cv.clear(sootbg, m.fg)
    t, P = ctx.t, ctx.params
    vp = (0, 0, cv.W - 1, cv.H - 1)
    info = M.room(cv, vp, m.fg, m.mid, mix(sootbg, INK, 0.3), t=t, frame_globe_lon=None,
                  night_window=False)
    fy = info["floor_y"]
    # radio + ultrasound rings
    u0, u1 = P["ultra"]
    rx, ry = 44, int(fy + 9)
    cv.put(rx - 3, ry - 1, ".-^-.", m.fg)
    cv.put(rx - 3, ry, "[o_o]", m.fg, bold=True)
    if u0 <= t < u1 + 0.6:
        k = 1 - seg(t, u1, u1 + 0.6)
        S.ripple_rings(cv, rx, ry * cv.aspect, t, 30, 5.0, mix(sootbg, INK, 0.15 + 0.45 * k), "arc",
                       width=0.4, maxr=8 + 34 * seg(t, u0, u1))
        cv.put(rx - 3, ry, "[o_o]", m.accent, bold=True)
    # mocking laughter scribbled on the walls, one more per beat
    w0, w1 = P["laugh"]
    if t >= w0:
        b0 = int(math.floor(ctx.grid.beat_pos(w0)))
        b1 = int(math.floor(ctx.beat))
        for b in range(b0, min(b1, b0 + 40) + 1):
            rng = np.random.default_rng(b * 13 + 5)
            x = int(rng.integers(4, cv.W - 30))
            y = int(rng.integers(2, int(fy) - 2))
            s = "w" * int(rng.integers(3, 9))
            fresh = b == b1
            cv.put(x, y, s, m.accent if fresh else m.mid, bold=fresh)
    # cut-out squares (切り取った正解) stamped OK on each beat
    c0 = P["cut"]
    if t >= c0:
        b0 = int(math.floor(ctx.grid.beat_pos(c0)))
        b1 = int(math.floor(ctx.beat))
        for b in range(b0, b1 + 1):
            rng = np.random.default_rng(b * 7 + 1)
            w, h = int(rng.integers(10, 18)), int(rng.integers(4, 7))
            x = int(rng.integers(30, cv.W - 40))
            y = int(rng.integers(3, int(fy) - h - 1))
            cv.box(x, y, x + w, y + h, m.fg, "+- ", fill=True, bg=sootbg)
            cv.line(x, y, x + w, y, m.fg, "-")
            for yy in range(y + 1, y + h, 2):
                cv.put(x, yy, ":", m.fg)
                cv.put(x + w, yy, ":", m.fg)
            cv.put(x - 3, y, "8<", m.mid)
            cv.put(x + w // 2 - 1, y + h // 2, "OK", m.accent if b == b1 else m.fg, bold=True)
    # narrator
    S.figure(cv, 106, (cv.H - 4) * cv.aspect, 74, "sit", ph=t * 0.25, fg=m.fg)
    M.soot(cv, t, 3, 260, mix(sootbg, INK, 0.45))
    # mirror the whole room on alternate beats ("wrong truths, right lies")
    f0, f1 = P["mirror"]
    if f0 <= t < f1 and ctx.beat_i % 2 == 1:
        cv.ch[:] = cv.ch[:, ::-1]
        cv.fg[:] = cv.fg[:, ::-1]
        cv.bg[:] = cv.bg[:, ::-1]
        swap = {"/": "\\", "\\": "/", "(": ")", ")": "(", "<": ">", ">": "<", "[": "]", "]": "["}
        for a, b in swap.items():
            ia, ib = cv.ids(a)[0], cv.ids(b)[0]
            ma = cv.ch == ia
            cv.ch[cv.ch == ib] = ia
            cv.ch[ma] = ib
    # lyrics, written vertically (tategaki) down the right side
    cur = ctx.line()
    prev = [ln for ln in ctx.lines_between(ctx.t0, t) if ln is not cur][-1:]
    for ln in prev:
        cv.put(cv.W - 8, 4, "", m.mid)
        for i, c in enumerate(ln.text):
            cv.put(cv.W - 9, 4 + i, {"ー": "|"}.get(c, c), m.mid)
    if cur is not None:
        L.vertical(cv, ctx, cur, cv.W - 5, 4, m.fg, m.accent, m.mid)
    return post_for(m, ctx, vignette=0.45)


# ================================================================ PRE-CHORUS

def night_away(cv: Canvas, ctx: Ctx) -> Post:
    """Pre-chorus 1: the room recedes into a small frame in the dark; then
    colour drains away and the picture sways."""
    t, P = ctx.t, ctx.params
    grey = t >= P["grey"]
    m = NIGHT
    base(cv, m)
    S.stars(cv, t, 21, 0.004 + 0.02 * seg(t, P["dark"], P["dark"] + 2.5), m.fg if not grey else m.mid,
            m.low, twinkle=0 if grey else 1.5)
    s = 1 - 0.72 * ease_out(seg(t, ctx.t0, ctx.t0 + 2.4))
    drift = 4 * math.sin(t * 0.7) * seg(t, P["dark"], ctx.t1)
    cx, cy = cv.W / 2 + drift, cv.H / 2 - 2
    hw, hh = (cv.W / 2) * s, (cv.H / 2) * s
    x0, y0, x1, y1 = cx - hw, cy - hh, cx + hw, cy + hh
    pap = PAPER if not grey else mix(PAPER, GREY, 0.55)
    ink = INK
    ys, xs = slice(max(0, int(y0)), min(cv.H, int(y1) + 1)), slice(max(0, int(x0)), min(cv.W, int(x1) + 1))
    cv.ch[ys, xs] = 0
    cv.bg[ys, xs] = pap
    if not (grey and t >= P["empty"]):
        sub = (x0 + 2, y0 + 1, x1 - 2, y1 - 1)
        M.room(cv, sub, ink, mix(pap, ink, 0.6), mix(pap, ink, 0.3), t=t, window=s > 0.5,
               tatami=s > 0.4, wall_frame=s > 0.35)
        if s < 0.99:
            S.figure(cv, cx + hw * 0.3, (cy + hh * 0.78) * cv.aspect, 40 * s * 1.6, "sit", fg=ink)
    S.picture_frame(cv, x0 - 4, y0 - 2, x1 + 4, y1 + 2, m.fg if not grey else m.mid, m.mid,
                    style="gilded" if s > 0.4 else "simple", depth=3 if s > 0.4 else 2,
                    hl=m.fg if not grey else m.mid)
    if grey:
        cv.fg[:] = mix(cv.fg, GREY, 0.6)
    # sway: rows shifted by a slow sine ("staggering on purpose")
    w = seg(t, P["sway"], P["sway"] + 0.6)
    if w > 0:
        for y in range(cv.H):
            k = int(round(w * 5 * math.sin(y * 0.18 + t * 3.1)))
            if k:
                cv.ch[y] = np.roll(cv.ch[y], k)
                cv.fg[y] = np.roll(cv.fg[y], k, axis=0)
                cv.bg[y] = np.roll(cv.bg[y], k, axis=0)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, cv.H - 7, 9, m.fg if not grey else m.mid, m.accent if not grey else m.fg,
              max_w=cv.W - 12)
    p = post_for(m, ctx)
    p.fade = 1 - 0.18 * seg(t, P["dark"], P["dark"] + 2)
    return p


def sink(cv: Canvas, ctx: Ctx) -> Post:
    """Pre-chorus 2: walking away, sinking, question marks, the too-clean room,
    and the stop before the chorus."""
    t, P = ctx.t, ctx.params
    a, b, c, d = P["away"], P["sink"], P["ask"], P["clean"]
    if t < b:  # ---- walking away towards the horizon
        m = NIGHT
        base(cv, m)
        S.stars(cv, t, 31, 0.02, m.fg, m.low)
        hz = 22
        cv.line(0, hz, cv.W, hz, m.mid, "_")
        for k in range(-8, 9):
            cv.line(cv.W / 2 + k * 2, hz + 1, cv.W / 2 + k * 26, cv.H, m.faint, None)
        u = seg(t, a, b)
        sc = 1 - 0.8 * ease(u)
        fy = (hz + (cv.H - 4 - hz) * sc) * cv.aspect
        S.figure(cv, cv.W / 2 + 6 * sc, fy, 70 * sc, "walk", ph=ctx.beat * 0.5, fg=m.fg, flip=True)
        p = post_for(m, ctx)
    elif t < c:  # ---- sinking
        m = NIGHT
        base(cv, m)
        u = seg(t, b, c)
        water = mix(INK, hexmix(0.06), 1.0)
        cv.bg[:] = water
        for yy in range(0, cv.H, 3):
            M.wave_line(cv, yy + 1, 0.5, 30, t, 0.15 + yy * 0.003, m.faint, 0, cv.W)
        M.wave_line(cv, 3 - 5 * u, 1.0, 22, t, 0.5, m.fg)
        M.bubbles(cv, t, 41, 70, m.mid)
        fy = (24 + 26 * ease(u)) * cv.aspect
        S.figure(cv, cv.W / 2 + 3 * math.sin(t), fy, 46, "stand", fg=m.fg)
        M.bubbles(cv, t * 1.5, 43, 12, m.fg, "oO")
        p = post_for(m, ctx, glow=0.7)
    elif t < d:  # ---- question marks
        m = NIGHT
        base(cv, m)
        rng = np.random.default_rng(5)
        n = 90
        xs = rng.uniform(0, cv.W, n)
        ys = (rng.uniform(0, cv.H, n) + (t - c) * rng.uniform(2, 7, n)) % cv.H
        cv.scatter(xs, ys, "?", fg=m.mid)
        k = int((t - c) / 0.4)
        for i in range(min(k, 6)):
            r2 = np.random.default_rng(100 + i)
            cv.big_text("?", float(r2.uniform(15, cv.W - 15)), float(r2.uniform(8, cv.H - 12)),
                        int(r2.integers(8, 16)), fill="?", fg=m.low if i < k - 1 else m.fg)
        S.figure(cv, cv.W / 2, 44 * cv.aspect, 50, "stand", fg=m.fg)
        p = post_for(m, ctx)
    else:  # ---- the clean, pointlessly beautiful room + the stop
        m = DAY
        base(cv, m)
        M.room(cv, (0, 0, cv.W - 1, cv.H - 1), m.fg, m.mid, m.faint, t=t, tatami=True,
               window=True, wall_frame=True, night_window=False)
        S.figure(cv, cv.W / 2 + 24, 49 * cv.aspect, 52, "stand", fg=m.fg)
        p = post_for(m, ctx, vignette=0.2)
        stop = P["stop"]
        if t >= stop:
            on = ctx.feat("onset")
            if on > 0.8:
                S.invert(cv)
                S.glitch_rows(cv, ctx.rng(ctx.frame), 0.8, 20)
            p.fade = 1 - 0.3 * seg(t, stop, ctx.t1)
    ln = ctx.line()
    mm = DAY if t >= d else NIGHT
    bottom_lyric(cv, ctx, mm, y=cv.H - 4)
    return p


def hexmix(k):
    return mix(INK, PAPER, k)


# ==================================================================== CHORUS

def chorus_fx(cv: Canvas, ctx: Ctx, p: Post, invert_downbeat=True) -> Post:
    p = beat_hit(p, ctx, 1.0)
    if invert_downbeat and 0 <= ctx.since_bar < 1.5 / ctx.fps:   # one inverted frame per bar
        S.invert(cv)
    return p


def big_lyric(cv: Canvas, ctx: Ctx) -> Post:
    """Big ASCII-art lyric over a beat-flipped background pattern."""
    P = ctx.params
    style = P.get("bg", "frames")
    m = flip_mode(ctx, "beat", P.get("paper_first", False)) if P.get("flip", True) else (DAY if P.get("paper") else NIGHT)
    base(cv, m)
    t = ctx.t
    if style == "frames":
        M.frame_tunnel(cv, t, ctx.beat_frac, m.mid, m.low, m.faint, n=6, ratio=0.72, style="simple")
    elif style == "rays":
        ang = np.arctan2((cv.yy - cv.H / 2) * cv.aspect, cv.xx - cv.W / 2)
        k = ((ang / (2 * math.pi) * 24 + t * 0.6) % 1) < 0.18
        cv.fill(k, ".", fg=m.low)
    elif style == "dots":
        mk = ((cv.xx.astype(int) + cv.yy.astype(int) * 2 + ctx.beat_i) % 6 == 0)
        cv.fill(mk, ".", fg=m.low)
    elif style == "pain":  # jagged lines for 痛い
        rng = ctx.rng(ctx.beat_i, 3)
        for _ in range(9):
            x = rng.uniform(0, cv.W)
            y = rng.uniform(0, cv.H)
            pts = [(x + rng.uniform(-20, 20), y + rng.uniform(-6, 6)) for _ in range(4)]
            cv.polyline(pts, m.accent if _ % 3 == 0 else m.low)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, cv.H / 2 - 1, P.get("rows", 12), m.fg, m.accent,
              pop=0.25)
        # small echo of the line in a corner, like a caption
        cv.put(3, cv.H - 3, f"{ln.index + 1:02d}  " + ln.text, m.mid)
    p = chorus_fx(cv, ctx, post_for(m, ctx), invert_downbeat=False)
    return p


def spotlight_break(cv: Canvas, ctx: Ctx) -> Post:
    """A spotlight on the narrator -- smashed on the beat."""
    t, P = ctx.t, ctx.params
    tb = P["break"]
    m = NIGHT
    base(cv, m)
    S.stars(cv, t, 61, 0.006, m.low, m.faint)
    stage_y = cv.H - 8
    cx = cv.W / 2

    def draw_light(tt: float):
        rng = ctx.rng(int(tt * 30), 4)
        inten = 0.75 + 0.25 * math.sin(tt * 40) if tt > tb - 0.6 else 1.0
        M.lamp(cv, cx, 1, m.fg, m.mid)
        M.spotlight(cv, cx, 3, stage_y, 26, m.fg, intensity=inten, flicker=0.3, rng=rng)
        cv.line(10, stage_y + 1, cv.W - 10, stage_y + 1, m.fg, "=")

    if t < tb:
        draw_light(t)
        S.figure(cv, cx, (stage_y + 0.5) * cv.aspect, 50, "stand", fg=m.fg, fill="@", edge="#")
        p = post_for(m, ctx, glow=0.8)
    else:
        # freeze the light at break time, then explode it
        tmp = cv.snapshot()
        cv.ch[:] = 0
        draw_light(tb)
        snap = cv.snapshot()
        cv.restore(tmp)
        M.shatter(cv, snap, t - tb, (cx, stage_y - 10), seed=7, speed=48, gravity=70)
        S.figure(cv, cx, (stage_y + 0.5) * cv.aspect, 50, "stand", fg=m.accent, fill="#", edge="+")
        p = post_for(m, ctx)
        k = max(0.0, 1 - (t - tb) * 5)
        p.flash = 0.6 * k
        p.chroma = int(6 * k)
        if k > 0:
            p.shake = (int(6 * k * (1 if ctx.frame % 2 else -1)), int(3 * k))
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, 6, 9, m.fg, m.accent, max_w=cv.W - 24)
    return chorus_fx(cv, ctx, p, invert_downbeat=False)


def rise(cv: Canvas, ctx: Ctx) -> Post:
    """'Up, up high!' -- lifted upward through streaming speed lines."""
    t = ctx.t
    m = flip_mode(ctx, "beat")
    base(cv, m)
    M.speed_lines(cv, t, 71, 120, 70, m.mid, "|:'.", direction=1, length=8)
    u = ctx.u
    fy = (cv.H + 20 - (cv.H + 40) * ease(u)) * cv.aspect
    S.figure(cv, cv.W / 2 + 24, fy, 52, "stand", fg=m.fg)
    for k in range(5):
        y = int((cv.H - ((t * 30 + k * 11) % (cv.H + 6))))
        cv.put(cv.W // 2 - 40, y, "/\\", m.accent)
        cv.put(cv.W // 2 - 41, y + 1, "/  \\", m.accent)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, cv.H / 2 - 4 - 6 * ease(u), 10, m.fg, m.accent,
              max_w=cv.W - 10, pop=0.4)
    return chorus_fx(cv, ctx, post_for(m, ctx), invert_downbeat=False)


def globe_run(cv: Canvas, ctx: Ctx) -> Post:
    """Nowhere to run: she runs on top of the Earth, which just turns under her."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    S.stars(cv, t, 81, 0.02, m.fg, m.low, drift=(-6, 0))
    pull = ease(seg(t, P.get("pull", ctx.t1 + 1), ctx.t1))  # optional pull-back at the end
    R = 74 * (1 - pull) + 26 * pull
    cy = (cv.HU + R * 0.52) * (1 - pull) + (cv.HU / 2 + 6) * pull
    lon = 30 - 55 * ctx.lt
    S.globe(cv, cv.WU / 2, cy, R, lon, tilt=0.15, fg=m.fg, dim=m.low, accent=m.accent)
    top = cy - R
    h = 30 * (1 - pull) + 12 * pull
    S.figure(cv, cv.WU / 2, top + 0.6, h, "run", ph=ctx.beat * 0.5, fg=m.accent if ctx.pulse(8) > 0.6 else m.fg)
    if pull > 0:
        for i in range(3):
            k = 1 + i * 0.35
            S.picture_frame(cv, cv.W / 2 - R * k - 4, (cy - R * k) / cv.aspect - 2,
                            cv.W / 2 + R * k + 4, (cy + R * k) / cv.aspect + 2, m.mid, m.low,
                            style="simple", depth=2)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, 8, 8, m.fg, m.accent, max_w=cv.W - 8)
    return chorus_fx(cv, ctx, post_for(m, ctx))


def clock_face(cv: Canvas, ctx: Ctx) -> Post:
    """The face of the everyday: a cold clock whose hands race."""
    t, P = ctx.t, ctx.params
    m = DAY
    cold = mix(PAPER, hexc_cold(), 0.25)
    cv.clear(cold, m.fg)
    peek = P.get("peek", False)
    # snow / frost
    rng = np.random.default_rng(9)
    n = 160
    xs = (rng.uniform(0, cv.W, n) + 3 * np.sin(t + rng.uniform(0, 6, n))) % cv.W
    ys = (rng.uniform(0, cv.H, n) + t * rng.uniform(1.5, 4, n)) % cv.H
    cv.scatter(xs, ys, "*", fg=mix(cold, INK, 0.25))
    cx = cv.WU / 2 if not peek else cv.WU - 30 + 40 * (1 - ease_out(seg(t, ctx.t0, ctx.t0 + 0.8)))
    cy = cv.HU / 2 - 2
    R = 38 + 1.5 * ctx.pulse(6)
    hours = 7 + 9 * (t - ctx.t0) + 0.15 * ctx.beat_i
    S.clock(cv, cx, cy, R, hours, m.fg, mix(cold, INK, 0.45), m.accent, sweep=ctx.beat_frac)
    # a blank, cold face: two dots for eyes on the dial, a flat mouth
    cv.put(int(cx - 9), int(cy / cv.aspect - 4), "-", m.fg, bold=True)
    cv.put(int(cx + 8), int(cy / cv.aspect - 4), "-", m.fg, bold=True)
    cv.put(int(cx - 4), int(cy / cv.aspect + 6), "_____", m.fg)
    bottom_lyric(cv, ctx, Mode(True), y=cv.H - 3)
    p = chorus_fx(cv, ctx, post_for(m, ctx, vignette=0.4), invert_downbeat=False)
    return p


def hexc_cold():
    return np.array([0.62, 0.74, 0.86], np.float32)


def beckon(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on, over here': a door-shaped frame opens; light pours out; we go in."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    u = ctx.u
    open_ = ease_out(seg(t, ctx.t0, ctx.t0 + 0.8))
    zoom = ease(seg(t, P.get("zoom", ctx.t1 - 0.9), ctx.t1))
    hw = (8 + 8 * open_) * (1 + 9 * zoom ** 2)
    hh = 16 * (1 + 9 * zoom ** 2)
    cx, cy = cv.W / 2, cv.H / 2 + 4
    x0, y0, x1, y1 = cx - hw, cy - hh, cx + hw, cy + hh
    # light spilling out on the floor
    for k in range(1, 12):
        yy = int(y1 + k)
        if yy < cv.H:
            spread = hw + k * 4
            cv.line(cx - spread, yy, cx + spread, yy, mix(INK, PAPER, max(0.1, 0.7 - k * 0.06)),
                    "." if k > 5 else ":")
    ys, xs = slice(max(0, int(y0)), min(cv.H, int(y1) + 1)), slice(max(0, int(x0)), min(cv.W, int(x1) + 1))
    cv.ch[ys, xs] = 0
    cv.bg[ys, xs] = mix(PAPER_DIM, INK, 0.12 + 0.3 * (1 - open_))
    S.picture_frame(cv, x0, y0, x1, y1, m.fg, m.mid, style="gilded" if hw > 14 else "simple",
                    depth=3 if hw > 14 else 2)
    if zoom < 0.5:
        S.figure(cv, cx, (y1 - 0.5) * cv.aspect, 46 * (1 + 3 * zoom), "stand", fg=INK)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, 6, 9, m.fg, m.accent, max_w=cv.W - 24)
    p = chorus_fx(cv, ctx, post_for(m, ctx, glow=0.3), invert_downbeat=False)
    p.flash = 0.8 * zoom ** 3
    return p


def failure(cv: Canvas, ctx: Ctx) -> Post:
    """Second / third failure: a counter, an error log, and a big red X."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    n = P["n"]
    # scrolling log of attempts
    for y in range(cv.H):
        k = int(y + t * 12)
        cv.put(2, y, f"attempt {k % 997:04d} ........ FAILED", m.faint)
        cv.put(cv.W - 36, y, f"{(k * 37) % 10000:05d}  ERR  retry?", m.faint)
    # counter
    s = f"{n:02d}"
    w = S.seven_seg_width(s, 16)
    S.seven_seg(cv, int(cv.W / 2 - w / 2), 8, s, m.accent, off=None, w=16, h=8)
    cv.put_center(6, "F A I L U R E", m.fg, bold=True)
    # big X stamped on the next downbeat after the line starts
    x_t = ctx.grid.beat_time(math.ceil(ctx.grid.beat_pos(ctx.t0 + 0.4)))
    if t >= x_t:
        k = min(1.0, (t - x_t) / 0.12)
        a, b = 0.5 - 0.5 * k, 0.5 + 0.5 * k
        cx0, cy0, cx1, cy1 = 40, 4, cv.W - 40, 30
        for d in (0, 1):
            cv.line(cx0 + (cx1 - cx0) * a + d, cy0 + (cy1 - cy0) * a, cx0 + (cx1 - cx0) * b + d, cy0 + (cy1 - cy0) * b, m.accent, "\\", bold=True)
            cv.line(cx1 - (cx1 - cx0) * a + d, cy0 + (cy1 - cy0) * a, cx1 - (cx1 - cx0) * b + d, cy0 + (cy1 - cy0) * b, m.accent, "/", bold=True)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, cv.H - 9, 10, m.fg, m.accent, max_w=cv.W - 8)
    return chorus_fx(cv, ctx, post_for(m, ctx))


def repetition(cv: Canvas, ctx: Ctx) -> Post:
    """Monotonous work: the same tiny figure walking in a grid of identical
    frames, progress bars filling and resetting every bar."""
    t = ctx.t
    m = DAY
    base(cv, m)
    cols, rows = 6, 3
    cw, chh = (cv.W - 4) // cols, (cv.H - 12) // rows
    bp = ctx.bar % 1.0
    for r in range(rows):
        for c in range(cols):
            x0, y0 = 2 + c * cw, 1 + r * chh
            idx = r * cols + c
            on = (ctx.beat_i % (cols * rows)) == idx
            S.picture_frame(cv, x0 + 1, y0, x0 + cw - 2, y0 + chh - 2, m.accent if on else m.fg, m.mid,
                            style="simple", depth=1)
            S.figure(cv, x0 + cw / 2, (y0 + chh - 4) * cv.aspect, 16, "walk", ph=ctx.beat * 0.5, fg=m.fg)
            fill = int(bp * 10)
            cv.put(x0 + 3, y0 + chh - 3, "[" + "#" * fill + "." * (10 - fill) + "]", m.mid)
    ln = ctx.line()
    if ln is not None:
        L.big(cv, ctx, ln, cv.H - 6, 9, m.fg, m.accent, max_w=cv.W - 8)
    p = chorus_fx(cv, ctx, post_for(m, ctx))
    # copy-paste stutter: on the off-beats, duplicate the top half into the bottom
    if ctx.beat_frac > 0.5 and ctx.beat_i % 2 == 1:
        h = (cv.H - 12) // 2
        cv.ch[h:2 * h] = cv.ch[0:h]
        cv.fg[h:2 * h] = cv.fg[0:h]
    return p


# ===================================================================== SOLO

def solo_tunnel(cv: Canvas, ctx: Ctx) -> Post:
    """Guitar solo: an endless tunnel of picture frames with a ring spectrum
    around the Earth; then a counter rolls the days from the 2011 VOCALOID
    original to the 2018 band recording."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    warp = seg(t, P["warp"], ctx.t1)
    phase = (ctx.beat / 2.0) % 1.0 if warp == 0 else (ctx.beat * (0.5 + 3 * warp)) % 1.0
    M.frame_tunnel(cv, t, phase, m.fg, m.mid, m.low, n=8, ratio=0.7, style="gilded",
                   accent=m.accent, accent_k=ctx.beat_i % 8 if ctx.pulse(6) > 0.4 else None)
    cx, cy = cv.WU / 2, cv.HU / 2
    count_on = t >= P["count0"]
    # ring spectrum
    spec = ctx.spectrum
    n = len(spec)
    R0 = 15 if not count_on else 25
    clear = np.hypot(cv.X - cx, cv.Y - cy) < R0 + 15
    if count_on:
        clear = (np.abs(cv.xx - cv.W / 2) < 54) & (np.abs(cv.yy - cv.H / 2) < 10)
    cv.ch[clear] = 0
    if not count_on:
        for i in range(n * 2):
            v = float(spec[i % n])
            a = i / (n * 2) * 2 * math.pi + t * 0.3
            r1 = R0 + 2 + v * 12
            cv.line(cx / 1 + (R0 + 1) * math.cos(a), (cy + (R0 + 1) * math.sin(a)) / cv.aspect,
                    cx + r1 * math.cos(a), (cy + r1 * math.sin(a)) / cv.aspect,
                    m.accent if v > 0.85 else m.fg)
        S.globe(cv, cx, cy, R0, 40 * t, tilt=0.3, fg=m.fg, dim=m.low, accent=m.accent)
    else:
        d0 = _dt.date(*P["date0"])
        d1 = _dt.date(*P["date1"])
        total = (d1 - d0).days
        b0 = ctx.grid.beat_pos(P["count0"])
        b1 = ctx.grid.beat_pos(P["count1"])
        k = min(1.0, max(0.0, (math.floor(ctx.beat) - b0) / max(1, (b1 - b0))))
        k = k ** 1.6
        day = int(round(total * k))
        d = d0 + _dt.timedelta(days=day)
        s = d.strftime("%Y.%m.%d")
        done = t >= P["count1"]
        col = m.accent if done and (ctx.frame // 3) % 2 == 0 else m.fg
        cv.big_text(s, cv.W / 2, cv.H / 2 - 0.5, 9, fg=col, bold=True)
        cv.put_center(int(cv.H / 2 - 8), f"{P['label0']}  ->  {P['label1']}", m.mid)
        cv.put_center(int(cv.H / 2 + 6), f"day {day:04d} / {total}", m.accent if done else m.mid)
    p = beat_hit(post_for(m, ctx), ctx, 0.7)
    p.flash = 0.7 * warp ** 3
    return p


# ========================================================================= B2

def crowd(cv: Canvas, ctx: Ctx) -> Post:
    """Night street: everyone walks the other way; someone brushes past; she
    sidesteps on purpose."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    S.stars(cv, t, 91, 0.012, m.mid, m.low)
    hz = 30
    cv.line(0, hz, cv.W, hz, m.low, "_")
    # buildings on the horizon
    rng = np.random.default_rng(3)
    x = 0
    while x < cv.W:
        w = int(rng.integers(6, 16))
        h = int(rng.integers(3, 12))
        cv.box(x, hz - h, x + w, hz, m.faint, "+-|")
        for yy in range(hz - h + 1, hz, 2):
            for xx in range(x + 2, x + w - 1, 3):
                if rng.random() < 0.3:
                    cv.put(xx, yy, ".", m.low if rng.random() < 0.7 else m.mid)
        x += w + int(rng.integers(0, 4))
    # crowd walking right-to-left
    rng = np.random.default_rng(17)
    nw = 26
    lanes = rng.integers(hz + 4, cv.H - 3, nw)
    sp = rng.uniform(5, 13, nw)
    off = rng.uniform(0, cv.W + 40, nw)
    for i in range(nw):
        xw = (off[i] - sp[i] * (t - ctx.t0)) % (cv.W + 40) - 20
        S.walker(cv, xw, int(lanes[i]), (t * sp[i] * 0.25 + i * 0.3), m.low if lanes[i] < hz + 10 else m.mid)
    # the one who brushes past, and the one she dodges
    xs_ = cv.W / 2 - 30 + 50 * ctx.u
    lane = cv.H - 6
    dodge = ease(seg(t, P["dodge"], P["dodge"] + 0.5)) * (1 - ease(seg(t, P["dodge"] + 1.6, P["dodge"] + 2.2)))
    for tp, col in ((P["pass"], m.mid), (P["dodge"] + 0.4, m.mid)):
        xp = xs_ + (tp - t) * 30
        if -10 < xp < cv.W + 10:
            S.figure(cv, xp, (lane + 1.5) * cv.aspect, 20, "walk", ph=t * 1.6, fg=col, flip=True)
    S.figure(cv, xs_, (lane + 1.5 - 5 * dodge) * cv.aspect, 20, "walk", ph=ctx.beat * 0.5, fg=m.accent)
    ln = ctx.line()
    L.big(cv, ctx, ln, 10, 9, m.fg, m.accent, max_w=cv.W - 16)
    return post_for(m, ctx)


def road_sleep(cv: Canvas, ctx: Ctx) -> Post:
    """A road into the night; sleeping alone inside a frame; rain; the road
    tipping down to its bottom."""
    t, P = ctx.t, ctx.params
    m = NIGHT
    base(cv, m)
    a, b, c, d = ctx.t0, P["sleep"], P["rain"], P["down"]

    def road(vy: int, down=False):
        vx = cv.W / 2
        ye = cv.H - 1 if not down else 0
        for side in (-1, 1):
            cv.line(vx + side * 1, vy, vx + side * cv.W * 0.55, ye, m.fg)
            cv.line(vx + side * 1.5, vy, vx + side * cv.W * 0.75, ye, m.low)
        # centre dashes moving toward the viewer
        sp = 1.4 if not down else -0.8
        for k in range(14):
            z = ((k / 14) + t * sp * 0.25 + ctx.beat * 0.02) % 1.0
            zz = z ** 2.2
            y = vy + (ye - vy) * zz
            ln_ = 0.3 + 3 * zz
            cv.line(vx, y, vx, y + (ln_ if not down else -ln_), m.fg if zz > 0.2 else m.mid, "|")
        # roadside lamps
        for k in range(6):
            z = ((k / 6) + t * sp * 0.1) % 1.0
            zz = z ** 2
            y = vy + (ye - vy) * zz
            for side in (-1, 1):
                x = vx + side * (4 + cv.W * 0.6 * zz)
                hgt = 1 + 14 * zz
                cv.line(x, y, x, y - hgt if not down else y + hgt, m.mid, "|")
                cv.put(int(x), int(y - hgt if not down else y + hgt), "*", m.fg if zz > 0.15 else m.mid)

    if t < b:
        S.stars(cv, t, 95, 0.015, m.fg, m.low)
        road(18)
        cv.line(0, 18, cv.W, 18, m.low, "_")
    elif t < d:
        rain = seg(t, c, c + 0.5)
        sc = 1 - 0.25 * ease(seg(t, c, d))
        cx, cy = cv.W / 2, cv.H / 2 - 2
        hw, hh = 52 * sc, 17 * sc
        S.stars(cv, t, 97, 0.008, m.mid, m.low)
        S.picture_frame(cv, cx - hw, cy - hh, cx + hw, cy + hh, m.fg, m.mid, style="gilded",
                        depth=3, bg=mix(INK, PAPER, 0.06), clear_inside=True)
        bed_y = cy + hh * 0.55
        cv.line(cx - hw * 0.62, bed_y, cx + hw * 0.62, bed_y, m.mid, "=")
        cv.line(cx - hw * 0.62, bed_y + 1, cx - hw * 0.62, bed_y + 3, m.mid, "|")
        cv.line(cx + hw * 0.62, bed_y + 1, cx + hw * 0.62, bed_y + 3, m.mid, "|")
        S.figure(cv, cx + 2, (bed_y - 0.2) * cv.aspect, 62 * sc, "lie", ph=t * 0.2, fg=m.fg)
        for k in range(4):
            zt = (t * 0.5 + k * 0.25) % 1
            cv.put(int(cx - 26 * sc + zt * 10), int(bed_y - 6 - zt * 9), "zZ"[k % 2], m.mid if zt > 0.5 else m.fg)
        if rain > 0:
            rng = np.random.default_rng(12)
            n = int(220 * rain)
            xs = rng.uniform(0, cv.W, n)
            y0 = rng.uniform(0, cv.H, n)
            sp = rng.uniform(25, 40, n)
            ys = (y0 + sp * t) % cv.H
            cv.scatter(xs - (ys * 0.2) % 1, ys, "/", fg=m.low)
            cv.scatter(xs, (ys + 1) % cv.H, "/", fg=m.faint)
    else:
        road(cv.H - 4, down=True)
        brk = seg(t, P["brk"], P["brk"] + 0.3)
        if brk > 0:
            S.char_noise(cv, ctx.rng(ctx.frame), 0.03 * brk)
            cv.fg[:] = mix(cv.fg, INK, 0.55 * brk)
    bottom_lyric(cv, ctx, m, y=cv.H - 3 if t < d else 3)
    p = post_for(m, ctx)
    if t >= P.get("drums", 0):
        p = beat_hit(p, ctx, 0.5)
    return p


# ==================================================================== FINALE

def finale(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on' one last time: we pull back out of the Earth to find it hung in
    a picture frame on the wall of the narrator's room -- 日常と地球の額縁."""
    t, P = ctx.t, ctx.params
    m = DAY
    base(cv, m)
    end_hold = P["hold"]
    u = ease(seg(t, ctx.t0, end_hold))
    s = 7.0 * (1 - u) + 1.0 * u
    W, H = cv.W - 1, cv.H - 1
    # zoom about the centre of the wall frame: s=7 shows the framed Earth
    # full-screen, s=1 reveals the whole room around it
    fr = M.room_frame_rect((0, 0, W, H), 0.42, 0.55, 0.8)
    fc = ((fr[0] + fr[2]) / 2, (fr[1] + fr[3]) / 2)
    vx0 = fc[0] + (0 - fc[0]) * s
    vy0 = fc[1] + (0 - fc[1]) * s
    vx1 = fc[0] + (W - fc[0]) * s
    vy1 = fc[1] + (H - fc[1]) * s
    info = M.room(cv, (vx0, vy0, vx1, vy1), m.fg, m.mid, m.faint, t=t,
                  frame_globe_lon=140 - 24 * (t - end_hold), accent=m.accent, night_window=False,
                  frame_w=0.55, frame_h=0.8)
    if s < 2.2:
        S.figure(cv, vx0 + (vx1 - vx0) * 0.74, (vy0 + (vy1 - vy0) * 0.97) * cv.aspect,
                 (vy1 - vy0) * cv.aspect * 0.5, "sit", ph=t * 0.25, fg=m.fg)
    p = post_for(m, ctx, vignette=0.4)
    ln = ctx.line()
    if ln is not None and t < end_hold:
        bottom_lyric(cv, ctx, m, y=cv.H - 3)
    # the last hit
    hit = P["hit"]
    if t >= hit:
        k = max(0.0, 1 - (t - hit) * 4)
        p.flash = 0.7 * k
    if t >= P["out"]:
        p.fade = max(0.0, 1 - (t - P["out"]) * 6)
    return p


def credits(cv: Canvas, ctx: Ctx) -> Post:
    m = NIGHT
    base(cv, m)
    t, P = ctx.t, ctx.params
    rows = P["rows"]
    y = cv.H // 2 - len(rows)
    for i, (txt, style) in enumerate(rows):
        t0 = ctx.t0 + 0.25 + i * 0.45
        if t < t0:
            continue
        k = int(len(txt) * ease_out(seg(t, t0, t0 + 0.5)))
        col = {"title": m.fg, "main": m.fg, "dim": m.mid, "accent": m.accent}[style]
        cv.put_center(y + i * 2, txt[:k], col, bold=style in ("title", "accent"))
    p = post_for(m, ctx)
    p.fade = 1 - seg(t, ctx.t1 - 0.8, ctx.t1)
    return p
