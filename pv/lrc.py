"""LRC lyric parsing.

Handles plain ``[mm:ss.xx] text`` lines and the JSON metadata lines that some
players (e.g. NetEase Cloud Music) prepend, such as
``{"t":0,"c":[{"tx":"作词: "},{"tx":"wowaka"}]}``.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_TAG = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


@dataclass
class Line:
    t: float          # start (s)
    end: float        # end (s) — derived
    text: str
    index: int = 0    # index among sung lines

    @property
    def dur(self) -> float:
        return self.end - self.t


@dataclass
class Lyrics:
    lines: list[Line]
    credits: list[str]  # e.g. ["作词: wowaka", "作曲: wowaka"]

    def at(self, t: float) -> Line | None:
        for ln in self.lines:
            if ln.t <= t < ln.end:
                return ln
        return None

    def chars(self) -> set[str]:
        s: set[str] = set()
        for ln in self.lines:
            s.update(ln.text)
        for c in self.credits:
            s.update(c)
        return s


def parse(path: Path, song_end: float | None = None, max_tail: float = 3.4) -> Lyrics:
    raw: list[tuple[float, str]] = []
    credits: list[str] = []
    for row in path.read_text(encoding="utf-8-sig").splitlines():
        row = row.strip()
        if not row:
            continue
        if row.startswith("{"):
            try:
                obj = json.loads(row)
                credits.append("".join(c.get("tx", "") for c in obj.get("c", [])).strip())
            except json.JSONDecodeError:
                pass
            continue
        tags = list(_TAG.finditer(row))
        if not tags:
            continue
        text = _TAG.sub("", row).strip()
        text = unicodedata.normalize("NFC", text)
        for m in tags:
            raw.append((int(m.group(1)) * 60 + float(m.group(2)), text))
    raw.sort(key=lambda x: x[0])

    lines: list[Line] = []
    for i, (t, text) in enumerate(raw):
        if not text:
            continue
        nxt = raw[i + 1][0] if i + 1 < len(raw) else (song_end or t + max_tail)
        # cap the hold on the last line of a block (before instrumental gaps)
        hold = min(nxt - t, max_tail + 0.12 * len(text))
        lines.append(Line(t=t, end=t + max(0.3, hold), text=text))
    for k, ln in enumerate(lines):
        ln.index = k
    return Lyrics(lines=lines, credits=[c for c in credits if c])


def char_width(ch: str) -> int:
    """Terminal cell width of a character (1 or 2)."""
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_width(s: str) -> int:
    return sum(char_width(c) for c in s)
