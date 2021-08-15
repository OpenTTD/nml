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
from nml.actions import action6, action7, base_action
from nml.ast import base_statement, conditional


class ActionD(base_action.BaseAction):
    """
    ActionD class
    General procedure: target = param1 op param2
    If one of the params is 0xFF, the value of 'data' is read instead.

    @ivar target: Number of the target parameter
    @ivar target: L{ConstantNumeric}

    @ivar param1: Paramter number of the first operand
    @type param1: L{ConstantNumeric}

    @ivar op: (Binary) operator to use.
    @type op: L{Operator}

    @ivar param2: Paramter number of the second operand
    @type param2: L{ConstantNumeric}

    @ivar data: Numerical data that will be used instead of parameter value,
                    if the parameter number is 0xFF. None if n/a.
    @type data: L{ConstantNumeric} or C{None}
    """

    def __init__(self, target, param1, op, param2, data=None):
        self.target = target
        self.param1 = param1
        self.op = op
        self.param2 = param2
        self.data = data

    def write(self, file):
        size = 5
        if self.data is not None:
            size += 4

        # print the statement for easier debugging
        str1 = "param[{}]".format(self.param1) if self.param1.value != 0xFF else str(self.data)
        str2 = "param[{}]".format(self.param2) if self.param2.value != 0xFF else str(self.data)
        str_total = self.op.to_string(str1, str2) if self.op != nmlop.ASSIGN else str1
        file.comment("param[{}] = {}".format(self.target, str_total))

        file.start_sprite(size)
        file.print_bytex(0x0D)
        self.target.write(file, 1)
        file.print_bytex(self.op.actd_num, self.op.actd_str)
        self.param1.write(file, 1)
        self.param2.write(file, 1)
        if self.data is not None:
            self.data.write(file, 4)
        file.newline()
        file.end_sprite()

    def skip_action7(self):
        return False


class ParameterAssignment(base_statement.BaseStatement):
    """
    AST-node for a parameter assignment.
    NML equivalent: param[$num] = $expr;

    @ivar param: Target expression to assign (must evaluate to a parameter)
    @type param: L{Expression}

    @ivar value: Value to assign to this parameter
    @type value: L{Expression}
    """

    def __init__(self, param, value):
        base_statement.BaseStatement.__init__(self, "parameter assignment", param.pos)
        self.param = param
        self.value = value

    def pre_process(self):
        self.value = self.value.reduce(global_constants.const_list)

        self.param = self.param.reduce(global_constants.const_list, unknown_id_fatal=False)
        if isinstance(self.param, expression.SpecialParameter):
            if not self.param.can_assign():
                raise generic.ScriptError(
                    "Trying to assign a value to the read-only variable '{}'".format(self.param.name), self.param.pos
                )
        elif isinstance(self.param, expression.Identifier):
            if global_constants.identifier_refcount[self.param.value] == 0:
                generic.print_warning(
                    generic.Warning.OPTIMISATION,
                    "Named parameter '{}' is not referenced, ignoring.".format(self.param.value),
                    self.param.pos,
                )
                return
            num = action6.free_parameters.pop_unique(self.pos)
            global_constants.named_parameters[self.param.value] = num
        elif not isinstance(self.param, expression.Parameter):
            raise generic.ScriptError("Left side of an assignment must be a parameter.", self.param.pos)

    def debug_print(self, indentation):
        generic.print_dbg(indentation, "Parameter assignment")
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)

    def get_action_list(self):
        return parse_actionD(self)

    def __str__(self):
        return "{} = {};\n".format(self.param, self.value)


# prevent evaluating common sub-expressions multiple times
def parse_subexpression(expr, action_list):
    if isinstance(expr, expression.ConstantNumeric) or (
        isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric)
    ):
        return expr
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(expr)
        action_list.extend(tmp_param_actions)
        return expression.Parameter(expression.ConstantNumeric(tmp_param))


# returns a (param_num, action_list) tuple.
def get_tmp_parameter(expr):
    param = action6.free_parameters.pop(expr.pos)
    actions = parse_actionD(ParameterAssignment(expression.Parameter(expression.ConstantNumeric(param)), expr))
    return (param, actions)


