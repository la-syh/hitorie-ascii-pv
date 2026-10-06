"""Musical time: beat grid, bars, and the per-frame context handed to scenes."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .audio import Analysis
from .lrc import Line, Lyrics


class Grid:
    """Beat/bar positions from tracked beats, with a hand-picked downbeat anchor."""

    def __init__(self, beats: list[float], downbeat_anchor: float):
        b = np.asarray(beats, np.float64)
        self.beats = b
        self.ibi = float(np.median(np.diff(b)))
        self.anchor = int(np.argmin(np.abs(b - downbeat_anchor)))

    def beat_pos(self, t: float) -> float:
        """Fractional beat index (extrapolated outside the tracked range)."""
        b = self.beats
        if t <= b[0]:
            return (t - b[0]) / self.ibi
        if t >= b[-1]:
            return len(b) - 1 + (t - b[-1]) / self.ibi
        i = int(np.searchsorted(b, t) - 1)
        return i + (t - b[i]) / (b[i + 1] - b[i])

    def bar_pos(self, t: float) -> float:
        return (self.beat_pos(t) - self.anchor) / 4.0

    def beat_time(self, i: float) -> float:
        b = self.beats
        if i <= 0:
            return b[0] + i * self.ibi
        if i >= len(b) - 1:
            return b[-1] + (i - len(b) + 1) * self.ibi
        k = int(math.floor(i))
        return b[k] + (i - k) * (b[k + 1] - b[k])

    def nearest_beat_time(self, t: float) -> float:
        return self.beat_time(round(self.beat_pos(t)))

    def downbeats(self) -> np.ndarray:
        idx = np.arange(len(self.beats))
        return self.beats[(idx - self.anchor) % 4 == 0]


@dataclass
class Ctx:
    t: float
    frame: int
    fps: float
    an: Analysis
    grid: Grid
    lyrics: Lyrics
    # scene-local
    t0: float = 0.0
    t1: float = 1.0
    params: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- derived
    @property
    def u(self) -> float:
        """Progress through the current scene, 0..1."""
        return min(1.0, max(0.0, (self.t - self.t0) / max(1e-6, self.t1 - self.t0)))

    @property
    def lt(self) -> float:
        """Seconds since scene start."""
        return self.t - self.t0

    @property
    def beat(self) -> float:
        return self.grid.beat_pos(self.t)

    @property
    def bar(self) -> float:
        return self.grid.bar_pos(self.t)

    @property
    def beat_i(self) -> int:
        return int(math.floor(self.beat + 1e-6))

    @property
    def beat_frac(self) -> float:
        return self.beat - math.floor(self.beat + 1e-6)

    @property
    def since_beat(self) -> float:
        return self.t - self.grid.beat_time(self.beat_i)

    def pulse(self, decay: float = 7.0) -> float:
        """1 on each beat, decaying exponentially."""
        return math.exp(-decay * max(0.0, self.since_beat))

    @property
    def since_bar(self) -> float:
        k = math.floor(self.bar + 1e-6)
        return self.t - self.grid.beat_time(self.grid.anchor + 4 * k)

    def bar_pulse(self, decay: float = 4.0) -> float:
        b = self.bar
        k = math.floor(b + 1e-6)
        since = self.t - self.grid.beat_time(self.grid.anchor + 4 * k)
        return math.exp(-decay * max(0.0, since))

    def feat(self, name: str) -> float:
        arr = getattr(self.an, name)
        return float(arr[min(len(arr) - 1, max(0, self.frame))])

    @property
    def spectrum(self) -> np.ndarray:
        return self.an.spectrum[min(len(self.an.spectrum) - 1, self.frame)]

    def rng(self, *keys) -> np.random.Generator:
        """Deterministic RNG keyed on arbitrary ints (e.g. beat index)."""
        h = 1469598103934665603
        for k in keys:
            h = (h ^ (int(k) & 0xFFFFFFFF)) * 1099511628211 & 0xFFFFFFFFFFFF
        return np.random.default_rng(h)

    # ----------------------------------------------------------------- lyrics
    def line(self) -> Line | None:
        return self.lyrics.at(self.t)

    def lines_between(self, a: float, b: float) -> list[Line]:
        return [ln for ln in self.lyrics.lines if a - 1e-3 <= ln.t < b]
