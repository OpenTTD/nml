from nml import expression, generic, global_constants, nmlop
from nml.actions import action2, action2production
from nml.ast import switch

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

    @ivar switch: Switch block that precedes this produce block to put *stuff* in registers
    @type switch: L{Switch} or C{None} if N/A

    @ivar version: Version of the production CB (0 or 1) to be used
    @type version: C{int}
    """
    def __init__(self, param_list, pos):
        self.param_list = param_list
        self.pos = pos
        self.switch = None

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

        self.version = 0 if all(map(lambda x: x.supported_by_actionD(False), self.param_list)) else 1
        if self.version == 1:
            va2_expr = None
            for i, param in enumerate(self.param_list[:]):
                if isinstance(param, expression.Variable) and isinstance(param.num, expression.ConstantNumeric) and \
                        param.num.value == 0x7D and isinstance(param.param, expression.ConstantNumeric):
                    # We can load a register directly
                    self.param_list[i] = param.param
                else:
                    expr = expression.BinOp(nmlop.STO_TMP, param, expression.ConstantNumeric(0x80 + i))
                    if va2_expr is None:
                        va2_expr = expr
                    else:
                        va2_expr = expression.BinOp(nmlop.VAL2, va2_expr, expr)
                    self.param_list[i] = expression.ConstantNumeric(0x80 + i)

            if va2_expr is not None:
                # We need a preceding switch/varaction2 to store *stuff* in registers
                va2_feature = expression.ConstantNumeric(0x0A)
                va2_range = expression.Identifier('SELF', self.pos)
                va2_name = expression.Identifier(name.value, self.pos)

                # Rename ourself
                name.value += '@prod'

                va2_body = switch.SwitchBody([], action2.SpriteGroupRef(expression.Identifier(name.value, self.pos), [], self.pos))
                self.switch = switch.Switch(va2_feature, va2_range, va2_name, va2_expr, va2_body, self.pos)

        # initialize base class and pre_process it as well (in that order), do the same for switch if applicable
        self.initialize(name, expression.ConstantNumeric(0x0A))
        produce_base_class.pre_process(self)
        if self.switch is not None: self.switch.pre_process()

    def collect_references(self):
        return []

    def __str__(self):
        return 'produce(%s);\n' % ', '.join(str(x) for x in self.param_list)

    def debug_print(self, indentation):
        print indentation*' ' + 'Produce, name =', str(self.name)
        print (indentation+2)*' ' + ('Using numeric values' if self.version == 0 else 'Using temp. registers')
        print (indentation+2)*' ' + 'Subtract from input:'
        for expr in self.param_list[0:3]:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Add to output:'
        for expr in self.param_list[3:5]:
            expr.debug_print(indentation + 4)
        print (indentation+2)*' ' + 'Again:'
        self.param_list[5].debug_print(indentation + 4)
        if self.switch is not None:
            print (indentation+2)*' ' + 'Preceding switch block:'
            self.switch.debug_print(indentation + 4)

    def get_action_list(self):
        action_list = []
        if self.prepare_output():
            action_list += action2production.get_production_actions(self)
            if self.switch is not None: action_list += self.switch.get_action_list()
        return action_list
