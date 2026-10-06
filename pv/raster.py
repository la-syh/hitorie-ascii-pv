"""Canvas -> RGB pixels, plus light "screen" post-processing.

Post effects are deliberately subtle and pixel-level only (glow, scanlines,
chromatic split, shake, flash); the image content itself is always text.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter

from .canvas import Canvas


@dataclass
class Post:
    glow: float = 0.55        # bloom amount
    glow_radius: float = 5.0
    scan: float = 0.10        # scanline darkening
    chroma: int = 0           # px of R/B channel split
    shake: tuple[int, int] = (0, 0)
    flash: float = 0.0        # add white
    fade: float = 1.0         # multiply (fade to black)
    vignette: float = 0.35
    grain: float = 0.0


class Rasterizer:
    def __init__(self, cv: Canvas):
        self.cv = cv
        a = cv.atlas
        self.h, self.w = a.ch, a.cw
        self.Hpx, self.Wpx = cv.H * self.h, cv.W * self.w
        yy = (np.arange(self.Hpx) / self.Hpx - 0.5)[:, None]
        xx = (np.arange(self.Wpx) / self.Wpx - 0.5)[None, :]
        r2 = (xx * 1.0) ** 2 + (yy * 1.15) ** 2
        self._vig = (1.0 - np.clip(r2 * 1.6, 0, 1) ** 1.5).astype(np.float32)
        scan = np.ones(self.Hpx, np.float32)
        scan[1::3] = 0.0   # every third pixel row darker
        self._scan = scan[:, None]
        rng = np.random.default_rng(7)
        self._grain = [np.repeat(np.repeat(rng.standard_normal((self.Hpx // 2, self.Wpx // 2)).astype(np.float32),
                                           2, 0), 2, 1)[:, :, None] for _ in range(4)]
        self._mult_cache: dict = {}
        self._A = None
        self._A_n = -1

    def _atlas(self) -> np.ndarray:
        n = len(self.cv.atlas.tiles)
        if n != self._A_n:
            self._A = self.cv.atlas.array
            self._A_n = n
        return self._A

    def _covmean(self) -> np.ndarray:
        A = self._atlas()
        if getattr(self, "_cm_n", -1) != len(A):
            self._cm = A.mean(axis=(1, 2)).astype(np.float32)
            self._cm_n = len(A)
        return self._cm

    def _mult(self, scan: float, vig: float, fade: float) -> np.ndarray:
        key = (round(scan, 3), round(vig, 3), round(fade, 3))
        m = self._mult_cache.get(key)
        if m is None:
            m = (1.0 - scan * (1.0 - self._scan)) * (1.0 - vig * (1.0 - self._vig)) * fade
            m = m.astype(np.float32)[:, :, None]
            if len(self._mult_cache) > 64:
                self._mult_cache.clear()
            self._mult_cache[key] = m
        return m

    def compose(self) -> np.ndarray:
        cv = self.cv
        A = self._atlas()
        R, C = cv.H, cv.W
        cov = A[cv.ch].transpose(0, 2, 1, 3)                 # (R, h, C, w)
        bg = cv.bg[:, None, :, None, :]
        d = (cv.fg - cv.bg)[:, None, :, None, :]
        img = bg + d * cov[..., None]                       # (R, h, C, w, 3), output order
        return img.reshape(self.Hpx, self.Wpx, 3)

    def render(self, post: Post, frame_no: int = 0) -> np.ndarray:
        img = self.compose()
        if post.glow > 0:
            # bloom computed from per-cell average colour (cheap), then blurred & upscaled
            cv = self.cv
            covm = self._covmean()[cv.ch][..., None]
            cell = cv.bg + (cv.fg - cv.bg) * covm
            u8 = (np.clip(cell, 0, 1) * 255).astype(np.uint8)
            im = Image.fromarray(u8).resize((self.Wpx // 4, self.Hpx // 4), Image.BILINEAR)
            im = im.filter(ImageFilter.GaussianBlur(post.glow_radius))
            im = im.resize((self.Wpx, self.Hpx), Image.BILINEAR)
            g = np.asarray(im, np.float32)
            g *= np.float32(post.glow / 255.0 * 1.6)
            img += g
        if post.chroma:
            c = int(post.chroma)
            img[:, :, 0] = np.roll(img[:, :, 0], c, axis=1)
            img[:, :, 2] = np.roll(img[:, :, 2], -c, axis=1)
        if post.shake != (0, 0):
            img = np.roll(img, (int(post.shake[1]), int(post.shake[0])), axis=(0, 1))
        img *= self._mult(post.scan, post.vignette, post.fade)
        if post.grain > 0:
            img += self._grain[frame_no % len(self._grain)] * np.float32(post.grain)
        if post.flash > 0:
            img += np.float32(post.flash * post.fade)
        img *= 255.0
        img += 0.5
        np.clip(img, 0, 255, out=img)
        return img.astype(np.uint8)
