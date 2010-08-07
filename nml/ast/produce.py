from nml import expression, generic, global_constants
from nml.actions import action2production

class Produce(object):
    """
    AST node for a 'produce'-block, which is basically equivalent to the production callback.
    Syntax: produce(name, sub1, sub2, sub3, add1, add2[, again])

    @ivar param_list: List of parameters supplied to the produce-block.
    @type param_list: C{list} of L{Expression}

    @ivar pos: Position of produce-block.
    @type pos: L{Position}

    @ivar name: Name that identifies this block and can be used to refer to it.
    @type name: L{Identifier}

    @ivar sub_in: Amounts of cargo to subtract from the waiting input cargos.
    @type sub_in: C{list} of L{Expression}

    @ivar add_out: Amounts of cargo to add to the produced output cargos.
    @type add_out: C{list} of L{Expression}

    @ivar again: Run the production callback again if nonzero.
    @type again: L{Expression}
    """
    def __init__(self, param_list, pos):
        self.param_list = param_list
        self.pos = pos

    def pre_process(self):
        if not (6 <= len(self.param_list) <= 7):
            raise generic.ScriptError("produce-block requires 6 or 7 parameters, encountered " + str(len(self.param_list)), self.pos)

        self.name = self.param_list[0]
        if not isinstance(self.name, expression.Identifier):
            raise generic.ScriptError("produce parameter 1 'name' should be an identifier.", self.name.pos)

        self.sub_in = []
        for i in range(1, 4):
            self.sub_in.append(self.param_list[i].reduce(global_constants.const_list))
        self.add_out = []
        for i in range(4, 6):
            self.add_out.append(self.param_list[i].reduce(global_constants.const_list))

        if len(self.param_list) >= 7:
            self.again = self.param_list[6].reduce(global_constants.const_list)
        else:
            self.again = expression.ConstantNumeric(0)

    def debug_print(self, indentation):
        print indentation*' ' + 'Produce, name =', str(self.name)
        print (indentation+2)*' ' + 'Subtract from input:'
        for expr in self.sub_in:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Add to output:'
        for expr in self.add_out:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Again:'
        self.again.debug_print(indentation + 4)

    def get_action_list(self):
        return action2production.get_production_actions(self)