def write_action_value(expr, action_list, act6, offset, size):
    """
    Write a single numeric value that is part of an action
    Possibly use action6 and/or actionD if needed

    @param expr: Expression to write
    @type expr: L{Expression}

    @param action_list: Action list to append any extra actions to
    @type action_list: C{list} of L{BaseAction}

    @param act6: Action6 to append any modifications to
    @type act6: L{Action6}

    @param offset: Offset to use for the action 6 (if applicable)
    @type offset: C{int}

    @param size: Size to use for the action 6 (if applicable)
    @type size: C{int}

    @return: 2-tuple containing -
        - the value to be used when writing the action (0 if overwritten by action 6)
        - the offset just past this numeric value (=offset + size)
    @rtype: C{tuple} of (L{ConstantNumeric}, C{int})
    """
    if isinstance(expr, expression.ConstantNumeric):
        result = expr
    elif isinstance(expr, expression.Parameter) and isinstance(expr.num, expression.ConstantNumeric):
        act6.modify_bytes(expr.num.value, size, offset)
        result = expression.ConstantNumeric(0)
    else:
        tmp_param, tmp_param_actions = get_tmp_parameter(expr)
        action_list.extend(tmp_param_actions)
        act6.modify_bytes(tmp_param, size, offset)
        result = expression.ConstantNumeric(0)
    return result, offset + size


def parse_ternary_op(assignment):
    assert isinstance(assignment.value, expression.TernaryOp)
    actions = parse_actionD(ParameterAssignment(assignment.param, assignment.value.expr2))
    cond_block = conditional.Conditional(
        assignment.value.guard, [ParameterAssignment(assignment.param, assignment.value.expr1)], None
    )
    actions.extend(conditional.ConditionalList([cond_block]).get_action_list())
    return actions


def parse_special_check(assignment):
    check = assignment.value
    assert isinstance(check, expression.SpecialCheck)
    actions = parse_actionD(ParameterAssignment(assignment.param, expression.ConstantNumeric(check.results[0])))

    value = check.value
    if check.mask is not None:
        value &= check.mask
        value += check.mask << 32
        assert check.varsize == 8
    else:
        assert check.varsize <= 4
    actions.append(action7.SkipAction(9, check.varnum, check.varsize, check.op, value, 1))

    actions.extend(parse_actionD(ParameterAssignment(assignment.param, expression.ConstantNumeric(check.results[1]))))
    return actions


def parse_grm(assignment):
    assert isinstance(assignment.value, expression.GRMOp)

    action6.free_parameters.save()
    action_list = []
    act6 = action6.Action6()
    assert isinstance(assignment.param, expression.Parameter)
    target = assignment.param.num
    if isinstance(target, expression.Parameter) and isinstance(target.num, expression.ConstantNumeric):
        act6.modify_bytes(target.num.value, 1, 1)
        target = expression.ConstantNumeric(0)
    elif not isinstance(target, expression.ConstantNumeric):
        tmp_param, tmp_param_actions = get_tmp_parameter(target)
        act6.modify_bytes(tmp_param, 1, 1)
        target = expression.ConstantNumeric(0)
        action_list.extend(tmp_param_actions)

    op = nmlop.ASSIGN
    param1 = assignment.value.op
    param2 = expression.ConstantNumeric(0xFE)
    data = expression.ConstantNumeric(0xFF | (assignment.value.feature << 8) | (assignment.value.count << 16))

    if len(act6.modifications) > 0:
        action_list.append(act6)

    action_list.append(ActionD(target, param1, op, param2, data))
    action6.free_parameters.restore()
    return action_list


def parse_hasbit(assignment):
    assert isinstance(assignment.value, expression.BinOp) and (
        assignment.value.op == nmlop.HASBIT or assignment.value.op == nmlop.NOTHASBIT
    )
    actions = parse_actionD(ParameterAssignment(assignment.param, expression.ConstantNumeric(0)))
    cond_block = conditional.Conditional(
        assignment.value, [ParameterAssignment(assignment.param, expression.ConstantNumeric(1))], None
    )
    actions.extend(conditional.ConditionalList([cond_block]).get_action_list())
    return actions


def parse_min_max(assignment):
    assert isinstance(assignment.value, expression.BinOp) and assignment.value.op in (nmlop.MIN, nmlop.MAX)
    # min(a, b) ==> a < b ? a : b.
    # max(a, b) ==> a > b ? a : b.
    action6.free_parameters.save()
    action_list = []
    expr1 = parse_subexpression(assignment.value.expr1, action_list)
    expr2 = parse_subexpression(assignment.value.expr2, action_list)
    guard = expression.BinOp(nmlop.CMP_LT if assignment.value.op == nmlop.MIN else nmlop.CMP_GT, expr1, expr2)
    action_list.extend(
        parse_actionD(ParameterAssignment(assignment.param, expression.TernaryOp(guard, expr1, expr2, None)))
    )
    action6.free_parameters.restore()
    return action_list


