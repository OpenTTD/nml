from nml import generic, expression, global_constants

class RandomChoice(object):
    def __init__ (self, probability, result):
        self.probability = probability.reduce_constant(global_constants.const_list)
        if self.probability.value <= 0:
            raise generic.ScriptError("Value for probability should be higher than 0, encountered %d" % self.probability.value, self.probability.pos)
        if result is None:
            raise generic.ScriptError("Returning the computed value is not possible in a random-block, as there is no computed value.", self.probability.pos)
        self.result = result.reduce(global_constants.const_list, False)

    def debug_print(self, indentation):
        print indentation*' ' + 'Probability:'
        self.probability.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.result.debug_print(indentation + 4);
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.probability)
        if isinstance(self.result, expression.Identifier):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret
