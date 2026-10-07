#!/usr/bin/env python3
"""Photosensitivity sanity check: count full-screen luminance flashes.

    python3 tools/flash_check.py

Approximates each frame's mean luminance from the character grid (no
rasterising, so it is fast), then counts 'flashes' -- a jump of more than
FLASH_DELTA in mean luminance followed by a jump back -- in every one-second
window.  The common guideline (WCAG 2.3.1 / ITU-R BT.1702) is no more than
three flashes per second.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pv.render import PV, find_inputs  # noqa: E402

FLASH_DELTA = 0.20


def main():
    audio, lrc = find_inputs()
    pv = PV(audio, lrc, 30.0, 0.25)
    lum = np.zeros(pv.n_frames, np.float32)
    w = np.array([0.2126, 0.7152, 0.0722], np.float32)
    for f in range(pv.n_frames):
        post = pv.draw(f)
        cv = pv.cv
        cm = pv.rast._covmean()
        cell = cv.bg + (cv.fg - cv.bg) * cm[cv.ch][..., None]
        lum[f] = float((cell @ w).mean()) * post.fade + post.flash
    d = np.diff(lum)
    ev = np.nonzero(np.abs(d) > FLASH_DELTA)[0]
    # a flash = two opposing transitions; count transitions/2 per 1 s window
    worst, worst_t = 0.0, 0.0
    fps = pv.fps
    for i in ev:
        win = ev[(ev >= i) & (ev < i + fps)]
        n = len(win) / 2.0
        if n > worst:
            worst, worst_t = n, i / fps
    print(f"{len(ev)} large luminance transitions; worst 1 s window: {worst:.1f} flashes at {worst_t:.2f}s")
    print("OK (<= 3 per second)" if worst <= 3 else "WARNING: more than 3 flashes per second")
    out = Path(__file__).resolve().parent.parent / "build" / "luminance.npy"
    np.save(out, lum)


if __name__ == "__main__":
    main()
