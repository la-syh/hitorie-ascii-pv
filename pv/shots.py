"""Per-line shots: one literal, full-screen action for every lyric line.

Design rules (after review feedback):
* every lyric line gets its own idea, and the idea *moves* within the line,
  locked to the beat (hits, stamps, hops) -- no static tableaux;
* objects and symbols instead of drawn people: the narrator appears only as
  an eye, a cursor, footprints or a shadow, which read clearly in ASCII;
* bold: shapes fill most of the frame, solid colour blocks (cells with a
  coloured background and a texture character), hard red accents.

All shots are pure functions of ``ctx.t``.  Rows 51-53 are reserved for the
Chinese caption strip drawn by ``render.py``; the Japanese line sits on row 47.
"""
from __future__ import annotations

import math

import numpy as np

from . import lyricfx as L
from . import motifs as M
from . import shapes as S
from .canvas import Canvas, hexc
from .palette import DAY, GREY, INK, NIGHT, PAPER, RED, RED_DIM, Mode, mix
from .raster import Post
from .scenes import beat_hit, ease, ease_out, post_for, seg
from .timeline import Ctx

PIC_H = 46            # picture rows 0..45; row 47 Japanese line; 51-53 Chinese captions
JP_ROW = 47
COLD = hexc("#9fc3df")
DEEP = hexc("#16161b")
REDBG = hexc("#c4241c")
REDDK = hexc("#5a0f0c")


# ------------------------------------------------------------------ helpers

class Red(Mode):
    """Red poster mode: red background, ink-dark and paper-light marks."""

    def __init__(self):
        super().__init__(False)
        self.bg = REDBG
        self.fg = PAPER
        self.mid = mix(REDBG, PAPER, 0.45)
        self.low = mix(REDBG, INK, 0.45)
        self.faint = mix(REDBG, INK, 0.2)
        self.accent = INK


REDM = Red()


def clear(cv: Canvas, m: Mode):
    cv.clear(m.bg, m.fg)


def punch(ctx: Ctx, amt=0.08, decay=8.0) -> float:
    return 1.0 + amt * ctx.pulse(decay)


def sym(cv: Canvas, s: str, cx: float, cy: float, rows: float, fg, fill="#", bold=True):
    """A glyph/word drawn huge as structural ASCII; centred at cell (cx, cy)."""
    rows = max(3, int(round(rows)))
    bmp = cv.text_bitmap(s, rows, bold)
    h, w = bmp.shape
    cv.shape_field(bmp, int(round(cx - w / 2)), int(round(cy - h / 2)), fg, fill=fill)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def solid(cv: Canvas, s: str, cx: float, cy: float, rows: float, color, tex="#", tex_fg=None,
          thresh=0.42, bold=True):
    """A glyph as a solid colour block (cells with background ``color``) carrying a
    texture character -- the bold 'poster' look."""
    rows = max(3, int(round(rows)))
    bmp = cv.text_bitmap(s, rows, bold)
    h, w = bmp.shape
    ox, oy = int(round(cx - w / 2)), int(round(cy - h / 2))
    m = np.zeros((cv.H, cv.W), bool)
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(cv.W, ox + w), min(cv.H, oy + h)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = bmp[y0 - oy:y1 - oy, x0 - ox:x1 - ox] > thresh
    paint(cv, m, color, tex, tex_fg)
    return m


def paint(cv: Canvas, mask, color, tex=" ", tex_fg=None):
    cv.bg[mask] = color
    cv.ch[mask] = cv.ids(tex)[0] if tex != " " else 0
    cv.fg[mask] = color * 0.6 if tex_fg is None else tex_fg


def disc(cv: Canvas, cx, cy, r):
    """Mask of a disc; centre in cells/rows, radius in cell widths."""
    return np.hypot(cv.X - cx, cv.Y - cy * cv.aspect) < r


def ring(cv: Canvas, cx, cy, r, w):
    d = np.hypot(cv.X - cx, cv.Y - cy * cv.aspect)
    return (d < r) & (d > r - w)


def poly(cv: Canvas, pts):
    """Mask of a polygon given in (cell x, row y) points."""
    return S.sd_poly(cv.X, cv.Y, [(x, y * cv.aspect) for x, y in pts]) < 0


def rect(cv: Canvas, x0, y0, x1, y1):
    return (cv.xx >= x0) & (cv.xx <= x1) & (cv.yy >= y0) & (cv.yy <= y1)


def arrow_mask(cv: Canvas, x0, y, x1, h):
    """Horizontal block arrow from x0 to x1 (pointing at x1), centred on row y, h rows tall."""
    d = 1 if x1 > x0 else -1
    head = min(abs(x1 - x0) * 0.4, h * 2.2)
    xs = x1 - d * head
    shaft = rect(cv, min(x0, xs), y - h * 0.22, max(x0, xs), y + h * 0.22)
    return shaft | poly(cv, [(xs, y - h / 2), (x1, y), (xs, y + h / 2)])


def jp(cv: Canvas, ctx: Ctx, m: Mode, y: int = JP_ROW, band=True):
    L.subtitle(cv, ctx, ctx.line(), y, m.fg, m.accent if m is not REDM else PAPER, m.mid,
               band=m.bg if band else None)


def finish(cv, ctx, m, hit=1.0, **post):
    """Japanese line + post settings + beat shake."""
    cv.ch[PIC_H:] = 0                      # nothing from the picture under the lyric rows
    jp(cv, ctx, m)
    p = post_for(m if m is not REDM else NIGHT, ctx, **post)
    if m is REDM:
        p.glow = post.get("glow", 0.25)
    elif not m.paper and "glow" not in post:
        p.glow = 0.35
    return beat_hit(p, ctx, hit)


def beats_in(ctx: Ctx) -> float:
    """Beats elapsed since the start of this shot."""
    return ctx.beat - ctx.grid.beat_pos(ctx.t0)


def label(cv, x, y, s, col, bold=True):
    cv.put(x, y, s, col, bold=bold)


# ============================================================ VERSE 1 (phone)

def sh_machine(cv: Canvas, ctx: Ctx) -> Post:
    """Answering-machine service: a giant ☎, the PLAY key is pressed on beat 2,
    the red LCD starts counting."""
    m = NIGHT
    clear(cv, m)
    b = beats_in(ctx)
    k = punch(ctx, 0.06)
    solid(cv, "☎", 46, 22, 40 * k, mix(INK, PAPER, 0.85), "%", mix(INK, PAPER, 0.55))
    # LCD
    cv.box(92, 6, 152, 30, m.fg, "+-|", bold=True)
    n = "01" if b < 1 else f"{min(99, int((b - 1) * 4) + 1):02d}"
    w = S.seven_seg_width(n, 13)
    S.seven_seg(cv, int(122 - w / 2), 9, n, m.accent, w=13, h=8)
    label(cv, 96, 32, "NEW MESSAGE", m.mid)
    # PLAY key: pressed on beat 2
    down = b >= 1
    y = 37 + (1 if down else 0)
    cv.box(96, y, 148, y + 6, m.accent if down else m.fg, "+=|", fill=True,
           bg=REDDK if down else m.bg, bold=True)
    label(cv, 112, y + 3, ">  PLAY" if down else "|> PLAY", PAPER if down else m.fg)
    led = (ctx.beat_frac < 0.5) if down else True
    disc_m = disc(cv, 150, 3, 2.2)
    paint(cv, disc_m, RED if led else REDDK, "@", mix(RED, PAPER, 0.4))
    return finish(cv, ctx, m)


