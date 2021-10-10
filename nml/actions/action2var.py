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
from nml.actions import action2, action2real, action2var_variables, action4, action6, actionD
from nml.ast import switch


class Action2Var(action2.Action2):
    """
    Variational Action2. This is the NFO equivalent of a switch-block in NML.
    It computes a single integer from one or more variables and picks it's
    return value based on the result of the computation. The return value can
    be either a 15bit integer or a reference to another action2.

    @ivar type_byte: The size (byte, word, double word) and access type (own
                     object or related object). 0x89 (own object, double word)
                     and 0x8A (related object, double word) and the only
                     supported values.
    @type type_byte: C{int}

    @ivar ranges: List of return value ranges. Each range contains a minimum and
                  a maximum value and a return value. The list is checked in order,
                  if the result of the computation is between the minimum and
                  maximum (inclusive) of one range the result of that range is
                  returned. The result can be either an integer of another
                  action2.
    @ivar ranges: C{list} of L{VarAction2Range}
    """

    def __init__(self, feature, name, pos, type_byte, param_registers=None):
        action2.Action2.__init__(self, feature, name, pos)
        self.type_byte = type_byte
        self.ranges = []
        self.param_registers = param_registers or []

    def resolve_tmp_storage(self):
        # A return action may use the parameters of its parent
        # Make sure param registers are not reused
        for var in self.var_list:
            if isinstance(var, VarAction2LoadCallParam):
                self.remove_tmp_location(var.parameter, False)

        for var in self.param_registers + self.var_list:  # Allocate param registers first
            if isinstance(var, (VarAction2StoreTempVar, VarAction2CallParam)):
                if not self.tmp_locations:
                    raise generic.ScriptError(
                        "There are not enough registers available "
                        + "to perform all required computations in switch blocks. "
                        + "Please reduce the complexity of your code.",
                        self.pos,
                    )
                location = self.tmp_locations[0]
                self.remove_tmp_location(location, False)
                var.set_register(location)

    def prepare_output(self, sprite_num):
        action2.Action2.prepare_output(self, sprite_num)
        for i in range(0, len(self.var_list) - 1, 2):
            self.var_list[i].shift |= 0x20

        for i in range(0, len(self.var_list), 2):
            if isinstance(self.var_list[i], VarAction2ProcCallVar):
                self.var_list[i].resolve_parameter(self.feature)

        for r in self.ranges:
            if isinstance(r.result, expression.SpriteGroupRef):
                r.result = r.result.get_action2_id(self.feature)
            else:
                r.result = r.result.value | 0x8000
        if isinstance(self.default_result, expression.SpriteGroupRef):
            self.default_result = self.default_result.get_action2_id(self.feature)
        else:
            self.default_result = self.default_result.value | 0x8000

    def write(self, file):
        # type_byte, num_ranges, default_result = 4
        # 2 bytes for the result, 8 bytes for the min/max range.
        size = 4 + (2 + 8) * len(self.ranges)
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                size += 1
            else:
                size += var.get_size()

        regs = ["{} : register {:X}".format(reg.name, reg.register) for reg in self.param_registers]
        self.write_sprite_start(file, size, regs)
        file.print_bytex(self.type_byte)
        file.newline()
        for var in self.var_list:
            if isinstance(var, nmlop.Operator):
                file.print_bytex(var.act2_num, var.act2_str)
            else:
                var.write(file, 4)
                file.newline(var.comment)
        file.print_byte(len(self.ranges))
        file.newline()
        for r in self.ranges:
            file.print_wordx(r.result)
            file.print_varx(r.min.value, 4)
            file.print_varx(r.max.value, 4)
            file.newline(r.comment)
        file.print_wordx(self.default_result)
        file.comment(self.default_comment)
        file.end_sprite()


class VarAction2Var:
    """
    Represents a variable for use in a (advanced) variational action2.

    @ivar var_num: Number of the variable to use.
    @type var_num: C{int}

    @ivar shift: The number of bits to shift the value of the given variable to the right.
    @type shift: C{int}

    @ivar mask: Bitmask to use on the value after shifting it.
    @type mask: C{int}

    @ivar parameter: Parameter to be used as argument for the variable.
    @type parameter: C{int} or C{None}
    @precondition: (0x60 <= var_num <= 0x7F) == (parameter is not None)

    @ivar add: If not C{None}, add this value to the result.
    @type add: C{int} or C{None}

    @ivar div: If not C{None}, divide the result by this.
    @type add: C{int} or C{None}

    @ivar mod: If not C{None}, compute (result module mod).
    @type add: C{int} or C{None}

    @ivar comment: Textual description of this variable.
    @type comment: C{basestr}
    """

    def __init__(self, var_num, shift, mask, parameter=None, comment=""):
        self.var_num = var_num
        self.shift = shift
        self.mask = mask
        self.parameter = parameter
        self.add = None
        self.div = None
        self.mod = None
        self.comment = comment

    def write(self, file, size):
        file.print_bytex(self.var_num)
        if self.parameter is not None:
            file.print_bytex(self.parameter)
        if self.mod is not None:
            self.shift |= 0x80
        elif self.add is not None or self.div is not None:
            self.shift |= 0x40
        file.print_bytex(self.shift)
        file.print_varx(self.mask, size)
        if self.add is not None:
            file.print_varx(self.add, size)
            if self.div is not None:
                file.print_varx(self.div, size)
            elif self.mod is not None:
                file.print_varx(self.mod, size)
            else:
                # no div or add, just divide by 1
                file.print_varx(1, size)

    def get_size(self):
        # var number (1) [+ parameter (1)] + shift num (1) + and mask (4) [+ add (4) + div/mod (4)]
        size = 6
        if self.parameter is not None:
            size += 1
        if self.add is not None or self.div is not None or self.mod is not None:
            size += 8
        return size

    def supported_by_actionD(self, raise_error):
        assert not raise_error
        return False


