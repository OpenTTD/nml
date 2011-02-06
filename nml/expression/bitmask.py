from nml import generic, nmlop
from base_expression import Type, Expression, ConstantNumeric
from binop import BinOp

class BitMask(Expression):
    def __init__(self, values, pos):
        Expression.__init__(self, pos)
        self.values = values

    def debug_print(self, indentation):
        print indentation*' ' + 'Get bitmask:'
        for value in self.values:
            value.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        ret = ConstantNumeric(0, self.pos)
        for orig_expr in self.values:
            val = orig_expr.reduce(id_dicts)
            if val.type() != Type.INTEGER:
                raise generic.ScriptError("Parameters of 'bitmask' must be integers.", orig_expr.pos)
            if isinstance(val, ConstantNumeric) and val.value >= 32:
                raise generic.ScriptError("Parameters of 'bitmask' cannot be greater then 31", orig_expr.pos)
            val = BinOp(nmlop.SHIFT_LEFT, ConstantNumeric(1), val, val.pos)
            ret = BinOp(nmlop.OR, ret, val, self.pos)
        return ret.reduce()

    def __str__(self):
        return "bitmask(" + ", ".join(str(e) for e in self.values) + ")"
