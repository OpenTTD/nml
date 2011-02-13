from nml import expression, generic, global_constants
from nml.actions import action2, action2production

produce_base_class = action2.make_sprite_group_class(action2.SpriteGroupRefType.SPRITEGROUP, action2.SpriteGroupRefType.NONE, action2.SpriteGroupRefType.SPRITEGROUP, True)

class Produce(produce_base_class):
    """
    AST node for a 'produce'-block, which is basically equivalent to the production callback.
    Syntax: produce(name, sub1, sub2, sub3, add1, add2[, again])

    @ivar param_list: List of parameters supplied to the produce-block.
                      After pre-processing, their order is:
                       - 0..2: Amounts of cargo to subtract from input
                       - 3..4: Amounts of cargo to add to output
                       - 5:    Run the production CB again if nonzero
    @type param_list: C{list} of L{Expression}

    @ivar pos: Position of produce-block.
    @type pos: L{Position}
    """
    def __init__(self, param_list, pos):
        self.param_list = param_list
        self.pos = pos

    def pre_process(self):
        if not (6 <= len(self.param_list) <= 7):
            raise generic.ScriptError("produce-block requires 6 or 7 parameters, encountered " + str(len(self.param_list)), self.pos)

        name = self.param_list[0]
        if not isinstance(name, expression.Identifier):
            raise generic.ScriptError("produce parameter 1 'name' should be an identifier.", name.pos)

        self.param_list = self.param_list[1:]
        for i, param in enumerate(self.param_list):
            self.param_list[i] = param.reduce(global_constants.const_list)

        if len(self.param_list) < 6:
            self.param_list.append(expression.ConstantNumeric(0))

        # initialize base class and pre_process it as well (in that order)
        self.initialize(name, expression.ConstantNumeric(0x0A))
        produce_base_class.pre_process(self)

    def collect_references(self):
        return []

    def debug_print(self, indentation):
        print indentation*' ' + 'Produce, name =', str(self.name)
        print (indentation+2)*' ' + 'Subtract from input:'
        for expr in self.param_list[0:3]:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Add to output:'
        for expr in self.param_list[3:5]:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Again:'
        self.param_list[5].debug_print(indentation + 4)

    def get_action_list(self):
        if self.prepare_output():
            return action2production.get_production_actions(self)
        return []
