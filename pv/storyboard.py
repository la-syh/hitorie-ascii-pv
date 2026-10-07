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
from . import scenes2 as s2
from . import scenes3 as s3
from . import scenes4 as s4
from . import scenes5 as s5
from . import scenes6 as s6
from . import scenes7 as s7
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
        # === guitar solo: abstract patterns change every two bars (every bar in the count), then burn out
        Seg(D(112.4), 141.00, s7.z_solo, dict(count0=D(125.2), count1=D(138.0), warp=D(139.6))),
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
        # verse 1 -- her room at night, then out to the station and the last train
        (s5.a_message, {}),         # 0  answering-machine service: PLAY is pressed in the dark room
        (s6.b_oscillo, {}),         # 1  recorded low hum: speaker throbs, rings in the tea
        (s6.b_tide_paper, {}),       # 2  front line of everyday: rush-hour platform, red line
        (s6.b_where_quiz, {}),           # 3  where should I go?: departure board can't settle
        (s5.a_stockpile, {}),           # 4  jokes kept to herself: corkboard fills with notes
        (s5.a_burst, {}),            # 5  spat out at once: the notes stream out the window
        (s5.a_freeze, {}),           # 6  well, yeah: sitcom shrug on the TV, cat asleep on it
        (s6.b_bigclock, {}),         # 7  not stopping even now: inside the last train
        (s6.b_kaleido_color, {}),        # 8  everything changes: the train windows flick scenery
        # verse 2 -- the flat, the street, the store window, the desk
        (s5.a_soot, {}),           # 9  sooty four-and-a-half mats: laundry, boxes, dust
        (s6.b_moire_color, {}),      # 10 the ultrasound she brought: only the cat hears it
        (s6.b_lattice_paper, {}),          # 11 ran from the everyday: window goes dark, down the stairs
        (s6.b_grin_red, {}),           # 12 you'll laugh at me: the group chat floods with www
        (s6.b_truth_verdicts, {}),     # 13 mistaken truth: TV wall news gets a CORRECTION
        (s5.a_lie_of_truths, {}),       # 14 correct lie: 100% HAPPY commercial ticks TRUE
        (s5.a_cutouts, {}),          # 15 cut-out answers: scissors, scrapbook
        (s6.b_check_show, {}),        # 16 checking every day: day/night flip, calendar tears
        # pre-chorus 1 -- abstract: receding, night closing in, colour draining, staggering
        (s7.z_recede, {}),          # 17 gone far away: text planes stream to a vanishing point
        (s7.z_dark, {}),            # 18 waited for the dark night: a wall of 暗 closes in per beat
        (s7.z_drain, {}),           # 19 suddenly the colour was gone: grey eats the hues outward
        (s7.z_stagger, {}),         # 20 staggering on purpose: sheared type, tilting rules
        # pre-chorus 2
        (s7.z_far, {}),             # 21 go somewhere far: a floor of light rushing to the horizon
        (s5.a_descent, {}),         # 22 just want to sink: the water
        (s6.b_exam, {}),            # 23 don't know the answer: exam cards, ✓ ✗ ✓ ✗ ?
        (s7.z_room, {"stop": 87.1}),   # 24 pointlessly pretty room: sterile pastel symmetry; the stop
        # chorus 1
        (s7.z_quiz, {"skin": "big_red", "cards": [("期待しても？", "いい", "✗"),
                                                  ("期待しない？", "しない", "✓")]}),  # 25 mustn't expect
        (s7.z_shards, {}),          # 26 a talent that hurts: needles burst from 才能
        (s7.z_spot, {"break": B(94.43)}),   # 27 smash the spotlight: the cone of 光 shatters
        (s7.z_rise, {"pal": "sky"}),        # 28 up up high: tossed higher on every beat
        (s7.z_sphere, {}),          # 29 no way out, just a sphere: the path returns to START
        (s7.z_quiz, {"skin": "term", "title": "~/everyday $ expect",
                     "cards": [("expect(tomorrow)", "false", "✓"),
                               ("expect(you)", "true", "✗")]}),   # 30 mustn't expect
        (s7.z_ecg, {"pal": "red"}),        # 31 an emotion that hurts?: the trace spikes too high
        (s7.z_frost, {}),           # 32 the everyday's face is cold: frost over a face of 日常
        (s7.z_rise, {"pal": "dusk"}),       # 33 how about up high
        (s7.z_door, {}),            # 34 come on: the curtain of text parts, light
        # B section 2
        (s7.z_frames, {}),          # 35 gone far away: pulled back through picture frames
        (s7.z_stars, {}),           # 36 waited for the dark night: star trails of 夜
        (s7.z_graze, {}),           # 37 someone brushed past: two streams bend around each other
        (s7.z_dodge, {}),           # 38 dodging on purpose: the rain parts around one point
        (s7.z_sea, {}),             # 39 somewhere far: evening sea, the swell converging
        (s7.z_breath, {}),          # 40 sleep all alone: one breathing glow, rings of z
        (s7.z_rain, {}),            # 41 that looks sad: 悲 seen only through the rain
        (s7.z_vortex, {"brk": 164.0}),  # 42 bottom of a worn-out road: spiral down; the break
        # chorus 2
        (s7.z_retry, {"n": 2}),     # 43 second failure: attempt bars, FAILED again
        (s6.b_loss_show, {}),       # 44 expecting was a loss: ✗ then ✓
        (s7.z_stamp, {}),           # 45 only monotonous work: the same stamp, over and over
        (s7.z_droste, {}),          # 46 repeat it again: a Droste spiral of frames
        (s7.z_maze, {}),            # 47 no way out: a maze without an exit
        (s7.z_eye, {}),             # 48 you've noticed: the eye snaps to us
        (s7.z_retry, {"n": 3, "paper": True}),   # 49 third failure
        (s7.z_quiz, {"skin": "big", "cards": [("期待する？", "しない", "✓"),
                                              ("ほんとに？", "……する", "✗")]}),  # 50 want to stop expecting
        (s7.z_slats, {}),           # 51 peeking at the everyday's face: through the slats
        (s7.z_rise, {"pal": "night"}),      # 52 how about up high
        (s7.z_door, {"morning": True}),     # 53 come on
        # last chorus
        (s7.z_quiz, {"skin": "big_red", "cards": [("期待していい？", "だめ", "✓"),
                                                  ("もう一度？", "いい", "✗")]}),  # 54 mustn't expect
        (s7.z_shards, {"pal": "paper"}),    # 55 painful talent
        (s7.z_spot, {"break": B(198.43)}),  # 56 smash the spotlight
        (s7.z_rise, {"pal": "dawn"}),       # 57 up up high
        (s7.z_maze, {"paper": True}),       # 58 no way out
        (s7.z_sphere, {"pull": True}),      # 59 just a sphere: it shrinks into a frame
        (s7.z_quiz, {"skin": "big", "cards": [("また期待した？", "した", "✗"),
                                              ("もう期待しない？", "しない", "✓")]}),  # 60 mustn't expect
        (s7.z_ecg, {"pal": "green"}),       # 61 painful emotion
        (s7.z_frost, {"pal": "paper"}),     # 62 the everyday's face is cold
        (s7.z_rise, {"pal": "red"}),        # 63 how about up high
        (s7.z_finale, {"hold": 219.8, "hit": 221.0, "out": 221.12}),  # 64 come on -> the Earth, framed
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
        "☎☂☀♨〒☁※♪♥★◆○◎↑←→×✓▲▶°℃笑ツ_\\" + "❄雪◯⌫▮●↻≡¥" + "→↗↑↖←↙↓↘◎≈°○✓✗●家本笑顔期待今日昨同はい答いいえ何処行正嘘とはしても私"+"嘘本当正解正しい答え日常最前線草四畳半" + \
        "明曜遠くなったそれ暗夜を待色彩無フラつくわざ綺麗駄才能痛光逃げ道もよ冷顔額縁地球繰り返し済疲果て道底悲しそう人誰か一気づているのでしょう？……ほんとにだめもう度一ATEMPFLDSRGOHAL%=@#♥・" + "abcdefghijklmnopqrstuvwxyz"
