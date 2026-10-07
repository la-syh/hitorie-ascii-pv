# hitorie-ascii-pv

日常と地球の額縁 · ASCII PV

**A music video built from characters, rhythm and typography.**

[简体中文](README.md) · **English**

An unofficial character-art PV for Hitorie's **日常と地球の額縁**, written and composed by wowaka. Python generates the visuals; no HTML, browser or video-editing application is required.

Each frame is a 160-column, 54-row character grid. ASCII symbols, Japanese glyphs and text textures form the image, rendered to **1920 × 1080 at 30 fps**. The same scene engine can also play directly in a true-colour terminal.

## Features of the final version

- **A shot for every sung line:** 65 lyric lines mapped to scenes and timed against the local LRC and recording.
- **Abstract character animation:** typographic tides, waveforms, soot, kaleidoscopes, interference patterns, frame tunnels and a text globe.
- **New imagery for recurring lyrics:** rising text lanterns, endless stairs, a chart exceeding its axes and a lighting rig extinguishing lamp by lamp.
- **Varied palettes and layouts:** monochrome, red, blue, full colour and pastel; questions, verdicts and repetition become visual material.
- **Protected Chinese captions:** a caption strip kept clear of shake, flashes and glitches, plus bilingual Japanese/Chinese SRT export.
- **Time-based rendering:** parallel encoding, resumable segment caches, still frames and contact sheets.

[`pv/storyboard.py`](pv/storyboard.py) defines the active edit, primarily using `scenes5.py` through `scenes8.py`. Earlier room, character and street scenes remain in the source as reusable material; they are not a description of the entire final edit.

## Quick start

You need Python, NumPy, Pillow and FFmpeg / FFprobe on your command path. A Python 3.11 conda environment is recommended. Terminal playback with sound also requires FFplay.

After cloning the repository and entering its directory:

```bash
conda create -n ascii-pv python=3.11 -y
conda activate ascii-pv
python -m pip install -r requirements.txt
conda install -c conda-forge ffmpeg
```

Supply your own recording and line-timed lyrics in the project root, next to the Makefile:

```text
ヒトリエ - 日常と地球の額縁.flac
ヒトリエ - 日常と地球の額縁.lrc
```

Check the inputs and render:

```bash
python tools/check_inputs.py
python -m pv render --workers 4 --preset fast --out out/pv-final.mp4
```

The output contains H.264 video and stereo AAC audio, lasting approximately 3 minutes 46 seconds. Rendering time depends on your hardware and settings. The first run analyses the audio; reduce `--workers` if memory is limited.

**This is a bespoke PV for one song and recording, not an automatic music-video generator for arbitrary songs.** The storyboard expects 65 lyric lines. A different recording or LRC may require changes to timing, captions and shot mapping.

## Commands

Run these from the project root in the activated environment:

| Purpose | Command |
|---|---|
| Analyse audio | `python -m pv analyze` |
| Print the storyboard | `python -m pv info` |
| Low-resolution preview | `python -m pv render --scale 0.5 --workers 4 --out out/preview.mp4` |
| Render a section | `python -m pv render --start 89.5 --end 112.5 --out out/chorus.mp4` |
| Export stills at song times | `python -m pv still 52 94.6 173 216` |
| Generate a contact sheet | `python -m pv sheet --every 5 --out out/contact-sheet.png` |
| Play in the terminal | `python -m pv play --start 89.5` |
| Export bilingual SRT | `python tools/export_subtitles.py` |
| Check captions, boundaries and determinism | `python tools/check_redesign.py` |
| Estimate full-frame luminance changes | `python tools/flash_check.py` |

To specify input paths, place global options before the subcommand:

```bash
python -m pv --audio /path/to/song.flac --lrc /path/to/song.lrc render --out out/pv-final.mp4
```

Full renders are encoded in approximately 20-second chunks under `build/segments/`. Repeat the same command to reuse completed chunks after an interruption. Code, caption and setting changes generally produce a new cache. When replacing the recording, run `python -m pv analyze` first to refresh the audio analysis.

