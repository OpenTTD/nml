# SPDX-License-Identifier: GPL-2.0-or-later

from nml import generic

from .base_expression import Expression, Type


class FunctionPtr(Expression):
    """
    Pointer to a function.
    If this appears inside an expression, the user has made an error.

    @ivar name: Identifier that has been resolved to this function pointer.
    @type name: L{Identifier}

    @ivar func: Function that will be called to resolve this function call. Arguments:
                    Name of the function (C{str})
                    List of passed arguments (C{list} of L{Expression})
                    Position information (L{Position})
                    Any extra arguments passed to the constructor of this class
    @type func: C{function}

    @ivar extra_args List of arguments that should be passed to the function that is to be called.
    @type extra_args C{list}
    """

    def __init__(self, name, func, *extra_args):
        super().__init__(pos=None)
        self.name = name
        self.func = func
        self.extra_args = extra_args

    def debug_print(self, indentation):
        raise AssertionError("Function pointers should not appear inside expressions.")

    def __str__(self):
        raise AssertionError("Function pointers should not appear inside expressions.")

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        raise generic.ScriptError(
            "'{}' is a function and should be called using the function call syntax.".format(str(self.name)),
            self.name.pos,
        )

    def type(self):
        return Type.FUNCTION_PTR

    def call(self, args):
        return self.func(self.name.value, args, self.name.pos, *self.extra_args)
