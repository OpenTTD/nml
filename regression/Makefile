.PHONY: clean all
.DEFAULT:

_V ?= @
_E ?= @echo
_SE ?= echo

TEST_FILES = $(basename $(shell ls *.nml))
NMLC ?= ../nmlc -s

all: clean
	$(_V) mkdir output nml_output output2
	$(_V) for i in $(TEST_FILES); do $(NMLC) --nfo output/$$i.nfo --grf output/$$i.grf $$i.nml --nml nml_output/$$i.nml && \
$(NMLC) --nfo output2/$$i.nfo --grf output2/$$i.grf nml_output/$$i.nml || echo "in $$i"; done
	$(_V) diff -u output expected && diff -u output2 expected

clean:
	$(_V) rm -rf output nml_output output2