# Class for var 7E procedure calls
class VarAction2ProcCallVar(VarAction2Var):
    def __init__(self, sg_ref):
        if not isinstance(action2.resolve_spritegroup(sg_ref.name), (switch.Switch, switch.RandomSwitch)):
            raise generic.ScriptError("Block with name '{}' is not a valid procedure".format(sg_ref.name), sg_ref.pos)
        if not sg_ref.is_procedure:
            raise generic.ScriptError("Unexpected identifier encountered: '{}'".format(sg_ref.name), sg_ref.pos)
        VarAction2Var.__init__(self, 0x7E, 0, 0, comment=str(sg_ref))
        # Reference to the called action2
        self.sg_ref = sg_ref

    def resolve_parameter(self, feature):
        self.parameter = self.sg_ref.get_action2_id(feature)

    def get_size(self):
        return 7

    def write(self, file, size):
        self.mask = get_mask(size)
        VarAction2Var.write(self, file, size)


# General load and store class for temp parameters
# Register is allocated at the store operation
class VarAction2StoreTempVar(VarAction2Var):
    def __init__(self):
        VarAction2Var.__init__(self, 0x1A, 0, 0)
        # mask holds the number, it's resolved in Action2Var.resolve_tmp_storage
        self.load_vars = []

    def set_register(self, register):
        self.mask = register
        for load_var in self.load_vars:
            load_var.parameter = register

    def get_size(self):
        return 6


def get_mask(size):
    if size == 1:
        return 0xFF
    elif size == 2:
        return 0xFFFF
    return 0xFFFFFFFF


class VarAction2LoadTempVar(VarAction2Var, expression.Expression):
    def __init__(self, tmp_var):
        VarAction2Var.__init__(self, 0x7D, 0, 0)
        expression.Expression.__init__(self, None)
        assert isinstance(tmp_var, VarAction2StoreTempVar)
        tmp_var.load_vars.append(self)

    def write(self, file, size):
        self.mask = get_mask(size)
        VarAction2Var.write(self, file, size)

    def get_size(self):
        return 7

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        assert not raise_error
        return False


# Temporary load and store classes used for spritelayout parameters
# Register is allocated in a separate entity
class VarAction2CallParam:
    def __init__(self, name):
        self.register = None
        self.store_vars = []
        self.load_vars = []
        self.name = name

    def set_register(self, register):
        self.register = register
        for store_var in self.store_vars:
            store_var.mask = register
        for load_var in self.load_vars:
            load_var.parameter = register


class VarAction2LoadCallParam(VarAction2Var, expression.Expression):
    def __init__(self, param, name):
        assert isinstance(param, VarAction2CallParam)
        VarAction2Var.__init__(self, 0x7D, 0, 0, comment=param.name)
        expression.Expression.__init__(self, None)
        assert isinstance(param, VarAction2CallParam)
        param.load_vars.append(self)
        self.name = name
        # Register is stored in parameter

    def write(self, file, size):
        self.mask = get_mask(size)
        VarAction2Var.write(self, file, size)

    def get_size(self):
        return 7

    def reduce(self, id_dicts=None, unknown_id_fatal=True):
        return self

    def supported_by_action2(self, raise_error):
        return True

    def supported_by_actionD(self, raise_error):
        assert not raise_error
        return False

    def __str__(self):
        return self.name


class VarAction2StoreCallParam(VarAction2Var):
    def __init__(self, param):
        VarAction2Var.__init__(self, 0x1A, 0, 0)
        assert isinstance(param, VarAction2CallParam)
        param.store_vars.append(self)
        # Register is stored in mask

    def get_size(self):
        return 6


class VarAction2Range:
    def __init__(self, min, max, result, comment):
        self.min = min
        self.max = max
        self.result = result
        self.comment = comment


class Modification:
    def __init__(self, param, size, offset):
        self.param = param
        self.size = size
        self.offset = offset


