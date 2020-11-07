__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

# Available units, mapping of unit name to L{Unit} objects.
units = {}


def get_unit(name):
    """
    Get a unit by name.

    @param name: Name of the unit.
    @type  name: C{str}

    @return: The requested unit.
    @rtype:  L{Unit}
    """
    return units[name]


class Unit:
    def __init__(self, name, type, convert, ottd_mul, ottd_shift):
        """
        Unit definition.

        Conversion factor works like this:
        1 reference_unit = convert other_unit
        So nfo_value = property_value / convert * property_specific_conversion_factor
        To avoid using fractions, rational numbers (as 2-tuples) are used instead.

        ottd_mul and ottd_shift are the values taken from OpenTTD's src/strings.cpp and
        are used to calculate the displayed value by OpenTTD. If possible, adjust_values
        increases or decreases the NFO value so that the desired display value is actually
        achieved.

        @ivar name: Name of the unit.
        @type name: C{str}

        @ivar type: Kind of unit.
        @type type: C{str}

        @ivar convert: Conversion factor of the unit.
        @type convert: Either C{int} or a rational tuple (C{int}, C{int})

        @ivar ottd_mul: OpenTTD multiplication factor for displaying a value of this unit.
        @type ottd_mul: C{int}

        @ivar ottd_shift: OpenTTD shift factor for displaying a value of this unit.
        @type ottd_shift: C{int}
        """
        self.name = name
        self.type = type
        self.convert = convert
        self.ottd_mul = ottd_mul
        self.ottd_shift = ottd_shift

    def __str__(self):
        return self.name


def add_unit(name, type, convert, ottd_mul, ottd_shift):
    """
    Construct new unit, and add it to L{units}.

    @param name: Name of the unit.
    @type  name: C{str}

    @param type: Kind of unit.
    @type  type: C{str}

    @param convert: Conversion factor of the unit.
    @type  convert: Either C{int} or a rational tuple (C{int}, C{int})

    @param ottd_mul: OpenTTD multiplication factor for displaying a value of this unit.
    @type  ottd_mul: C{int}

    @param ottd_shift: OpenTTD shift factor for displaying a value of this unit.
    @type  ottd_shift: C{int}
    """
    unit = Unit(name, type, convert, ottd_mul, ottd_shift)
    units[name] = unit


#          name       type     convert      mul  shift
add_unit("nfo", "nfo", 1, 1, 0)  # don't convert, take value literal

# Speed (reference: m/s)
#          name       type     convert      mul  shift
add_unit("mph", "speed", (3125, 1397), 1, 0)
add_unit("km/h", "speed", (18, 5), 103, 6)
add_unit("m/s", "speed", 1, 1831, 12)

# Power (reference: hpI (imperial hp))

#          name       type     convert      mul  shift
add_unit("hp", "power", 1, 1, 0)  # Default to imperial hp
add_unit("kW", "power", (2211, 2965), 6109, 13)
add_unit("hpM", "power", (731, 721), 4153, 12)
add_unit("hpI", "power", 1, 1, 0)

# Weight (reference: ton)

#          name       type     convert      mul  shift
add_unit("ton", "weight", 1, 1, 0)
add_unit("tons", "weight", 1, 1, 0)
add_unit("kg", "weight", 1000, 1000, 0)

# Snowline height

#          name       type     convert      mul  shift
add_unit("snow%", "snowline", (255, 100), 1, 0)