def sh_lowfreq(cv: Canvas, ctx: Ctx) -> Post:
    """Recorded low frequency: a speaker cone throbbing with the kick, sound
    arcs filling the screen."""
    m = NIGHT
    clear(cv, m)
    low = ctx.feat("low")
    cx, cy = 28, 23
    S.ripple_rings(cv, cx, cy * cv.aspect, ctx.lt, 34, 9, m.fg, "arc", width=1.4, maxr=190)
    for r, ch, col in ((26, "#", mix(INK, PAPER, 0.25)), (20, "%", mix(INK, PAPER, 0.4)),
                       (13 + 3 * low, "@", mix(INK, PAPER, 0.7)), (6 + 2 * low, "O", PAPER)):
        paint(cv, disc(cv, cx, cy, r), mix(INK, PAPER, 0.08), ch, col)
    paint(cv, disc(cv, cx, cy, 3), RED, "@", PAPER)
    # oscilloscope band
    amp = 2 + 9 * low
    M.wave_line(cv, 38, amp, 40, ctx.t, 0.4, m.accent, 60, cv.W)
    label(cv, 62, 3, f"LOW FREQ  {28 + int(30 * low):3d} Hz", m.mid)
    return finish(cv, ctx, m, 1.4)


def sh_frontline(cv: Canvas, ctx: Ctx) -> Post:
    """The front line of everyday: daily objects march in ranks toward a red
    front line that cuts the screen."""
    m = DAY
    clear(cv, m)
    paint(cv, rect(cv, 0, 29, cv.W, 33), REDBG, "=", PAPER)
    label(cv, 4, 31, "FRONT LINE ////////", PAPER)
    icons = "☎☂☀♨〒☁※♪"
    for row, (y, sz) in enumerate(((10, 15), (21, 9), (40, 9))):
        sp = 22 + row * 9
        off = (ctx.lt * sp + row * 13) % 24
        for i in range(9):
            x = -12 + i * 24 + off
            hop = 1.5 * ctx.pulse(9) if (i + row) % 2 == ctx.beat_i % 2 else 0
            sym(cv, icons[(i + row * 3) % len(icons)], x, y - hop, sz, m.fg if row else INK)
    for x in range(4, cv.W, 8):
        cv.put(x, 34, ">>", m.accent, bold=True)
    return finish(cv, ctx, m)


def sh_where(cv: Canvas, ctx: Ctx) -> Post:
    """Where should I go?  A signpost whose arrows spin and never agree."""
    m = NIGHT
    clear(cv, m)
    sym(cv, "?", 80, 22, 48, m.faint)
    cv.line(80, 4, 80, 45, m.fg, "#", bold=True)
    cv.line(79, 4, 79, 45, m.mid, "|")
    b = beats_in(ctx)
    for i, y in enumerate((4, 17, 30)):
        dirs = ("←", "→")
        d = (int(b * 2) + i) % 2
        spin = (b * 2 + i * 0.3) % 1
        width = int(56 * abs(math.cos(spin * math.pi)))
        x0 = 81 if d else 79 - width
        col = m.accent if i == int(b) % 3 else m.fg
        cv.box(x0, y, x0 + width, y + 10, col, "+=|", fill=True,
               bg=REDDK if col is m.accent else mix(INK, PAPER, 0.1), bold=True)
        if width > 16:
            ax0, ax1 = (x0 + 4, x0 + width - 4) if d else (x0 + width - 4, x0 + 4)
            paint(cv, arrow_mask(cv, ax0, y + 5, ax1, 9), PAPER, "=", mix(PAPER, INK, 0.4))
    return finish(cv, ctx, m)


def sh_jar(cv: Canvas, ctx: Ctx) -> Post:
    """Stored-up jokes: a jar filling with HA, one layer per beat, lid rattling."""
    m = DAY
    clear(cv, m)
    x0, x1, y0, y1 = 48, 112, 6, 44
    level = y1 - (y1 - y0 - 2) * ease(min(1, beats_in(ctx) / 4.2))
    for y in range(int(math.ceil(level)), y1):
        cv.put(x0 + 2, y, ("HAha" * 20)[(y % 4): (y % 4) + (x1 - x0 - 3)], m.fg if y % 2 else m.mid)
    cv.line(x0, y0, x0, y1, INK, "#", bold=True)
    cv.line(x1, y0, x1, y1, INK, "#", bold=True)
    cv.line(x0, y1, x1, y1, INK, "#", bold=True)
    rattle = int(2 * math.sin(ctx.t * 40) * seg(ctx.u, 0.6, 1.0))
    cv.box(x0 - 3 + rattle, y0 - 4, x1 + 3 + rattle, y0 - 2, INK, "+=|", fill=True, bg=REDBG, bold=True)
    label(cv, 6, 6, "STOCK", m.mid)
    label(cv, 6, 8, f"{int(100 * (y1 - level) / (y1 - y0)):3d}%", m.accent)
    return finish(cv, ctx, m)


def sh_burst(cv: Canvas, ctx: Ctx) -> Post:
    """Spat out all at once: an explosion of HA filling the screen."""
    m = REDM
    clear(cv, m)
    dt = ctx.lt
    rng = np.random.default_rng(11)
    n = 220
    ang = rng.uniform(0, 2 * math.pi, n)
    sp = rng.uniform(25, 110, n)
    words = ["HA", "ha", "w", "!!", "HAHA", "www"]
    for i in range(n):
        r = sp[i] * dt
        x = 80 + r * math.cos(ang[i])
        y = 23 + r * math.sin(ang[i]) / cv.aspect
        cv.put(int(x), int(y), words[i % len(words)], PAPER if i % 3 else INK, bold=True)
    for i in range(6):
        r = 30 * dt * (1 + i * 0.4)
        a = i * 1.05
        sym(cv, "HA", 80 + r * 2.0 * math.cos(a), 23 + r * math.sin(a), 9 + 3 * i % 7, PAPER)
    paint(cv, disc(cv, 80, 23, max(0, 14 - 40 * dt)), PAPER, "@", REDBG)
    return finish(cv, ctx, m, 1.6, flash=0.5 * max(0, 1 - dt * 6))


def sh_shrug(cv: Canvas, ctx: Ctx) -> Post:
    """'Well, of course': a giant shrug."""
    m = DAY
    clear(cv, m)
    k = punch(ctx, 0.12)
    up = 2 * math.sin(min(1, ctx.u * 2) * math.pi)
    sym(cv, "\\_(ツ)_/", 80, 22 - up, 22 * k, INK)
    return finish(cv, ctx, m)


def sh_counter(cv: Canvas, ctx: Ctx) -> Post:
    """Still not stopping: a time counter running flat out under speed lines."""
    m = NIGHT
    clear(cv, m)
    for y in range(0, PIC_H, 2):
        off = int((ctx.t * (60 + 13 * (y % 5))) % cv.W)
        cv.put(-off % cv.W - 30, y, "-" * 22, m.low)
    t = ctx.t * 7.3
    s = f"{int(t // 60) % 100:02d}:{int(t) % 60:02d}.{int(t * 100) % 100:02d}"
    sym(cv, s, 80, 21, 20 * punch(ctx, 0.05), m.fg)
    label(cv, 66, 36, ">> NO  STOP  >>", m.accent)
    return finish(cv, ctx, m)


def sh_morph(cv: Canvas, ctx: Ctx) -> Post:
    """Everything keeps changing: the whole frame swaps icon and colour twice a beat."""
    i = int(beats_in(ctx) * 2)
    icons = "☀☁☂♥☎★◆○♪◎"
    bgs = [DEEP, REDBG, mix(INK, PAPER, 0.3), DEEP, REDBG, mix(INK, PAPER, 0.18)]
    m = REDM if i % 3 == 1 else NIGHT
    clear(cv, m)
    cv.bg[:] = bgs[i % len(bgs)]
    solid(cv, icons[i % len(icons)], 80, 22, 46, PAPER if i % 3 != 1 else INK, "#",
          mix(PAPER, INK, 0.35))
    sym(cv, icons[(i + 3) % len(icons)], 18 + (i * 37) % 120, 8 + (i * 11) % 26, 10, m.accent)
    return finish(cv, ctx, m, 1.2)


# ============================================================ VERSE 2

