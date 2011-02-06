from nml import generic
from base_expression import Type, Expression

class StringLiteral(Expression):
    def __init__(self, value, pos):
        Expression.__init__(self, pos)
        self.value = value

    def debug_print(self, indentation):
        print indentation*' ' + 'String literal: "%s"' % self.value

    def __str__(self):
        return '"%s"' % self.value

    def write(self, file, size):
        assert(len(self.value) == size)
        file.print_string(self.value, final_zero = False, force_ascii = True)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return self

    def type(self):
        return Type.STRING_LITERAL
