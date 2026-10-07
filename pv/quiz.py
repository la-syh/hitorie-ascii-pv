"""Question -> answer -> verdict sequences, cut to the beat.

A line becomes a rapid run of cards: a question types in, an answer types in,
then a verdict stamps down (✓ / ✗ / ?) with a hit; the next card slides in.
Three skins: 'exam' (answer sheet on paper), 'term' (terminal on black),
'show' (quiz-show panel in red/black).
"""
from __future__ import annotations

import math

import numpy as np

from . import world as Wd
from .canvas import Canvas, hexc
from .palette import GREY, INK, PAPER, RED, mix
from .timeline import Ctx

RED2 = hexc("#ff3b2e")
GREEN = hexc("#2fbf5a")
P = 46


def _typed(s: str, k: float) -> str:
    return s[: max(0, int(round(len(s) * min(1.0, max(0.0, k)))))]


def card_state(ctx: Ctx, n_cards: int, beats_per_card: float):
    """Which card is current and its phase (0..1)."""
    b = ctx.beat - ctx.grid.beat_pos(ctx.t0)
    i = int(b / beats_per_card)
    ph = (b / beats_per_card) % 1.0
    return min(i, n_cards - 1), (ph if i < n_cards else 1.0), b


def stamp(cv: Canvas, s: str, cx, cy, rows, col, k):
    """A big glyph landing: oversized at k=0, settles at k=1."""
    if k <= 0:
        return
    r = int(round(rows * (1.6 - 0.6 * min(1.0, k))))
    bmp = cv.text_bitmap(s, max(3, r), True)
    h, w = bmp.shape
    m = np.zeros((cv.H, cv.W), bool)
    ox, oy = int(cx - w / 2), int(cy - h / 2)
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(cv.W, ox + w), min(P, oy + h)
    if x1 > x0 and y1 > y0:
        m[y0:y1, x0:x1] = bmp[y0 - oy:y1 - oy, x0 - ox:x1 - ox] > 0.42
    cv.bg[m] = col
    cv.ch[m] = cv.ids("#")[0]
    cv.fg[m] = mix(col, PAPER, 0.35)


