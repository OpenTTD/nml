.PHONY: clean all
.DEFAULT:

_V ?= @
_E ?= @echo
_SE ?= echo

TEST_FILES = $(basename $(shell ls *.nml))
NMLC ?= ../nmlc

all: clean
	$(_V) mkdir output
	$(_V) for i in $(TEST_FILES); do $(NMLC) --nfo output/$$i.nfo --grf output/$$i.grf $$i.nml || echo "in $$i"; done
	$(_V) diff -u output expected

clean:
	$(_V) rm -rf output
