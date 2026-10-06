"""Play the PV as real text in a terminal (ANSI truecolor), with audio.

The same scene code that renders the video draws into the character grid;
here the grid is printed instead of rasterised.  Needs a terminal of at least
160x54 cells (shrink the font) and one supporting 24-bit colour.
Audio is played with ``ffplay`` (part of FFmpeg) when available.
"""
from __future__ import annotations

import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .render import COLS, ROWS, PV


def _reverse_map(pv: PV):
    """glyph index -> (text, kind) where kind 0=normal,1=wide-left,2=wide-right."""
    n = len(pv.atlas.tiles)
    text = [" "] * n
    kind = np.zeros(n, np.int8)
    for (c, _bold), g in pv.atlas.index.items():
        if isinstance(g, tuple):
            text[g[0]] = c
            kind[g[0]] = 1
            text[g[1]] = ""
            kind[g[1]] = 2
        else:
            text[g] = c
    return text, kind


def frame_ansi(pv: PV, text, kind, color: bool, cols: int, rows: int) -> str:
    cv = pv.cv
    x0 = max(0, (COLS - cols) // 2)
    y0 = max(0, (ROWS - rows) // 2)
    ch = cv.ch[y0:y0 + rows, x0:x0 + cols]
    fg = (np.clip(cv.fg[y0:y0 + rows, x0:x0 + cols], 0, 1) * 255).astype(np.uint8) & 0xF8
    bg = (np.clip(cv.bg[y0:y0 + rows, x0:x0 + cols], 0, 1) * 255).astype(np.uint8) & 0xF8
    out = ["\x1b[H"]
    for y in range(ch.shape[0]):
        row = ch[y]
        prev = None
        x = 0
        W = row.shape[0]
        while x < W:
            g = row[x]
            k = kind[g] if g < len(kind) else 0
            if color:
                key = (fg[y, x, 0], fg[y, x, 1], fg[y, x, 2], bg[y, x, 0], bg[y, x, 1], bg[y, x, 2])
                if key != prev:
                    out.append("\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm" % key)
                    prev = key
            if k == 1 and x + 1 < W and g < len(text):
                out.append(text[g])
                x += 2
                continue
            out.append(" " if (k != 0 or g >= len(text)) else text[g])
            x += 1
        out.append("\x1b[0m\n" if y < ch.shape[0] - 1 else "\x1b[0m")
    return "".join(out)


def play(audio: Path, lrc: Path, fps: float = 30.0, start: float = 0.0, with_audio: bool = True,
         color: bool = True) -> None:
    pv = PV(audio, lrc, fps, scale=0.25)  # raster unused; tiny atlas loads faster
    text, kind = _reverse_map(pv)
    tw, th = shutil.get_terminal_size((COLS, ROWS))
    cols, rows = min(COLS, tw), min(ROWS, th - 1)
    if tw < COLS or th - 1 < ROWS:
        print(f"note: terminal is {tw}x{th}; the PV is {COLS}x{ROWS} cells -- shrink the font "
              f"for the full picture. Showing the centre. (starting in 2 s)")
        time.sleep(2)
    proc = None
    if with_audio and shutil.which("ffplay"):
        proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                                 "-ss", f"{start:.3f}", str(audio)],
                                stdin=subprocess.DEVNULL)
    elif with_audio:
        print("ffplay not found: playing without audio (install FFmpeg for sound)")
        time.sleep(1)
    sys.stdout.write("\x1b[?25l\x1b[2J")
    t_wall0 = time.perf_counter() + (0.12 if proc else 0.0)
    try:
        while True:
            t = start + (time.perf_counter() - t_wall0)
            if t >= pv.an.duration:
                break
            f = int(t * fps)
            pv.draw(f)
            sys.stdout.write(frame_ansi(pv, text, kind, color, cols, rows))
            sys.stdout.flush()
            # sleep until the next frame is due (frames are dropped when late)
            nxt = (f + 1) / fps - (time.perf_counter() - t_wall0) - start
            if nxt > 0:
                time.sleep(nxt)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")
        sys.stdout.flush()
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
