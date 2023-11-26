.PHONY: clean all
.DEFAULT:

_V ?= @
_E ?= @echo
_SE ?= echo

TEST_FILES = $(basename $(shell ls *.nml))
EXAMPLES = $(shell ls ../examples)
NMLC ?= $(abspath ../nmlc)
# Note: Manually overriding NML_FLAGS may break the regression test
NML_FLAGS ?= -s -c --verbosity=1

.PHONY: $(TEST_FILES) $(EXAMPLES) clean

all: $(TEST_FILES) $(EXAMPLES)

$(TEST_FILES):
	$(_V) echo "Running test $@"
	$(_V) mkdir -p output nml_output output2
# First pass : check compilation of source nml and generation of optimised nml
	$(_V) $(NMLC) $(NML_FLAGS) --nfo output/$@.nfo --grf output/$@.grf $@.nml --nml nml_output/$@.nml
	$(_V) diff -u --strip-trailing-cr expected/$@.nfo output/$@.nfo
	$(_V) diff expected/$@.grf output/$@.grf
# Second pass : check compilation of optimised nml
	$(_V) $(NMLC) $(NML_FLAGS) -n --nfo output2/$@.nfo --grf output2/$@.grf nml_output/$@.nml
	$(_V) diff -u --strip-trailing-cr expected/$@.nfo output2/$@.nfo
	$(_V) diff expected/$@.grf output2/$@.grf

$(EXAMPLES):
	$(_V) echo "Testing example $@"
	$(_V) mkdir -p output nml_output output2
# First pass as above
# We must change directory, because nmlc provides no way to set a base directory for realsprite files.
	$(_V) cd ../examples/$@/ && \
		$(NMLC) $(NML_FLAGS) -n \
		--nfo ../../regression/output/example_$@.nfo \
		--nml ../../regression/nml_output/example_$@.nml \
		--grf ../../regression/output/example_$@.grf \
		example_$@.nml && cd ../../regression
	$(_V) diff -u --strip-trailing-cr expected/example_$@.nfo output/example_$@.nfo
	$(_V) diff expected/example_$@.grf output/example_$@.grf
# Second pass
	$(_V) cd ../examples/$@/ && \
		$(NMLC) $(NML_FLAGS) -n \
		--nfo ../../regression/output2/example_$@.nfo \
		--grf ../../regression/output2/example_$@.grf \
		../../regression/nml_output/example_$@.nml && cd ../../regression
	$(_V) diff -u --strip-trailing-cr expected/example_$@.nfo output2/example_$@.nfo
	$(_V) diff expected/example_$@.grf output2/example_$@.grf

clean:
	$(_V) rm -rf output nml_output output2 .nmlcache
