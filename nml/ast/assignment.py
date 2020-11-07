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

from nml import generic


class Assignment:
    """
    Simple storage container for a name / value pair.
    This class does not enforce any type information.
    Create a subclass to do this, or hard-code it in the parser.

    @ivar name: Name of the parameter / property / whatever to be set.
    @type name: Anything

    @ivar value: Value to assign to <name>
    @type value: Anything

    @ivar pos: Position information of the assignment
    @type pos: L{Position}
    """

    def __init__(self, name, value, pos):
        self.name = name
        self.value = value
        self.pos = pos

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Assignment")
        generic.print_dbg(indentation + 2, "Name:")
        self.name.debug_print(indentation + 4)

        generic.print_dbg(indentation + 2, "Value:")
        self.value.debug_print(indentation + 4)

    def __str__(self):
        return "{}: {};".format(self.name, self.value)


class UnitAssignment(Assignment):
    """
    Storage container where the value can have a unit.

    @ivar unit: Unit of the value, or not C{None}
    @type unit: L{Unit}
    """

    def __init__(self, name, value, unit, pos):
        Assignment.__init__(self, name, value, pos)
        self.unit = unit

    def debug_print(self, indentation):
        Assignment.debug_print(self, indentation)
        generic.print_dbg(indentation + 2, "Unit:")
        if self.unit is None:
            generic.print_dbg(indentation + 4, "None")
        else:
            generic.print_dbg(indentation + 4, self.unit)

    def __str__(self):
        if self.unit is None:
            return Assignment.__str__(self)
        else:
            return "{}: {} {};".format(self.name, self.value, self.unit.name)


class Range:
    """
    Storage container for a range of values (inclusive). This Contains
    a minimum value and optionally also a maximum value. If the maximum
    values is omitted, the minimum is also used as maximum.

    @ivar min: The minimum value of this range.
    @type min: L{Expression}

    @ivar max: The maximum value of this range.
    @type max: L{Expression} or C{None}
    """

    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __str__(self):
        if self.max is None:
            return str(self.min)
        return "{} .. {}".format(self.min, self.max)
