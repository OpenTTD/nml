from nml import generic
from base_expression import Expression, ConstantNumeric

class Identifier(Expression):
    def __init__(self, value, pos = None):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'ID: ' + self.value

    def __str__(self):
        return self.value

    def reduce(self, id_dicts = [], unknown_id_fatal = True, search_func_ptr = False):
        for id_dict in id_dicts:
            id_d, func = (id_dict, lambda x, pos: StringLiteral(x, pos) if isinstance(x, basestring) else ConstantNumeric(x, pos)) if not isinstance(id_dict, tuple) else id_dict
            if self.value in id_d:
                if search_func_ptr:
                    # Do not reduce function pointers, since they have no (numerical) value
                    return func(id_d[self.value], self.pos)
                else:
                    return func(id_d[self.value], self.pos).reduce(id_dicts)
        if unknown_id_fatal: raise generic.ScriptError("Unrecognized identifier '" + self.value + "' encountered", self.pos)
        return self

    def supported_by_actionD(self, raise_error):
        if raise_error: raise generic.ScriptError("Unknown identifier '%s'" % self.value, self.pos)
        return False

    def __eq__(self, other):
        return other is not None and isinstance(other, Identifier) and self.value == other.value

    def __hash__(self):
        return hash(self.value)
