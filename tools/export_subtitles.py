"""Export the same translations and LRC holds used by the PV as bilingual SRT."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pv.render import ROOT, find_inputs, load_analysis
from pv.lrc import parse


def timestamp(t):
    ms = round(t * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def main():
    audio, lrc = find_inputs()
    lyrics = parse(lrc, load_analysis(audio, 30).duration)
    translations = json.loads((ROOT / 'assets/subtitles.zh.json').read_text())
    blocks = []
    for i, ln in enumerate(lyrics.lines, 1):
        blocks.append(f'{i}\n{timestamp(ln.t)} --> {timestamp(ln.end)}\n{ln.text}\n{translations[ln.text]}')
    out = ROOT / 'out/subtitles.zh.srt'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
