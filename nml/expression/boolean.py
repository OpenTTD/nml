from nml import generic
from base_expression import Type, Expression

class Boolean(Expression):
    def __init__(self, expr, pos = None):
        Expression.__init__(self, pos)
        self.expr = expr

    def debug_print(self, indentation):
        print indentation*' ' + 'Force expression to boolean:'
        self.expr.debug_print(indentation + 2)

    def reduce(self, id_dicts = [], unknown_id_fatal = True):
        expr = self.expr.reduce(id_dicts)
        if expr.type() != Type.INTEGER:
            raise generic.ScriptError("Only integers can be converted to a boolean value.", self.pos)
        if expr.is_boolean(): return expr
        return Boolean(expr)

    def supported_by_action2(self, raise_error):
        return self.expr.supported_by_action2(raise_error)

    def supported_by_actionD(self, raise_error):
        return self.expr.supported_by_actionD(raise_error)

    def is_boolean(self):
        return True

    def __str__(self):
        return "!!(%s)" % str(self.expr)