def parse_boolean(assignment):
    assert isinstance(assignment.value, expression.Boolean)
    actions = parse_actionD(ParameterAssignment(assignment.param, expression.ConstantNumeric(0)))
    expr = nmlop.CMP_NEQ(assignment.value.expr, 0)
    cond_block = conditional.Conditional(
        expr, [ParameterAssignment(assignment.param, expression.ConstantNumeric(1))], None
    )
    actions.extend(conditional.ConditionalList([cond_block]).get_action_list())
    return actions


def transform_bin_op(assignment):
    op = assignment.value.op
    expr1 = assignment.value.expr1
    expr2 = assignment.value.expr2
    extra_actions = []

    if op == nmlop.CMP_GE:
        expr1, expr2 = expr2, expr1
        op = nmlop.CMP_LE

    if op == nmlop.CMP_LE:
        extra_actions.extend(parse_actionD(ParameterAssignment(assignment.param, nmlop.SUB(expr1, expr2))))
        op = nmlop.CMP_LT
        expr1 = assignment.param
        expr2 = expression.ConstantNumeric(1)

    if op == nmlop.CMP_GT:
        expr1, expr2 = expr2, expr1
        op = nmlop.CMP_LT

    if op == nmlop.CMP_LT:
        extra_actions.extend(parse_actionD(ParameterAssignment(assignment.param, nmlop.SUB(expr1, expr2))))
        op = nmlop.SHIFTU_LEFT  # shift left by negative number = shift right
        expr1 = assignment.param
        expr2 = expression.ConstantNumeric(-31)

    elif op == nmlop.CMP_NEQ:
        extra_actions.extend(parse_actionD(ParameterAssignment(assignment.param, nmlop.SUB(expr1, expr2))))
        op = nmlop.DIV
        # We rely here on the (ondocumented) behavior of both OpenTTD and TTDPatch
        # that expr/0==expr. What we do is compute A/A, which will result in 1 if
        # A != 0 and in 0 if A == 0
        expr1 = assignment.param
        expr2 = assignment.param

    elif op == nmlop.CMP_EQ:
        # We compute A==B by doing not(A - B) which will result in a value != 0
        # if A is equal to B
        extra_actions.extend(parse_actionD(ParameterAssignment(assignment.param, nmlop.SUB(expr1, expr2))))
        # Clamp the value to 0/1, see above for details
        extra_actions.extend(
            parse_actionD(ParameterAssignment(assignment.param, nmlop.DIV(assignment.param, assignment.param)))
        )
        op = nmlop.SUB
        expr1 = expression.ConstantNumeric(1)
        expr2 = assignment.param

    if op == nmlop.SHIFT_RIGHT or op == nmlop.SHIFTU_RIGHT:
        if isinstance(expr2, expression.ConstantNumeric):
            expr2.value *= -1
        else:
            expr2 = nmlop.SUB(0, expr2)
        op = nmlop.SHIFT_LEFT if op == nmlop.SHIFT_RIGHT else nmlop.SHIFTU_LEFT

    elif op == nmlop.XOR:
        # a ^ b ==> (a | b) - (a & b)
        expr1 = parse_subexpression(expr1, extra_actions)
        expr2 = parse_subexpression(expr2, extra_actions)
        tmp_param1, tmp_action_list1 = get_tmp_parameter(nmlop.OR(expr1, expr2))
        tmp_param2, tmp_action_list2 = get_tmp_parameter(nmlop.AND(expr1, expr2))
        extra_actions.extend(tmp_action_list1)
        extra_actions.extend(tmp_action_list2)
        expr1 = expression.Parameter(expression.ConstantNumeric(tmp_param1))
        expr2 = expression.Parameter(expression.ConstantNumeric(tmp_param2))
        op = nmlop.SUB

    return op, expr1, expr2, extra_actions


