from nml.actions import action2, action6, actionD
from nml import expression

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

    result_list = []
    for i, param in enumerate(produce.param_list):
        if isinstance(param, expression.ConstantNumeric):
            result_list.append(param.value)
        else:
            if isinstance(param, expression.Parameter) and isinstance(param.num, expression.ConstantNumeric):
                param_num = param.num.value
            else:
                param_num, tmp_param_actions = actionD.get_tmp_parameter(param)
                action_list.extend(tmp_param_actions)
            act6.modify_bytes(param_num, 2 if i < 5 else 1, 1 + 2 * i)
            result_list.append(0)

    if len(act6.modifications) > 0: action_list.append(act6)
    action6.free_parameters.restore()
    prod_action = Action2Production(produce.name.value, produce.version, result_list[0:3], result_list[3:5], result_list[5])
    action_list.append(prod_action)
    produce.set_action2(prod_action)

    return action_list