def sh_tatami(cv: Canvas, ctx: Ctx) -> Post:
    """A sooty four-and-a-half-mat room, seen from straight above: the mats'
    pinwheel, soot raining down, the ceiling light swinging."""
    m = DAY
    soot = mix(PAPER, GREY, 0.35)
    cv.clear(soot, INK)
    z = 1 + 0.12 * ctx.u
    cx, cy = 80, 23
    S_ = 21 * z   # half mat in rows; mats are 2:1
    # 4.5 mats inside a square of 3 half-mats per side
    hw = 3 * S_ * cv.aspect / 2  # half-size in cells (square in square units)
    hh = 3 * S_ / 2
    x0, y0 = cx - hw, cy - hh
    u = hw * 2 / 3
    v = hh * 2 / 3
    mats = [(0, 0, 2, 1), (2, 0, 3, 2), (1, 2, 3, 3), (0, 1, 1, 3), (1, 1, 2, 2)]
    for i, (a, b, c, d) in enumerate(mats):
        r = rect(cv, x0 + a * u, y0 + b * v, x0 + c * u - 1, y0 + d * v - 1)
        horiz = (c - a) > (d - b)
        paint(cv, r, mix(PAPER, hexc("#b5ac86"), 0.5 if i != 4 else 0.25), "-" if horiz else "|",
              mix(PAPER, INK, 0.35))
        cv.box(x0 + a * u, y0 + b * v, x0 + c * u - 1, y0 + d * v - 1, INK, "#=H", bold=True)
    # soot
    rng = np.random.default_rng(4)
    n = 420
    xs = rng.uniform(0, cv.W, n)
    ys = (rng.uniform(0, PIC_H, n) + ctx.lt * rng.uniform(3, 9, n)) % PIC_H
    cv.scatter(xs, ys, "*", fg=mix(INK, PAPER, 0.25))
    cv.scatter(xs[::3] + 1, ys[::3], ",", fg=INK)
    # swinging light (seen from above)
    a = math.sin(ctx.t * 3.1) * 9
    paint(cv, disc(cv, cx + a, cy, 5), PAPER, "@", REDBG)
    cv.line(cx, cy, cx + a, cy, INK, "-")
    return finish(cv, ctx, m)


def sh_ultrasound(cv: Canvas, ctx: Ctx) -> Post:
    """Brought-in ultrasound: a tiny emitter floods the room with tight rings;
    the 'glass' of the screen cracks."""
    m = NIGHT
    clear(cv, m)
    S.ripple_rings(cv, 80, 23 * cv.aspect, ctx.lt, 70, 2.4, m.fg, "arc", width=0.6, maxr=200)
    S.ripple_rings(cv, 80, 23 * cv.aspect, ctx.lt + 0.03, 70, 2.4, m.accent, "arc", width=0.25, maxr=200)
    cv.box(72, 20, 88, 26, PAPER, "+=|", fill=True, bg=REDBG, bold=True)
    label(cv, 74, 23, "((( 40kHz )))", PAPER)
    rng = np.random.default_rng(8)
    nb = int(beats_in(ctx)) + 1
    for k in range(min(nb, 4) * 4):
        a = rng.uniform(0, 2 * math.pi)
        pts = [(80, 23)]
        r = 0
        for _ in range(6):
            r += rng.uniform(6, 18)
            a += rng.normal(0, 0.35)
            pts.append((80 + r * math.cos(a) * 1.7, 23 + r * math.sin(a)))
        cv.polyline(pts, PAPER)
    return finish(cv, ctx, m, 1.3)


def sh_escape(cv: Canvas, ctx: Ctx) -> Post:
    """Escaped from the everyday: footprints walk out of the picture frame and
    off the screen, one step per beat."""
    m = DAY
    clear(cv, m)
    S.picture_frame(cv, 6, 3, 66, 42, INK, mix(PAPER, INK, 0.5), style="gilded")
    paint(cv, rect(cv, 20, 9, 52, 36), mix(PAPER, INK, 0.12), " ")
    label(cv, 26, 22, "[ everyday ]", mix(PAPER, INK, 0.45))
    steps = int(beats_in(ctx) * 2) + 1
    for i in range(min(steps, 14)):
        x = 40 + i * 9
        y = 26 + (3 if i % 2 else -3) - i * 0.6
        col = REDBG if i == steps - 1 else INK
        paint(cv, poly(cv, [(x, y - 1.5), (x + 4, y - 1.2), (x + 4.5, y + 0.8), (x, y + 1.2)]), col, "#", PAPER)
        paint(cv, disc(cv, x - 1.6, y, 1.2), col, "o", PAPER)
    for x in range(110, 156, 3):
        cv.put(x, 41, ">", m.accent, bold=True)
    label(cv, 128, 43, "EXIT", m.accent)
    return finish(cv, ctx, m)


