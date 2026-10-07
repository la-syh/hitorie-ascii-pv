"""Glyph atlas: every character the PV can show, pre-rasterised into cell tiles.

A frame is a grid of glyph *indices*; turning it into pixels is then a single
numpy gather (see ``raster.py``).  Wide (CJK) characters occupy two cells and
are stored as a left half and a right half.
"""
from __future__ import annotations

import string
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .lrc import char_width

ROOT = Path(__file__).resolve().parent.parent
FONT_REGULAR = ROOT / "assets" / "fonts" / "BIZUDGothic-Regular.ttf"
FONT_BOLD = ROOT / "assets" / "fonts" / "BIZUDGothic-Bold.ttf"

ASCII = "".join(chr(c) for c in range(32, 127))


class Atlas:
    """Maps (char, bold) -> glyph index, and holds the tile bitmaps."""

    def __init__(self, cell_w: int = 12, cell_h: int = 20, size: int = 22):
        self.cw, self.ch, self.size = cell_w, cell_h, size
        self.fonts = {
            False: ImageFont.truetype(str(FONT_REGULAR), size),
            True: ImageFont.truetype(str(FONT_BOLD), size),
        }
        self.zh_font = ImageFont.truetype(str(ROOT / "assets/fonts/FusionPixel-12px.ttf"), max(12, round(size / 12) * 12))
        self.zh_chars = set()
        self.tiles: list[np.ndarray] = []
        self.index: dict[tuple[str, bool], int | tuple[int, int]] = {}
        self._arr: np.ndarray | None = None
        # baseline for half-width text: centre the ink of "Hg|" vertically
        f = self.fonts[False]
        top = min(f.getbbox(c)[1] for c in "H|(")
        bot = max(f.getbbox(c)[3] for c in "gjy|(")
        self._latin_dy = (cell_h - (bot - top)) / 2 - top
        self.tiles.append(np.zeros((cell_h, cell_w), np.float32))  # 0 = blank
        self.index[(" ", False)] = 0
        self.index[(" ", True)] = 0
        self.ensure(ASCII)
        self.ensure(ASCII, bold=True)

    # ------------------------------------------------------------------ build
    def _render(self, c: str, bold: bool) -> list[np.ndarray]:
        w = char_width(c)
        W, H = self.cw * w, self.ch
        im = Image.new("L", (W * 2, H * 2), 0)
        d = ImageDraw.Draw(im)
        f = self.zh_font if c in self.zh_chars else self.fonts[bold]
        adv = f.getlength(c)
        if w == 1:
            x = (W - adv) / 2
            d.text((x + W / 2, self._latin_dy + H / 2), c, font=f, fill=255)
        else:
            l, t, r, b = f.getbbox(c)
            x = (W - adv) / 2
            y = (H - (b - t)) / 2 - t if b > t else 0
            d.text((x + W / 2, y + H / 2), c, font=f, fill=255)
        a = np.asarray(im, dtype=np.float32)[H // 2: H // 2 + H, W // 2: W // 2 + W] / 255.0
        return [a[:, i * self.cw:(i + 1) * self.cw] for i in range(w)]

    def ensure(self, chars, bold: bool = False) -> None:
        for c in chars:
            if (c, bold) in self.index:
                continue
            parts = self._render(c, bold)
            ids = []
            for p in parts:
                self.tiles.append(p)
                ids.append(len(self.tiles) - 1)
            self.index[(c, bold)] = ids[0] if len(ids) == 1 else (ids[0], ids[1])
            self._arr = None

    # ----------------------------------------------------------------- access
    def get(self, c: str, bold: bool = False):
        key = (c, bold)
        if key not in self.index:
            self.ensure(c, bold)
        return self.index[key]

    def ids(self, s: str, bold: bool = False) -> np.ndarray:
        """Indices for a string of *half-width* characters (e.g. a ramp)."""
        out = []
        for c in s:
            g = self.get(c, bold)
            out.append(g if isinstance(g, int) else g[0])
        return np.array(out, dtype=np.int32)

    @property
    def array(self) -> np.ndarray:
        if self._arr is None:
            self._arr = np.stack(self.tiles).astype(np.float32)
        return self._arr

    def coverage(self, s: str, bold: bool = False) -> np.ndarray:
        arr = self.array
        return np.array([arr[i].mean() for i in self.ids(s, bold)])

    def ramp(self, chars: str, n: int | None = None, bold: bool = False) -> str:
        """Sort characters by ink coverage (light -> dark), optionally subsample."""
        uniq = "".join(dict.fromkeys(chars))
        cov = self.coverage(uniq, bold)
        order = np.argsort(cov, kind="stable")
        s = "".join(uniq[i] for i in order)
        if n and n < len(s):
            pick = np.linspace(0, len(s) - 1, n).round().astype(int)
            s = "".join(s[i] for i in pick)
        return s


def charset_for(text_iterable) -> set[str]:
    s: set[str] = set(ASCII)
    for t in text_iterable:
        s.update(t)
    return s


# a few useful pre-built ramps (sorted at runtime by actual font coverage)
RAMP_FULL = " .'`,:;-~_^\"!i|/\\()<>+=*?1lcrtvxzsjfJunoaeYCLTZ#%&$@MWB8"
RAMP_SOFT = " .,:-=+*#%@"
RAMP_DOTS = " .:oO@"
RAMP_BIN = " 01"
RAMP_HATCH = " .-=#"