class Varaction2Parser:
    def __init__(self, action_feature, var_scope):
        self.action_feature = action_feature
        self.var_scope = var_scope  # Depends on action_feature and var_range
        self.extra_actions = []
        self.mods = []
        self.var_list = []
        self.var_list_size = 0
        self.proc_call_list = []

    def preprocess_binop(self, expr):
        """
        Several nml operators are not directly support by nfo so we have to work
        around that by implementing those operators in terms of others.

        @return: A pre-processed version of the expression.
        @rtype:  L{Expression}
        """
        assert isinstance(expr, expression.BinOp)
        if expr.op == nmlop.CMP_LT:
            # return value is 0, 1 or 2, we want to map 0 to 1 and the others to 0
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            # reduce the problem to 0/1
            expr = nmlop.MIN(expr, 1)
            # and invert the result
            expr = nmlop.XOR(expr, 1)
        elif expr.op == nmlop.CMP_GT:
            # return value is 0, 1 or 2, we want to map 2 to 1 and the others to 0
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            # subtract one
            expr = nmlop.SUB(expr, 1)
            # map -1 and 0 to 0
            expr = nmlop.MAX(expr, 0)
        elif expr.op == nmlop.CMP_LE:
            # return value is 0, 1 or 2, we want to map 2 to 0 and the others to 1
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            # swap 0 and 2
            expr = nmlop.XOR(expr, 2)
            # map 1/2 to 1
            expr = nmlop.MIN(expr, 1)
        elif expr.op == nmlop.CMP_GE:
            # return value is 0, 1 or 2, we want to map 1/2 to 1
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            expr = nmlop.MIN(expr, 1)
        elif expr.op == nmlop.CMP_EQ:
            # return value is 0, 1 or 2, we want to map 1 to 1, other to 0
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            expr = nmlop.AND(expr, 1)
        elif expr.op == nmlop.CMP_NEQ:
            # same as CMP_EQ but invert the result
            expr = nmlop.VACT2_CMP(expr.expr1, expr.expr2)
            expr = nmlop.AND(expr, 1)
            expr = nmlop.XOR(expr, 1)

        elif expr.op == nmlop.HASBIT:
            # hasbit(x, n) ==> (x >> n) & 1
            expr = nmlop.SHIFTU_RIGHT(expr.expr1, expr.expr2)
            expr = nmlop.AND(expr, 1)
        elif expr.op == nmlop.NOTHASBIT:
            # !hasbit(x, n) ==> ((x >> n) & 1) ^ 1
            expr = nmlop.SHIFTU_RIGHT(expr.expr1, expr.expr2)
            expr = nmlop.AND(expr, 1)
            expr = nmlop.XOR(expr, 1)

        return expr.reduce()

    def preprocess_ternaryop(self, expr):
        assert isinstance(expr, expression.TernaryOp)
        guard = expression.Boolean(expr.guard).reduce()
        self.parse(guard)
        if isinstance(expr.expr1, expression.ConstantNumeric) and isinstance(expr.expr2, expression.ConstantNumeric):
            # This can be done more efficiently as (guard)*(expr1-expr2) + expr2
            self.var_list.append(nmlop.MUL)
            diff_var = VarAction2Var(0x1A, 0, expr.expr1.value - expr.expr2.value)
            diff_var.comment = "expr1 - expr2"
            self.var_list.append(diff_var)
            self.var_list.append(nmlop.ADD)
            # Add var sizes, +2 for the operators
            self.var_list_size += 2 + diff_var.get_size()
            return expr.expr2
        else:
            if not expr.is_read_only() and guard.is_read_only():
                generic.print_warning(
                    generic.Warning.GENERIC, "Ternary operator may have unexpected side effects", expr.pos
                )
            guard_var = VarAction2StoreTempVar()
            guard_var.comment = "guard"
            inverted_guard_var = VarAction2StoreTempVar()
            inverted_guard_var.comment = "!guard"
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(guard_var)
            self.var_list.append(nmlop.XOR)
            var = VarAction2Var(0x1A, 0, 1)
            self.var_list.append(var)
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(inverted_guard_var)
            self.var_list.append(nmlop.VAL2)
            # the +4 is for the 4 operators added above (STO_TMP, XOR, STO_TMP, VAL2)
            self.var_list_size += 4 + guard_var.get_size() + inverted_guard_var.get_size() + var.get_size()
            expr1 = nmlop.MUL(expr.expr1, VarAction2LoadTempVar(guard_var))
            expr2 = nmlop.MUL(expr.expr2, VarAction2LoadTempVar(inverted_guard_var))
            return nmlop.ADD(expr1, expr2)

    def preprocess_storageop(self, expr):
        assert isinstance(expr, expression.StorageOp)
        if expr.info["perm"] and not self.var_scope.has_persistent_storage:
            raise generic.ScriptError(
                "Persistent storage is not supported for feature '{}'".format(self.var_scope.name),
                expr.pos,
            )

        if expr.info["store"]:
            op = nmlop.STO_PERM if expr.info["perm"] else nmlop.STO_TMP
            ret = expression.BinOp(op, expr.value, expr.register, expr.pos)
        else:
            var_num = 0x7C if expr.info["perm"] else 0x7D
            ret = expression.Variable(expression.ConstantNumeric(var_num), param=expr.register, pos=expr.pos)

        if expr.info["perm"] and self.var_scope is action2var_variables.scope_towns:
            # store grfid in register 0x100 for town persistent storage
            grfid = expression.ConstantNumeric(
                0xFFFFFFFF if expr.grfid is None else expression.parse_string_to_dword(expr.grfid)
            )
            store_op = nmlop.STO_TMP(grfid, 0x100, expr.pos)
            ret = nmlop.VAL2(store_op, ret)
        elif expr.grfid is not None:
            raise generic.ScriptError("Specifying a grfid is only possible for town persistent storage.", expr.pos)
        return ret

    def parse_expr_to_constant(self, expr, offset):
        if isinstance(expr, expression.ConstantNumeric):
            return expr.value

        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
        self.extra_actions.extend(tmp_param_actions)
        self.mods.append(Modification(tmp_param, 4, self.var_list_size + offset))
        return 0

    def parse_variable(self, expr):
        """
        Parse a variable in an expression.

        @param expr:
        @type  expr: L{expression.Variable}
        """
        if not isinstance(expr.num, expression.ConstantNumeric):
            raise generic.ScriptError("Variable number must be a constant number", expr.pos)
        if not (expr.param is None or isinstance(expr.param, expression.ConstantNumeric)):
            raise generic.ScriptError("Variable parameter must be a constant number", expr.pos)

        if len(expr.extra_params) > 0:
            first_var = len(self.var_list) == 0
            backup_op = None
            value_backup = None
            if not first_var:
                backup_op = self.var_list.pop()
                value_backup = VarAction2StoreTempVar()
                self.var_list.append(nmlop.STO_TMP)
                self.var_list.append(value_backup)
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += value_backup.get_size() + 1

            # Last value == 0, and this is right before we're going to use
            # the extra parameters. Set them to their correct value here.
            for extra_param in expr.extra_params:
                self.parse(extra_param[1])
                self.var_list.append(nmlop.STO_TMP)
                var = VarAction2Var(0x1A, 0, extra_param[0])
                self.var_list.append(var)
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += var.get_size() + 2

            if not first_var:
                value_loadback = VarAction2LoadTempVar(value_backup)
                self.var_list.append(value_loadback)
                self.var_list.append(backup_op)
                self.var_list_size += value_loadback.get_size() + 1

        if expr.param is None:
            offset = 2
            param = None
        else:
            offset = 3
            param = expr.param.value
        mask = self.parse_expr_to_constant(expr.mask, offset)

        var = VarAction2Var(expr.num.value, expr.shift.value, mask, param)

        if expr.add is not None:
            var.add = self.parse_expr_to_constant(expr.add, offset + 4)
        if expr.div is not None:
            var.div = self.parse_expr_to_constant(expr.div, offset + 8)
        if expr.mod is not None:
            var.mod = self.parse_expr_to_constant(expr.mod, offset + 8)
        self.var_list.append(var)
        self.var_list_size += var.get_size()

    def parse_not(self, expr):
        self.parse_binop(nmlop.XOR(expr.expr, 1))

    def parse_binop(self, expr):
        if expr.op.act2_num is None:
            expr.supported_by_action2(True)

        if (
            isinstance(expr.expr2, (expression.ConstantNumeric, expression.Variable))
            or isinstance(expr.expr2, (VarAction2LoadTempVar, VarAction2LoadCallParam))
            or (isinstance(expr.expr2, expression.Parameter) and isinstance(expr.expr2.num, expression.ConstantNumeric))
            or expr.op == nmlop.VAL2
        ):
            expr2 = expr.expr2
        elif expr.expr2.supported_by_actionD(False):
            tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr.expr2)
            self.extra_actions.extend(tmp_param_actions)
            expr2 = expression.Parameter(expression.ConstantNumeric(tmp_param))
        else:
            # The expression is so complex we need to compute it first, store the
            # result and load it back later.
            self.parse(expr.expr2)
            tmp_var = VarAction2StoreTempVar()
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(tmp_var)
            self.var_list.append(nmlop.VAL2)
            # the +2 is for both operators
            self.var_list_size += tmp_var.get_size() + 2
            expr2 = VarAction2LoadTempVar(tmp_var)

        # parse expr1
        self.parse(expr.expr1)
        self.var_list.append(expr.op)
        self.var_list_size += 1

        self.parse(expr2)

    def parse_constant(self, expr):
        var = VarAction2Var(0x1A, 0, expr.value)
        self.var_list.append(var)
        self.var_list_size += var.get_size()

    def parse_param(self, expr):
        self.mods.append(Modification(expr.num.value, 4, self.var_list_size + 2))
        var = VarAction2Var(0x1A, 0, 0)
        var.comment = str(expr)
        self.var_list.append(var)
        self.var_list_size += var.get_size()

    def parse_string(self, expr):
        str_id, actions = action4.get_string_action4s(0, 0xD0, expr)
        self.extra_actions.extend(actions)
        self.parse_constant(expression.ConstantNumeric(str_id))

    def parse_via_actionD(self, expr):
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(expr)
        self.extra_actions.extend(tmp_param_actions)
        num = expression.ConstantNumeric(tmp_param)
        self.parse(expression.Parameter(num))

    def parse_proc_call(self, expr):
        assert isinstance(expr, expression.SpriteGroupRef)
        var_access = VarAction2ProcCallVar(expr)
        target = action2.resolve_spritegroup(expr.name)
        refs = expr.collect_references()

        # Fill param registers for the call
        tmp_vars = []
        for i, param in enumerate(expr.param_list):
            if i > 0:  # No operator before first param as per advanced VarAct2 syntax
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += 1
            if refs != [expr]:
                # For f(x, g(y)), x can be overwritten by y if f and g share the same param registers
                # Use temporary variables as an intermediate step
                store_tmp = VarAction2StoreTempVar()
                tmp_vars.append(
                    (
                        VarAction2LoadTempVar(store_tmp),
                        VarAction2StoreCallParam(target.register_map[self.action_feature][i]),
                    )
                )
            else:
                store_tmp = VarAction2StoreCallParam(target.register_map[self.action_feature][i])
            self.parse_expr(reduce_varaction2_expr(param, self.var_scope))
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(store_tmp)
            self.var_list_size += store_tmp.get_size() + 1  # Add 1 for operator

        # Fill param registers with temporary variables if needed
        for (src, dest) in tmp_vars:
            self.var_list.append(nmlop.VAL2)
            self.var_list.append(src)
            self.var_list.append(nmlop.STO_TMP)
            self.var_list.append(dest)
            self.var_list_size += src.get_size() + dest.get_size() + 2  # Add 2 for operators

        if expr.param_list:
            self.var_list.append(nmlop.VAL2)
            self.var_list_size += 1
        self.var_list.append(var_access)
        self.var_list_size += var_access.get_size()
        self.proc_call_list.append(expr)

    def parse_expr(self, expr):
        if isinstance(expr, expression.Array):
            if len(expr.values) == 0:
                raise generic.ScriptError("An array of expressions cannot be empty", expr.pos)
            for expr2 in expr.values:
                self.parse(expr2)
                self.var_list.append(nmlop.VAL2)
                self.var_list_size += 1
            # Drop the trailing VAL2 again
            self.var_list.pop()
            self.var_list_size -= 1
        else:
            self.parse(expr)

    def parse(self, expr):
        # Preprocess the expression
        if isinstance(expr, expression.SpecialParameter):
            # do this first, since it may evaluate to a BinOp
            expr = expr.to_reading()

        if isinstance(expr, expression.BinOp):
            expr = self.preprocess_binop(expr)

        elif isinstance(expr, expression.Boolean):
            expr = nmlop.MINU(expr.expr, 1)

        elif isinstance(expr, expression.BinNot):
            expr = nmlop.XOR(expr.expr, 0xFFFFFFFF)

        elif isinstance(expr, expression.TernaryOp) and not expr.supported_by_actionD(False):
            expr = self.preprocess_ternaryop(expr)

        elif isinstance(expr, expression.StorageOp):
            expr = self.preprocess_storageop(expr)

        # Try to parse the expression to a list of variables+operators
        if isinstance(expr, expression.ConstantNumeric):
            self.parse_constant(expr)

        elif isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
            self.parse_param(expr)

        elif isinstance(expr, expression.Variable):
            self.parse_variable(expr)

        elif expr.supported_by_actionD(False):
            self.parse_via_actionD(expr)

        elif isinstance(expr, expression.BinOp):
            self.parse_binop(expr)

        elif isinstance(expr, expression.Not):
            self.parse_not(expr)

        elif isinstance(expr, expression.String):
            self.parse_string(expr)

        elif isinstance(expr, (VarAction2LoadTempVar, VarAction2LoadCallParam)):
            self.var_list.append(expr)
            self.var_list_size += expr.get_size()

        elif isinstance(expr, expression.SpriteGroupRef):
            self.parse_proc_call(expr)

        else:
            expr.supported_by_action2(True)
            raise AssertionError("supported_by_action2 should have raised the correct error already")


