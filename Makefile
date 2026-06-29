.PHONY: install install-dev build pdf all test serve clean

VENV ?= .venv
PY := $(VENV)/bin/python
DATA ?= data/shikoku.yaml

install:            ## HTML 生成に必要な依存のみ
	python3 -m venv $(VENV)
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements.txt

install-dev: install  ## PDF・テスト含む依存
	$(PY) -m pip install -r requirements-dev.txt
	$(PY) -m playwright install chromium

build:              ## データ -> dist/index.html（＋公開用 index.html）
	$(PY) scripts/build.py $(DATA) dist/index.html --root

pdf: build          ## dist/index.html -> dist/itinerary.pdf
	$(PY) scripts/to_pdf.py dist/index.html dist/itinerary.pdf

all: pdf            ## HTML + PDF を一気通貫で生成

test:               ## ユニット/スナップショット/PDF テスト
	$(PY) -m pytest

serve: build        ## ローカル確認用サーバ（http://localhost:8000/dist/）
	$(PY) -m http.server 8000

clean:
	rm -f dist/*.html dist/*.pdf index.html
