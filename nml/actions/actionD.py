import nml
from nml.expression import *
from nml import generic
from action6 import *

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
    actions = parse_actionD(nml.ast.ParameterAssignment(ConstantNumeric(param), expr))
    return (param, actions)

def parse_actionD(assignment):
    global free_parameters
    free_parameters_backup = free_parameters[:]
    action_list = []
    action6 = Action6()
    target = assignment.param
    if isinstance(target, Parameter) and isinstance(target.num, ConstantNumeric):
        action6.modify_bytes(target.num.value, 1, 1)
        target = ConstantNumeric(0)
    elif not isinstance(target, ConstantNumeric):
        tmp_param, tmp_param_actions = get_tmp_parameter(target)
        action6.modify_bytes(tmp_param, 1, 1)
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
            action6.modify_bytes(tmp_param, 1, 3)
            action_list.extend(tmp_param_actions)
            op = ActionDOperator.EQUAL
            param1 = ConstantNumeric(0)
        param2 = ConstantNumeric(0)
    elif isinstance(assignment.value, BinOp):
        expr = assignment.value
        op = convert_op_to_actiond(expr.op)

        if isinstance(expr.expr1, ConstantNumeric):
            param1 = ConstantNumeric(0xFF)
            data = expr.expr1
        elif isinstance(expr.expr1, Parameter) and isinstance(expr.expr1.num, ConstantNumeric):
            param1 = expr.expr1.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr1)
            action_list.extend(tmp_param_actions)
            param1 = ConstantNumeric(tmp_param)

        # We can use the data only for one for the parameters.
        # If the first parameter uses "data" we need a temp parameter for this one
        if isinstance(expr.expr2, ConstantNumeric) and data is None:
            param2 = ConstantNumeric(0xFF)
            data = expr.expr2
        elif isinstance(expr.expr2, Parameter) and isinstance(expr.expr2.num, ConstantNumeric):
            param2 = expr.expr2.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr2)
            action_list.extend(tmp_param_actions)
            param2 = ConstantNumeric(tmp_param)

    else: raise generic.ScriptError("Invalid expression in argument assignment")

    if len(action6.modifications) > 0: action_list.append(action6)

    action_list.append(ActionD(target, param1, op, param2, data))
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