def sh_laugh(cv: Canvas, ctx: Ctx) -> Post:
    """You'll laugh at me: laughter floods in from every edge toward a small
    target in the middle."""
    m = REDM
    clear(cv, m)
    close = ease(ctx.u)
    rad = 70 * (1 - close) + 9
    for y in range(PIC_H):
        for x0 in range(0, cv.W, 6):
            d = math.hypot((x0 - 80) / 1.0, (y - 23) * cv.aspect)
            if d > rad:
                cv.put(x0 + (y * 3) % 6, y, "w" if (x0 + y) % 4 else "笑", PAPER if (x0 // 6 + y) % 3 else INK)
    paint(cv, ring(cv, 80, 23, 9, 2), PAPER, "@", REDBG)
    paint(cv, disc(cv, 80, 23, 3), INK, "@", PAPER)
    sym(cv, "www", 80 + 6 * math.sin(ctx.t * 9), 9, 10 * punch(ctx, 0.2), PAPER)
    return finish(cv, ctx, m, 1.2)


def sh_wrong_true(cv: Canvas, ctx: Ctx) -> Post:
    """Even a mistaken truth: a giant ○ … struck through by a red × on beat 2."""
    m = DAY
    clear(cv, m)
    b = beats_in(ctx)
    paint(cv, ring(cv, 80, 22, 34, 7), INK, "#", mix(INK, PAPER, 0.4))
    label(cv, 74, 22, "TRUE ?", INK)
    if b >= 1:
        k = min(1, (b - 1) * 4)
        for off in range(-3, 4):
            cv.line(30 + off, 2, 30 + off + 100 * k, 2 + 42 * k, REDBG, "#", bold=True)
            cv.line(130 + off, 2, 130 + off - 100 * k, 2 + 42 * k, REDBG, "#", bold=True)
    return finish(cv, ctx, m, 1.3)


def sh_right_lie(cv: Canvas, ctx: Ctx) -> Post:
    """Even a correct lie: the word LIE flips from mirror-image to readable,
    then gets a red check."""
    m = NIGHT
    clear(cv, m)
    b = beats_in(ctx)
    flip = min(1, b / 1.5)
    rows = 28
    bmp = cv.text_bitmap("LIE", rows, True)
    if flip < 0.5:
        bmp = bmp[:, ::-1]
    sx = abs(math.cos(flip * math.pi))
    w = max(1, int(bmp.shape[1] * sx))
    idx = np.linspace(0, bmp.shape[1] - 1, w).astype(int)
    sub = bmp[:, idx]
    cv.shape_field(sub, int(64 - w / 2), 8, m.fg, fill="#")
    if b >= 2:
        k = min(1, (b - 2) * 5)
        solid(cv, "✓", 128, 22, 40 * (0.6 + 0.4 * k), REDBG, "#", PAPER)
    return finish(cv, ctx, m, 1.2)


def sh_cut(cv: Canvas, ctx: Ctx) -> Post:
    """Cut-out correct answers: scissors run along a dashed line; the piece
    drops out."""
    m = DAY
    clear(cv, m)
    x0, y0, x1, y1 = 34, 7, 126, 39
    per = 2 * ((x1 - x0) + (y1 - y0))
    p = min(1.0, ctx.u * 1.25) * per

    def at(d):
        if d < x1 - x0:
            return x0 + d, y0
        d -= x1 - x0
        if d < y1 - y0:
            return x1, y0 + d
        d -= y1 - y0
        if d < x1 - x0:
            return x1 - d, y1
        return x0, y1 - (d - (x1 - x0))

    drop = max(0.0, ctx.u - 0.8) * 60
    cv.box(x0, y0 + drop, x1, y1 + drop, mix(PAPER, INK, 0.3), "+..", fill=True,
           bg=mix(PAPER, hexc("#e8d9a8"), 0.6))
    sym(cv, "ANSWER", 80, 23 + drop, 14, INK)
    for d in range(0, per, 2):
        x, y = at(d)
        cv.put(int(x), int(y), "-" if d < p else "- ", INK if d < p else mix(PAPER, INK, 0.5))
    sx, sy = at(p)
    sym(cv, "8<", sx, sy, 7, REDBG)
    return finish(cv, ctx, m)


def sh_checks(cv: Canvas, ctx: Ctx) -> Post:
    """Checking, again and again, every day: a calendar ticked off at 16th-note speed."""
    m = DAY
    clear(cv, m)
    cv.box(8, 1, 151, 44, INK, "+=|", bold=True)
    label(cv, 66, 3, "E V E R Y   D A Y", INK)
    days = "SUN MON TUE WED THU FRI SAT".split()
    cw, rh = 20, 7
    for i, d in enumerate(days):
        label(cv, 12 + i * cw + 7, 8, d, REDBG if i == 0 else INK)
    n = int(beats_in(ctx) * 4) + 1
    for k in range(35):
        c, r = k % 7, k // 7
        x, y = 11 + c * cw, 10 + r * rh
        cv.box(x, y, x + cw - 2, y + rh - 1, mix(PAPER, INK, 0.4), "+-|")
        label(cv, x + 1, y + 1, f"{k + 1:2d}", INK, bold=False)
        if k < n:
            col = REDBG if k == n - 1 else INK
            for o in (0, 1):
                cv.line(x + 5 + o, y + 3, x + 8 + o, y + 5, col, "\\", bold=True)
                cv.line(x + 8 + o, y + 5, x + 15 + o, y + 1, col, "/", bold=True)
    return finish(cv, ctx, m)


# ======================================================== PRE-CHORUS 1

def sh_recede(cv: Canvas, ctx: Ctx) -> Post:
    """It has become far away: we fly backwards out of a tunnel of frames; the
    lit window at the end shrinks to a point."""
    m = NIGHT
    clear(cv, m)
    ph = (-ctx.lt * 1.4) % 1.0
    M.frame_tunnel(cv, ctx.t, ph, m.fg, m.mid, m.low, n=8, ratio=0.72, style="gilded",
                   aspect_hw=(cv.W * 0.62, PIC_H * 0.62), center=(80, 23))
    r = 18 * (1 - ease_out(ctx.u)) + 1.5
    paint(cv, disc(cv, 80, 23, r), PAPER, "@", mix(PAPER, INK, 0.4))
    return finish(cv, ctx, m)


def sh_dusk(cv: Canvas, ctx: Ctx) -> Post:
    """Waiting for the dark, dark night: a huge sun sinks; the sky bands go
    black one by one and stars come out."""
    m = NIGHT
    clear(cv, m)
    u = ease(ctx.u)
    hz = 34
    for i in range(8):
        y0 = i * 4
        k = max(0.0, min(1.0, u * 1.6 - (7 - i) * 0.1))
        col = mix(mix(REDBG, PAPER, 0.15 * i / 7), INK, k)
        paint(cv, rect(cv, 0, y0, cv.W, y0 + 3), col, " ")
    S.stars(cv, ctx.t, 3, 0.03 * u, PAPER, GREY)
    cy = 14 + 30 * u
    paint(cv, disc(cv, 80, cy, 24) & (cv.yy < hz), RED, "#", mix(RED, PAPER, 0.4))
    paint(cv, rect(cv, 0, hz, cv.W, PIC_H), INK, "_", mix(INK, PAPER, 0.25))
    cv.line(0, hz, cv.W, hz, PAPER, "=", bold=True)
    return finish(cv, ctx, m)


def sh_moon(cv: Canvas, ctx: Ctx) -> Post:
    """Waiting for the night (second time): a crescent moon rises in a black sky."""
    m = NIGHT
    clear(cv, m)
    S.stars(cv, ctx.t, 9, 0.03, PAPER, GREY)
    y = 34 - 18 * ease_out(ctx.u)
    moon = disc(cv, 80, y, 20) & ~disc(cv, 89, y - 3, 18)
    paint(cv, moon, PAPER, "@", mix(PAPER, INK, 0.35))
    return finish(cv, ctx, m)


def sh_colorbars(cv: Canvas, ctx: Ctx) -> Post:
    """Suddenly the colour is gone: TV colour bars drain to grey, bar by bar."""
    m = NIGHT
    clear(cv, m)
    cols = ["#c0c0c0", "#c0c000", "#00c0c0", "#00c000", "#c000c0", "#c00000", "#0000c0"]
    drain = seg(ctx.u, 0.25, 0.85)
    bw = cv.W / 7
    for i, c in enumerate(cols):
        col = hexc(c)
        k = max(0.0, min(1.0, drain * 7 - (6 - i)))
        g = float(col @ np.array([0.3, 0.59, 0.11]))
        col = mix(col, np.array([g, g, g], np.float32), k)
        paint(cv, rect(cv, i * bw, 0, (i + 1) * bw - 1, 33), col, "|", col * 0.75)
    for i in range(7):
        paint(cv, rect(cv, i * bw, 34, (i + 1) * bw - 1, 37), mix(INK, PAPER, i / 6), " ")
    paint(cv, rect(cv, 0, 38, cv.W, PIC_H), DEEP, ".", GREY)
    label(cv, 66, 41, "NO  SIGNAL" if drain >= 1 else "COLOR  ....", PAPER)
    return finish(cv, ctx, m)


def sh_wobble(cv: Canvas, ctx: Ctx) -> Post:
    """Staggering on purpose: a tall stack of blocks sways; the whole frame
    lurches with it."""
    m = DAY
    clear(cv, m)
    lean = 0.35 * math.sin(ctx.t * 4.2) + 0.1 * math.sin(ctx.t * 9)
    for i in range(10):
        y = 42 - i * 4
        x = 80 + lean * (i ** 1.6) * 1.6
        col = REDBG if i == 9 else (INK if i % 2 else mix(INK, PAPER, 0.3))
        paint(cv, rect(cv, x - 16, y - 3, x + 16, y), col, "=" if i % 2 else "#", mix(col, PAPER, 0.4))
    cv.line(0, 43, cv.W, 43, INK, "=", bold=True)
    for y in range(PIC_H):
        k = int(round(3 * math.sin(y * 0.15 + ctx.t * 5) * (0.5 + 0.5 * math.sin(ctx.t * 2))))
        if k:
            for a in (cv.ch, cv.fg, cv.bg):
                a[y] = np.roll(a[y], k, axis=0)
    return finish(cv, ctx, m)


# ======================================================== PRE-CHORUS 2

def sh_warp(cv: Canvas, ctx: Ctx) -> Post:
    """Somewhere far away: warp-speed streaks out of a single point."""
    m = NIGHT
    clear(cv, m)
    rng = np.random.default_rng(21)
    n = 260
    a = rng.uniform(0, 2 * math.pi, n)
    z0 = rng.uniform(0, 1, n)
    sp = 0.7 + 1.6 * ctx.u
    for i in range(n):
        z = (z0[i] + ctx.lt * sp) % 1.0
        r1 = 4 + 110 * z ** 2.2
        r0 = r1 * (0.75 - 0.3 * ctx.u)
        ca, sa = math.cos(a[i]), math.sin(a[i])
        cv.line(80 + r0 * ca, 23 + r0 * sa / cv.aspect, 80 + r1 * ca, 23 + r1 * sa / cv.aspect,
                PAPER if z > 0.5 else GREY)
    paint(cv, disc(cv, 80, 23, 2.5), RED, "@", PAPER)
    return finish(cv, ctx, m, 0.8)


def sh_road(cv: Canvas, ctx: Ctx) -> Post:
    """Far away (second time): a night highway rushing under us."""
    m = NIGHT
    clear(cv, m)
    S.stars(cv, ctx.t, 33, 0.02, PAPER, GREY)
    vy = 14
    paint(cv, poly(cv, [(79, vy), (81, vy), (200, PIC_H), (-40, PIC_H)]), mix(INK, PAPER, 0.12), ".",
          mix(INK, PAPER, 0.3))
    for side in (-1, 1):
        cv.line(80, vy, 80 + side * 120, PIC_H, PAPER, None, bold=True)
    for k in range(10):
        z = (k / 10 + ctx.lt * 0.9) % 1.0
        zz = z ** 2.4
        y = vy + (PIC_H - vy) * zz
        cv.line(80, y, 80, y + 0.5 + 5 * zz, RED, "#", bold=True)
    return finish(cv, ctx, m, 0.8)


def sh_sink(cv: Canvas, ctx: Ctx) -> Post:
    """Just want to sink: the water line climbs past us; a paper boat tips and goes down."""
    m = NIGHT
    clear(cv, m)
    u = ease(ctx.u)
    surface = 30 - 34 * u
    water = cv.yy > surface
    paint(cv, water, hexc("#0e2236"), "~", hexc("#1d4566"))
    M.wave_line(cv, surface, 1.0, 18, ctx.t, 0.6, PAPER, 0, cv.W)
    for k in range(5):
        x = 20 + k * 30
        cv.line(x, max(0, surface), x + 12, PIC_H, hexc("#2b5d82"), "/")
    M.bubbles(cv, ctx.t, 5, 80, PAPER)
    by = surface - 3 + 30 * seg(ctx.u, 0.35, 1.0)
    tilt = 4 * seg(ctx.u, 0.2, 0.5)
    paint(cv, poly(cv, [(64, by), (96, by - tilt), (90, by + 5 - tilt), (70, by + 5)]), PAPER, "#", GREY)
    paint(cv, poly(cv, [(80, by - 14), (80, by - 1), (92, by - 2 - tilt)]), PAPER, "/", GREY)
    return finish(cv, ctx, m, 0.6)


def sh_answer(cv: Canvas, ctx: Ctx) -> Post:
    """Don't know the answer: a quiz; the cursor hops between A-D, everything gets crossed out."""
    m = DAY
    clear(cv, m)
    sym(cv, "Q.", 18, 10, 14, REDBG)
    cv.box(34, 4, 152, 15, INK, "+=|", bold=True)
    sym(cv, "? ? ?", 93, 9.5, 8, INK)
    i = int(beats_in(ctx) * 2)
    for k, opt in enumerate("ABCD"):
        x, y = 10 + (k % 2) * 72, 20 + (k // 2) * 12
        on = k == i % 4
        cv.box(x, y, x + 66, y + 9, INK, "+-|", fill=True, bg=REDBG if on else PAPER, bold=on)
        sym(cv, opt, x + 8, y + 4.5, 7, PAPER if on else INK)
        if k < i // 4 or ctx.u > 0.8:
            cv.line(x + 2, y + 4, x + 64, y + 5, INK, "=", bold=True)
    return finish(cv, ctx, m)


def sh_clean(cv: Canvas, ctx: Ctx) -> Post:
    """A uselessly pretty room: perfectly symmetrical and empty, a glint
    sweeping across; then the music stops and the lights cut."""
    P = ctx.params
    m = DAY
    clear(cv, m)
    M.room(cv, (0, 0, cv.W - 1, PIC_H), m.fg, m.mid, m.faint, t=ctx.t, tatami=True, window=False,
           wall_frame=True, night_window=False)
    gx = (ctx.lt * 90) % 260 - 50
    for k in range(-6, 7):
        cv.line(gx + k, 0, gx + k - 25, PIC_H, PAPER if abs(k) > 2 else mix(PAPER, RED, 0.2), "/")
    sym(cv, "✧" if False else "*", 120, 12, 8 * punch(ctx, 0.3), REDBG)
    p = finish(cv, ctx, m, 0.3, vignette=0.15)
    stop = P.get("stop", 1e9)
    if ctx.t >= stop:
        on = ctx.feat("onset") > 0.8
        if on:
            cv.bg[:] = INK
            cv.ch[:] = 0
            jp(cv, ctx, NIGHT)
        p.fade = 1 - 0.35 * seg(ctx.t, stop, ctx.t1)
    return p


# =============================================================== CHORUS

def sh_forbid(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect: the word slams in, then a red NO sign stamps over it."""
    m = NIGHT if not ctx.params.get("red") else REDM
    clear(cv, m)
    ln = ctx.line()
    word = (ln.text[:2] if ln else "期待")
    b = beats_in(ctx)
    k = punch(ctx, 0.1)
    solid(cv, word, 80, 22, 38 * k, PAPER if m is NIGHT else INK, "#",
          mix(PAPER, INK, 0.4) if m is NIGHT else mix(INK, REDBG, 0.4))
    if b >= 1.0:
        s = min(1.0, (b - 1) * 4)
        r = 34 * (1.6 - 0.6 * s)
        sign_col = RED if m is NIGHT else PAPER
        paint(cv, ring(cv, 80, 22, r, 5), sign_col, "#", mix(sign_col, INK, 0.3))
        a = -math.pi / 4
        for off in np.linspace(-2.2, 2.2, 9):
            cv.line(80 - r * 0.92 * math.cos(a) + off, 22 - r * 0.92 * math.sin(a) / cv.aspect,
                    80 + r * 0.92 * math.cos(a) + off, 22 + r * 0.92 * math.sin(a) / cv.aspect,
                    sign_col, "#", bold=True)
    return finish(cv, ctx, m, 1.5)


def sh_expectbar(cv: Canvas, ctx: Ctx) -> Post:
    """Mustn't expect (again): an EXPECTATION bar loads to 99% … and crashes to 0."""
    m = NIGHT
    clear(cv, m)
    u = ctx.u
    crash = u > 0.62
    v = 0.0 if crash else min(0.99, ease(u / 0.62))
    sym(cv, "EXPECTATION", 80, 9, 9, m.fg)
    cv.box(10, 18, 150, 30, m.fg, "+=|", bold=True)
    fill = int(138 * v)
    paint(cv, rect(cv, 12, 20, 12 + fill, 28), RED if not crash else DEEP, "#", PAPER)
    sym(cv, f"{int(v * 100):2d}%" if not crash else "0%", 80, 38, 10, RED if crash else m.fg)
    p = finish(cv, ctx, m, 1.5)
    if crash:
        S.glitch_rows(cv, ctx.rng(ctx.frame), 0.8, 20)
        p.chroma = 5
    return p


def sh_shard(cv: Canvas, ctx: Ctx) -> Post:
    """A talent so sharp it hurts: a red crystal grows a new spike on every beat."""
    m = NIGHT
    clear(cv, m)
    rng = np.random.default_rng(5)
    nb = int(beats_in(ctx)) + 1
    for k in range(min(nb, 5)):
        n = 9
        ang = np.sort(rng.uniform(0, 2 * math.pi, n))
        grow = ease_out(min(1.0, (beats_in(ctx) - k) * 2.5))
        pts = []
        for i, a in enumerate(ang):
            r = (10 + 30 * rng.uniform(0.3, 1.0)) * grow * (1.15 if i % 2 else 0.45)
            pts.append((80 + r * math.cos(a) * 1.7, 23 + r * math.sin(a)))
        col = RED if k == min(nb, 5) - 1 else mix(RED, INK, 0.45 + 0.1 * k)
        paint(cv, poly(cv, pts), col, "/" if k % 2 else "\\", mix(col, PAPER, 0.35))
    paint(cv, disc(cv, 80, 23, 4 * punch(ctx, 0.5)), PAPER, "@", RED)
    return finish(cv, ctx, m, 1.6)


def sh_spotlight(cv: Canvas, ctx: Ctx) -> Post:
    """Smash the spotlight: the light on an empty microphone flickers, then
    bursts into flying shards."""
    m = NIGHT
    clear(cv, m)
    tb = ctx.params["break"]
    stage = 42

    def draw_light(tt):
        rng = ctx.rng(int(tt * 30), 4)
        M.lamp(cv, 80, 0, m.fg, m.mid)
        M.spotlight(cv, 80, 2, stage, 34, m.fg, intensity=1.0, flicker=0.3, rng=rng)
        cv.line(4, stage + 1, cv.W - 4, stage + 1, m.fg, "=", bold=True)

    if ctx.t < tb:
        draw_light(ctx.t)
        p = finish(cv, ctx, m, 0.6, glow=0.9)
    else:
        tmp = cv.snapshot()
        cv.ch[:] = 0
        draw_light(tb)
        snap = cv.snapshot()
        cv.restore(tmp)
        M.shatter(cv, snap, ctx.t - tb, (80, 20), seed=7, speed=60, gravity=80)
        p = finish(cv, ctx, m, 1.0)
        k = max(0.0, 1 - (ctx.t - tb) * 5)
        p.flash, p.chroma = 0.6 * k, int(7 * k)
    # the empty microphone
    cv.line(80, 24, 80, stage, PAPER, "|", bold=True)
    paint(cv, disc(cv, 80, 21, 3.2), RED, "#", PAPER)
    cv.line(74, stage, 86, stage, PAPER, "=", bold=True)
    return p


def sh_up(cv: Canvas, ctx: Ctx) -> Post:
    """Up, up high!  Variants: an elevator racing up a tower, a rocket of
    arrows, a balloon of light."""
    v = ctx.params.get("v", "elevator")
    b = beats_in(ctx)
    if v == "elevator":
        m = NIGHT
        clear(cv, m)
        for side, x0 in ((0, 4), (1, 116)):
            for y in range(-4, PIC_H + 4, 4):
                yy = (y + ctx.lt * 60) % (PIC_H + 8) - 4
                for x in range(x0, x0 + 40, 6):
                    lit = ((x * 7 + int(y)) % 5) == 0
                    cv.put(x, int(yy), "[]" if lit else "..", PAPER if lit else GREY)
        cv.box(52, 2, 108, 44, PAPER, "+=|", bold=True)
        floor = int(10 + ctx.lt * 40)
        sym(cv, f"{floor:3d}F", 80, 18, 18, RED)
        sym(cv, "↑", 80, 36, 12 * punch(ctx, 0.25), PAPER)
    elif v == "arrows":
        m = REDM
        clear(cv, m)
        for i in range(7):
            y = (40 - (ctx.lt * 50 + i * 9) % 60)
            sym(cv, "↑", 20 + i * 20, y, 14, PAPER if i % 2 else INK)
        sym(cv, "UP", 80, 22, 26 * punch(ctx, 0.12), PAPER)
    else:  # balloon
        m = DAY
        clear(cv, m)
        y = 40 - 46 * ease(ctx.u)
        cv.line(80, y + 11, 80 + 3 * math.sin(ctx.t * 6), y + 30, INK, "|")
        paint(cv, disc(cv, 80, y, 11), REDBG, "@", mix(REDBG, PAPER, 0.4))
        for k in range(5):
            cv.put(10 + k * 30, int((ctx.lt * 30 + k * 7) % PIC_H), "-- " * 3, mix(PAPER, INK, 0.3))
        label(cv, 6, 3, f"ALT {int(ctx.lt * 1200):5d} m", INK)
    return finish(cv, ctx, m, 1.2)


def sh_sphere(cv: Canvas, ctx: Ctx) -> Post:
    """No way out -- it's just a sphere: a red escape path runs around the
    globe and comes back to where it started."""
    m = NIGHT
    clear(cv, m)
    S.stars(cv, ctx.t, 13, 0.015, PAPER, GREY)
    pull = ctx.params.get("pull", False)
    R = 36 if not pull else 36 - 16 * ease(ctx.u)
    cx, cy = 80, 23 * cv.aspect
    lon = 40 - 120 * ctx.u
    S.globe(cv, cx, cy, R, lon, tilt=0.35, fg=m.fg, dim=m.low, accent=m.mid)
    u = ctx.u
    n = 160
    for i in range(n):
        a = i / n * 2 * math.pi
        if a > u * 2.2 * math.pi:
            break
        x = cx + R * 1.05 * math.cos(a)
        y = cy + R * 0.32 * math.sin(a) - 4
        front = math.sin(a) > 0
        cv.put(int(x), int(y / cv.aspect), "#" if front else ".", RED if front else REDDK, bold=front)
    a = u * 2.2 * math.pi
    sym(cv, "▲", cx + R * 1.05 * math.cos(a), (cy + R * 0.32 * math.sin(a) - 4) / cv.aspect - 2, 5, RED)
    if u > 0.75:
        label(cv, 64, 2, "RETURNED TO START", RED)
    if pull:
        for i in range(3):
            k = 1 + i * 0.35
            S.picture_frame(cv, 80 - R * k - 6, 23 - R * k / cv.aspect - 2, 80 + R * k + 6,
                            23 + R * k / cv.aspect + 2, m.mid, m.low, style="simple", depth=2)
    return finish(cv, ctx, m, 1.0)


def sh_heart(cv: Canvas, ctx: Ctx) -> Post:
    """An emotion that hurts: a red heart beating on every kick, an ECG line
    spiking across it."""
    m = NIGHT
    clear(cv, m)
    k = 1 + 0.18 * ctx.pulse(7)
    solid(cv, "♥", 80, 23, 44 * k, RED, "#", mix(RED, PAPER, 0.35))
    xs = np.arange(cv.W)
    ph = (xs / 40 - ctx.lt * 1.3) % 1.0
    ys = 23 - np.where((ph > 0.45) & (ph < 0.5), 14 * np.sin((ph - 0.45) / 0.05 * math.pi), 0) \
        + np.where((ph > 0.5) & (ph < 0.53), 6, 0)
    for x in xs[1:]:
        cv.line(x - 1, ys[x - 1], x, ys[x], PAPER, None, bold=True)
    label(cv, 6, 3, f"BPM {int(152 + 40 * ctx.pulse(4)):3d}", RED)
    return finish(cv, ctx, m, 1.4)


def sh_coldclock(cv: Canvas, ctx: Ctx) -> Post:
    """The everyday's face is cold: a frozen clock, icicles growing, a
    thermometer dropping below zero.  ``peek=True`` sees it through a keyhole."""
    m = DAY
    cv.clear(mix(PAPER, COLD, 0.55), INK)
    R = 34
    S.clock(cv, 70, 23 * cv.aspect, R, 7 + 3 * ctx.u, INK, mix(INK, COLD, 0.6), RED, sweep=ctx.beat_frac)
    for i in range(16):
        x = 8 + i * 10
        ln_ = (3 + (i * 7) % 6) * ease_out(min(1.0, ctx.u * 1.5 + 0.1 * (i % 3)))
        paint(cv, poly(cv, [(x - 2, 0), (x + 2, 0), (x, ln_)]), PAPER, "V", COLD)
    # thermometer
    t = 5 - 25 * ease(ctx.u)
    cv.box(140, 4, 148, 40, INK, "+-|", bold=True)
    lvl = 38 - (t + 25) / 35 * 32
    paint(cv, rect(cv, 142, lvl, 146, 39), hexc("#3b82c4"), "|", PAPER)
    label(cv, 132, 42, f"{t:+5.1f}°C", INK)
    if ctx.params.get("peek"):
        hole = disc(cv, 70, 15, 22) | poly(cv, [(58, 22), (82, 22), (92, 45), (48, 45)])
        cv.ch[~hole] = cv.ids("#")[0]
        cv.bg[~hole] = INK
        cv.fg[~hole] = mix(INK, PAPER, 0.12)
    return finish(cv, ctx, m, 0.8)


def sh_door(cv: Canvas, ctx: Ctx) -> Post:
    """Come on, over here: a door swings open, light floods the floor, arrows
    pull us in; at the end we go through."""
    m = NIGHT
    clear(cv, m)
    op = ease_out(seg(ctx.u, 0.0, 0.5))
    zoom = ease(seg(ctx.t, ctx.t1 - 0.8, ctx.t1))
    s = 1 + 5 * zoom ** 2
    cx, cy = 80, 24
    hw, hh = 14 * s, 20 * s
    paint(cv, poly(cv, [(cx - hw, cy + hh), (cx + hw, cy + hh), (cx + hw * 3, PIC_H + 10),
                        (cx - hw * 3, PIC_H + 10)]), mix(INK, PAPER, 0.25), ".", PAPER)
    paint(cv, rect(cv, cx - hw, cy - hh, cx + hw, cy + hh), PAPER, " ")
    # door leaf swinging toward us (perspective quad)
    leaf_w = hw * 2 * (1 - op)
    paint(cv, poly(cv, [(cx - hw, cy - hh), (cx - hw + leaf_w, cy - hh - 3 * op), (cx - hw + leaf_w, cy + hh + 3 * op),
                        (cx - hw, cy + hh)]), REDBG, "#", REDDK)
    S.picture_frame(cv, cx - hw - 3, cy - hh - 2, cx + hw + 3, cy + hh + 1, m.fg, m.mid, style="gilded")
    for i in range(4):
        x = (ctx.lt * 50 + i * 18) % 70
        cv.put(int(cx - hw - 10 - 60 + x), int(cy + 8), ">>", RED, bold=True)
        cv.put(int(cx + hw + 10 + 60 - x), int(cy + 8), "<<", RED, bold=True)
    return finish(cv, ctx, m, 0.8, flash=0.8 * zoom ** 3, glow=0.2)


# ============================================================ B SECTION 2

def sh_pass(cv: Canvas, ctx: Ctx) -> Post:
    """Someone brushed past: two lights rush toward each other on the same
    line and graze at the centre."""
    m = NIGHT
    clear(cv, m)
    u = ctx.u
    for y in range(4, PIC_H, 6):
        cv.line(0, y, cv.W, y, mix(INK, PAPER, 0.08), "-")
    xa = -20 + 200 * u
    xb = 180 - 200 * u
    for x, y, col, d in ((xa, 21, PAPER, 1), (xb, 25, RED, -1)):
        for k in range(30):
            cv.put(int(x - d * k * 2), y, "=" if k < 10 else "-", mix(col, INK, k / 30), bold=k < 3)
        paint(cv, disc(cv, x, y, 3), col, "@", mix(col, INK, 0.3))
    near = math.exp(-((u - 0.5) * 12) ** 2)
    p = finish(cv, ctx, m, 0.6)
    p.flash = 0.25 * near
    p.chroma = int(5 * near)
    return p


def sh_dodge(cv: Canvas, ctx: Ctx) -> Post:
    """Dodging on purpose: a cursor zig-zags between falling blocks."""
    m = DAY
    clear(cv, m)
    rng = np.random.default_rng(31)
    for i in range(22):
        x = rng.uniform(4, 156)
        y = (rng.uniform(0, PIC_H) + ctx.lt * rng.uniform(15, 30)) % (PIC_H + 6) - 6
        paint(cv, rect(cv, x - 4, y, x + 4, y + 3), INK, "#", mix(INK, PAPER, 0.3))
    b = beats_in(ctx)
    x = 80 + 40 * math.sin(b * math.pi)
    sym(cv, "▲", x, 37, 12, REDBG)
    for k in range(1, 8):
        xx = 80 + 40 * math.sin((b - k * 0.08) * math.pi)
        cv.put(int(xx), 41 + k // 2, ".", REDBG)
    return finish(cv, ctx, m, 0.6)


def sh_sleep(cv: Canvas, ctx: Ctx) -> Post:
    """Want to sleep alone: a battery drains to empty; giant Zzz float up; the screen dims."""
    m = NIGHT
    clear(cv, m)
    lvl = 1 - ease(ctx.u)
    cv.box(30, 12, 100, 34, PAPER, "+=|", bold=True)
    paint(cv, rect(cv, 101, 19, 104, 27), PAPER, " ")
    col = RED if lvl < 0.25 else PAPER
    paint(cv, rect(cv, 33, 15, 33 + 64 * lvl, 31), col, "#", mix(col, INK, 0.4))
    label(cv, 52, 37, f"{int(lvl * 100):3d}%  SLEEP MODE", m.mid)
    for k in range(3):
        z = (ctx.lt * 0.6 + k / 3) % 1
        sym(cv, "Z", 118 + 14 * z + 6 * k, 38 - 34 * z, 6 + 10 * z, mix(PAPER, INK, z))
    return finish(cv, ctx, m, 0.3, fade=1 - 0.35 * ctx.u)


def sh_rain(cv: Canvas, ctx: Ctx) -> Post:
    """That seems sad: a downpour beating on one umbrella."""
    m = NIGHT
    clear(cv, m)
    rng = np.random.default_rng(12)
    n = 360
    xs = rng.uniform(0, cv.W, n)
    y0 = rng.uniform(0, PIC_H, n)
    ys = (y0 + ctx.lt * rng.uniform(30, 45, n)) % PIC_H
    um = solid(cv, "☂", 80, 24, 40, mix(INK, PAPER, 0.2), "#", mix(INK, PAPER, 0.45))
    hit = ~um[np.clip(ys.astype(int), 0, cv.H - 1), np.clip(xs.astype(int), 0, cv.W - 1)]
    cv.scatter(xs[hit], ys[hit], "/", fg=mix(PAPER, INK, 0.35))
    for k in range(10):
        x = 52 + k * 6 + 2 * math.sin(ctx.t * 7 + k)
        cv.put(int(x), 8 - (k % 3), "'", PAPER)
    return finish(cv, ctx, m, 0.3)


def sh_bottom(cv: Canvas, ctx: Ctx) -> Post:
    """The bottom of a worn-out road: we stare down a square well of steps;
    in the break it goes dark."""
    P = ctx.params
    m = NIGHT
    clear(cv, m)
    ph = (ctx.lt * 0.8) % 1.0
    for k in range(12, -1, -1):
        s = 0.75 ** (k - ph)
        hw, hh = 80 * s, 26 * s
        col = mix(INK, PAPER, max(0.05, 0.8 - k * 0.07))
        cv.box(80 - hw, 23 - hh, 80 + hw, 23 + hh, col, "+=|" if k % 2 else "+-:")
    paint(cv, rect(cv, 78, 22, 82, 24), RED, "@", PAPER)
    p = finish(cv, ctx, m, 0.5)
    brk = seg(ctx.t, P.get("brk", 1e9), P.get("brk", 1e9) + 0.4)
    if brk > 0:
        S.char_noise(cv, ctx.rng(ctx.frame), 0.04 * brk)
        cv.fg[:PIC_H] = mix(cv.fg[:PIC_H], INK, 0.6 * brk)
    return p


# ============================================================ CHORUS 2

def sh_gameover(cv: Canvas, ctx: Ctx) -> Post:
    """Second / third failure: a GAME OVER card stamps the strike count."""
    n = ctx.params["n"]
    m = REDM if n == 3 else NIGHT
    clear(cv, m)
    sym(cv, "FAILED", 80, 10, 16 * punch(ctx, 0.08), PAPER)
    b = beats_in(ctx)
    for i in range(n):
        on = b >= i * 0.75
        x = 80 + (i - (n - 1) / 2) * 34
        if on:
            solid(cv, "×", x, 31, 22, RED if m is NIGHT else INK, "#", PAPER)
        else:
            cv.box(x - 10, 24, x + 10, 38, m.mid, "+-|")
    rng = np.random.default_rng(n)
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi)
        cv.line(80, 23, 80 + 120 * math.cos(a), 23 + 40 * math.sin(a), mix(PAPER, INK, 0.3))
    return finish(cv, ctx, m, 1.6)


def sh_crash(cv: Canvas, ctx: Ctx) -> Post:
    """Expecting it was a loss: the stock chart of hope plunges off the bottom."""
    m = NIGHT
    clear(cv, m)
    for y in range(4, 44, 8):
        cv.line(8, y, 152, y, mix(INK, PAPER, 0.1), "-")
    rng = np.random.default_rng(3)
    steps = np.cumsum(rng.normal(0.35, 1.2, 80))
    pts = []
    n = int(80 * min(1, ctx.u * 1.3))
    for i in range(n):
        x = 8 + i * 1.8
        y = 30 - steps[i] * 0.6
        if i > 50:
            y += (i - 50) ** 1.7 * 0.35
        pts.append((x, min(PIC_H + 5, y)))
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED if b[1] > a[1] else PAPER, None, bold=True)
    if n > 55:
        sym(cv, "-100%", 120, 12, 12, RED)
    return finish(cv, ctx, m, 1.2)


def sh_conveyor(cv: Canvas, ctx: Ctx) -> Post:
    """Nothing but monotonous work: identical boxes on a belt, a press
    stamping each one on the beat."""
    m = DAY
    clear(cv, m)
    sp = ctx.beat * 20.0
    for i in range(-2, 10):
        x = (i * 20 + sp) % 220 - 30
        stamped = x > 80
        cv.box(x, 26, x + 16, 36, INK, "+-|", fill=True, bg=PAPER, bold=True)
        if stamped:
            label(cv, int(x) + 5, 31, "OK", REDBG)
    cv.line(0, 37, cv.W, 37, INK, "=", bold=True)
    for x in range(int(-sp) % 4, cv.W, 4):
        cv.put(x, 38, "o", INK)
    press = 22 * (1 - ctx.pulse(10))
    paint(cv, rect(cv, 70, 0, 92, 4 + (1 - press / 22) * 20), INK, "#", mix(INK, PAPER, 0.3))
    paint(cv, rect(cv, 68, 4 + (1 - press / 22) * 20, 94, 6 + (1 - press / 22) * 20), REDBG, "=", PAPER)
    label(cv, 110, 4, f"TASK {int(ctx.beat) % 1000:04d}", INK)
    return finish(cv, ctx, m, 1.3)


def sh_loop(cv: Canvas, ctx: Ctx) -> Post:
    """How about repeating it?  A giant loop arrow spins; the counter climbs."""
    m = REDM
    clear(cv, m)
    rot = ctx.lt * 6
    r = 30
    for i in range(200):
        a = i / 200 * 2 * math.pi * 0.85 + rot
        x = 60 + r * 1.7 * math.cos(a)
        y = 23 + r * math.sin(a) * 0.62
        cv.put(int(x), int(y), "#", PAPER, bold=True)
        cv.put(int(x) + 1, int(y), "#", PAPER, bold=True)
    a = 2 * math.pi * 0.85 + rot
    sym(cv, "▶", 60 + r * 1.7 * math.cos(a), 23 + r * math.sin(a) * 0.62, 8, PAPER)
    sym(cv, f"×{int(beats_in(ctx) * 4) + 1:03d}", 128, 22, 12, INK)
    return finish(cv, ctx, m, 1.2)


def sh_maze(cv: Canvas, ctx: Ctx) -> Post:
    """No escape route: maze walls build in around a single red dot."""
    m = NIGHT
    clear(cv, m)
    rng = np.random.default_rng(17)
    cells_x, cells_y, cw, chh = 20, 9, 8, 5
    n = int(len(range(cells_x * cells_y)) * min(1.0, ctx.u * 1.2))
    order = rng.permutation(cells_x * cells_y)
    for k in order[:n]:
        cx_, cy_ = k % cells_x, k // cells_x
        x, y = cx_ * cw, cy_ * chh
        if rng.random() < 0.5:
            cv.line(x, y, x + cw, y, PAPER, "#", bold=True)
        else:
            cv.line(x, y, x, y + chh, PAPER, "#", bold=True)
    cv.box(0, 0, cells_x * cw - 1, cells_y * chh, PAPER, "###", bold=True)
    a = ctx.t * 9
    paint(cv, disc(cv, 80 + 2 * math.sin(a), 22 + math.cos(a), 2.4), RED, "@", PAPER)
    return finish(cv, ctx, m, 1.0)


def sh_eye(cv: Canvas, ctx: Ctx) -> Post:
    """You've noticed, haven't you?  A giant eye opens, looks around -- and
    looks straight at us."""
    m = DAY
    clear(cv, m)
    op = ease_out(seg(ctx.u, 0.0, 0.3))
    blink = ctx.u > 0.85 and ctx.u < 0.9
    h = 17 * op * (0.1 if blink else 1.0)
    W_ = 66
    pts_top = [(80 + W_ * math.cos(a), 23 - h * math.sin(a)) for a in np.linspace(0, math.pi, 30)]
    pts_bot = [(80 + W_ * math.cos(a), 23 - h * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 30)]
    eye = poly(cv, pts_top + pts_bot)
    paint(cv, eye, PAPER, " ")
    look = ctx.u
    ix = 80 + (28 * math.sin(look * 9) if look < 0.6 else 0)
    iy = 23
    iris = disc(cv, ix, iy, 14) & eye
    paint(cv, iris, REDBG, "*", mix(REDBG, INK, 0.3))
    paint(cv, disc(cv, ix, iy, 6) & eye, INK, "@", mix(INK, PAPER, 0.15))
    paint(cv, disc(cv, ix - 4, iy - 3, 1.8) & eye, PAPER, " ")
    cv.polyline(pts_top, INK, char="#", bold=True)
    cv.polyline(pts_bot, INK, char="#", bold=True)
    for i, a in enumerate(np.linspace(0.3, math.pi - 0.3, 9)):
        x, y = 80 + W_ * math.cos(a), 23 - h * math.sin(a)
        cv.line(x, y, x + 6 * math.cos(a), y - 4 * math.sin(a) - 1, INK, None)
    return finish(cv, ctx, m, 0.8)


def sh_switch(cv: Canvas, ctx: Ctx) -> Post:
    """Want to stop expecting: a big switch labelled EXPECT is thrown ON → OFF;
    the red drains out."""
    b = beats_in(ctx)
    off = b >= 1.5
    m = NIGHT
    clear(cv, m)
    if not off:
        cv.bg[:PIC_H] = mix(INK, RED, 0.3)
    sym(cv, "EXPECT", 80, 6, 7, PAPER)
    cv.box(54, 12, 106, 42, PAPER, "+=|", fill=True, bg=DEEP, bold=True)
    k = min(1.0, max(0.0, (b - 1.2) * 5))
    ly = 18 + 18 * k
    paint(cv, rect(cv, 64, ly - 3, 96, ly + 3), RED if not off else GREY, "#", PAPER)
    label(cv, 110, 16, "ON", RED if not off else GREY)
    label(cv, 110, 38, "OFF", PAPER if off else GREY)
    return finish(cv, ctx, m, 1.0)


# ================================================================ FINALE

def finale_room(cv: Canvas, ctx: Ctx) -> Post:
    """'Come on' one last time: we pull back out of the Earth to find it hung
    in a picture frame on the wall of an empty room -- 日常と地球の額縁."""
    P = ctx.params
    m = DAY
    clear(cv, m)
    end_hold = P["hold"]
    u = ease(seg(ctx.t, ctx.t0, end_hold))
    s = 7.0 * (1 - u) + 1.0 * u
    W, H = cv.W - 1, PIC_H
    fr = M.room_frame_rect((0, 0, W, H), 0.42, 0.55, 0.8)
    fc = ((fr[0] + fr[2]) / 2, (fr[1] + fr[3]) / 2)
    vp = (fc[0] - fc[0] * s, fc[1] - fc[1] * s, fc[0] + (W - fc[0]) * s, fc[1] + (H - fc[1]) * s)
    M.room(cv, vp, m.fg, m.mid, m.faint, t=ctx.t, frame_globe_lon=140 - 24 * (ctx.t - end_hold),
           accent=m.accent, night_window=False, frame_w=0.55, frame_h=0.8)
    p = post_for(m, ctx, vignette=0.4)
    if ctx.t < end_hold:
        jp(cv, ctx, m)
    hit = P["hit"]
    if ctx.t >= hit:
        p.flash = 0.7 * max(0.0, 1 - (ctx.t - hit) * 4)
    if ctx.t >= P["out"]:
        p.fade = max(0.0, 1 - (ctx.t - P["out"]) * 6)
    return p