def parse_var(name, info, pos):
    if "replaced_by" in info:
        generic.print_warning(
            generic.Warning.DEPRECATION,
            "'{}' is deprecated, consider using '{}' instead".format(name, info["replaced_by"]),
            pos,
        )
    param = expression.ConstantNumeric(info["param"]) if "param" in info else None
    res = expression.Variable(
        expression.ConstantNumeric(info["var"]),
        expression.ConstantNumeric(info["start"]),
        expression.ConstantNumeric((1 << info["size"]) - 1),
        param,
        pos,
    )
    if "value_function" in info:
        return info["value_function"](res, info)
    return res


def parse_60x_var(name, args, pos, info):
    if "param_function" in info:
        # Special function to extract parameters if there is more than one
        param, extra_params = info["param_function"](name, args, pos, info)
    else:
        # Default function to extract parameters
        param, extra_params = action2var_variables.default_60xvar(name, args, pos, info)

    if isinstance(param, expression.ConstantNumeric) and (0 <= param.value <= 255):
        res = expression.Variable(
            expression.ConstantNumeric(info["var"]),
            expression.ConstantNumeric(info["start"]),
            expression.ConstantNumeric((1 << info["size"]) - 1),
            param,
            pos,
        )

        res.extra_params.extend(extra_params)
    else:
        # Make use of var 7B to pass non-constant parameters
        var = expression.Variable(
            expression.ConstantNumeric(0x7B),
            expression.ConstantNumeric(info["start"]),
            expression.ConstantNumeric((1 << info["size"]) - 1),
            expression.ConstantNumeric(info["var"]),
            pos,
        )

        var.extra_params.extend(extra_params)
        # Set the param in the accumulator beforehand
        res = nmlop.VAL2(param, var, pos)

    if "value_function" in info:
        res = info["value_function"](res, info)
    return res


