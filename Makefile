MAKE?=make
PYTHON?=/usr/bin/env python3

.PHONY: regression install bundle extensions clean

regression: extensions
	$(MAKE) -C regression
test: regression

install:
	$(PYTHON) setup.py install

extensions:
	$(PYTHON) setup.py build_ext --inplace

clean:
	$(MAKE) -C regression clean
