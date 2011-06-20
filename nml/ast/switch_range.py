from nml import expression, global_constants, generic
from nml.actions import action2

class SwitchRange(object):
    def __init__(self, min, max, result, unit = None, comment = None):
        self.min = min
        self.max = max
        self.result = result
        self.unit = unit
        self.comment = comment

    def pre_process(self):
        self.min = self.min.reduce(global_constants.const_list)
        self.max = self.max.reduce(global_constants.const_list)
        # Result may be None here, not pre-processed yet
        if isinstance(self.result, expression.Expression):
            try:
                self.result = self.result.reduce(global_constants.const_list)
            except generic.ScriptError:
                # We want to reduce the result here as much as possible however there
                # are valid expressions that will still fail here. Ignore the error for
                # now, if it was a real error it'll be raised again later.
                pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Min:'
        self.min.debug_print(indentation + 2)
        print indentation*' ' + 'Max:'
        self.max.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.min)
        if not isinstance(self.min, expression.ConstantNumeric) or not isinstance(self.max, expression.ConstantNumeric) or self.max.value != self.min.value:
            ret += '..' + str(self.max)
        if self.result is None:
            ret += ': return;'
        elif isinstance(self.result, action2.SpriteGroupRef):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret