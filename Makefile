MAKE?=make
PYTHON?=python

.PHONY: regression install bundle

regression:
	$(MAKE) -C regression
test: regression

install:
	$(PYTHON) setup.py

bundle:
	$(PYTHON) bootstrap.py
