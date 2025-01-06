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


class Type:
    """
    Enum-type class of the various value types possible in NML
    """

    INTEGER = 0
    FLOAT = 1
    STRING_LITERAL = 2
    FUNCTION_PTR = 3
    SPRITEGROUP_REF = 4


class Expression:
    """
    Superclass for all expression classes.

    @ivar pos: Position of the data in the original file.
    @type pos: :L{Position}
    """

    def __init__(self, pos):
        self.pos = pos

    def debug_print(self, indentation):
        """
        Print all data with explanation of what it is to standard output.

        @param indentation: Indent all printed lines with at least
            C{indentation} spaces.
        """
        raise NotImplementedError("debug_print must be implemented in expression-subclass {!r}".format(type(self)))

    def __str__(self):
        """
        Convert this expression to a string representing this expression in valid NML-code.

        @return: A string representation of this expression.
        """
        raise NotImplementedError("__str__ must be implemented in expression-subclass {!r}".format(type(self)))

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        """
        Reduce this expression to the simplest representation possible.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.
        @param unknown_id_fatal: Is encountering an unknown identifier somewhere
            in this expression a fatal error?

        @return: A deep copy of this expression simplified as much as possible.
        """
        raise NotImplementedError("reduce must be implemented in expression-subclass {!r}".format(type(self)))

    def reduce_constant(self, id_dicts=None):
        """
        Reduce this expression and make sure the result is a constant number.

        @param id_dicts: A list with dicts that are used to map identifiers
            to another (often numeric) representation.

        @return: A constant number that is the result of this expression.
        """
        expr = self.reduce(id_dicts)
        if not isinstance(expr, ConstantNumeric):
            raise generic.ConstError(self.pos)
        return expr

    def supported_by_action2(self, raise_error):
        """
        Check if this expression can be used inside a switch-block.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by advanced varaction2.
        """
        if raise_error:
            raise generic.ScriptError("This expression is not supported in a switch-block or produce-block", self.pos)
        return False

    def supported_by_actionD(self, raise_error):
        """
        Check if this expression can be used inside a parameter-assignment.

        @param raise_error: If true raise a scripterror instead of returning false.

        @return: True if this expression can be calculated by actionD.
        """
        if raise_error:
            raise generic.ScriptError("This expression can not be assigned to a parameter", self.pos)
        return False

    def collect_references(self):
        """
        This function should collect all references to other nodes from this instance.

        @return: A collection containing all links to other nodes.
        @rtype: C{iterable} of L{SpriteGroupRef}
        """
        return []

    def is_read_only(self):
        """
        Check if this expression store values.

        @return: True if the expression doesn't store values.
        """
        return True

    def is_boolean(self):
        """
        Check if this expression is limited to 0 or 1 as value.

        @return: True if the value of this expression is either 0 or 1.
        """
        return False

    def type(self):
        """
        Determine the datatype of this expression.

        @return: A constant from the L{Type} class, representing the data type.
        """
        return Type.INTEGER


class ConstantNumeric(Expression):
    def __init__(self, value, pos=None):
        Expression.__init__(self, pos)
        self.value = generic.truncate_int32(value)
        self.uvalue = self.value
        if self.uvalue < 0:
            self.uvalue += 2**32

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Int:", self.value)

    def write(self, file, size):
        file.print_varx(self.value, size)

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        return True

    def is_boolean(self):
        return self.value == 0 or self.value == 1

    def __eq__(self, other):
        return other is not None and isinstance(other, ConstantNumeric) and other.value == self.value

    def __hash__(self):
        return self.value


class ConstantFloat(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = float(value)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Float:", self.value)

    def __str__(self):
        return str(self.value)

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def type(self):
        return Type.FLOAT
