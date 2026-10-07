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
from . import shots as sh
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


def build(grid: Grid, duration: float, lyrics=None) -> list[Seg]:
    db = grid.downbeats()

    def D(t: float) -> float:          # nearest downbeat
        return float(db[abs(db - t).argmin()])

    def B(t: float) -> float:          # nearest beat
        return float(grid.nearest_beat_time(t))

    line_segs = _line_segs(lyrics, D, B)

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
        # === every sung line below gets its own shot (see LINE_SHOTS)
        *line_segs,
        # === guitar solo: frame tunnel + ring spectrum, then an everyday-object montage
        Seg(D(112.4), 141.00, sc.solo_tunnel, dict(count0=D(125.2), count1=D(138.0), warp=D(139.6))),
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
    segs.sort(key=lambda sg: sg.t0)
    # sanity: contiguous, ordered
    for a, b in zip(segs, segs[1:]):
        assert abs(a.t1 - b.t0) < 1e-6, (a.name, a.t1, b.name, b.t0)
    return segs


# One literal action per lyric line (index = line number in the .lrc).
# The comments paraphrase what the line is about; the lyric text itself is
# only ever read from the .lrc file.
def _line_shots(B):
    return [
        # verse 1
        (sh.sh_machine, {}),        # 0  answering-machine service: PLAY is pressed
        (sh.sh_lowfreq, {}),        # 1  recorded low frequency: speaker throbs
        (sh.sh_frontline, {}),      # 2  front line of everyday: objects march to a red line
        (sh.sh_where, {}),          # 3  where should I go?: signpost arrows spin
        (sh.sh_jar, {}),            # 4  jokes stored up: a jar fills with HA
        (sh.sh_burst, {}),          # 5  spat out at once: HA explodes everywhere
        (sh.sh_shrug, {}),          # 6  well, of course: a giant shrug
        (sh.sh_counter, {}),        # 7  not stopping even now: a timer runs flat out
        (sh.sh_morph, {}),          # 8  everything keeps changing: the frame swaps twice a beat
        # verse 2
        (sh.sh_tatami, {}),         # 9  sooty four-and-a-half mats, from above
        (sh.sh_ultrasound, {}),     # 10 brought-in ultrasound: rings + cracking glass
        (sh.sh_escape, {}),         # 11 ran away from the everyday: footprints leave the frame
        (sh.sh_laugh, {}),          # 12 you'll laugh at me: laughter closes in
        (sh.sh_wrong_true, {}),     # 13 a mistaken truth: O struck by a red X
        (sh.sh_right_lie, {}),      # 14 a correct lie: LIE flips readable, gets a check
        (sh.sh_cut, {}),            # 15 cut-out correct answers: scissors on the dotted line
        (sh.sh_checks, {}),         # 16 checking it every day: calendar ticks
        # pre-chorus 1
        (sh.sh_recede, {}),         # 17 it has gone far away: backwards out of the frames
        (sh.sh_dusk, {}),           # 18 waited for the dark night: the sun sinks
        (sh.sh_colorbars, {}),      # 19 the colour suddenly gone: colour bars drain
        (sh.sh_wobble, {}),         # 20 staggering on purpose: a swaying tower
        # pre-chorus 2
        (sh.sh_warp, {}),           # 21 go somewhere far: warp streaks
        (sh.sh_sink, {}),           # 22 just want to sink: water rises, a boat goes down
        (sh.sh_answer, {}),         # 23 don't know the answer: quiz, all crossed out
        (sh.sh_clean, {"stop": 87.1}),  # 24 pointlessly pretty room; the stop
        # chorus 1
        (sh.sh_forbid, {}),         # 25 mustn't expect: NO sign stamps the word
        (sh.sh_shard, {}),          # 26 a talent so sharp it hurts: a growing red crystal
        (sh.sh_spotlight, {"break": B(94.43)}),   # 27 smash the spotlight
        (sh.sh_up, {"v": "elevator"}),   # 28 up up high!: elevator races up
        (sh.sh_sphere, {}),         # 29 no way out, just a sphere: the path loops back
        (sh.sh_expectbar, {}),      # 30 mustn't expect: the bar crashes to 0
        (sh.sh_heart, {}),          # 31 an emotion that hurts: beating heart, ECG
        (sh.sh_coldclock, {}),      # 32 the everyday's face is cold: frozen clock
        (sh.sh_up, {"v": "arrows"}),     # 33 how about up high?: arrows rising
        (sh.sh_door, {}),           # 34 come on: the door opens, we go in
        # B section 2
        (sh.sh_recede, {}),         # 35 it has gone far away (again)
        (sh.sh_moon, {}),           # 36 waited for the dark night: a crescent rises
        (sh.sh_pass, {}),           # 37 someone brushed past
        (sh.sh_dodge, {}),          # 38 dodging on purpose
        (sh.sh_road, {}),           # 39 go somewhere far: night highway
        (sh.sh_sleep, {}),          # 40 want to sleep alone: battery drains
        (sh.sh_rain, {}),           # 41 that seems sad: rain on one umbrella
        (sh.sh_bottom, {"brk": 164.0}),  # 42 the bottom of a worn-out road
        # chorus 2
        (sh.sh_gameover, {"n": 2}), # 43 second failure
        (sh.sh_crash, {}),          # 44 expecting was a loss: chart plunges
        (sh.sh_conveyor, {}),       # 45 only monotonous work: stamping press
        (sh.sh_loop, {}),           # 46 how about repeating: loop arrow
        (sh.sh_maze, {}),           # 47 no escape route: maze walls close in
        (sh.sh_eye, {}),            # 48 you've noticed, haven't you: the eye looks at us
        (sh.sh_gameover, {"n": 3}), # 49 third failure
        (sh.sh_switch, {}),         # 50 want to stop expecting: switch thrown OFF
        (sh.sh_coldclock, {"peek": True}),  # 51 peeking at the everyday's face: keyhole
        (sh.sh_up, {"v": "balloon"}),    # 52 how about up high: a balloon rises
        (sh.sh_door, {}),           # 53 come on
        # last chorus
        (sh.sh_forbid, {"red": True}),   # 54 mustn't expect
        (sh.sh_shard, {}),          # 55 painful talent
        (sh.sh_spotlight, {"break": B(198.43)}),  # 56 smash the spotlight
        (sh.sh_up, {"v": "elevator"}),   # 57 up up high
        (sh.sh_maze, {}),           # 58 no escape route
        (sh.sh_sphere, {"pull": True}),  # 59 just a sphere: pull back to the whole globe
        (sh.sh_expectbar, {}),      # 60 mustn't expect
        (sh.sh_heart, {}),          # 61 painful emotion
        (sh.sh_coldclock, {}),      # 62 the everyday's face is cold
        (sh.sh_up, {"v": "arrows"}),     # 63 how about up high
        (sh.finale_room, {"hold": 219.8, "hit": 221.0, "out": 221.12}),  # 64 come on -> the framed Earth
    ]


def _line_segs(lyrics, D, B) -> list[Seg]:
    lines = lyrics.lines
    shots = _line_shots(B)
    assert len(shots) == len(lines), (len(shots), len(lines))
    starts = [ln.t for ln in lines]
    starts[0] = 38.55            # cut a hair before the first pickup
    starts[35] = 141.00          # after the guitar solo
    starts[43] = D(166.8)        # chorus-2 band hit
    ends = starts[1:] + [221.30]
    ends[34] = D(112.4)          # guitar solo starts
    ends[42] = D(166.8)
    return [Seg(a, b, fn, dict(p)) for (fn, p), a, b in zip(shots, starts, ends)]


def text_chars() -> str:
    """All non-lyric text the storyboard may draw (for the glyph atlas)."""
    return TITLE + ROMAJI + ARTIST + CREDIT + "ASCII PV  /  unofficial fan work for wowaka" + \
        "☎☂☀♨〒☁※♪♥★◆○◎↑←→×✓▲▶°℃笑ツ_\\" + "abcdefghijklmnopqrstuvwxyz"
