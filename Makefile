MAKE?=make
PYTHON?=/usr/bin/env python3
BLACK_OPTIONS=-l 120 --exclude 'action2var_variables.py|action3_callbacks.py|generated'

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
	$(PYTHON) -m black --check $(BLACK_OPTIONS) nml
	$(PYTHON) -m flake8 nml

black:
	$(PYTHON) -m black $(BLACK_OPTIONS) nml
