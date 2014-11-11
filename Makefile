MAKE?=make
PYTHON?=/usr/bin/env python3

.PHONY: regression install bundle clean

regression:
	$(MAKE) -C regression
test: regression

install:
	$(PYTHON) setup.py install

bundle:
	$(PYTHON) bootstrap.py

clean:
	$(MAKE) -C regression clean