def parse_actionD(assignment):
    assignment.value.supported_by_actionD(True)

    if isinstance(assignment.param, expression.SpecialParameter):
        assignment.param, assignment.value = assignment.param.to_assignment(assignment.value)
    elif isinstance(assignment.param, expression.Identifier):
        if global_constants.identifier_refcount[assignment.param.value] == 0:
            # Named parameter is not referenced, ignoring
            return []
        assignment.param = expression.Parameter(
            expression.ConstantNumeric(global_constants.named_parameters[assignment.param.value]), assignment.param.pos
        )
    assert isinstance(assignment.param, expression.Parameter)

    if isinstance(assignment.value, expression.SpecialParameter):
        assignment.value = assignment.value.to_reading()

    if isinstance(assignment.value, expression.TernaryOp):
        return parse_ternary_op(assignment)

    if isinstance(assignment.value, expression.SpecialCheck):
        return parse_special_check(assignment)

    if isinstance(assignment.value, expression.GRMOp):
        return parse_grm(assignment)

    if isinstance(assignment.value, expression.BinOp):
        op = assignment.value.op
        if op == nmlop.HASBIT or op == nmlop.NOTHASBIT:
            return parse_hasbit(assignment)
        elif op == nmlop.MIN or op == nmlop.MAX:
            return parse_min_max(assignment)

    if isinstance(assignment.value, expression.Boolean):
        return parse_boolean(assignment)

    if isinstance(assignment.value, expression.Not):
        expr = nmlop.SUB(1, assignment.value.expr)
        assignment = ParameterAssignment(assignment.param, expr)

    if isinstance(assignment.value, expression.BinNot):
        expr = nmlop.SUB(0xFFFFFFFF, assignment.value.expr)
        assignment = ParameterAssignment(assignment.param, expr)

    action6.free_parameters.save()
    action_list = []
    act6 = action6.Action6()
    assert isinstance(assignment.param, expression.Parameter)
    target = assignment.param.num
    if isinstance(target, expression.Parameter) and isinstance(target.num, expression.ConstantNumeric):
        act6.modify_bytes(target.num.value, 1, 1)
        target = expression.ConstantNumeric(0)
    elif not isinstance(target, expression.ConstantNumeric):
        tmp_param, tmp_param_actions = get_tmp_parameter(target)
        act6.modify_bytes(tmp_param, 1, 1)
        target = expression.ConstantNumeric(0)
        action_list.extend(tmp_param_actions)

    data = None
    # print assignment.value
    if isinstance(assignment.value, expression.ConstantNumeric):
        op = nmlop.ASSIGN
        param1 = expression.ConstantNumeric(0xFF)
        param2 = expression.ConstantNumeric(0)
        data = assignment.value
    elif isinstance(assignment.value, expression.Parameter):
        if isinstance(assignment.value.num, expression.ConstantNumeric):
            op = nmlop.ASSIGN
            param1 = assignment.value.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(assignment.value.num)
            act6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            op = nmlop.ASSIGN
            param1 = expression.ConstantNumeric(0)
        param2 = expression.ConstantNumeric(0)
    elif isinstance(assignment.value, expression.OtherGRFParameter):
        op = nmlop.ASSIGN
        if isinstance(assignment.value.num, expression.ConstantNumeric):
            param1 = assignment.value.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(assignment.value.num)
            act6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            param1 = expression.ConstantNumeric(0)
        param2 = expression.ConstantNumeric(0xFE)
        data = expression.ConstantNumeric(expression.parse_string_to_dword(assignment.value.grfid))
    elif isinstance(assignment.value, expression.PatchVariable):
        op = nmlop.ASSIGN
        param1 = expression.ConstantNumeric(assignment.value.num)
        param2 = expression.ConstantNumeric(0xFE)
        data = expression.ConstantNumeric(0xFFFF)
    elif isinstance(assignment.value, expression.BinOp):
        op, expr1, expr2, extra_actions = transform_bin_op(assignment)
        action_list.extend(extra_actions)

        if isinstance(expr1, expression.ConstantNumeric):
            param1 = expression.ConstantNumeric(0xFF)
            data = expr1
        elif isinstance(expr1, expression.Parameter) and isinstance(expr1.num, expression.ConstantNumeric):
            param1 = expr1.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr1)
            action_list.extend(tmp_param_actions)
            param1 = expression.ConstantNumeric(tmp_param)

        # We can use the data only for one for the parameters.
        # If the first parameter uses "data" we need a temp parameter for this one
        if isinstance(expr2, expression.ConstantNumeric) and data is None:
            param2 = expression.ConstantNumeric(0xFF)
            data = expr2
        elif isinstance(expr2, expression.Parameter) and isinstance(expr2.num, expression.ConstantNumeric):
            param2 = expr2.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr2)
            action_list.extend(tmp_param_actions)
            param2 = expression.ConstantNumeric(tmp_param)

    else:
        raise generic.ScriptError("Invalid expression in argument assignment", assignment.value.pos)

    if len(act6.modifications) > 0:
        action_list.append(act6)

    action_list.append(ActionD(target, param1, op, param2, data))
    action6.free_parameters.restore()
    return action_list
