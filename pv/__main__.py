"""Command line: python3 -m pv {analyze,still,sheet,render,play,info}"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from .render import BUILD, ROOT, PV, find_inputs, load_analysis, render_video


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m pv", description="ASCII PV renderer")
    ap.add_argument("--audio", help="audio file (default: the .flac in the project root)")
    ap.add_argument("--lrc", help="lyrics file (default: the .lrc in the project root)")
    ap.add_argument("--fps", type=float, default=30.0)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("analyze", help="beat/tempo/feature analysis -> build/analysis.*")
    sub.add_parser("info", help="print the storyboard with timings")

    s = sub.add_parser("still", help="render single frames to PNG")
    s.add_argument("times", nargs="+", type=float, help="song times in seconds")
    s.add_argument("--out", default=str(ROOT / "out" / "stills"))
    s.add_argument("--scale", type=float, default=1.0)

    s = sub.add_parser("sheet", help="contact sheet of the whole PV")
    s.add_argument("--every", type=float, default=4.0, help="seconds between thumbnails")
    s.add_argument("--out", default=str(ROOT / "out" / "contact_sheet.png"))

    s = sub.add_parser("render", help="render the PV to video")
    s.add_argument("--out", default=str(ROOT / "out" / "pv.mp4"))
    s.add_argument("--start", type=float, default=0.0)
    s.add_argument("--end", type=float, default=None)
    s.add_argument("--scale", type=float, default=1.0, help="0.5 = 960x540 quick preview")
    s.add_argument("--workers", type=int, default=None)
    s.add_argument("--crf", type=int, default=18)
    s.add_argument("--preset", default="medium")
    s.add_argument("--segment", type=float, default=20.0, help="chunk length (s) for resumable renders")
    s.add_argument("--max-time", type=float, default=None,
                   help="stop (exit 3) after this many seconds; rerun to resume")

    s = sub.add_parser("play", help="play the PV as text in this terminal")
    s.add_argument("--start", type=float, default=0.0)
    s.add_argument("--no-audio", action="store_true")
    s.add_argument("--mono", action="store_true", help="no colours")

    a = ap.parse_args(argv)
    audio, lrc = find_inputs(a.audio, a.lrc)

    if a.cmd == "analyze":
        an = load_analysis(audio, a.fps, force=True)
        print(f"wrote {BUILD / 'analysis.json'} ({len(an.beats)} beats, {an.bpm:.2f} BPM)")
    elif a.cmd == "info":
        pv = PV(audio, lrc, a.fps, 0.25)
        print(f"{pv.an.duration:.2f}s  {pv.an.bpm:.2f} BPM  {pv.n_frames} frames @ {a.fps} fps")
        for sg in pv.segs:
            print(f"  {sg.t0:7.2f} - {sg.t1:7.2f}  {sg.name}")
    elif a.cmd == "still":
        pv = PV(audio, lrc, a.fps, a.scale)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for t in a.times:
            f = int(round(t * a.fps))
            img = pv.frame(f)
            p = out / f"t{t:07.2f}.png"
            Image.fromarray(img).save(p)
            print(p)
    elif a.cmd == "sheet":
        pv = PV(audio, lrc, a.fps, 0.5)
        ts = [t for t in frange(0.5, pv.an.duration - 0.2, a.every)]
        thumbs = [Image.fromarray(pv.frame(int(t * a.fps))).resize((480, 270), Image.BILINEAR) for t in ts]
        cols = 6
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 484, rows * 274), (40, 40, 40))
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % cols) * 484 + 2, (i // cols) * 274 + 2))
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(a.out)
        print(a.out)
    elif a.cmd == "render":
        render_video(audio, lrc, Path(a.out), a.fps, a.scale, a.start, a.end, a.workers, a.crf, a.preset,
                     a.segment, a.max_time)
    elif a.cmd == "play":
        from .player import play
        play(audio, lrc, a.fps, a.start, not a.no_audio, not a.mono)


def frange(a, b, step):
    x = a
    while x < b:
        yield x
        x += step


if __name__ == "__main__":
    main(sys.argv[1:])
