# ASCII PV for ヒトリエ「日常と地球の額縁」
#
#   make setup    create .venv and install numpy + pillow
#   make check    verify tools, packages and the song/lyrics inputs
#   make render   full PV  -> out/pv.mp4  (1920x1080, 30 fps)
#
# Uses .venv/bin/python when it exists, otherwise python3 (override: make PY=...).

PY ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
WORKERS ?=
W := $(if $(WORKERS),--workers $(WORKERS),)

.PHONY: all setup check analyze info render preview sheet stills play clean

all: render

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

check:
	$(PY) tools/check_inputs.py

analyze:
	$(PY) -m pv analyze

info:
	$(PY) -m pv info

render:
	$(PY) -m pv render --out out/pv.mp4 $(W)

preview:
	$(PY) -m pv render --scale 0.5 --crf 23 --preset veryfast --out out/preview_540p.mp4 $(W)

sheet:
	$(PY) -m pv sheet --every 2.5 --out out/contact_sheet.png

stills:
	$(PY) -m pv still 20 33 44 58 68 92 94.6 100 107 118 132 151 158 168 173 199 216 220.5

play:
	$(PY) -m pv play

# removes generated files only (build/ cache and out/ renders)
clean:
	rm -rf build out
