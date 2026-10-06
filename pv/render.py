"""Frame renderer + video encoder."""
from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from . import shapes as S
from .audio import Analysis, analyze
from .canvas import Canvas
from .glyphs import Atlas
from .lrc import parse
from .raster import Rasterizer
from .storyboard import DOWNBEAT_ANCHOR, build, text_chars
from .timeline import Ctx, Grid

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

COLS, ROWS = 160, 54


def find_inputs(audio: str | None = None, lrc: str | None = None) -> tuple[Path, Path]:
    def pick(ext: str, given: str | None) -> Path:
        if given:
            return Path(given)
        cands = sorted(p for p in ROOT.iterdir() if p.suffix.lower() == ext)
        if not cands:
            sys.exit(f"error: no *{ext} file found in {ROOT}; pass it explicitly")
        return cands[0]
    return pick(".flac", audio), pick(".lrc", lrc)


def load_analysis(audio: Path, fps: float, force: bool = False) -> Analysis:
    meta = BUILD / "analysis.json"
    if not force and meta.exists() and (BUILD / "analysis.npz").exists():
        an = Analysis.load(BUILD)
        if abs(an.fps - fps) < 1e-6:
            return an
    an = analyze(audio, fps)
    an.save(BUILD)
    return an


class PV:
    def __init__(self, audio: Path, lrc: Path, fps: float = 30.0, scale: float = 1.0):
        self.fps = fps
        self.an = load_analysis(audio, fps)
        self.lyrics = parse(lrc, self.an.duration)
        self.grid = Grid(self.an.beats, DOWNBEAT_ANCHOR)
        self.segs = build(self.grid, self.an.duration)
        cw, ch = max(2, int(round(12 * scale))), max(4, int(round(20 * scale)))
        self.atlas = Atlas(cw, ch, max(4, int(round(22 * scale))))
        self.atlas.ensure("".join(self.lyrics.chars()) + text_chars(), bold=False)
        self.atlas.ensure("".join(self.lyrics.chars()) + text_chars(), bold=True)
        self.cv = Canvas(self.atlas, COLS, ROWS)
        self.rast = Rasterizer(self.cv)
        self.n_frames = int(math.ceil(self.an.duration * fps))
        self.size = (self.rast.Wpx, self.rast.Hpx)

    def segment(self, t: float):
        for s in self.segs:
            if s.t0 <= t < s.t1:
                return s
        return self.segs[-1]

    def draw(self, frame: int):
        """Draw frame into the canvas; returns the Post settings."""
        t = frame / self.fps
        sg = self.segment(t)
        ctx = Ctx(t=t, frame=frame, fps=self.fps, an=self.an, grid=self.grid, lyrics=self.lyrics,
                  t0=sg.t0, t1=sg.t1, params=sg.params)
        post = sg.fn(self.cv, ctx)
        # hard cut: a couple of torn frames
        if sg.glitch_in and t - sg.t0 < 2.0 / self.fps:
            rng = ctx.rng(frame, 99)
            S.glitch_rows(self.cv, rng, 0.9, 16)
            S.char_noise(self.cv, rng, 0.06)
            post.chroma = max(post.chroma, 4)
        return post

    def frame(self, frame: int) -> np.ndarray:
        post = self.draw(frame)
        return self.rast.render(post, frame)


# ------------------------------------------------------------- multiprocess
_PV: PV | None = None


def _init(audio, lrc, fps, scale):
    global _PV
    _PV = PV(Path(audio), Path(lrc), fps, scale)


def _work(frame: int) -> bytes:
    return _PV.frame(frame).tobytes()


def render_video(audio: Path, lrc: Path, out: Path, fps: float = 30.0, scale: float = 1.0,
                 start: float = 0.0, end: float | None = None, workers: int | None = None,
                 crf: int = 18, preset: str = "medium") -> None:
    pv = PV(audio, lrc, fps, scale)   # also builds the analysis cache before forking
    f0 = int(round(start * fps))
    f1 = pv.n_frames if end is None else min(pv.n_frames, int(round(end * fps)))
    W, H = pv.size
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-nostats",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
        "-ss", f"{f0 / fps:.6f}", "-t", f"{(f1 - f0) / fps:.6f}", "-i", str(audio),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-tune", "animation", "-g", str(int(fps * 2)),
        "-c:a", "aac", "-b:a", "256k", "-ac", "2",
        "-movflags", "+faststart", "-shortest", str(out),
    ]
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    print(f"rendering frames {f0}..{f1} ({(f1 - f0) / fps:.1f}s) at {W}x{H}@{fps} "
          f"with {workers} worker(s) -> {out}", flush=True)
    t_start = time.time()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        if workers == 1:
            it = (pv.frame(i).tobytes() for i in range(f0, f1))
            pool = None
        else:
            ctx = get_context("spawn")
            pool = ctx.Pool(workers, initializer=_init, initargs=(str(audio), str(lrc), fps, scale))
            it = pool.imap(_work, range(f0, f1), chunksize=4)
        for k, buf in enumerate(it):
            proc.stdin.write(buf)
            if k % 150 == 0:
                el = time.time() - t_start
                print(f"  frame {f0 + k}/{f1}  {(k + 1) / max(el, 1e-6):.1f} fps", file=sys.stderr, flush=True)
        if pool:
            pool.close()
            pool.join()
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed with code {proc.returncode}")
    print(f"done in {time.time() - t_start:.0f}s -> {out}")
