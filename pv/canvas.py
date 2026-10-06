"""Character-grid canvas with drawing primitives.

The canvas stores, per cell: a glyph index, a foreground colour and a
background colour.  Everything in the PV is drawn with these primitives, so
the final picture is *always* made of characters.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .glyphs import Atlas, FONT_BOLD, FONT_REGULAR
from .lrc import char_width

Color = tuple[float, float, float]


def hexc(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


class Canvas:
    def __init__(self, atlas: Atlas, cols: int, rows: int):
        self.atlas = atlas
        self.W, self.H = cols, rows
        self.ch = np.zeros((rows, cols), np.int32)
        self.fg = np.zeros((rows, cols, 3), np.float32)
        self.bg = np.zeros((rows, cols, 3), np.float32)
        # cell-centre coordinates, in "square" units (y scaled by cell aspect)
        self.aspect = atlas.ch / atlas.cw  # cell height / width (~1.67)
        yy, xx = np.mgrid[0:rows, 0:cols].astype(np.float32)
        self.xx, self.yy = xx, yy
        # "square" coordinates of cell centres: X in cells, Y in cell-widths
        self.X = xx + 0.5
        self.Y = (yy + 0.5) * self.aspect
        self.WU, self.HU = float(cols), rows * self.aspect  # canvas size in square units
        self._cache: dict = {}

    # ------------------------------------------------------------------ basics
    def clear(self, bg=(0, 0, 0), fg=(1, 1, 1)) -> None:
        self.ch[:] = 0
        self.bg[:] = bg
        self.fg[:] = fg

    def copy_from(self, other: "Canvas") -> None:
        self.ch[:] = other.ch
        self.fg[:] = other.fg
        self.bg[:] = other.bg

    def snapshot(self):
        return self.ch.copy(), self.fg.copy(), self.bg.copy()

    def restore(self, snap) -> None:
        self.ch[:], self.fg[:], self.bg[:] = snap

    def ids(self, s: str, bold=False) -> np.ndarray:
        key = ("ids", s, bold)
        if key not in self._cache:
            self._cache[key] = self.atlas.ids(s, bold)
        return self._cache[key]

    # -------------------------------------------------------------------- text
    def put(self, x: int, y: int, s: str, fg=None, bg=None, bold=False,
            mask: np.ndarray | None = None) -> int:
        """Write text starting at cell (x, y). Returns the end x."""
        if y < 0 or y >= self.H:
            return x + sum(char_width(c) for c in s)
        for c in s:
            w = char_width(c)
            if c == "\n":
                continue
            g = self.atlas.get(c, bold)
            parts = (g,) if isinstance(g, int) else g
            for k, gi in enumerate(parts):
                xx = x + k
                if 0 <= xx < self.W:
                    if c == " " and bg is None:
                        pass  # transparent space
                    else:
                        self.ch[y, xx] = gi
                        if fg is not None:
                            self.fg[y, xx] = fg
                    if bg is not None:
                        self.bg[y, xx] = bg
            x += w
        return x

    def put_center(self, y: int, s: str, fg=None, bg=None, bold=False, cx: float | None = None) -> int:
        w = sum(char_width(c) for c in s)
        x0 = int(round((self.W if cx is None else 2 * cx) / 2 - w / 2))
        self.put(x0, y, s, fg, bg, bold)
        return x0

    # ----------------------------------------------------------------- fields
    def density(self, field: np.ndarray, ramp: str, fg=None, bg=None, thresh=0.0,
                bold=False, color: np.ndarray | None = None, offset: tuple[int, int] = (0, 0)) -> None:
        """Map a [0,1] intensity field onto ramp characters.

        ``field`` may be smaller than the canvas; ``offset`` places it.  Cells
        whose value is <= ``thresh`` are left untouched (transparent).
        ``color`` is an optional per-cell RGB array for the foreground.
        """
        ids = self.ids(ramp, bold)
        h, w = field.shape
        ox, oy = offset
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(self.W, ox + w), min(self.H, oy + h)
        if x1 <= x0 or y1 <= y0:
            return
        f = field[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        m = f > thresh
        k = np.clip((f * (len(ids) - 1) + 0.5).astype(np.int32), 0, len(ids) - 1)
        sub_ch = self.ch[y0:y1, x0:x1]
        sub_ch[m] = ids[k[m]]
        if fg is not None:
            self.fg[y0:y1, x0:x1][m] = fg
        if color is not None:
            self.fg[y0:y1, x0:x1][m] = color[y0 - oy:y1 - oy, x0 - ox:x1 - ox][m]
        if bg is not None:
            self.bg[y0:y1, x0:x1][m] = bg

    def fill(self, mask: np.ndarray, char: str | None = None, fg=None, bg=None, bold=False) -> None:
        if char is not None:
            self.ch[mask] = self.ids(char, bold)[0]
        if fg is not None:
            self.fg[mask] = fg
        if bg is not None:
            self.bg[mask] = bg

    def scatter(self, xs, ys, chars, fg=None, bold=False) -> None:
        """Place single half-width characters at many (float) positions."""
        xs = np.asarray(xs).round().astype(int)
        ys = np.asarray(ys).round().astype(int)
        ok = (xs >= 0) & (xs < self.W) & (ys >= 0) & (ys < self.H)
        if isinstance(chars, str) and len(chars) == 1:
            gid = np.full(ok.sum(), self.ids(chars, bold)[0])
        else:
            gid = np.asarray(chars)[ok] if not isinstance(chars, str) else self.ids(chars, bold)[ok]
        self.ch[ys[ok], xs[ok]] = gid
        if fg is not None:
            fgv = np.asarray(fg, np.float32)
            self.fg[ys[ok], xs[ok]] = fgv if fgv.ndim == 1 else fgv[ok]

    # ------------------------------------------------------------------ lines
    def line(self, x0, y0, x1, y1, fg=None, char: str | None = None, bold=False) -> None:
        """Line with slope-aware characters ( - | / \\ ) unless ``char`` given."""
        dx, dy = x1 - x0, y1 - y0
        n = int(max(abs(dx), abs(dy))) + 1
        if n <= 0:
            return
        if char is None:
            ang = math.degrees(math.atan2(-dy * self.aspect, dx)) % 180
            if ang < 22.5 or ang >= 157.5:
                char = "-"
            elif ang < 67.5:
                char = "/"
            elif ang < 112.5:
                char = "|"
            else:
                char = "\\"
        ts = np.linspace(0, 1, n)
        self.scatter(x0 + dx * ts, y0 + dy * ts, char, fg, bold)

    def polyline(self, pts, fg=None, closed=False, char=None, bold=False) -> None:
        for i in range(len(pts) - (0 if closed else 1)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            self.line(a[0], a[1], b[0], b[1], fg, char, bold)

    def box(self, x0: int, y0: int, x1: int, y1: int, fg=None, style: str = "+-|",
            bg=None, fill: bool = False, bold=False) -> None:
        """Rectangle outline. style = corner, horizontal, vertical chars."""
        x0, x1 = sorted((int(x0), int(x1)))
        y0, y1 = sorted((int(y0), int(y1)))
        if fill and bg is not None:
            ys, xs = slice(max(0, y0), min(self.H, y1 + 1)), slice(max(0, x0), min(self.W, x1 + 1))
            self.ch[ys, xs] = 0
            self.bg[ys, xs] = bg
        corner, hz, vt = style[0], style[1], style[2]
        if x1 > x0:
            self.line(x0, y0, x1, y0, fg, hz, bold)
            self.line(x0, y1, x1, y1, fg, hz, bold)
        if y1 > y0:
            self.line(x0, y0, x0, y1, fg, vt, bold)
            self.line(x1, y0, x1, y1, fg, vt, bold)
        for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            self.scatter([cx], [cy], corner, fg, bold)

    # --------------------------------------------------------------- big text
    def text_bitmap(self, s: str, rows: int, bold=True, spacing: float = 0.0) -> np.ndarray:
        """Rasterise ``s`` to a coverage map that is ``rows`` cells tall.

        The bitmap is sampled per cell with cell aspect correction, so glyphs
        keep their proportions on the character grid.
        """
        key = ("bmp", s, rows, bold, spacing)
        if key in self._cache:
            return self._cache[key]
        ss = 4  # supersample
        px_h = rows * ss
        font = _font(bold, int(px_h * 0.92))
        # width of string in "square" pixels then convert to cells
        adv = [font.getlength(c) for c in s]
        gap = spacing * px_h
        total = sum(adv) + gap * max(0, len(s) - 1)
        W = int(math.ceil(total)) + 2
        im = Image.new("L", (W, px_h), 0)
        d = ImageDraw.Draw(im)
        x = 1.0
        asc, desc = font.getmetrics()
        for c, a in zip(s, adv):
            l, t, r, b = font.getbbox(c)
            y = (px_h - (b - t)) / 2 - t if b > t else 0
            if char_width(c) == 1 and c.isascii():
                y = (px_h - (asc + desc) * 0.86) / 2  # consistent latin baseline
            d.text((x, y), c, font=font, fill=255)
            x += a + gap
        # resample to cells: a cell is ss px tall and ss/aspect px wide in image space
        cols = max(1, int(round(W * self.aspect / ss)))
        small = im.resize((cols, rows), Image.BOX)
        bmp = np.asarray(small, np.float32) / 255.0
        self._cache[key] = bmp
        return bmp

    def shape_field(self, bmp: np.ndarray, ox: int, oy: int, fg=None, fill: str = "#",
                    tin: float = 0.5, tedge: float = 0.16, bold=False, color=None) -> np.ndarray:
        """Draw a coverage bitmap as 'structural' ASCII: solid cells get ``fill``,
        edge cells get a line character chosen from the local gradient
        ( _ " | / \\ ), which keeps letter shapes crisp at low resolution.
        Returns the boolean mask (bitmap-sized) of drawn cells."""
        h, w = bmp.shape
        gy, gx = np.gradient(bmp.astype(np.float32))
        gy = gy / self.aspect
        ang = (np.degrees(np.arctan2(gy, gx)) + 360.0) % 360.0
        key = ("shape_ids", fill, bold)
        if key not in self._cache:
            self._cache[key] = self.atlas.ids(fill + '_"|\\/', bold)
        ids = self._cache[key]
        k = np.full((h, w), 3, np.int32)                       # '|'
        k[(ang >= 67.5) & (ang < 112.5)] = 1                   # ink below  -> '_'
        k[(ang >= 247.5) & (ang < 292.5)] = 2                  # ink above  -> '"'
        k[((ang >= 22.5) & (ang < 67.5)) | ((ang >= 202.5) & (ang < 247.5))] = 4   # '\'
        k[((ang >= 112.5) & (ang < 157.5)) | ((ang >= 292.5) & (ang < 337.5))] = 5  # '/'
        k[bmp > tin] = 0
        m = bmp > tedge
        x0, y0 = max(0, ox), max(0, oy)
        x1, y1 = min(self.W, ox + w), min(self.H, oy + h)
        if x1 <= x0 or y1 <= y0:
            return m
        sl = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
        mm = m[sl]
        self.ch[y0:y1, x0:x1][mm] = ids[k[sl][mm]]
        if fg is not None:
            self.fg[y0:y1, x0:x1][mm] = fg
        if color is not None:
            self.fg[y0:y1, x0:x1][mm] = color[sl][mm]
        return m

    def big_text(self, s: str, cx: float, cy: float, rows: int, ramp: str = " .:-=+*#%@",
                 fg=None, bold=True, spacing=0.0, thresh=0.08, gamma=0.7, fillchars: str | None = None,
                 color: np.ndarray | None = None, shadow=None, style: str = "shape",
                 fill: str = "#") -> tuple[int, int, int, int]:
        """Draw ``s`` as big ASCII-art letters centred at (cx, cy).

        If ``fillchars`` is given, inked cells cycle through those characters
        (e.g. the lyric's own kana) instead of a density ramp.
        Returns the bounding box (x0, y0, x1, y1).
        """
        bmp = self.text_bitmap(s, rows, bold, spacing)
        if style != "shape":
            bmp = bmp ** gamma
        h, w = bmp.shape
        ox, oy = int(round(cx - w / 2)), int(round(cy - h / 2))
        if shadow is not None:
            m = np.zeros((self.H, self.W), bool)
            sx, sy = ox + 1, oy + 1
            ys0, xs0 = max(0, sy), max(0, sx)
            ys1, xs1 = min(self.H, sy + h), min(self.W, sx + w)
            if ys1 > ys0 and xs1 > xs0:
                m[ys0:ys1, xs0:xs1] = bmp[ys0 - sy:ys1 - sy, xs0 - sx:xs1 - sx] > 0.35
                self.fill(m, ".", fg=shadow)
        if fillchars:
            ids = self.ids(fillchars, True)
            field = np.zeros_like(bmp)
            field[:] = bmp
            m = field > max(thresh, 0.3)
            yy, xx = np.mgrid[0:h, 0:w]
            k = (xx + yy * 3) % len(ids)
            x0, y0 = max(0, ox), max(0, oy)
            x1, y1 = min(self.W, ox + w), min(self.H, oy + h)
            if x1 > x0 and y1 > y0:
                sl = (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))
                mm = m[sl]
                self.ch[y0:y1, x0:x1][mm] = ids[k[sl][mm]]
                if fg is not None:
                    self.fg[y0:y1, x0:x1][mm] = fg
        elif style == "shape":
            self.shape_field(bmp, ox, oy, fg, fill=fill, bold=bold, color=color)
        else:
            self.density(bmp, ramp, fg=fg, thresh=thresh, bold=bold, offset=(ox, oy),
                         color=color)
        return ox, oy, ox + w, oy + h


@lru_cache(maxsize=64)
def _font(bold: bool, px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), max(4, px))