Terminal playback needs space for at least 160 columns and 54 rows, plus 24-bit colour support. Generated files go under `out/`. The Makefile remains available, for example `make PY=python render`; conda users do not need `make setup`, which creates a separate virtual environment.

## How it works

1. **Audio analysis:** FFmpeg decodes the recording; NumPy extracts spectra, onset strength, frequency-band energy and beats.
2. **Timeline and storyboard:** LRC timestamps identify sung lines; `storyboard.py` chooses the scene and its parameters.
3. **Character drawing:** scene functions write glyphs and foreground/background colours into a grid using time and audio features.
4. **Rasterisation:** a font atlas turns the grid into pixels, with glow, scanlines and other post-processing. The caption strip is protected from these effects.
5. **Encoding:** worker processes generate frames; FFmpeg encodes them and muxes the recording. The terminal player instead emits ANSI true-colour text.

Per-character lyric reveals are visual estimates from line timestamps, not manually aligned word timings. `flash_check.py` is an approximate luminance check, not a comprehensive photosensitivity certification. The visuals contain flashes and high-contrast cuts.

## Editing and source layout

| File / directory | Purpose |
|---|---|
| `pv/storyboard.py` | Active storyboard; `_line_shots()` maps lyrics to shots |
| `pv/scenes5.py` through `pv/scenes8.py` | Main scenes used in the final edit |
| `pv/abstract.py`, `pv/quiz.py` | Abstract fields, colour tools, questions and verdicts |
| `pv/audio.py`, `pv/lrc.py`, `pv/timeline.py` | Audio features, lyric parsing and musical time |
| `pv/canvas.py`, `pv/glyphs.py` | Character-grid drawing and font atlas |
| `pv/lyricfx.py` | Lyric layout and animation |
| `pv/raster.py`, `pv/render.py` | Post-processing, parallel rendering and encoding |
| `pv/player.py` | Terminal playback |
| `assets/fonts/` | Bundled fonts and their licenses |
| `assets/earth_mask.txt` | Earth land mask |
| `assets/subtitles.zh.json` | Ordered Japanese/Chinese caption pairs |
| `tools/` | Checks, subtitle export and asset-generation utilities |

Captions are an ordered list of `ja` and `zh` fields matching the LRC. Repeated Japanese lines may have different translations. The loader validates both line count and Japanese text, and reports mismatches. After edits, inspect stills or short clips before rendering the full video; rerun `tools/export_subtitles.py` to refresh the SRT.

## Credits and distribution scope

- **Song:** Hitorie, 日常と地球の額縁; words and music by wowaka. This is an unofficial fan project.
- **Fonts:** [BIZ UDGothic](https://github.com/googlefonts/morisawa-biz-ud-gothic) and [Fusion Pixel](https://github.com/TakWolf/fusion-pixel-font). Their licenses are preserved in [`OFL.txt`](assets/fonts/OFL.txt) and [`OFL-FusionPixel.txt`](assets/fonts/OFL-FusionPixel.txt).
- **Earth data:** public-domain land data from [Natural Earth](https://www.naturalearthdata.com/), rebuildable with `tools/make_earth_mask.py`.
- **Visual references:** the locally supplied `world.execute(me).mp4` and the [11-person tribute PV](https://www.bilibili.com/video/BV1ZV4y1S7Q9). These informed composition and rhythm; the renderer does not require the reference videos.

The recording, external LRC, reference videos, rendered videos and caches are excluded from source commits. Reference input checksums are recorded in [`inputs.sha256`](inputs.sha256). However, **`assets/subtitles.zh.json` contains the full Japanese lyrics and Chinese translations, and some scene code includes lyric excerpts**. The repository must therefore not be described as containing no lyrics. A code license does not automatically license the music, lyrics, translations or fonts on the same terms.

## License

Original program code is released under the [MIT License](LICENSE), copyright `2026 la-syh`.

The MIT License does not cover the song recording, Japanese lyrics, Chinese translations, reference videos or lyric excerpts embedded in the code. `assets/subtitles.zh.json` is excluded from the MIT grant. Fonts retain their accompanying SIL Open Font License terms; Natural Earth data remains public domain.

See [Third-party content and licensing scope](NOTICE.md) for details.
