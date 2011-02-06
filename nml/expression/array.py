from base_expression import Expression, ConstantNumeric

class Array(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Array of values:'
        for v in self.values:
            v.debug_print(indentation + 2)

    def __str__(self):
        return '[' + ', '.join([str(expr) for expr in self.values]) + ']'

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        return Array([val.reduce(id_dicts, unknown_id_fatal) for val in self.values], self.pos)
