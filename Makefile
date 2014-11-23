MAKE?=make
PYTHON?=/usr/bin/env python3

.PHONY: regression install bundle extensions clean

regression: extensions
	$(MAKE) -C regression
test: regression

install:
	$(PYTHON) setup.py install

bundle:
	$(PYTHON) bootstrap.py

extensions:
	$(PYTHON) setup.py build_ext --inplace

clean:
	$(MAKE) -C regression clean
