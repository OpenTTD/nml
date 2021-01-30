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

from nml import expression, generic, global_constants, nmlop
from nml.actions import action2, action2var, action6, actionD


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

    def __init__(self, name, pos, version, sub_in, add_out, again):
        action2.Action2.__init__(self, 0x0A, name, pos)
        self.version = version
        if version in (0, 1):
            self.sub_in = sub_in
            assert len(self.sub_in) == 3
            self.add_out = add_out
            assert len(self.add_out) == 2
        elif version == 2:
            self.sub_in = sub_in
            self.add_out = add_out
        else:
            raise AssertionError()
        self.again = again

    def prepare_output(self, sprite_num):
        action2.Action2.prepare_output(self, sprite_num)

    def write(self, file):
        if self.version in (0, 1):
            cargo_size = 2 if self.version == 0 else 1
            size = 2 + 5 * cargo_size
            action2.Action2.write_sprite_start(self, file, size)
            file.print_bytex(self.version)
            values = self.sub_in + self.add_out + [self.again]
            # Read register numbers if needed
            if self.version == 1:
                values = [val.parameter for val in values]

            for val in values[:-1]:
                file.print_varx(val, cargo_size)
            file.print_bytex(values[-1])
        elif self.version == 2:
            size = 4 + 2 * (len(self.sub_in) + len(self.add_out))
            action2.Action2.write_sprite_start(self, file, size)
            file.print_bytex(self.version)
            file.print_byte(len(self.sub_in))
            for cargoindex, value in self.sub_in:
                file.print_bytex(cargoindex)
                file.print_bytex(value.parameter)
            file.print_byte(len(self.add_out))
            for cargoindex, value in self.add_out:
                file.print_bytex(cargoindex)
                file.print_bytex(value.parameter)
            file.print_bytex(self.again.parameter)
        file.newline()
        file.end_sprite()


def resolve_prodcb_register(param, varact2parser):
    if (
        isinstance(param, expression.StorageOp)
        and param.name == "LOAD_TEMP"
        and isinstance(param.register, expression.ConstantNumeric)
    ):
        # We can load a register directly
        res = action2var.VarAction2Var(0x7D, 0, 0xFFFFFFFF, param.register.value)
    else:
        if len(varact2parser.var_list) != 0:
            varact2parser.var_list.append(nmlop.VAL2)
            varact2parser.var_list_size += 1
        varact2parser.parse_expr(action2var.reduce_varaction2_expr(param, 0x0A))
        store_tmp = action2var.VarAction2StoreTempVar()
        res = action2var.VarAction2LoadTempVar(store_tmp)
        varact2parser.var_list.append(nmlop.STO_TMP)
        varact2parser.var_list.append(store_tmp)
        varact2parser.var_list_size += store_tmp.get_size() + 1  # Add 1 for operator
    return res


def finish_production_actions(produce, prod_action, action_list, varact2parser):
    action_list.append(prod_action)

    if len(varact2parser.var_list) == 0:
        produce.set_action2(prod_action, 0x0A)
    else:
        # Create intermediate varaction2
        varaction2 = action2var.Action2Var(0x0A, "{}@registers".format(produce.name.value), produce.pos, 0x89)
        varaction2.var_list = varact2parser.var_list
        action_list.extend(varact2parser.extra_actions)
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
        if len(extra_act6.modifications) > 0:
            action_list.append(extra_act6)
        ref = expression.SpriteGroupRef(produce.name, [], None, prod_action)
        varaction2.ranges.append(
            action2var.VarAction2Range(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, "")
        )
        varaction2.default_result = ref
        varaction2.default_comment = ""

        # Add two references (default + range)
        action2.add_ref(ref, varaction2)
        action2.add_ref(ref, varaction2)
        produce.set_action2(varaction2, 0x0A)
        action_list.append(varaction2)

    action6.free_parameters.restore()

    return action_list


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
    varact2parser = action2var.Varaction2Parser(0x0A, 0x0A)
    if all(x.supported_by_actionD(False) for x in produce.param_list):
        version = 0
        offset = 4
        for i, param in enumerate(produce.param_list):
            result, offset = actionD.write_action_value(param, action_list, act6, offset, 2 if i < 5 else 1)
            result_list.append(result.value)
    else:
        version = 1
        for param in produce.param_list:
            result_list.append(resolve_prodcb_register(param, varact2parser))

    if len(act6.modifications) > 0:
        action_list.append(act6)
    prod_action = Action2Production(
        produce.name.value, produce.pos, version, result_list[0:3], result_list[3:5], result_list[5]
    )

    return finish_production_actions(produce, prod_action, action_list, varact2parser)


def get_production_v2_actions(produce):
    """
    Get the action list that implements the given produce-block in nfo.

    @param produce: Produce-block to parse.
    @type produce: L{Produce2}
    """
    action_list = []
    action6.free_parameters.save()

    varact2parser = action2var.Varaction2Parser(0x0A, 0x0A)

    def resolve_cargoitem(item):
        cargolabel = item.name.value
        if cargolabel not in global_constants.cargo_numbers:
            raise generic.ScriptError("Cargo label {0} not found in your cargo table".format(cargolabel), produce.pos)
        cargoindex = global_constants.cargo_numbers[cargolabel]
        valueregister = resolve_prodcb_register(item.value, varact2parser)
        return (cargoindex, valueregister)

    sub_in = [resolve_cargoitem(item) for item in produce.subtract_in]
    add_out = [resolve_cargoitem(item) for item in produce.add_out]
    again = resolve_prodcb_register(produce.again, varact2parser)

    prod_action = Action2Production(produce.name.value, produce.pos, 2, sub_in, add_out, again)

    return finish_production_actions(produce, prod_action, action_list, varact2parser)


def make_empty_production_action2(pos):
    """
    Make an empty production action2
    For use with failed callbacks

    @param pos: Positional context.
    @type  pos: L{Position}

    @return: The created production action2
    @rtype: L{Action2Production}
    """
    return Action2Production("@CB_FAILED_PROD", pos, 0, [0, 0, 0], [0, 0], 0)
