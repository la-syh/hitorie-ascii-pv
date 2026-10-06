"""Frame renderer + video encoder."""
from __future__ import annotations

import hashlib
import math
import os
import subprocess
import sys
import time
from collections import deque
from itertools import islice
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


def _ordered(pool, items, window: int):
    """Like pool.imap, but with at most ``window`` frames in flight, so fast
    workers can't pile up gigabytes of finished frames ahead of the encoder."""
    q: deque = deque()
    it = iter(items)
    for x in islice(it, window):
        q.append(pool.apply_async(_work, (x,)))
    while q:
        res = q.popleft().get()
        nxt = next(it, None)
        if nxt is not None:
            q.append(pool.apply_async(_work, (nxt,)))
        yield res


def _ffmpeg_video_cmd(W: int, H: int, fps: float, out: Path, crf: int, preset: str,
                      audio: Path | None = None, t0: float = 0.0, dur: float = 0.0) -> list[str]:
    cmd = ["ffmpeg", "-y", "-v", "error", "-nostats",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
    if audio is not None:
        cmd += ["-ss", f"{t0:.6f}", "-t", f"{dur:.6f}", "-i", str(audio), "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-tune", "animation", "-g", str(int(fps * 2))]
    if audio is not None:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-ac", "2", "-shortest"]
    cmd += ["-movflags", "+faststart", str(out)]
    return cmd


def _encode(frames_iter, cmd: list[str], f0: int, f1: int, t_start: float) -> None:
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for k, buf in enumerate(frames_iter):
            proc.stdin.write(buf)
            if (f0 + k) % 300 == 0:
                print(f"  frame {f0 + k}/{f1}  ({time.time() - t_start:.0f}s)", file=sys.stderr, flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed with code {proc.returncode}")


def cache_key(audio: Path, lrc: Path, fps: float, scale: float, crf: int, preset: str) -> str:
    """Hash of everything that affects the pixels: code, assets, inputs, settings."""
    h = hashlib.sha1()
    for p in sorted((ROOT / "pv").glob("*.py")) + [ROOT / "assets" / "earth_mask.txt", lrc,
                                                     BUILD / "analysis.json"]:
        h.update(p.read_bytes())
    for p in sorted((ROOT / "assets" / "fonts").glob("*.ttf")):
        h.update(f"{p.name}:{p.stat().st_size}".encode())
    h.update(f"{audio.stat().st_size}|{fps}|{scale}|{crf}|{preset}".encode())
    return h.hexdigest()[:12]


def render_video(audio: Path, lrc: Path, out: Path, fps: float = 30.0, scale: float = 1.0,
                 start: float = 0.0, end: float | None = None, workers: int | None = None,
                 crf: int = 18, preset: str = "medium", segment: float = 20.0,
                 max_time: float | None = None) -> None:
    """Render the PV.

    A full render is done in ``segment``-second chunks (video only), cached in
    build/segments/<key>/ and then joined and muxed with the audio in one pass.
    Interrupted renders resume where they stopped; any change to the code,
    inputs or settings changes the key, so stale chunks are never reused.
    ``--start/--end`` renders just that range in a single pass (with audio).
    """
    pv = PV(audio, lrc, fps, scale)   # also builds the analysis cache before forking
    W, H = pv.size
    out.parent.mkdir(parents=True, exist_ok=True)
    workers = workers or max(1, (os.cpu_count() or 2) - 1)
    t_start = time.time()
    pool = None

    def frames(a: int, b: int):
        nonlocal pool
        if workers == 1:
            return (pv.frame(i).tobytes() for i in range(a, b))
        if pool is None:
            pool = get_context("spawn").Pool(workers, initializer=_init,
                                             initargs=(str(audio), str(lrc), fps, scale))
        return _ordered(pool, range(a, b), window=3 * workers)

    try:
        if start > 0 or end is not None:
            f0 = int(round(start * fps))
            f1 = pv.n_frames if end is None else min(pv.n_frames, int(round(end * fps)))
            print(f"rendering {f0 / fps:.2f}-{f1 / fps:.2f}s at {W}x{H}@{fps} with {workers} worker(s) -> {out}",
                  flush=True)
            _encode(frames(f0, f1), _ffmpeg_video_cmd(W, H, fps, out, crf, preset, audio, f0 / fps,
                                                       (f1 - f0) / fps), f0, f1, t_start)
            print(f"done in {time.time() - t_start:.0f}s -> {out}")
            return

        key = cache_key(audio, lrc, fps, scale, crf, preset)
        segdir = BUILD / "segments" / key
        segdir.mkdir(parents=True, exist_ok=True)
        seg_f = int(round(segment * fps))
        bounds = [(a, min(pv.n_frames, a + seg_f)) for a in range(0, pv.n_frames, seg_f)]
        todo = [i for i in range(len(bounds)) if not (segdir / f"seg_{i:04d}.mp4").exists()]
        print(f"rendering {pv.n_frames} frames ({pv.an.duration:.1f}s) at {W}x{H}@{fps} with "
              f"{workers} worker(s); {len(bounds) - len(todo)}/{len(bounds)} segments cached "
              f"in {segdir.relative_to(ROOT)}", flush=True)
        for i in todo:
            if max_time is not None and time.time() - t_start > max_time:
                left = sum(1 for j in todo if not (segdir / f"seg_{j:04d}.mp4").exists())
                print(f"stopping after --max-time; {left} segment(s) left -- run the same command again to resume")
                sys.exit(3)
            a, b = bounds[i]
            tmp = segdir / f"seg_{i:04d}.tmp.mp4"
            _encode(frames(a, b), _ffmpeg_video_cmd(W, H, fps, tmp, crf, preset), a, pv.n_frames, t_start)
            tmp.rename(segdir / f"seg_{i:04d}.mp4")
            print(f"  segment {i + 1}/{len(bounds)} done ({time.time() - t_start:.0f}s)", flush=True)
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    lst = segdir / "segments.txt"
    lst.write_text("".join(f"file '{(segdir / f'seg_{i:04d}.mp4').as_posix()}'\n"
                           for i in range(len(bounds))))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio),
           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ac", "2",
           "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"done in {time.time() - t_start:.0f}s -> {out}")
