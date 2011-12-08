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

from .base_expression import Expression

class SpecialParameter(Expression):
    """
    Class for handling special grf parameters.
    These can be assigned special, custom methods for reading / writing to them.

    @ivar name: Name of the parameter, for debugging purposes
    @type name: C{basestring}

    @ivar info: Information about the parameter
    @type info: C{dict}

    @ivar write_func: Function that will be called when the parameter is the target of an assignment
                        Arguments:
                            Dictionary with parameter information (self.info)
                            Target expression to assign
                            Position information
                        Return value is a 2-tuple:
                            Left side of the assignment (must be a parameter)
                            Right side of the assignment (may be any expression)
    @type write_func: C{function}

    @ivar read_func: Function that will be called to read out the parameter value
                        Arguments:
                            Dictionary with parameter information (self.info)
                            Position information
                        Return value:
                            Expression that should be evaluated to get the parameter value
    @type read_func: C{function}

    @ivar is_bool: Does read_func return a boolean value?
    @type is_bool: C{bool}
    """

    def __init__(self, name, info, write_func, read_func, is_bool, pos = None):
        Expression.__init__(self, pos)
        self.name = name
        self.info = info
        self.write_func = write_func
        self.read_func = read_func
        self.is_bool = is_bool

    def debug_print(self, indentation):
        print indentation*' ' + "Special parameter '%s'" % self.name

    def __str__(self):
        return self.name

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def is_boolean(self):
        return self.is_bool

    def can_assign(self):
        return self.write_func is not None

    def to_assignment(self, expr):
        param, expr = self.write_func(self.info, expr, self.pos)
        param = param.reduce()
        expr = expr.reduce()
        return (param, expr)

    def to_reading(self):
        param = self.read_func(self.info, self.pos)
        param = param.reduce()
        return param

    def supported_by_actionD(self, raise_error):
        return True

    def supported_by_action2(self, raise_error):
        return True
