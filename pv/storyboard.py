"""The storyboard: which scene plays when, cut to the music.

Times were hand-annotated against the beat grid from ``python3 -m pv analyze``
(152 BPM, bars of ~1.58 s; the chorus downbeat at 90.00 s anchors the bar
grid).  Lyric lines start ~half a beat before the downbeat (pickups), so the
chorus cuts land on the line starts; section cuts land on downbeats via ``D``.

No lyric text is stored here -- lyrics are read from the .lrc file at render
time.  The comments describe each moment in English.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from . import scenes as sc
from .timeline import Grid

TITLE = "日常と地球の額縁"
ROMAJI = "NICHIJOU TO CHIKYUU NO GAKUBUCHI"
ARTIST = "ヒトリエ"
CREDIT = "words & music : wowaka"
DOWNBEAT_ANCHOR = 90.0   # a known downbeat (first chorus hit), seconds


@dataclass
class Seg:
    t0: float
    t1: float
    fn: Callable
    params: dict = field(default_factory=dict)
    glitch_in: bool = True   # a couple of noisy frames on the cut

    @property
    def name(self) -> str:
        return self.fn.__name__


def build(grid: Grid, duration: float) -> list[Seg]:
    db = grid.downbeats()

    def D(t: float) -> float:          # nearest downbeat
        return float(db[abs(db - t).argmin()])

    def B(t: float) -> float:          # nearest beat
        return float(grid.nearest_beat_time(t))

    segs = [
        # --- intro: the riff alone; a signal line; the frame draws itself
        Seg(0.0, D(13.2), sc.intro_signal, dict(line=D(2.0), frame0=D(3.6), frame1=D(11.6),
                                                build=D(11.6), kick=12.83), glitch_in=False),
        # --- band in: title card inside the frame, Earth behind
        Seg(D(13.2), D(26.0), sc.title, dict(title=TITLE, split=3, romaji=ROMAJI, artist=ARTIST,
                                             credit_text=CREDIT, credit=D(16.4), grow=D(22.8))),
        # --- the Earth, frames emanating, title ring orbiting; dive in
        Seg(D(26.0), 38.55, sc.globe_intro,
            dict(zoom=D(37.2), ring=f"{ROMAJI} * HITORIE * WOWAKA * ")),
        # --- verse 1: answering machine + transcript; jokes burst out; everything changes
        Seg(38.55, 51.30, sc.phone, dict(burst=(45.03, 48.2), chaos=48.2)),
        # --- verse 2: sooty little room; ultrasound; laughter; truths/lies; cut-outs
        Seg(51.30, 64.10, sc.room_scene, dict(ultra=(52.98, 54.5), laugh=(54.52, 57.8),
                                              mirror=(57.8, 60.95), cut=60.98)),
        # --- pre-chorus 1: room recedes into a frame in the night; colour drains; sway
        Seg(64.10, 76.70, sc.night_away, dict(dark=66.85, grey=70.3, empty=71.9, sway=73.24)),
        # --- pre-chorus 2: walk away; sink; question marks; the too-clean room; stop
        Seg(76.70, 89.50, sc.sink, dict(away=76.70, sink=80.10, ask=83.20, clean=86.35, stop=87.1)),

        # === chorus 1
        Seg(89.50, 91.28, sc.big_lyric, dict(bg="frames")),
        Seg(91.28, 92.95, sc.big_lyric, dict(bg="pain")),
        Seg(92.95, 95.97, sc.spotlight_break, {"break": B(94.43)}),
        Seg(95.97, 97.77, sc.rise),
        Seg(97.77, 102.39, sc.globe_run),
        Seg(102.39, 104.00, sc.big_lyric, dict(bg="rays", paper_first=True)),
        Seg(104.00, 105.79, sc.big_lyric, dict(bg="pain")),
        Seg(105.79, 108.88, sc.clock_face),
        Seg(108.88, 110.55, sc.rise),
        Seg(110.55, D(112.4), sc.beckon, dict(zoom=D(112.4) - 0.9)),

        # === guitar solo: frame tunnel + ring spectrum, then the 2011 -> 2018 day counter
        Seg(D(112.4), 141.00, sc.solo_tunnel,
            dict(count0=D(125.2), count1=D(138.0), warp=D(139.6),
                 date0=(2011, 5, 18), date1=(2018, 11, 28),
                 label0="アンハッピーリフレイン 2011", label1="ポラリス 2018")),

        # === B section 2
        Seg(141.00, 153.60, sc.crowd, {"pass": 148.4, "dodge": 150.9}),
        Seg(153.60, D(166.8), sc.road_sleep, dict(sleep=156.55, rain=160.0, down=163.2,
                                                  brk=164.0, drums=153.9)),

        # === chorus 2: failures, repetition
        Seg(D(166.8), 169.60, sc.failure, dict(n=2)),
        Seg(169.60, 171.37, sc.big_lyric, dict(bg="dots")),
        Seg(171.37, 176.13, sc.repetition),
        Seg(176.13, 180.82, sc.globe_run),
        Seg(180.82, 184.10, sc.failure, dict(n=3)),
        Seg(184.10, 187.26, sc.clock_face, dict(peek=True)),
        Seg(187.26, 188.88, sc.rise),
        Seg(188.88, 193.60, sc.beckon, dict(zoom=192.7)),

        # === final chorus
        Seg(193.60, 195.20, sc.big_lyric, dict(bg="frames", paper_first=True)),
        Seg(195.20, 196.98, sc.big_lyric, dict(bg="pain")),
        Seg(196.98, 200.03, sc.spotlight_break, {"break": B(198.43)}),
        Seg(200.03, 201.55, sc.rise),
        Seg(201.55, 206.41, sc.globe_run, dict(pull=203.25)),
        Seg(206.41, 207.99, sc.big_lyric, dict(bg="rays")),
        Seg(207.99, 209.64, sc.big_lyric, dict(bg="pain")),
        Seg(209.64, 212.92, sc.clock_face),
        Seg(212.92, 214.58, sc.rise),
        # --- pull back out of the Earth: it hangs framed on the wall of her room
        Seg(214.58, 221.30, sc.finale, dict(hold=219.8, hit=221.0, out=221.12)),
        # --- credits in the silence
        Seg(221.30, duration, sc.credits, dict(rows=[
            (TITLE, "title"),
            (ARTIST, "main"),
            (CREDIT, "dim"),
            ("", "dim"),
            ("ASCII PV  /  unofficial fan work", "dim"),
            ("for wowaka", "accent"),
        ]), glitch_in=False),
    ]
    # sanity: contiguous, ordered
    for a, b in zip(segs, segs[1:]):
        assert abs(a.t1 - b.t0) < 1e-6, (a.name, a.t1, b.name, b.t0)
    return segs


def text_chars() -> str:
    """All non-lyric text the storyboard may draw (for the glyph atlas)."""
    return TITLE + ROMAJI + ARTIST + CREDIT + "アンハッピーリフレイン 2011ポラリス 2018" + \
        "ASCII PV  /  unofficial fan work for wowaka"
