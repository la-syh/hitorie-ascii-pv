#!/usr/bin/env python3
"""Pre-flight check: tools, Python packages, and the song/lyrics inputs.

    python3 tools/check_inputs.py

Exits non-zero only when something required is missing; checksum
mismatches are reported as warnings (a different rip of the song will still
render, but the hand-annotated storyboard timings may drift).
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ok = True


def say(flag, msg):
    print(f"[{flag}] {msg}")


if sys.version_info < (3, 9):
    say("FAIL", f"Python 3.9+ required, found {sys.version.split()[0]}")
    ok = False
else:
    say(" ok ", f"Python {sys.version.split()[0]}")

for tool in ("ffmpeg", "ffprobe"):
    if shutil.which(tool):
        v = subprocess.run([tool, "-version"], capture_output=True, text=True).stdout.split("\n")[0]
        say(" ok ", v[:70])
    else:
        say("FAIL", f"{tool} not found (macOS: brew install ffmpeg)")
        ok = False
if not shutil.which("ffplay"):
    say("warn", "ffplay not found: `make play` will run without sound")

for mod in ("numpy", "PIL"):
    try:
        m = __import__(mod)
        say(" ok ", f"{mod} {getattr(m, '__version__', '')}")
    except ImportError:
        say("FAIL", f"python package {mod} missing (make setup)")
        ok = False

expected = {}
sums = ROOT / "inputs.sha256"
if sums.exists():
    for row in sums.read_text(encoding="utf-8").splitlines():
        if row.strip() and not row.startswith("#"):
            h, name = row.split(None, 1)
            expected[name.strip().lstrip("*")] = h

for ext in (".flac", ".lrc"):
    files = sorted(p for p in ROOT.iterdir() if p.suffix.lower() == ext)
    if not files:
        say("FAIL", f"no *{ext} in {ROOT} (put the song and its lyrics next to the Makefile)")
        ok = False
        continue
    f = files[0]
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    exp = expected.get(f.name)
    if exp is None:
        say("warn", f"{f.name}: no reference checksum")
    elif exp == h:
        say(" ok ", f"{f.name}: sha256 matches")
    else:
        say("warn", f"{f.name}: sha256 differs from inputs.sha256 (timings may not line up)")

for asset in ("assets/fonts/BIZUDGothic-Regular.ttf", "assets/fonts/BIZUDGothic-Bold.ttf",
              "assets/earth_mask.txt"):
    say(" ok " if (ROOT / asset).exists() else "FAIL", asset)
    ok &= (ROOT / asset).exists()

sys.exit(0 if ok else 1)