def parse_minmax(value, unit_str, action_list, act6, offset):
    """
    Parse a min or max value in a switch block.

    @param value: Value to parse
    @type value: L{Expression}

    @param unit_str: Unit to use
    @type unit_str: C{str} or C{None}

    @param action_list: List to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param act6: Action6 to add any modifications to
    @type act6: L{Action6}

    @param offset: Current offset to use for action6
    @type offset: C{int}

    @return: A tuple of two values:
                - The value to use as min/max
                - Whether the resulting range may need a sanity check
    @rtype: C{tuple} of (L{ConstantNumeric} or L{SpriteGroupRef}), C{bool}
    """
    if unit_str is not None:
        raise generic.ScriptError("Using a unit is in switch-ranges is not (temporarily) not supported", value.pos)
    result, offset = actionD.write_action_value(value, action_list, act6, offset, 4)
    check_range = isinstance(value, expression.ConstantNumeric)
    return (result, offset, check_range)


return_action_id = 0


def create_return_action(expr, feature, name, var_range):
    """
    Create a varaction2 to return the computed value

    @param expr: Expression to return
    @type expr: L{Expression}

    @param feature: Feature of the switch-block
    @type feature: C{int}

    @param name: Name of the new varaction2
    @type name: C{str}

    @return: A tuple of two values:
                - Action list to prepend
                - Reference to the created varaction2
    @rtype: C{tuple} of (C{list} of L{BaseAction}, L{SpriteGroupRef})
    """
    varact2parser = Varaction2Parser(feature, get_scope(feature, var_range))
    varact2parser.parse_expr(expr)

    action_list = varact2parser.extra_actions
    extra_act6 = action6.Action6()
    for mod in varact2parser.mods:
        extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
    if len(extra_act6.modifications) > 0:
        action_list.append(extra_act6)

    varaction2 = Action2Var(feature, name, expr.pos, var_range)
    varaction2.var_list = varact2parser.var_list
    varaction2.default_result = expression.ConstantNumeric(0)  # Bogus result, it's the nvar == 0 that matters
    varaction2.default_comment = "Return computed value"

    for proc in varact2parser.proc_call_list:
        action2.add_ref(proc, varaction2, True)

    ref = expression.SpriteGroupRef(expression.Identifier(name), [], None, varaction2)
    action_list.append(varaction2)
    return (action_list, ref)


