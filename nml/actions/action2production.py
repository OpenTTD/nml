__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

from nml.actions import action2, action2var, action6, actionD
from nml import expression, nmlop

class Action2Production(action2.Action2):
    """
    Class corresponding to Action2Industries (=production CB)

    @ivar version: Production CB version. Version 0 uses constants, version 1 uses registers.
    @type version: C{int}

    @ivar sub_in: Amounts (v0) or registers (v1) to subtract from incoming cargos.
    @type sub_in: C{list} of (C{int} or L{VarAction2Var})

    @ivar add_out: Amounts (v0) or registers (v1) to add to the output cargos.
    @type add_out: C{list} of (C{int} or L{VarAction2Var})

    @ivar again: Number (v0) or register (v1), production CB will be run again if nonzero.
    @type again C{int} or L{VarAction2Var}
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
        values = self.sub_in + self.add_out + [self.again]
        # Read register numbers if needed
        if self.version == 1: values = [val.parameter for val in values]

        for val in values[:-1]:
            file.print_varx(val, cargo_size)
        file.print_bytex(values[-1])
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
    varact2parser = action2var.Varaction2Parser(0x0A)
    if all(map(lambda x: x.supported_by_actionD(False), produce.param_list)):
        version = 0
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
    else:
        version = 1
        for i, param in enumerate(produce.param_list):
            if isinstance(param, expression.StorageOp) and param.name == 'LOAD_TEMP' and \
                    isinstance(param.register, expression.ConstantNumeric):
                # We can load a register directly
                result_list.append(action2var.VarAction2Var(0x7D, 0, 0xFFFFFFFF, param.register.value))
            else:
                if len(varact2parser.var_list) != 0:
                    varact2parser.var_list.append(nmlop.VAL2)
                    varact2parser.var_list_size += 1
                varact2parser.parse_expr(action2var.reduce_varaction2_expr(param, 0x0A))
                store_tmp = action2var.VarAction2StoreTempVar()
                result_list.append(action2var.VarAction2LoadTempVar(store_tmp))
                varact2parser.var_list.append(nmlop.STO_TMP)
                varact2parser.var_list.append(store_tmp)
                varact2parser.var_list_size += store_tmp.get_size() + 1 # Add 1 for operator

    if len(act6.modifications) > 0: action_list.append(act6)
    prod_action = Action2Production(produce.name.value, version, result_list[0:3], result_list[3:5], result_list[5])
    action_list.append(prod_action)

    if len(varact2parser.var_list) == 0:
        produce.set_action2(prod_action, 0x0A)
    else:
        # Create intermediate varaction2
        varaction2 = action2var.Action2Var(0x0A, '%s@registers' % produce.name.value, 0x89)
        varaction2.var_list = varact2parser.var_list
        action_list.extend(varact2parser.extra_actions)
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
        if len(extra_act6.modifications) > 0: action_list.append(extra_act6)
        ref = expression.SpriteGroupRef(produce.name, [], None, prod_action)
        varaction2.ranges.append(action2var.VarAction2Range(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, ''))
        varaction2.default_result = ref
        varaction2.default_comment = ''

        # Add two references (default + range)
        action2.add_ref(ref, varaction2)
        action2.add_ref(ref, varaction2)
        produce.set_action2(varaction2, 0x0A)
        action_list.append(varaction2)

    action6.free_parameters.restore()

    return action_list
