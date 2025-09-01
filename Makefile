MAKE?=make
PYTHON?=/usr/bin/env python3

.PHONY: regression test install extensions clean flake black

regression: extensions
	$(MAKE) -C regression

test: regression flake

install:
	$(PYTHON) setup.py install

extensions:
	$(PYTHON) setup.py build_ext --inplace

clean:
	$(MAKE) -C regression clean
	# Clean extension put into root dir by --inplace
	rm -f *.so

flake:
	$(PYTHON) -m black --check nml
	$(PYTHON) -m flake8 nml

black:
	$(PYTHON) -m black nml
