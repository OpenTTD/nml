.PHONY: clean all
.DEFAULT:

_V ?= @
_E ?= @echo
_SE ?= echo

TEST_FILES = $(basename $(shell ls *.nml))
NMLC ?= ../nmlc
# Note: Manually overriding NML_FLAGS may break the regression test
NML_FLAGS ?= -s -c

.PHONY: $(TEST_FILES) clean

all: $(TEST_FILES)

$(TEST_FILES):
	$(_V) echo "Running test $@"
	$(_V) mkdir -p output nml_output output2
	$(_V) $(NMLC) $(NML_FLAGS) --nfo output/$@.nfo --grf output/$@.grf $@.nml --nml nml_output/$@.nml && \
$(NMLC) $(NML_FLAGS) -n --nfo output2/$@.nfo --grf output2/$@.grf nml_output/$@.nml
	$(_V) diff -u output/$@.nfo expected/$@.nfo && diff -u output/$@.grf expected/$@.grf && \
diff -u output2/$@.nfo expected/$@.nfo && diff -u output2/$@.grf expected/$@.grf

clean:
	$(_V) rm -rf output nml_output output2 parsetab.py
