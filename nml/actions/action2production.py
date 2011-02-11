from nml.actions import action2, action6, actionD
from nml.ast import switch
from nml import expression, nmlop

class Action2Production(action2.Action2):
    """
    Class corresponding to Action2Industries (=production CB)

    @ivar version: Production CB version. Version 0 uses constants, version 1 uses registers.
    @type version: C{int}

    @ivar sub_in: Amounts (v0) or registers (v1) to subtract from incoming cargos.
    @type sub_in: C{list} of C{int}

    @ivar add_out: Amounts (v0) or registers (v1) to add to the output cargos.
    @type add_out: C{list} of C{int}

    @ivar again: Number (v0) or register (v1), production CB will be run again if nonzero.
    @type again C{int}
    """
    def __init__(self, name, version, sub_in, add_out, again):
        action2.Action2.__init__(self, 0x0A, name)
        self.version = version
        assert version == 0 or version == 1
        self.sub_in = sub_in
        assert len(self.sub_in) == 3
        self.add_out = add_out
        assert len(self.add_out) == 2
        self.again = again

    def prepare_output(self):
        action2.Action2.prepare_output(self)

    def write(self, file):
        cargo_size = 2 if self.version == 0 else 1
        size = 2 + 5 * cargo_size
        action2.Action2.write_sprite_start(self, file, size)
        file.print_bytex(self.version)
        for c in self.sub_in + self.add_out:
            file.print_varx(c, cargo_size)
        file.print_bytex(self.again)
        file.newline()
        file.end_sprite()

def get_production_actions(produce):
    """
    Get the action list that implements the given produce-block in nfo.

    @param produce: Produce-block to parse.
    @type produce: L{Produce}
    """
    action_list = []
    act6 = action6.Action6()
    action6.free_parameters.save()

    #all constants / supported by actionD?
    all_params = produce.sub_in + produce.add_out + [produce.again]
    version = 0 if all(map(lambda x: x.supported_by_actionD(False), all_params)) else 1

    cargo_list = len(all_params)*[None]
    act2_expressions = len(all_params)*[None]
    for i, c in enumerate(all_params):
        if version == 0:
            if isinstance(c, expression.ConstantNumeric):
                cargo_list[i] = c.value
            else:
                if isinstance(c, expression.Parameter) and isinstance(c.num, expression.ConstantNumeric):
                    param = c.num.value
                else:
                    param, tmp_param_actions = actionD.get_tmp_parameter(c)
                    action_list.extend(tmp_param_actions)
                act6.modify_bytes(param, 2 if i < 5 else 1, 1 + 2 * i)
                cargo_list[i] = 0
        else:
            if isinstance(c, expression.Variable) and isinstance(c.num, expression.ConstantNumeric) \
                    and c.num.value == 0x7D and isinstance(c.param, expression.ConstantNumeric):
                #loading a register does not need special treatment
                cargo_list[i] = c.param.value
            else:
                act2_expressions[i] = c

    va2_expr = None
    for i, expr in enumerate(act2_expressions):
        if expr is None: continue
        #Registers 0x80-0x85 are reserved for this purpose
        expr = expression.BinOp(nmlop.STO_TMP, expr, expression.ConstantNumeric(0x80 + i))
        if va2_expr is None:
            va2_expr = expr
        else:
            va2_expr = expression.BinOp(nmlop.VAL2, va2_expr, expr)
        cargo_list[i] = i

    if va2_expr is not None:
        #make a varaction2
        name = produce.name.value + "@prod" #rename production act2
        pos = produce.pos
        va2_feature = expression.ConstantNumeric(0x0A)
        va2_range = expression.Identifier('SELF', pos)
        va2_name = expression.Identifier(produce.name.value, pos)
        va2_body = switch.SwitchBody([], action2.SpriteGroupRef(expression.Identifier(name, pos), [], pos))
        switch_block = switch.Switch(va2_feature, va2_range, va2_name, va2_expr, va2_body, pos)
    else:
        name = produce.name.value

    if len(act6.modifications) > 0: action_list.append(act6)
    action6.free_parameters.restore()
    action_list.append(Action2Production(name, version, cargo_list[0:3], cargo_list[3:5], cargo_list[5]))
    if va2_expr is not None:
        action_list.extend(switch_block.get_action_list())

    return action_list
