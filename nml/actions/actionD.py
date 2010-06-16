from nml.expression import *
from nml import generic, global_constants
from action6 import *
import nml.ast

class ActionDOperator(object):
    EQUAL = r'\D='
    ADD   = r'\D+'
    SUB   = r'\D-'
    MULU  = r'\Du*'
    MULS  = r'\D*'
    SHFTU = r'\Du<<'
    SHFTS = r'\D<<'
    AND   = r'\D&'
    OR    = r'\D|'
    DIVU  = r'\Du/'
    DIVS  = r'\D/'
    MODU  = r'\Du%'
    MODS  = r'\D%'

actionDoperator_to_num = {
    ActionDOperator.EQUAL: 0,
    ActionDOperator.ADD: 1,
    ActionDOperator.SUB: 2,
    ActionDOperator.MULU: 3,
    ActionDOperator.MULS: 4,
    ActionDOperator.SHFTU: 5,
    ActionDOperator.SHFTS: 6,
    ActionDOperator.AND: 7,
    ActionDOperator.OR: 8,
    ActionDOperator.DIVU: 9,
    ActionDOperator.DIVS: 0x0A,
    ActionDOperator.MODU: 0x0B,
    ActionDOperator.MODS: 0x0C,
}

class ActionD(object):
    def __init__(self, target, param1, op, param2, data = None):
        self.target = target
        self.param1 = param1
        self.op = op
        self.param2 = param2
        self.data = data

    def prepare_output(self):
        pass

    def write(self, file):
        global actionDoperator_to_num
        size = 5
        if self.data is not None: size += 4
        file.print_sprite_size(size)
        file.print_bytex(0x0D)
        self.target.write(file, 1)
        file.print_bytex(actionDoperator_to_num[self.op], self.op)
        self.param1.write(file, 1)
        self.param2.write(file, 1)
        if self.data is not None: self.data.write(file, 4)
        file.newline()
        file.newline()

    def skip_action7(self):
        return False

    def skip_action9(self):
        return True

    def skip_needed(self):
        return True

class ParameterAssignment(object):
    def __init__(self, param, value):
        self.param = param
        self.value = value.reduce(global_constants.const_list + [cargo_numbers])

    def debug_print(self, indentation):
        print indentation*' ' + 'Parameter assignment'
        self.param.debug_print(indentation + 2)
        self.value.debug_print(indentation + 2)

    def get_action_list(self):
        return parse_actionD(self)

    def __str__(self):
        return 'param[%s] = %s;\n' % (str(self.param), str(self.value))

def convert_op_to_actiond(op):
    if op == Operator.ADD: return ActionDOperator.ADD
    if op == Operator.SUB: return ActionDOperator.SUB
    if op == Operator.AND: return ActionDOperator.AND
    if op == Operator.OR: return ActionDOperator.OR
    if op == Operator.MUL: return ActionDOperator.MULS
    if op == Operator.DIV: return ActionDOperator.DIVS
    if op == Operator.MOD: return ActionDOperator.MODS
    raise generic.ScriptError("Unsupported operator in parameter assignment: " + str(op))

#returns a (param_num, action_list) tuple.
def get_tmp_parameter(expr):
    param = free_parameters.pop()
    actions = parse_actionD(ParameterAssignment(ConstantNumeric(param), expr))
    return (param, actions)

def parse_actionD(assignment):
    if isinstance(assignment.value, TernaryOp):
        actions = parse_actionD(ParameterAssignment(assignment.param, assignment.value.expr2))
        cond_block = nml.ast.Conditional(assignment.value.guard, [ParameterAssignment(assignment.param, assignment.value.expr1)])
        actions.extend(cond_block.get_action_list())
        return actions

    global free_parameters
    free_parameters_backup = free_parameters[:]
    action_list = []
    act6 = Action6()
    target = assignment.param
    if isinstance(target, Parameter) and isinstance(target.num, ConstantNumeric):
        act6.modify_bytes(target.num.value, 1, 1)
        target = ConstantNumeric(0)
    elif not isinstance(target, ConstantNumeric):
        tmp_param, tmp_param_actions = get_tmp_parameter(target)
        act6.modify_bytes(tmp_param, 1, 1)
        target = ConstantNumeric(0)
        action_list.extend(tmp_param_actions)

    data = None
    #print assignment.value
    if isinstance(assignment.value, ConstantNumeric):
        op = ActionDOperator.EQUAL
        param1 = ConstantNumeric(0xFF)
        param2 = ConstantNumeric(0)
        data = assignment.value
    elif isinstance(assignment.value, Parameter):
        if isinstance(assignment.value.num, ConstantNumeric):
            op = ActionDOperator.EQUAL
            param1 = assignment.value.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(assignment.value.num)
            act6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            op = ActionDOperator.EQUAL
            param1 = ConstantNumeric(0)
        param2 = ConstantNumeric(0)
    elif isinstance(assignment.value, BinOp):
        op = assignment.value.op
        expr1 = assignment.value.expr1
        expr2 = assignment.value.expr2

        if op == Operator.CMP_GT:
            expr1, expr2 = expr2, expr1
            op = Operator.CMP_LT

        if op == Operator.CMP_LT:
            action_list.extend(parse_actionD(ParameterAssignment(assignment.param, BinOp(Operator.SUB, expr1, expr2))))
            op = ActionDOperator.SHFTU
            expr1 = Parameter(assignment.param)
            expr2 = ConstantNumeric(-31)

        elif op == Operator.CMP_NEQ:
            action_list.extend(parse_actionD(ParameterAssignment(assignment.param, BinOp(Operator.SUB, expr1, expr2))))
            op = ActionDOperator.DIVU
            # We rely here on the (ondocumented) behavior of both OpenTTD and TTDPatch
            # that expr/0==expr. What we do is compute A/A, which will result in 1 if
            # A != 0 and in 0 if A == 0
            expr1 = Parameter(assignment.param)
            expr2 = Parameter(assignment.param)

        elif op == Operator.CMP_EQ:
            # We compute A==B by doing not(A - B) which will result in a value != 0
            # if A is equal to B
            action_list.extend(parse_actionD(ParameterAssignment(assignment.param, BinOp(Operator.SUB, expr1, expr2))))
            # Clamp the value to 0/1, see above for details
            action_list.extend(parse_actionD(ParameterAssignment(assignment.param, BinOp(Operator.DIV, Parameter(assignment.param), Parameter(assignment.param)))))
            op = ActionDOperator.SUB
            expr1 = ConstantNumeric(1)
            expr2 = Parameter(assignment.param)

        else:
            op = convert_op_to_actiond(op)


        if isinstance(expr1, ConstantNumeric):
            param1 = ConstantNumeric(0xFF)
            data = expr1
        elif isinstance(expr1, Parameter) and isinstance(expr1.num, ConstantNumeric):
            param1 = expr1.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr1)
            action_list.extend(tmp_param_actions)
            param1 = ConstantNumeric(tmp_param)

        # We can use the data only for one for the parameters.
        # If the first parameter uses "data" we need a temp parameter for this one
        if isinstance(expr2, ConstantNumeric) and data is None:
            param2 = ConstantNumeric(0xFF)
            data = expr2
        elif isinstance(expr2, Parameter) and isinstance(expr2.num, ConstantNumeric):
            param2 = expr2.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr2)
            action_list.extend(tmp_param_actions)
            param2 = ConstantNumeric(tmp_param)

    else: raise generic.ScriptError("Invalid expression in argument assignment")

    if len(act6.modifications) > 0: action_list.append(act6)

    action_list.append(ActionD(target, param1, op, param2, data))
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
