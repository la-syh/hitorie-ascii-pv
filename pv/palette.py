"""Colour palette.

wowaka drew his own VOCALOID-era thumbnails as simple monochrome
illustrations, so the PV is monochrome too: warm paper white and ink black,
swapped on the beat, plus a single accent red used sparingly.
"""
import numpy as np

from .canvas import hexc

INK = hexc("#0b0b0d")
PAPER = hexc("#eeebe3")
GREY = hexc("#8a8884")
DIM = hexc("#45444a")
FAINT = hexc("#232227")
RED = hexc("#ff3b2e")
RED_DIM = hexc("#7a1d18")
PAPER_DIM = hexc("#c9c5bb")


def mix(a, b, k: float):
    return (np.asarray(a) * (1 - k) + np.asarray(b) * k).astype(np.float32)


class Mode:
    """Foreground/background pair for 'night' (ink bg) or 'paper' (paper bg)."""

    def __init__(self, paper: bool):
        self.paper = paper
        self.bg = PAPER if paper else INK
        self.fg = INK if paper else PAPER
        self.mid = mix(self.bg, self.fg, 0.55)
        self.low = mix(self.bg, self.fg, 0.28)
        self.faint = mix(self.bg, self.fg, 0.12)
        self.accent = RED


NIGHT = Mode(False)
DAY = Mode(True)