failed_cb_results = {}


def get_failed_cb_result(feature, action_list, parent_action, pos):
    """
    Get a sprite group reference to use for a failed callback
    The actions needed are created on first use, then cached in L{failed_cb_results}

    @param feature: Feature to use
    @type feature: C{int}

    @param action_list: Action list to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param parent_action: Reference to the action of which this is a result
    @type parent_action: L{BaseAction}

    @param pos: Positional context.
    @type  pos: L{Position}

    @return: Sprite group reference to use
    @rtype: L{SpriteGroupRef}
    """
    if feature in failed_cb_results:
        varaction2 = failed_cb_results[feature]
    else:
        # Create action2 (+ action1, if needed)
        # Import here to avoid circular imports
        from nml.actions import action1, action2layout, action2production, action2real

        if feature == 0x0A:
            # Industries -> production action2
            act2 = action2production.make_empty_production_action2(pos)
        elif feature in (0x07, 0x09, 0x0F, 0x11):
            # Tile layout action2
            act2 = action2layout.make_empty_layout_action2(feature, pos)
        else:
            # Normal action2
            act1_actions, act1_index = action1.make_cb_failure_action1(feature)
            action_list.extend(act1_actions)
            act2 = action2real.make_simple_real_action2(
                feature, "@CB_FAILED_REAL{:02X}".format(feature), pos, act1_index
            )
        action_list.append(act2)

        # Create varaction2, to choose between returning graphics and 0, depending on CB
        varact2parser = Varaction2Parser(feature, get_scope(feature))
        varact2parser.parse_expr(
            expression.Variable(expression.ConstantNumeric(0x0C), mask=expression.ConstantNumeric(0xFFFF))
        )

        varaction2 = Action2Var(feature, "@CB_FAILED{:02X}".format(feature), pos, 0x89)
        varaction2.var_list = varact2parser.var_list

        varaction2.ranges.append(
            VarAction2Range(
                expression.ConstantNumeric(0),
                expression.ConstantNumeric(0),
                expression.ConstantNumeric(0),
                "graphics callback -> return 0",
            )
        )
        varaction2.default_result = expression.SpriteGroupRef(expression.Identifier(act2.name), [], None, act2)
        varaction2.default_comment = "Non-graphics callback, return graphics result"
        action2.add_ref(varaction2.default_result, varaction2)

        action_list.append(varaction2)
        failed_cb_results[feature] = varaction2

    ref = expression.SpriteGroupRef(expression.Identifier(varaction2.name), [], None, varaction2)
    action2.add_ref(ref, parent_action)
    return ref


