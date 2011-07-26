from nml import expression, global_constants, generic
from nml.actions import action2, action2var

class SwitchRange(object):
    def __init__(self, min, max, result, unit = None):
        self.min = min
        self.max = max
        self.result = result
        self.unit = unit

    def reduce_expressions(self, var_feature):
        self.min = self.min.reduce(global_constants.const_list)
        self.max = self.max.reduce(global_constants.const_list)
        if self.result is not None:
            self.result = action2var.reduce_varaction2_expr(self.result, var_feature)

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if self.result is not None:
            self.result.debug_print(indentation + 2)
        else:
            print (indentation+2)*' ' + 'Return computed value'

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if self.result is None:
            ret += ': return;'
        elif isinstance(self.result, expression.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret