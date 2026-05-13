PYTHON ?= .venv/bin/python
HOST ?= pi-window

.PHONY: setup converter build rebuild reconvert deploy display-current test

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

converter: setup
	$(PYTHON) scripts/download_waveshare_converter.py

build: setup
	$(PYTHON) scripts/compile_hokusai_photopainter.py

rebuild: setup
	$(PYTHON) scripts/compile_hokusai_photopainter.py --force

reconvert: setup
	$(PYTHON) scripts/reconvert_from_manifest.py --conversion waveshare

deploy:
	scripts/deploy_to_pi.sh $(HOST)

display-current:
	scripts/display_current_on_pi.sh $(HOST)

test:
	python3 -m py_compile scripts/*.py
