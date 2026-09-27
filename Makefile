.PHONY: install data build results figures all test clean

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e .

data:
	$(PYTHON) scripts/00_download_data.py

build:
	$(PYTHON) run_all.py --from 1 --to 2

results:
	$(PYTHON) run_all.py --from 3 --to 4

figures:
	$(PYTHON) run_all.py --from 5 --to 5

all:
	$(PYTHON) run_all.py

test:
	$(PYTHON) -m pytest

clean:
	rm -rf data/processed/*.parquet