def parse_sg_ref_result(result, action_list, parent_action, var_range):
    """
    Parse a result that is a sprite group reference.

    @param result: Result to parse
    @type result: L{SpriteGroupRef}

    @param action_list: List to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param parent_action: Reference to the action of which this is a result
    @type parent_action: L{BaseAction}

    @param var_range: Variable range to use for variables in the expression
    @type var_range: C{int}

    @return: Result to use in the calling varaction2
    @rtype: L{SpriteGroupRef}
    """
    if result.name.value == "CB_FAILED":
        return get_failed_cb_result(parent_action.feature, action_list, parent_action, result.pos)

    if len(result.param_list) == 0:
        action2.add_ref(result, parent_action)
        return result

    # Result is parametrized
    # Insert an intermediate varaction2 to store expressions in registers
    var_scope = get_scope(parent_action.feature, var_range)
    varact2parser = Varaction2Parser(parent_action.feature, var_scope)
    layout = action2.resolve_spritegroup(result.name)
    for i, param in enumerate(result.param_list):
        if i > 0:
            varact2parser.var_list.append(nmlop.VAL2)
            varact2parser.var_list_size += 1
        varact2parser.parse_expr(reduce_varaction2_expr(param, var_scope))
        varact2parser.var_list.append(nmlop.STO_TMP)
        store_tmp = VarAction2StoreCallParam(layout.register_map[parent_action.feature][i])
        varact2parser.var_list.append(store_tmp)
        varact2parser.var_list_size += store_tmp.get_size() + 1  # Add 1 for operator

    action_list.extend(varact2parser.extra_actions)
    extra_act6 = action6.Action6()
    for mod in varact2parser.mods:
        extra_act6.modify_bytes(mod.param, mod.size, mod.offset + 4)
    if len(extra_act6.modifications) > 0:
        action_list.append(extra_act6)

    global return_action_id
    name = "@return_action_{:d}".format(return_action_id)
    varaction2 = Action2Var(parent_action.feature, name, result.pos, var_range)
    return_action_id += 1
    varaction2.var_list = varact2parser.var_list
    ref = expression.SpriteGroupRef(result.name, [], result.pos)
    varaction2.ranges.append(
        VarAction2Range(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, result.name.value)
    )
    varaction2.default_result = ref
    varaction2.default_comment = result.name.value
    # Add the references as procs, to make sure, that any intermediate registers
    # are freed at the spritelayout and thus not selected to pass parameters
    # Reference is used twice (range + default) so call add_ref twice
    action2.add_ref(ref, varaction2, True)
    action2.add_ref(ref, varaction2, True)

    ref = expression.SpriteGroupRef(expression.Identifier(name), [], None, varaction2)
    action_list.append(varaction2)
    action2.add_ref(ref, parent_action)

    return ref


def parse_result(value, action_list, act6, offset, parent_action, none_result, var_range, repeat_result=1):
    """
    Parse a result (another switch or CB result) in a switch block.

    @param value: Value to parse
    @type value: L{Expression}

    @param action_list: List to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param act6: Action6 to add any modifications to
    @type act6: L{Action6}

    @param offset: Current offset to use for action6
    @type offset: C{int}

    @param parent_action: Reference to the action of which this is a result
    @type parent_action: L{BaseAction}

    @param none_result: Result to use to return the computed value
    @type none_result: L{Expression}

    @param var_range: Variable range to use for variables in the expression
    @type var_range: C{int}

    @param repeat_result: Repeat any action6 modifying of the next sprite this many times.
    @type repeat_result: C{int}

    @return: A tuple of two values:
                - The value to use as return value
                - Comment to add to this value
    @rtype: C{tuple} of (L{ConstantNumeric} or L{SpriteGroupRef}), C{str}
    """
    if value is None:
        comment = "return;"
        assert none_result is not None
        if isinstance(none_result, expression.SpriteGroupRef):
            result = parse_sg_ref_result(none_result, action_list, parent_action, var_range)
        else:
            result = none_result
    elif isinstance(value, expression.SpriteGroupRef):
        result = parse_sg_ref_result(value, action_list, parent_action, var_range)
        comment = result.name.value + ";"
    elif isinstance(value, expression.ConstantNumeric):
        comment = "return {:d};".format(value.value)
        result = value
        if not (-16384 <= value.value <= 32767):
            msg = (
                "Callback results are limited to -16384..16383 (when the result is a signed number)"
                " or 0..32767 (unsigned), encountered {:d}."
            ).format(value.value)
            raise generic.ScriptError(msg, value.pos)

    elif isinstance(value, expression.String):
        comment = "return {};".format(str(value))
        str_id, actions = action4.get_string_action4s(0, 0xD0, value)
        action_list.extend(actions)
        result = expression.ConstantNumeric(str_id - 0xD000 + 0x8000)
    elif value.supported_by_actionD(False):
        tmp_param, tmp_param_actions = actionD.get_tmp_parameter(nmlop.OR(value, 0x8000).reduce())
        comment = "return param[{:d}];".format(tmp_param)
        action_list.extend(tmp_param_actions)
        for i in range(repeat_result):
            act6.modify_bytes(tmp_param, 2, offset + 2 * i)
        result = expression.ConstantNumeric(0)
    else:
        global return_action_id
        extra_actions, result = create_return_action(
            value, parent_action.feature, "@return_action_{:d}".format(return_action_id), var_range
        )
        return_action_id += 1
        action2.add_ref(result, parent_action)
        action_list.extend(extra_actions)
        comment = "return {}".format(value)
    return (result, comment)


