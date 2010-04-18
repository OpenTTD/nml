from expression import *
from generic import ScriptError	
from action6 import *

class ActionDOperator:
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

class ActionD:
    def __init__(self, target, param1, op, param2, data = None):
        self.target = target
        self.param1 = param1
        self.op = op
        self.param2 = param2
        self.data = data
    
    def write(self, file):
        file.write("0 0D ")
        self.target.write(file, 1)
        file.write(self.op + " ")
        self.param1.write(file, 1)
        self.param2.write(file, 1)
        if self.data != None: self.data.write(file, 4)
        file.write("\n\n")
    
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
    raise ScriptError("Unsupported operator in parameter assignment: " + str(op))

#returns a (param_num, action_list) tuple.
def get_tmp_parameter(expr):
    param = free_parameters.pop()
    actions = parse_actionD(ParameterAssignment(ConstantNumeric(param), expr))
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
        elif isinstance(expr.expr1, Parameter):
            param1 = expr.expr1.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr1)
            action_list.extend(tmp_param_actions)
            param1 = ConstantNumeric(tmp_param)
        
        # We can use the data only for one for the parameters.
        # If the first parameter uses "data" we need a temp parameter for this one
        if isinstance(expr.expr2, ConstantNumeric) and data == None:
            param2 = ConstantNumeric(0xFF)
            data = expr.expr2
        elif isinstance(expr.expr2, Parameter):
            param2 = expr.expr2.num
        else:
            tmp_param, tmp_param_actions = get_tmp_parameter(expr.expr2)
            action_list.extend(tmp_param_actions)
            param2 = ConstantNumeric(tmp_param)
        
    else: raise ScriptError("Invalid expression in argument assignment")
    
    if len(action6.modifications) > 0: action_list.append(action6)
    
    action_list.append(ActionD(target, param1, op, param2, data))
    free_parameters.extend([item for item in free_parameters_backup if not item in free_parameters])
    return action_list
