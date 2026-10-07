"""Regression checks for subtitle timing, glyph coverage and stateless new scenes."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pv.render import PV, find_inputs

pv = PV(*find_inputs(), scale=.5)
assert all(ln.t in pv.translations for ln in pv.lyrics.lines)
# The fallback's missing glyph must not silently appear in Chinese captions.
missing = bytes(pv.atlas.zh_font.getmask(chr(0x10ffff)))
for ch in pv.atlas.zh_chars:
    if not ch.isspace():
        assert bytes(pv.atlas.zh_font.getmask(ch)) != missing, f'Missing Chinese glyph: {ch}'
for ln in pv.lyrics.lines:
    assert pv.lyrics.at(ln.t + .01) is ln
    pv.draw(int(np.ceil(ln.t * pv.fps)) + 1)
    assert np.any(pv.cv.ch[52]), f'No caption for {ln.text}'
for t in (20, 120, 140, 225):
    assert pv.lyrics.at(t) is None, f'Stale caption at {t}'
# Out-of-order drawing must not change the result (multiprocess renderer contract).
for t in (52,55,59,62,72,87,127,130,133,136,173,219):
    frame=round(t*pv.fps)
    first=pv.frame(frame)
    pv.frame(0)
    assert np.array_equal(first,pv.frame(frame)), f'Non-deterministic scene at {t}'
    assert first.shape==(540,960,3)
# Exercise every cut and its neighboring frames.
for sg in pv.segs:
    for f in (round(sg.t0*30)-1,round(sg.t0*30),round(sg.t0*30)+1):
        if f>=0: pv.draw(f)
print(f'PASS: {len(pv.lyrics.lines)} translated lines, glyph coverage, gaps, scene boundaries and determinism')
