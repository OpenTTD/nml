#!/usr/bin/env python3

import re, sys

from itertools import tee, zip_longest

def pairwise(iterable):
    # Get the current and next entries of an iterable, ending with (last, None).
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b)

text = open("docs/changelog.txt")

out = sys.stdout

# Whether to convert the whole changelog, or just the most recent version
print_all = (len(sys.argv) > 1 and sys.argv[1] == "all")
versions_printed = 0

list_depth = 0
biggening = underlining = False

for line, next_line in pairwise(text):
    line = line[:-1] # No newline

    if re.match("^-+$", line):
        # Remove ----------- lines
        continue

    if next_line and re.match("^-+$", next_line):
        if re.match("^[0-9]+\.[0-9]+", line):
            # Matches only version headings, not other subheadings
            if versions_printed > 0 and not print_all:
                sys.exit(0)
            versions_printed += 1
            # Make these ones bigger
            biggening = True
            out.write("[size=150]")
        underlining = True
        out.write("[u]")

    li_prefix = re.match("^( *)-", line)

    # Two spaces per level of list nesting, with no spaces at first level.
    new_list_depth = (len(li_prefix.group(1)) // 2 + 1) if li_prefix else 0

    if new_list_depth > list_depth:
        out.write("[list]" * (new_list_depth - list_depth) + "\n")
    elif new_list_depth < list_depth:
        out.write("[/list]" * (list_depth - new_list_depth) + "\n")
    list_depth = new_list_depth

    if list_depth:
        line = line.lstrip(" -")
        out.write("[*]")

    # TT-Forums (at least) automagically converts "https://..." to URLs, so don't bother.
    ...

    # Italics
    # Can't use \b because * isn't a word character
    line = re.sub(r"(\A|\W)\*(\w+)\*(\W|\Z)", r"\1[i]\2[/i]\3", line)

    # Issue/PR numbers

    # The format "#1234" is ambiguous with Github. Assume 4-digit numbers are Devzone...
    line = re.sub(r"(?<!OpenTTD)(\A|\W)#([0-9]{4})\b", r"\1[url=https://dev.openttdcoop.org/issues/\2]#\2[/url]", line)

    # ...and 1-3 digits are Github. This URL works for issues too.
    line = re.sub(r"(?<!OpenTTD)(\A|\W)#([0-9]{1,3})\b", r"\1[url=https://github.com/OpenTTD/nml/pull/\2]#\2[/url]", line)

    # Special-case for "fix OpenTTD #1234"
    line = re.sub(r"OpenTTD #([0-9]+)\b", r"[url=https://github.com/OpenTTD/OpenTTD/pull/\1]OpenTTD #\1[/url]", line)

    out.write(line)

    if biggening:
        biggening = False
        out.write("[/size]")
    if underlining:
        underlining = False
        out.write("[/u]")

    out.write("\n")
