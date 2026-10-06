"""Audio decoding and music analysis (numpy only, no librosa/scipy).

The analysis produces everything the visuals need to "hear" the song:

* a beat grid (dynamic-programming beat tracker, Ellis 2007 style),
* bar/downbeat phase (assumes 4/4, picks the phase with the strongest kicks),
* per-video-frame features: loudness, low/mid/high band energy, onset strength.

Results are cached in ``build/analysis.npz`` + ``build/analysis.json`` so the
renderer never has to touch the audio decoder again.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

SR = 22050          # analysis sample rate
N_FFT = 2048
HOP = 256           # ~11.6 ms hop -> fine-grained onsets for a ~200 BPM song


# --------------------------------------------------------------------------- io
def decode_mono(path: Path, sr: int = SR) -> np.ndarray:
    """Decode any ffmpeg-readable file to mono float32 at ``sr``."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-ac", "1", "-ar", str(sr), "-f", "f32le", "-",
    ]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


# --------------------------------------------------------------------- spectra
def stft_mag(y: np.ndarray) -> np.ndarray:
    """Magnitude STFT, shape (frames, bins)."""
    pad = N_FFT // 2
    y = np.pad(y, (pad, pad))
    n_frames = 1 + (len(y) - N_FFT) // HOP
    win = np.hanning(N_FFT).astype(np.float32)
    out = np.empty((n_frames, N_FFT // 2 + 1), dtype=np.float32)
    step = 2048
    for s in range(0, n_frames, step):
        e = min(n_frames, s + step)
        idx = (np.arange(s, e) * HOP)[:, None] + np.arange(N_FFT)[None, :]
        out[s:e] = np.abs(np.fft.rfft(y[idx] * win, axis=1))
    return out


def log_bands(mag: np.ndarray, n_bands: int = 48, fmin: float = 30.0) -> tuple[np.ndarray, np.ndarray]:
    """Collapse STFT bins into log-spaced triangular bands. Returns (bands, centre_freqs)."""
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / SR)
    edges = np.geomspace(fmin, SR / 2 * 0.95, n_bands + 2)
    fb = np.zeros((n_bands, len(freqs)), dtype=np.float32)
    for b in range(n_bands):
        lo, c, hi = edges[b], edges[b + 1], edges[b + 2]
        up = (freqs - lo) / (c - lo)
        down = (hi - freqs) / (hi - c)
        fb[b] = np.clip(np.minimum(up, down), 0, None)
        if fb[b].sum() == 0:  # very narrow low bands: take nearest bin
            fb[b, np.argmin(np.abs(freqs - c))] = 1
        fb[b] /= fb[b].sum()
    return mag @ fb.T, edges[1:-1]


def onset_envelope(bands: np.ndarray) -> np.ndarray:
    lg = np.log1p(1000.0 * bands)
    flux = np.maximum(0.0, np.diff(lg, axis=0, prepend=lg[:1]))
    env = flux.mean(axis=1)
    # remove slow trend so loud passages don't dominate
    k = 64
    trend = np.convolve(env, np.ones(k) / k, mode="same")
    env = np.maximum(0.0, env - trend)
    return env / (env.std() + 1e-9)


# ----------------------------------------------------------------------- tempo
def estimate_tempo(env: np.ndarray, fps: float, lo: float = 70, hi: float = 260,
                   prior_bpm: float = 180.0) -> tuple[float, list[tuple[float, float]]]:
    """Autocorrelation tempo estimate with a broad log-normal prior.

    Returns (bpm, top candidates [(bpm, score), ...]).
    """
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    ac /= ac[0]
    lags = np.arange(len(ac))
    bpms = 60.0 * fps / np.maximum(lags, 1)
    valid = (bpms >= lo) & (bpms <= hi)
    prior = np.exp(-0.5 * (np.log2(bpms / prior_bpm) / 0.9) ** 2)
    score = np.where(valid, ac * prior, -np.inf)
    order = np.argsort(score)[::-1]
    cands: list[tuple[float, float]] = []
    for i in order:
        if not np.isfinite(score[i]):
            break
        b = float(bpms[i])
        if all(abs(b - c) / c > 0.04 for c, _ in cands):
            cands.append((b, float(score[i])))
        if len(cands) >= 6:
            break
    # refine the best lag with parabolic interpolation
    i = int(np.argmax(score))
    if 1 <= i < len(ac) - 1:
        a, b_, c = ac[i - 1], ac[i], ac[i + 1]
        denom = a - 2 * b_ + c
        off = 0.5 * (a - c) / denom if denom != 0 else 0.0
        lag = i + off
    else:
        lag = float(i)
    return 60.0 * fps / lag, cands


def track_beats(env: np.ndarray, fps: float, bpm: float, tightness: float = 300.0) -> np.ndarray:
    """Dynamic-programming beat tracker. Returns beat times in seconds."""
    period = 60.0 * fps / bpm
    # local score: onset env smoothed by a gaussian of ~period/16
    sig = period / 16
    k = np.arange(-int(4 * sig), int(4 * sig) + 1)
    g = np.exp(-0.5 * (k / sig) ** 2)
    local = np.convolve(env, g / g.sum(), mode="same")

    n = len(local)
    backlink = -np.ones(n, dtype=np.int64)
    cum = local.copy()
    lo, hi = int(round(-2 * period)), int(round(-period / 2))
    window = np.arange(lo, hi + 1)
    txwt = -tightness * (np.log(-window / period) ** 2)
    for i in range(n):
        idx = i + window
        ok = idx >= 0
        if not ok.any():
            continue
        cand = cum[idx[ok]] + txwt[ok]
        j = int(np.argmax(cand))
        cum[i] = local[i] + cand[j]
        backlink[i] = idx[ok][j]
    # pick best end in the last period
    tail = cum[-int(period * 2):]
    i = n - int(period * 2) + int(np.argmax(tail))
    beats = [i]
    while backlink[i] >= 0:
        i = int(backlink[i])
        beats.append(i)
    beats = np.array(beats[::-1], dtype=np.float64)
    # drop beats in silent lead-in / tail
    loud = local[beats.astype(int)] > 0.05 * local.max()
    first = np.argmax(loud)
    last = len(loud) - np.argmax(loud[::-1])
    return beats[first:last] / fps


# -------------------------------------------------------------------- results
@dataclass
class Analysis:
    duration: float
    bpm: float
    tempo_candidates: list
    beats: list            # seconds
    downbeat_phase: int    # index into beats of the first bar's downbeat (0..3)
    fps: float             # video fps the frame features were sampled at

    # numpy blobs stored separately
    rms: np.ndarray | None = None
    low: np.ndarray | None = None
    mid: np.ndarray | None = None
    high: np.ndarray | None = None
    onset: np.ndarray | None = None
    spectrum: np.ndarray | None = None  # (frames, 32) normalised band energies

    # ------------------------------------------------------------- helpers
    def frame(self, t: float) -> int:
        return int(np.clip(round(t * self.fps), 0, len(self.rms) - 1))

    def save(self, build: Path) -> None:
        build.mkdir(parents=True, exist_ok=True)
        meta = {k: v for k, v in asdict(self).items()
                if not isinstance(v, np.ndarray) and v is not None}
        (build / "analysis.json").write_text(json.dumps(meta, indent=1))
        np.savez_compressed(build / "analysis.npz", rms=self.rms, low=self.low, mid=self.mid,
                            high=self.high, onset=self.onset, spectrum=self.spectrum)

    @classmethod
    def load(cls, build: Path) -> "Analysis":
        meta = json.loads((build / "analysis.json").read_text())
        blobs = np.load(build / "analysis.npz")
        a = cls(**meta)
        for k in ("rms", "low", "mid", "high", "onset", "spectrum"):
            setattr(a, k, blobs[k])
        return a


def _norm(x: np.ndarray, pct: float = 99.0) -> np.ndarray:
    hi = np.percentile(x, pct)
    return np.clip(x / (hi + 1e-9), 0, 1.5).astype(np.float32)


def _resample(x: np.ndarray, src_fps: float, dst_fps: float, n_dst: int) -> np.ndarray:
    """Max-pool + interpolate a feature track from analysis rate to video rate."""
    t_dst = np.arange(n_dst) / dst_fps
    # max over the window covering each video frame keeps transients visible
    w = max(1, int(round(src_fps / dst_fps)))
    if x.ndim == 1:
        pooled = np.maximum.reduce([np.roll(x, -s) for s in range(w)])
        return np.interp(t_dst, np.arange(len(x)) / src_fps, pooled).astype(np.float32)
    cols = [_resample(x[:, i], src_fps, dst_fps, n_dst) for i in range(x.shape[1])]
    return np.stack(cols, axis=1)


def analyze(audio: Path, video_fps: float, bpm_hint: float | None = None,
            verbose: bool = True) -> Analysis:
    y = decode_mono(audio)
    duration = len(y) / SR
    a_fps = SR / HOP
    mag = stft_mag(y)
    bands, centres = log_bands(mag)
    env = onset_envelope(bands)

    bpm, cands = estimate_tempo(env, a_fps)
    if bpm_hint:
        # snap to the candidate closest to the hint (guards against octave errors)
        bpm = min([c for c, _ in cands] + [bpm], key=lambda b: abs(b - bpm_hint))
    beats = track_beats(env, a_fps, bpm)
    # refine bpm from the median inter-beat interval
    if len(beats) > 8:
        bpm = 60.0 / float(np.median(np.diff(beats)))

    # band energies (power) for visual features
    power = bands ** 2
    low = power[:, centres < 150].sum(1)
    mid = power[:, (centres >= 150) & (centres < 2500)].sum(1)
    high = power[:, centres >= 2500].sum(1)
    rms = np.sqrt(np.convolve(y ** 2, np.ones(HOP) / HOP, mode="same")[::HOP][: len(low)])

    # downbeat phase: which beat (mod 4) has most low-end energy on average
    li = np.clip((beats * a_fps).astype(int), 0, len(low) - 1)
    lowb = np.log1p(low[li] / (np.median(low) + 1e-9))
    phase_scores = [float(lowb[p::4].mean()) for p in range(4)]
    downbeat_phase = int(np.argmax(phase_scores))

    n_video = int(np.ceil(duration * video_fps))
    spec32 = bands[:, np.linspace(2, bands.shape[1] - 3, 32).astype(int)]
    spec32 = np.log1p(200 * spec32 / (np.percentile(spec32, 99, axis=0) + 1e-9))
    spec32 /= np.percentile(spec32, 99.5) + 1e-9

    an = Analysis(
        duration=duration, bpm=float(bpm),
        tempo_candidates=[[round(b, 2), round(s, 4)] for b, s in cands],
        beats=[round(float(b), 4) for b in beats],
        downbeat_phase=downbeat_phase, fps=video_fps,
        rms=_norm(_resample(rms, a_fps, video_fps, n_video)),
        low=_norm(_resample(np.log1p(low / np.median(low)), a_fps, video_fps, n_video)),
        mid=_norm(_resample(np.log1p(mid / np.median(mid)), a_fps, video_fps, n_video)),
        high=_norm(_resample(np.log1p(high / np.median(high)), a_fps, video_fps, n_video)),
        onset=_norm(_resample(env, a_fps, video_fps, n_video), 99.5),
        spectrum=np.clip(_resample(spec32, a_fps, video_fps, n_video), 0, 1.2).astype(np.float32),
    )
    if verbose:
        print(f"duration {duration:.2f}s  bpm {an.bpm:.2f}  beats {len(beats)}  "
              f"downbeat phase {downbeat_phase} {['%.2f' % p for p in phase_scores]}")
        print("tempo candidates:", an.tempo_candidates)
    return an
