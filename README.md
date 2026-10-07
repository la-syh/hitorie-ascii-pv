# ascii-song — an ASCII-art PV for ヒトリエ「日常と地球の額縁」

A music video made entirely of characters. Every frame is a 160 × 54 grid of
text: letters, punctuation and kana. The grid is either rasterised to a
1920 × 1080 / 30 fps MP4 or printed live in a terminal. The cuts follow a beat
grid taken from the recording, and the lyrics come from the `.lrc` file at
render time.

> Unofficial fan work. Song: ヒトリエ「日常と地球の額縁」(words & music: wowaka).
> The recording and lyrics are **not** in this repository (see [Inputs](#inputs)).

---

## Per-line redesign (branch `per-line-redesign`)

Every sung line now has its own shot: one literal, animated idea that fills
the frame and moves on the beat (`pv/shots.py`, wired up in
`pv/storyboard.py` by line number). Drawn people are gone. The narrator only
appears as an eye, a cursor, footprints or a light, because those read
cleanly in ASCII. Shots use solid colour blocks, full-screen red, and stamps
and hits on the beat. The Chinese caption strip from the enhanced edition is
kept.

| lines | shots |
|---|---|
| verse 1 | ☎ PLAY pressed · speaker throbbing · objects marching to a red front line · spinning signpost · jar filling with HA · HA explodes · giant shrug · runaway timer · frame swapping twice a beat |
| verse 2 | sooty four-and-a-half mats from above · ultrasound cracks the glass · footprints walk out of the picture frame · laughter closes in · ○ struck by × · LIE flips and gets a ✓ · scissors cut out ANSWER · calendar ticked off |
| pre-chorus | backwards out of a frame tunnel · sun sinks · colour bars drain · swaying tower · warp · water rises, paper boat sinks · quiz all crossed out · pristine empty room, the stop |
| chorus 1 | NO sign stamps 期待 · red crystal grows · spotlight on an empty mic shatters · elevator to the top · escape path loops round the globe · EXPECTATION bar crashes · beating heart + ECG · frozen clock · rising arrows · door opens |
| B section 2 | frame tunnel · crescent moon · two lights graze · cursor dodges · night highway · battery drains · rain on an umbrella · stairwell down to the bottom |
| chorus 2 | FAILED ×× · chart plunges · stamping press · loop ×N · maze closes in · the eye looks at us · FAILED ××× · EXPECT switch thrown OFF · clock through a keyhole · balloon · door |
| last chorus | chorus-1 shots, with a red NO sign, a maze, and a pull back from the globe into the framed Earth on the wall |

## Enhanced edition (2026-10-07)

The enhanced render is `out/pv-enhanced-zh.mp4` (1080p / 30 fps). The
original `out/pv.mp4` is retained. `out/subtitles.zh.srt` contains bilingual
subtitles; Chinese in the video is burned in and needs no player setup.
The translation is an original interpretive translation of the supplied LRC,
not an official translation. Source audio and Japanese LRC are unchanged.

The four-mat room now has books, a low desk, a mug, curtains, a sliding door,
a hanging lamp and oblique window light. Verse two cuts between the room,
a window-side close-up, a cracked mirror and a desk of cut-out answers.
The original character now has a hair clip, sailor collar, facial detail and
clothing texture. Later shots show a moonlit portrait, an empty clean room,
and three framed selves repeating the same task. The instrumental alternates
between the answering machine, portrait, clock and Earth rather than a date counter.

Reference: the supplied `world.execute(me).mp4` (visual hierarchy / caption
separation) and the supplied 11-person tribute PV (framed collage / repeated
figures / object montage). Drawings are original procedural character art;
no reference-video frames are embedded in the output. The reference edit has
a different duration, so timing always follows the local Hitorie recording.

Chinese strings are editable in `assets/subtitles.zh.json`, keyed by the
original Japanese lines. Fusion Pixel 12px supplies missing Chinese glyphs;
its license is in `assets/fonts/OFL-FusionPixel.txt`. Captions follow LRC
line timings, including instrumental gaps, and stay clear of glitch/flash effects.

Render using the local conda environment:

```bash
conda run -n ML python -m pv render --workers 4 --preset fast --out out/pv-enhanced-zh.mp4
conda run -n ML python -m pv sheet --every 5 --out out/redesign-contact-sheet.png
conda run -n ML python tools/check_redesign.py
conda run -n ML python tools/export_subtitles.py
```

## Quick start

Prerequisites: **Python 3.9+** and **FFmpeg** (`brew install ffmpeg` on macOS,
`apt install ffmpeg` on Debian/Ubuntu).

```bash
# put the two input files in the project root (next to the Makefile):
#   ヒトリエ - 日常と地球の額縁.flac
#   ヒトリエ - 日常と地球の額縁.lrc

make setup     # creates .venv and installs numpy + Pillow
make check     # verifies ffmpeg, packages, input files (+ sha256), fonts
make render    # -> out/pv.mp4   (1920x1080, 30 fps, H.264 + AAC stereo)
```

The full render takes about 4–15 minutes, depending on the number of CPU cores
(4½ minutes with 3 workers on a 4-core arm64 Linux VM). The result is about
190 MB (H.264 at roughly 6.7 Mbit/s, with AAC stereo audio).
Frames are drawn in parallel worker processes and piped straight into FFmpeg,
so no frame files are written to disk. The video is encoded in 20-second
chunks, cached in `build/segments/<key>/`, and then joined and muxed with the
audio in a single pass. If a render is interrupted, run `make render` again and
it picks up where it stopped. The cache key is a hash of the code, assets,
inputs and settings, so editing a scene never reuses a stale chunk.

### All commands

| command | what it does |
|---|---|
| `make setup` | `python3 -m venv .venv` + `pip install -r requirements.txt` |
| `make check` | pre-flight check (`tools/check_inputs.py`) |
| `make analyze` | beat/tempo/feature analysis → `build/analysis.{json,npz}` (runs automatically if missing) |
| `make info` | prints the storyboard (scene list with start/end times) |
| `make render` | full-quality video → `out/pv.mp4` (`WORKERS=3` sets parallelism; `ARGS="--max-time 120"` stops early so you can resume later) |
| `make preview` | fast 960 × 540 draft → `out/preview_540p.mp4` |
| `make sheet` | contact sheet, one frame every 2.5 s → `out/contact_sheet.png` |
| `make stills` | a set of PNG stills → `out/stills/` |
| `make play` | **plays the PV as live text in your terminal**, with audio via `ffplay` |
| `make clean` | deletes the generated `build/` and `out/` folders |

You can also run the commands without `make`:

```bash
python3 -m pv render --out out/pv.mp4            # --start/--end (s), --scale, --crf, --workers
python3 -m pv render --start 89.5 --end 112.5    # render only the first chorus
python3 -m pv still 94.6 100 216                 # PNG stills at song times (seconds)
python3 -m pv play --start 89.5                  # terminal playback from the chorus
python3 tools/flash_check.py                     # photosensitivity check (flashes per second)
```

For `play`, the terminal must be at least 160 × 54 cells and support 24-bit
colour (iTerm2, kitty, WezTerm, recent macOS Terminal). Make the font smaller
until the picture fits.

---

## Inputs

| file | sha256 |
|---|---|
| `ヒトリエ - 日常と地球の額縁.flac` (44.1 kHz, 5.1, 3:46) | `384e3f8a…4a611d` |
| `ヒトリエ - 日常と地球の額縁.lrc` (line-timed lyrics) | `b72c9178…dd9f4` |

The full hashes are in `inputs.sha256`. Both files are listed in `.gitignore`
because the recording and lyrics are copyrighted and the audio is 70 MB. Any
`.flac` and `.lrc` in the project root are picked up automatically, or you can
pass `--audio` and `--lrc`. The 5.1 audio is downmixed to stereo AAC in the
output.

The storyboard times were set by hand against this recording. A different
master of the song will still render, but the cuts may drift.

---

## How it works

```
 .flac ──ffmpeg──► mono PCM ──► STFT ─► onset envelope ─► tempo (autocorr.) ─► DP beat tracker
                                   └──► band energies (low/mid/high), 32-band spectrum
 .lrc  ──► timed lines (char-by-char reveal over the sung duration)
                                   │
 storyboard.py  (scene list, cut on beats/downbeats)          build/analysis.*
                                   ▼
 scenes.py  draw(t) ──► character grid  (glyph index + fg/bg colour per cell)
                                   │
                     ┌─────────────┴──────────────┐
            raster.py: glyph atlas gather,    player.py: ANSI truecolor
            glow, scanlines → RGB24 ─► ffmpeg  text in the terminal
```

* **Audio analysis** (`pv/audio.py`) uses only numpy: an STFT, a log-band
  spectral-flux onset envelope, autocorrelation tempo estimation, and an Ellis
  style dynamic-programming beat tracker. The song comes out at **152 BPM**
  (552 beats; bars about 1.58 s long). Lyric lines start about half a beat
  before the downbeat, as pickups. The bar phase is anchored on a downbeat
  annotated by hand: the band hit at the start of the first chorus, at 90.00 s.
* **Rendering** (`pv/canvas.py`, `pv/raster.py`): the font is pre-rendered
  into a glyph atlas, with CJK characters stored as two half-cells. Turning the
  grid into pixels is then a single numpy gather. Large lyrics are drawn as
  "structural" ASCII: solid cells are filled with `#`, and edge cells get
  `_ " | / \` chosen from the local gradient, so the kanji stay readable at
  about 10 rows tall.
* **Determinism.** Every scene is a pure function of time: random choices use
  RNGs seeded from the beat index, and nothing is simulated from frame to
  frame. That is why frames can render in parallel and in any order, and why
  `still`, `render` and `play` all show the same picture. The font
  (BIZ UDGothic) and the Earth land mask are committed, and the analysis is
  cached in `build/`. As a check, stills rendered on two different machines
  (x86-64 with Python 3.13 and NumPy 2.5, and arm64 with Python 3.10 and NumPy
  2.2) came out bit-identical.
* **Photosensitivity.** The PV flips between black and white on the beat.
  `tools/flash_check.py` measures the result at no more than 2.5 full-screen
  flashes in any one-second window, under the common 3-per-second guideline.

---

## Concept: frames, the everyday, and the Earth

The title is 日常と地球の額縁, "the picture frame of the everyday and the
Earth", so the **picture frame (額縁)** is the main motif. It draws itself
around the screen in the intro, turns into a tunnel of frames during the guitar
solo, and in the last shot the camera pulls back out of the spinning Earth to
show that it has been a framed picture on the wall of the narrator's small room
all along.

Ideas taken from wowaka and from what has been written about him:

* **Monochrome.** wowaka drew his own VOCALOID-era thumbnails as simple
  black-and-white single illustrations, and never used the VOCALOID character
  herself ([niconico 大百科](https://dic.nicovideo.jp/a/wowaka),
  [pixiv 百科事典](https://dic.pixiv.net/a/wowaka)). The PV uses only ink black
  and paper white, swapped on the beat, plus one accent red.
* **A girl as the protagonist.** Each of his songs had an adolescent girl as
  its protagonist. Here that is an original silhouette with a bob haircut and a
  skirt, built from signed-distance shapes. She sits in a sooty
  four-mat room, sinks, runs on the globe and sleeps inside a frame.
* **Speed and bounce.** His style has been described as fast, quirky beats,
  an "over-compressed" band sound, and syllables that bounce on っ and ん
  ([ぴあ](https://lp.p.pia.jp/article/news/48033/index.html)). The PV answers
  with hard cuts on line starts, a camera shake on the kick, and lyric
  characters that hop up in red at the moment each one is sung.
* **The song's own story.** 日常と地球の額縁 was first released as a new
  track on wowaka's album *アンハッピーリフレイン* (Unhappy Refrain, 2011-05-18).
  Seven years later Hitorie recorded it as a band, live in the studio, for the
  single *ポラリス* (Polaris, 2018-11-28). It was the first wowaka VOCALOID
  composition on a Hitorie release
  ([ナタリー](https://natalie.mu/music/news/305562),
  [Wikipedia](https://en.wikipedia.org/wiki/Polaris_(Hitorie_single)),
  [pixiv 百科事典](https://dic.pixiv.net/a/%E6%97%A5%E5%B8%B8%E3%81%A8%E5%9C%B0%E7%90%83%E3%81%AE%E9%A1%8D%E7%B8%81)).
  The instrumental now reprises objects from the lyric narrative. The credits end "for wowaka", who died in April 2019.

### Storyboard

| time (s) | section | scene |
|---|---|---|
| 0.00–13.22 | intro (guitar alone) | REC light and time code; a single low-frequency signal line; the frame draws itself clockwise; build-up noise |
| 13.22–26.01 | intro (band) | title in big structural ASCII inside a gilded frame; the Earth turning behind it |
| 26.01–38.55 | intro | the Earth, frames emanating outward, the title orbiting as a ring of text; dive into the globe |
| 38.55–51.30 | verse 1 | answering machine and LCD counter; a timestamped transcript; jokes burst out of the speaker; then "everything changes" glitch inversions |
| 51.30–64.10 | verse 2 | sooty four-mat room; ultrasound ripples; `wwww` laughter scribbled on the walls; mirrored truths and lies; cut-out squares stamped OK; lyrics written vertically (tategaki) |
| 64.10–76.70 | pre-chorus 1 | the room recedes into a small frame in the night; colour drains; the picture sways |
| 76.70–89.50 | pre-chorus 2 | walking toward the horizon; sinking with bubbles; question marks; the "pointlessly beautiful" clean room; the stop |
| 89.50–112.43 | chorus 1 | beat-flipped big lyrics; a spotlight smashed into flying shards; rising through speed lines; running on the Earth; a cold clock face; a door-frame opens |
| 112.43–141.00 | guitar solo | endless frame tunnel with a ring spectrum around the globe, then a montage of the phone, portrait, clock and Earth |
| 141.00–153.60 | B section 2 | night street, a crowd walking the other way; someone brushes past; she sidesteps |
| 153.60–166.82 | B section 2 | the road at night; sleeping alone inside a frame; rain; the road tipping down to its bottom |
| 166.82–193.60 | chorus 2 | FAILURE 02 / 03 counters with a red X; three framed portraits of repeated work; the globe; the clock peeking in |
| 193.60–214.58 | last chorus | the chorus-1 imagery again, more intense; pull back to the whole globe |
| 214.58–221.30 | ending | out of the Earth, into the frame on the wall of her room: 日常と地球の額縁 |
| 221.30–226.39 | silence | credits |

---

## Project layout

```
pv/
  audio.py       numpy-only analysis (STFT, onsets, tempo, beat tracking, features)
  lrc.py         LRC parser (handles NetEase-style JSON credit lines)
  timeline.py    beat/bar grid + per-frame context passed to scenes
  glyphs.py      glyph atlas (half-width + double-width CJK)
  canvas.py      character grid + drawing primitives (text, lines, fields, big text)
  shapes.py      globe, picture frame, figure, clock, seven-segment, glitches
  motifs.py      room, answering machine, spotlight, frame tunnel, shatter, waves
  lyricfx.py     lyric typography (decode, big, vertical, transcript)
  scenes.py      the scenes
  storyboard.py  what plays when (timings; no lyric text stored)
  raster.py      grid → pixels, glow/scanlines/vignette
  render.py      parallel renderer → ffmpeg
  player.py      terminal playback
  __main__.py    CLI
assets/fonts/    BIZ UDGothic Regular/Bold (SIL OFL 1.1, see OFL.txt)
assets/earth_mask.txt   360×180 land mask from Natural Earth (public domain)
tools/           check_inputs.py, flash_check.py, make_earth_mask.py
```

## Credits

* Song: ヒトリエ「日常と地球の額縁」, words & music by wowaka. All rights belong
  to their holders. This PV is an unofficial, non-commercial fan work.
* Font: [BIZ UDGothic](https://github.com/googlefonts/morisawa-biz-ud-gothic)
  by Morisawa, under the SIL Open Font License 1.1 (`assets/fonts/OFL.txt`).
* Land mask: [Natural Earth](https://www.naturalearthdata.com/) `ne_110m_land`
  (public domain). You can rebuild it with `tools/make_earth_mask.py`.
* The scenes, the girl's silhouette and all the drawings are original and drawn
  procedurally. No artwork from the original releases or videos is reproduced.
