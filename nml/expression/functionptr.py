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
from .base_expression import Type, Expression

class FunctionPtr(Expression):
    """
    Pointer to a function.
    If this appears inside an expression, the user has made an error.

    @ivar name Identifier that has been resolved to this function pointer.
    @type name L{Identifier}

    @ivar func Function that will be called to resolve this function call. Arguments:
                    Name of the function (C{basestring})
                    List of passed arguments (C{list} of L{Expression})
                    Position information (L{Position})
                    Any extra arguments passed to the constructor of this class
    @type func C{function}

    @ivar extra_args List of arguments that should be passed to the function that is to be called.
    @type extra_args C{list}
    """
    def __init__(self, name, func, *extra_args):
        self.name = name
        self.func = func
        self.extra_args = extra_args

    def debug_print(self, indentation):
        assert False, "Function pointers should not appear inside expressions."

    def __str__(self):
        assert False, "Function pointers should not appear inside expressions."

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        raise generic.ScriptError("'%s' is a function and should be called using the function call syntax." % str(self.name), self.name.pos)

    def type(self):
        return Type.FUNCTION_PTR

    def call(self, args):
        return self.func(self.name.value, args, self.name.pos, *self.extra_args)
