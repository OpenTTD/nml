.PHONY: clean all
.DEFAULT:

_V ?= @
_E ?= @echo

TEST_FILES = $(basename $(shell ls *.nml))

all: clean
	$(_V) mkdir output
	$(_V) for i in $(TEST_FILES); do echo "testing $$i.nml"; nml2nfo --nfo output/$$i.nfo --grf output/$$i.grf $$i.nml 2>/dev/null; done
	$(_E) "Differences found: "
	$(_V) diff -u output expected && echo "Everything ok."

clean:
	$(_V) rm -rf output