def run(cv: Canvas, ctx: Ctx, cards, skin="exam", beats_per_card=1.0, title=""):
    """cards: list of (question, answer, verdict) with verdict in '✓', '✗', '?'.
    Returns (verdict_hit_strength, current_verdict) for the caller's post."""
    i, ph, b = card_state(ctx, len(cards), beats_per_card)
    q, a, v = cards[i]
    qk, ak = ph / 0.3, (ph - 0.3) / 0.3
    vk = (ph - 0.62) / 0.12
    hit = math.exp(-max(0.0, ph - 0.62) * beats_per_card * 10) if ph >= 0.62 else 0.0
    vcol = GREEN if v == "✓" else (RED2 if v == "✗" else GREY)

    if skin == "exam":
        cv.clear(PAPER, INK)
        for y in range(0, P, 2):
            cv.line(0, y, cv.W, y, mix(PAPER, hexc("#9fb8d0"), 0.35), "-")
        cv.line(14, 0, 14, P, mix(PAPER, RED2, 0.5), "|")
        cv.put(18, 1, title or "期末テスト   氏名 ________", INK, bold=True)
        # history of previous cards, small, down the left
        for j in range(max(0, i - 6), i):
            qq, aa, vv = cards[j]
            y = 5 + (j - max(0, i - 6)) * 2
            cv.put(18, y, f"({j + 1}) {qq}", mix(PAPER, INK, 0.6))
            cv.put(64, y, aa, mix(PAPER, INK, 0.5))
            cv.put(80, y, "×" if vv == "✗" else vv, GREEN if vv == "✓" else RED2, bold=True)
        bx0, by0 = 18, 21
        cv.box(bx0, by0, 150, 43, INK, "+=|", bold=True)
        cv.put(bx0 + 3, by0 + 2, f"Q{i + 1}.", RED2, bold=True)
        bmp = cv.text_bitmap(_typed(q, qk) or " ", 8, True)
        cv.shape_field(bmp, bx0 + 9, by0 + 1, INK)
        cv.put(bx0 + 3, by0 + 10, "A.", INK, bold=True)
        bmp = cv.text_bitmap(_typed(a, ak) or " ", 7, True)
        cv.shape_field(bmp, bx0 + 9, by0 + 9, mix(INK, hexc("#1f3a8a"), 0.6))
        if 0.3 < ph < 0.62 and int(ctx.t * 6) % 2:
            cv.put(bx0 + 9 + int(len(_typed(a, ak)) * 6), by0 + 15, "_", INK, bold=True)
        if ph >= 0.62:
            stamp(cv, "×" if v == "✗" else v, 128, 31, 18, vcol, vk)
    elif skin == "term":
        cv.clear(hexc("#05070a"), hexc("#7dff9a"))
        g = hexc("#7dff9a")
        cv.put(2, 1, title or "~/everyday $", mix(g, INK, 0.4))
        lines = []
        for j in range(max(0, i - 8), i):
            qq, aa, vv = cards[j]
            lines.append((f"> {qq}", g))
            lines.append((f"  {aa}  " + ("[ OK ]" if vv == "✓" else "[FAIL]" if vv == "✗" else "[ ?? ]"),
                          GREEN if vv == "✓" else RED2))
        y = 3
        for s, c in lines[-14:]:
            cv.put(4, y, s, mix(c, INK, 0.45))
            y += 1
        cv.put(4, y + 1, "> " + _typed(q, qk) + ("_" if ph < 0.3 and int(ctx.t * 6) % 2 else ""), g, bold=True)
        if ph >= 0.3:
            cv.put(4, y + 2, "  " + _typed(a, ak), PAPER, bold=True)
        bmp = cv.text_bitmap(_typed(q, qk) or " ", 9, True)
        cv.shape_field(bmp, 52, 24, mix(g, INK, 0.2))
        if ph >= 0.62:
            word = {"✓": "OK", "✗": "FAIL", "?": "NULL"}[v]
            stamp(cv, word, 104, 12, 10, vcol, vk)
    elif skin in ("big", "big_red", "big_paper"):
        # full-frame typography: question across the top, answer slammed in a
        # band below, the verdict stamped over the right third.
        bg, fg, band, bfg = {
            "big": (hexc("#07070b"), PAPER, hexc("#1b1b22"), PAPER),
            "big_red": (hexc("#d9261c"), PAPER, INK, PAPER),
            "big_paper": (PAPER, INK, INK, PAPER),
        }[skin]
        cv.clear(bg, fg)
        cv.put(3, 1, title or f"Q.{i + 1:02d}", mix(bg, fg, 0.55), bold=True)
        qs = _typed(q, qk) or " "
        rows = 13 if len(q) <= 7 else 10
        bmp = cv.text_bitmap(qs, rows, True)
        cv.shape_field(bmp, int(80 - cv.text_bitmap(q, rows, True).shape[1] / 2), 3, fg)
        y0 = 22
        slide = 1 - min(1.0, max(0.0, ak * 2.5))
        Wd.fill_rect(cv, int(-160 * slide), y0, int(160 - 160 * slide), y0 + 15, band, " ")
        if ph >= 0.3:
            bm = cv.text_bitmap(_typed(a, ak) or " ", 11, True)
            cv.shape_field(bm, 10, y0 + 2, bfg if not (ph >= 0.62) else mix(bfg, vcol, 0.6))
        for j in range(i + (1 if ph >= 0.62 else 0)):
            vv = cards[j][2]
            cv.put(4 + j * 4, 41, "×" if vv == "✗" else ("○" if vv == "✓" else "?"),
                   GREEN if vv == "✓" else (RED2 if vv == "✗" else GREY), bold=True)
        if ph >= 0.62:
            stamp(cv, "×" if v == "✗" else ("○" if v == "✓" else "?"), 128, 28, 20, vcol, vk)
    else:  # show
        cv.clear(hexc("#120406"), PAPER)
        for k in range(0, 160, 4):
            on = (k // 4 + int(ctx.t * 8)) % 3 == 0
            cv.put(k, 0, "●", RED2 if on else hexc("#3a1010"))
            cv.put(k, 45, "●", RED2 if on else hexc("#3a1010"))
        Wd.fill_rect(cv, 6, 2, 154, 17, hexc("#1a2a6a"), " ")
        cv.box(6, 2, 154, 17, hexc("#ffd84a"), "+=|", bold=True)
        cv.put(14, 4, f"QUESTION {i + 1:02d}", hexc("#ffd84a"), bold=True)
        bmp = cv.text_bitmap(_typed(q, qk) or " ", 9, True)
        cv.shape_field(bmp, int(80 - bmp.shape[1] / 2), 6, PAPER)
        for j, opt in enumerate(("A", "B", "C", "D")):
            x, y = 14 + (j % 2) * 70, 21 + (j // 2) * 10
            chosen = ph >= 0.3 and j == (i % 4)
            Wd.fill_rect(cv, x, y, x + 62, y + 6, RED2 if chosen and ph >= 0.62 and v == "✗" else
                         (GREEN if chosen and ph >= 0.62 and v == "✓" else
                          (hexc("#c9a020") if chosen else hexc("#1a1a2a"))), " ")
            cv.box(x, y, x + 62, y + 6, hexc("#ffd84a"), "+-|")
            cv.put(x + 2, y + 3, opt + ".", PAPER, bold=True)
            if chosen:
                bm = cv.text_bitmap(_typed(a, ak) or " ", 5, True)
                cv.shape_field(bm, x + 8, y + 1, PAPER)
        if ph >= 0.62:
            stamp(cv, "×" if v == "✗" else v, 80, 26, 22, vcol, vk)
    return hit, v