def get_scope(action_feature, var_range=0x89):
    return action2var_variables.varact2features[action_feature].get_scope(var_range)


def reduce_varaction2_expr(expr, var_scope, extra_dicts=None):
    # 'normal' and 60+x variables to use
    vars_normal = var_scope.vars_normal
    vars_60x = var_scope.vars_60x

    def func60x(name, value, pos):
        return expression.FunctionPtr(expression.Identifier(name, pos), parse_60x_var, value)

    id_dicts = (
        (extra_dicts or [])
        + [(action2var_variables.varact2_globalvars, parse_var), (vars_normal, parse_var), (vars_60x, func60x)]
        + global_constants.const_list
    )

    return expr.reduce(id_dicts)


def parse_varaction2(switch_block):
    global return_action_id
    return_action_id = 0

    action6.free_parameters.save()
    act6 = action6.Action6()
    action_list = action2real.create_spriteset_actions(switch_block)

    feature = next(iter(switch_block.feature_set))
    var_scope = get_scope(feature, switch_block.var_range)
    varaction2 = Action2Var(
        feature,
        switch_block.name.value,
        switch_block.pos,
        switch_block.var_range,
        switch_block.register_map[feature],
    )

    expr = reduce_varaction2_expr(switch_block.expr, var_scope)

    offset = 4  # first var

    parser = Varaction2Parser(feature, var_scope)
    parser.parse_expr(expr)
    action_list.extend(parser.extra_actions)
    for mod in parser.mods:
        act6.modify_bytes(mod.param, mod.size, mod.offset + offset)
    varaction2.var_list = parser.var_list
    offset += parser.var_list_size + 1  # +1 for the byte num-ranges
    for proc in parser.proc_call_list:
        action2.add_ref(proc, varaction2, True)

    none_result = None
    if any(
        x is not None and x.value is None
        for x in [r.result for r in switch_block.body.ranges] + [switch_block.body.default]
    ):
        # Computed result is returned in at least one result
        if len(switch_block.body.ranges) == 0:
            # There is only a default, which is 'return computed result', so we're fine
            none_result = expression.ConstantNumeric(0)  # Return value does not matter
        else:
            # Add an extra action to return the computed value
            extra_actions, none_result = create_return_action(
                expression.Variable(expression.ConstantNumeric(0x1C)),
                feature,
                switch_block.name.value + "@return",
                0x89,
            )
            action_list.extend(extra_actions)

    used_ranges = []
    for r in switch_block.body.ranges:
        comment = str(r.min) + " .. " + str(r.max) + ": "

        range_result, range_comment = parse_result(
            r.result.value, action_list, act6, offset, varaction2, none_result, switch_block.var_range
        )
        comment += range_comment
        offset += 2  # size of result

        range_min, offset, check_min = parse_minmax(r.min, r.unit, action_list, act6, offset)
        range_max, offset, check_max = parse_minmax(r.max, r.unit, action_list, act6, offset)

        range_overlap = False
        if check_min and check_max:
            for existing_range in used_ranges:
                if existing_range[0] <= range_min.value and range_max.value <= existing_range[1]:
                    generic.print_warning(
                        generic.Warning.GENERIC,
                        "Range overlaps with existing ranges so it'll never be reached",
                        r.min.pos,
                    )
                    range_overlap = True
                    break
            if not range_overlap:
                used_ranges.append([range_min.value, range_max.value])
                used_ranges.sort()
                i = 0
                while i + 1 < len(used_ranges):
                    if used_ranges[i + 1][0] <= used_ranges[i][1] + 1:
                        used_ranges[i][1] = max(used_ranges[i][1], used_ranges[i + 1][1])
                        used_ranges.pop(i + 1)
                    else:
                        i += 1

        if not range_overlap:
            varaction2.ranges.append(VarAction2Range(range_min, range_max, range_result, comment))

    if len(switch_block.body.ranges) == 0 and (
        switch_block.body.default is None or switch_block.body.default.value is not None
    ):
        # Computed result is not returned, but there are no ranges
        # Add one range, to avoid the nvar == 0 bear trap
        offset += 10
        varaction2.ranges.append(
            VarAction2Range(
                expression.ConstantNumeric(1),
                expression.ConstantNumeric(0),
                expression.ConstantNumeric(0),
                "Bogus range to avoid nvar == 0",
            )
        )

    # Handle default result
    if switch_block.body.default is not None:
        # there is a default value
        default_result = switch_block.body.default.value
    else:
        # Default to CB_FAILED
        default_result = expression.SpriteGroupRef(expression.Identifier("CB_FAILED", None), [], None)

    default, default_comment = parse_result(
        default_result, action_list, act6, offset, varaction2, none_result, switch_block.var_range
    )
    varaction2.default_result = default
    if switch_block.body.default is None:
        varaction2.default_comment = "No default specified -> fail callback"
    elif switch_block.body.default.value is None:
        varaction2.default_comment = "Return computed value"
    else:
        varaction2.default_comment = "default: " + default_comment

    if len(act6.modifications) > 0:
        action_list.append(act6)

    action_list.append(varaction2)
    switch_block.set_action2(varaction2, feature)

    action6.free_parameters.restore()
    return action_list
